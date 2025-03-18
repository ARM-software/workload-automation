#    Copyright 2013-2018 ARM Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


"""
This module contains the standard set of resource getters used by Workload Automation.

"""
import http.client
import json
import logging
import os
import shutil
import sys

import requests  # type:ignore

from typing import cast, List, Optional, Dict, Any
from typing_extensions import Protocol
from requests.models import Response  # type:ignore
from wa import Parameter, settings, __file__ as _base_filepath
from wa.framework.resource import (ResourceGetter, SourcePriority, NO_ONE, Resource,
                                   File, Executable, ResourceResolver)
from wa.framework.exception import ResourceError
from wa.utils.misc import (ensure_directory_exists as _d, atomic_write_path,
                           ensure_file_directory_exists as _f, sha256, urljoin)
from wa.utils.types import boolean, caseless_string

# Because of use of Enum (dynamic attrs)
# pylint: disable=no-member

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger: logging.Logger = logging.getLogger('resource')


class OwnerProtocol(Protocol):
    name: str
    dependencies_directory: str


def get_by_extension(path: str, ext: str) -> List[str]:
    """
    get files with the specified extension under the path
    """
    if not ext.startswith('.'):
        ext = '.' + ext
    ext = caseless_string(ext)

    found: List[str] = []
    for entry in os.listdir(path):
        entry_ext = os.path.splitext(entry)[1]
        if entry_ext == ext:
            found.append(os.path.join(path, entry))
    return found


def get_generic_resource(resource: Resource, files: List[str]) -> Optional[str]:
    """
    get generic resource
    """
    matches: List[str] = []
    for f in files:
        if resource.match(f):
            matches.append(f)
    if not matches:
        return None
    if len(matches) > 1:
        msg = 'Multiple matches for {}: {}'
        raise ResourceError(msg.format(resource, matches))
    return matches[0]


def get_path_matches(resource: Resource, files: List[str]) -> List[str]:
    """
    get path matches
    """
    matches: List[str] = []
    for f in files:
        if resource.match_path(f):
            matches.append(f)
    return matches


# pylint: disable=too-many-return-statements
def get_from_location(basepath: str, resource: Resource) -> Optional[str]:
    """
    get resource from location
    """
    if resource.kind == 'file':
        path = os.path.join(basepath, cast(File, resource).path)
        if os.path.exists(path):
            return path
    elif resource.kind == 'executable':
        bin_dir = os.path.join(basepath, 'bin', cast(Executable, resource).abi)
        if not os.path.exists(bin_dir):
            return None
        for entry in os.listdir(bin_dir):
            path = os.path.join(bin_dir, entry)
            if resource.match(path):
                return path
    elif resource.kind == 'revent':
        path = os.path.join(basepath, 'revent_files')
        if os.path.exists(path):
            files = get_by_extension(path, resource.kind)
            found_resource = get_generic_resource(resource, files)
            if found_resource:
                return found_resource
        files = get_by_extension(basepath, resource.kind)
        return get_generic_resource(resource, files)
    elif resource.kind in ['apk', 'jar']:
        files = get_by_extension(basepath, resource.kind)
        return get_generic_resource(resource, files)

    return None


class Package(ResourceGetter):

    name: str = 'package'

    def register(self, resolver: ResourceResolver) -> None:
        """
        register the package with resolver
        """
        resolver.register(self.get, SourcePriority.package)

    # pylint: disable=no-self-use
    def get(self, resource: Resource) -> Optional[str]:
        """
        get resource
        """
        if resource.owner == NO_ONE:
            basepath: str = os.path.join(os.path.dirname(_base_filepath), 'assets')
        else:
            modname: str = resource.owner.__module__
            basepath = os.path.dirname(sys.modules[modname].__file__ or '')
        return get_from_location(basepath, resource)


class UserDirectory(ResourceGetter):

    name: str = 'user'

    def register(self, resolver: ResourceResolver) -> None:
        """
        register user directory wiht the resolver
        """
        resolver.register(self.get, SourcePriority.local)

    # pylint: disable=no-self-use
    def get(self, resource: Resource) -> Optional[str]:
        """
        get resource
        """
        basepath: str = settings.dependencies_directory
        directory: str = _d(os.path.join(basepath, cast(OwnerProtocol, resource.owner).name))
        return get_from_location(directory, resource)


class HttpProtocol(Protocol):
    name: str
    description: str
    url: str
    username: str
    password: str
    always_fetch: bool
    chunk_size: int
    logger: logging.Logger
    index: Dict


