#    Copyright 2014-2015 ARM Limited
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

import sys
import argparse

from requests import ConnectionError, RequestException

from wlauto import File, ExtensionLoader, Command, settings
from wlauto.core.extension import Extension


REMOTE_ASSETS_URL = 'https://github.com/ARM-software/workload-automation-assets/raw/master/dependencies'


class GetAssetsCommand(Command):
    name = 'get-assets'
    description = '''
    This command downloads external extension dependencies used by Workload Automation.
    Works by first downloading a directory index of the assets, then iterating through
    it to get assets for the specified extensions.
    '''

    # Uses config setting if available otherwise defaults to ARM-software repo
    # Can be overriden with the --url argument
    assets_url = settings.remote_assets_url or REMOTE_ASSETS_URL

    def initialize(self, context):
        self.parser.add_argument('-f', '--force', action='store_true',
                                 help='Always fetch the assets, even if matching versions exist in local cache.')
        self.parser.add_argument('--url', metavar='URL', type=not_empty, default=self.assets_url,
                                 help='''The location from which to download the files. If not provided,
                                 config setting ``remote_assets_url`` will be used if available, else
                                 uses the default REMOTE_ASSETS_URL parameter in the script.''')
        group = self.parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-a', '--all', action='store_true',
                           help='Download assets for all extensions found in the index. Cannot be used with -e.')
        group.add_argument('-e', dest='exts', metavar='EXT', nargs='+', type=not_empty,
                           help='One or more extensions whose assets to download. Cannot be used with --all.')

    def execute(self, args):
        self.logger.debug('Program arguments: {}'.format(vars(args)))
        if args.force:
            self.logger.info('Force-download of assets requested')
        if not args.url:
            self.logger.debug('URL not provided, falling back to default setting in config')
        self.logger.info('Downloading external assets from {}'.format(args.url))

        # Get file index of assets
        ext_loader = ExtensionLoader(packages=settings.extension_packages, paths=settings.extension_paths)
        getter = ext_loader.get_resource_getter('http_assets', None, url=args.url, always_fetch=args.force)
        try:
            getter.index = getter.fetch_index()
        except (ConnectionError, RequestException) as e:
            self.exit_with_error(str(e))
        all_assets = dict()
        for k, v in getter.index.iteritems():
            all_assets[str(k)] = [str(asset['path']) for asset in v]

        # Here we get a list of all extensions present in the current WA installation,
        # and cross-check that against the list of extensions whose assets are requested.
        # The aim is to avoid downloading assets for extensions that do not exist, since
        # WA extensions and asset index can be updated independently and go out of sync.
        all_extensions = [ext.name for ext in ext_loader.list_extensions()]
        assets_to_get = set(all_assets).intersection(all_extensions)
        if args.exts:
            assets_to_get = assets_to_get.intersection(args.exts)
        # Check list is not empty
        if not assets_to_get:
            if args.all:
                self.exit_with_error('Could not find extensions: {}'.format(', '.join(all_assets.keys())))
            else:  # args.exts
                self.exit_with_error('Asset index has no entries for: {}'.format(', '.join(args.exts)))

        # Check out of sync extensions i.e. do not exist in both WA and assets index
        missing = set(all_assets).difference(all_extensions) | set(args.exts or []).difference(all_assets)
        if missing:
            self.logger.warning('Not getting assets for missing extensions: {}'.format(', '.join(missing)))

        # Ideally the extension loader would be used to instantiate, but it does full
        # validation of the extension, like checking connected devices or supported
        # platform(s). This info might be unavailable and is not required to download
        # assets, since they are classified by extension name alone. So instead we use
        # a simple subclass of ``Extension`` providing a valid ``name`` attribute.
        for ext_name in assets_to_get:
            owner = _instantiate(NamedExtension, ext_name)
            self.logger.info('Getting assets for: {}'.format(ext_name))
            for asset in all_assets[ext_name]:
                getter.get(File(owner, asset))  # Download the files

    def exit_with_error(self, message, code=1):
        self.logger.error(message)
        sys.exit(code)


class NamedExtension(Extension):
    def __init__(self, name, **kwargs):
        super(NamedExtension, self).__init__(**kwargs)
        self.name = name


def not_empty(val):
    if val:
        return val
    else:
        raise argparse.ArgumentTypeError('Extension name cannot be blank')


def _instantiate(cls, *args, **kwargs):
    return cls(*args, **kwargs)