class Http(ResourceGetter):

    name: str = 'http'
    description: str = """
    Downloads resources from a server based on an index fetched from the
    specified URL.

    Given a URL, this will try to fetch ``<URL>/index.json``. The index file
    maps extension names to a list of corresponing asset descriptons. Each
    asset description continas a path (relative to the base URL) of the
    resource and a SHA256 hash, so that this Getter can verify whether the
    resource on the remote has changed.

    For example, let's assume we want to get the APK file for workload "foo",
    and that assets are hosted at ``http://example.com/assets``. This Getter
    will first try to donwload ``http://example.com/assests/index.json``. The
    index file may contian something like ::

        {
            "foo": [
                {
                    "path": "foo-app.apk",
                    "sha256": "b14530bb47e04ed655ac5e80e69beaa61c2020450e18638f54384332dffebe86"
                },
                {
                    "path": "subdir/some-other-asset.file",
                    "sha256": "48d9050e9802246d820625717b72f1c2ba431904b8484ca39befd68d1dbedfff"
                }
            ]
        }

    This Getter will look through the list of assets for "foo" (in this case,
    two) check the paths until it finds one matching the resource (in this
    case, "foo-app.apk").  Finally, it will try to dowload that file relative
    to the base URL and extension name (in this case,
    "http://example.com/assets/foo/foo-app.apk"). The downloaded version will
    be cached locally, so that in the future, the getter will check the SHA256
    hash of the local file against the one advertised inside index.json, and
    provided that hasn't changed, it won't try to download the file again.

    """
    parameters: List[Parameter] = [
        Parameter('url', global_alias='remote_assets_url',
                  description="""
                  URL of the index file for assets on an HTTP server.
                  """),
        Parameter('username',
                  description="""
                  User name for authenticating with assets URL
                  """),
        Parameter('password',
                  description="""
                  Password for authenticationg with assets URL
                  """),
        Parameter('always_fetch', kind=boolean, default=False,
                  global_alias='always_fetch_remote_assets',
                  description="""
                  If ``True``, will always attempt to fetch assets from the
                  remote, even if a local cached copy is available.
                  """),
        Parameter('chunk_size', kind=int, default=1024,
                  description="""
                  Chunk size for streaming large assets.
                  """),
    ]

    def __init__(self, **kwargs) -> None:
        super(Http, self).__init__(**kwargs)
        self.logger = logger
        self.index: Dict[str, Dict] = {}

    def register(self, resolver: ResourceResolver) -> None:
        """
        register Http with resolver
        """
        resolver.register(self.get, SourcePriority.remote)

    def get(self, resource: Resource) -> Optional[str]:
        """
        get resource
        """
        if not resource.owner:
            return None  # TODO: add support for unowned resources
        if not self.index:
            try:
                self.index = self.fetch_index()
            except requests.exceptions.RequestException as e:
                msg = 'Skipping HTTP getter due to connection error: {}'
                self.logger.debug(msg.format(str(e)))
                return None
        if resource.kind == 'apk':
            # APKs must always be downloaded to run ApkInfo for version
            # information.
            return self.resolve_apk(resource)
        else:
            asset = self.resolve_resource(resource)
            if not asset:
                return None
            return self.download_asset(asset, cast(OwnerProtocol, resource.owner).name)

    def fetch_index(self) -> Dict:
        """
        fetch index page
        """
        if not cast(HttpProtocol, self).url:
            return {}
        index_url: str = urljoin(cast(HttpProtocol, self).url, 'index.json')
        response: Response = self.geturl(index_url)
        if response.status_code != http.client.OK:
            message: str = 'Could not fetch "{}"; received "{} {}"'
            self.logger.error(message.format(index_url,
                                             response.status_code,
                                             response.reason))
            return {}
        content = response.content.decode('utf-8')
        return json.loads(content)

    def download_asset(self, asset: Dict[str, Any], owner_name: str) -> Optional[str]:
        """
        download asset
        """
        url: str = urljoin(cast(HttpProtocol, self).url, owner_name, asset['path'])
        local_path: str = _f(os.path.join(settings.dependencies_directory, '__remote',
                                          owner_name, asset['path'].replace('/', os.sep)))

        if os.path.exists(local_path) and not self.always_fetch:
            local_sha: str = sha256(local_path)
            if local_sha == asset['sha256']:
                self.logger.debug('Local SHA256 matches; not re-downloading')
                return local_path
        self.logger.debug('Downloading {}'.format(url))
        response: Response = self.geturl(url, stream=True)
        if response.status_code != http.client.OK:
            message: str = 'Could not download asset "{}"; received "{} {}"'
            self.logger.warning(message.format(url,
                                               response.status_code,
                                               response.reason))
            return None
        with atomic_write_path(local_path) as at_path:
            with open(at_path, 'wb') as wfh:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    wfh.write(chunk)
        return local_path

    def geturl(self, url: str, stream: bool = False) -> Response:
        """
        get response from url request via http
        """
        if cast(HttpProtocol, self).username:
            auth = (cast(HttpProtocol, self).username, cast(HttpProtocol, self).password)
        else:
            auth = None
        return requests.get(url, auth=auth, stream=stream)

    def resolve_apk(self, resource: Resource) -> Optional[str]:
        """
        resolve apk
        """
        assets: Dict = self.index.get(cast(OwnerProtocol, resource.owner).name, {})
        if not assets:
            return None
        asset_map: Dict = {a['path']: a for a in assets}
        paths: List[str] = get_path_matches(resource, list(asset_map.keys()))
        local_paths: List[Optional[str]] = []
        for path in paths:
            local_paths.append(self.download_asset(asset_map[path],
                                                   cast(OwnerProtocol, resource.owner).name))
        for path in cast(List[str], local_paths):
            if resource.match(path):
                return path
        return None

    def resolve_resource(self, resource: Resource) -> Optional[Dict]:
        """
        resolve resource
        """
        # pylint: disable=too-many-branches,too-many-locals
        assets: Dict = self.index.get(cast(OwnerProtocol, resource.owner).name, {})
        if not assets:
            return {}

        asset_map: Dict = {a['path']: a for a in assets}
        if resource.kind in ['jar', 'revent']:
            path: Optional[str] = get_generic_resource(resource, list(asset_map.keys()))
            if path:
                return asset_map[path]
        elif resource.kind == 'executable':
            path = '/'.join(['bin', cast(Executable, resource).abi, cast(Executable, resource).filename])
            for asset in assets:
                if asset['path'].lower() == path.lower():
                    return asset
        else:  # file
            for asset in assets:
                if asset['path'].lower() == cast(File, resource).path.lower():
                    return asset
        return None


class FilerProtocol(Protocol):
    name: str
    description: str
    remote_path: str
    always_fetch: bool


class Filer(ResourceGetter):

    name: str = 'filer'
    description: str = """
    Finds resources on a (locally mounted) remote filer and caches them
    locally.

    This assumes that the filer is mounted on the local machine (e.g. as a
    samba share).

    """
    parameters: List[Parameter] = [
        Parameter('remote_path', global_alias='remote_assets_path',
                  default=settings.assets_repository,
                  description="""
                  Path, on the local system, where the assets are located.
                  """),
        Parameter('always_fetch', kind=boolean, default=False,
                  global_alias='always_fetch_remote_assets',
                  description="""
                  If ``True``, will always attempt to fetch assets from the
                  remote, even if a local cached copy is available.
                  """),
    ]

    def register(self, resolver: ResourceResolver) -> None:
        """
        register Filer with resource resolver
        """
        resolver.register(self.get, SourcePriority.lan)

    def get(self, resource: Resource) -> Optional[str]:
        """
        get filer
        """
        remote_path: str = ''
        if resource.owner:
            remote_path = os.path.join(cast(FilerProtocol, self).remote_path, cast(OwnerProtocol, resource.owner).name)
            local_path: str = os.path.join(settings.dependencies_directory, '__filer',
                                           cast(OwnerProtocol, resource.owner).dependencies_directory)
            return self.try_get_resource(resource, remote_path, local_path)
        else:  # No owner
            result: Optional[str] = None
            for entry in os.listdir(remote_path):
                remote_path = os.path.join(self.remote_path, entry)
                local_path = os.path.join(settings.dependencies_directory, '__filer',
                                          settings.dependencies_directory, entry)
                result = self.try_get_resource(resource, remote_path, local_path)
                if result:
                    break
            return result

    def try_get_resource(self, resource: Resource, remote_path: str,
                         local_path: str) -> Optional[str]:
        """
        try get resource
        """
        if not cast(FilerProtocol, self).always_fetch:
            result: Optional[str] = get_from_location(local_path, resource)
            if result:
                return result
        if not os.path.exists(local_path):
            return None
        if os.path.exists(remote_path):
            # Didn't find it cached locally; now check the remoted
            result = get_from_location(remote_path, resource)
            if not result:
                return result
        else:  # remote path is not set
            return None
        # Found it remotely, cache locally, then return it
        local_full_path: str = os.path.join(_d(local_path), os.path.basename(result))
        self.logger.debug('cp {} {}'.format(result, local_full_path))
        shutil.copy(result, local_full_path)
        return result
