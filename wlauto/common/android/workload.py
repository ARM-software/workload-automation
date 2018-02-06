#    Copyright 2013-2015 ARM Limited
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

import os
import sys
import time

from distutils.version import LooseVersion

from wlauto.core.extension import Parameter, ExtensionMeta, ListCollection
from wlauto.core.workload import Workload
from wlauto.common.android.resources import ApkFile
from wlauto.common.resources import ExtensionAsset, File
from wlauto.exceptions import WorkloadError, ResourceError, DeviceError
from wlauto.utils.android import (ApkInfo, ANDROID_NORMAL_PERMISSIONS,
                                  ANDROID_UNCHANGEABLE_PERMISSIONS, UNSUPPORTED_PACKAGES)
from wlauto.utils.types import boolean, ParameterDict
import wlauto.utils.statedetect as state_detector
from wlauto.common.linux.workload import ReventWorkload


DELAY = 5


# Due to the way `super` works you have to call it at every level but WA executes some
# methods conditionally and so has to call them directly via the class, this breaks super
# and causes it to run things mutiple times ect. As a work around for this untill workloads
# are reworked everything that subclasses workload calls parent methods explicitly


class UiAutomatorWorkload(Workload):
    """
    Base class for all workloads that rely on a UI Automator APK file.

    This class should be subclassed by workloads that rely on android UiAutomator
    to work. This class handles installing the UI Automator APK to the device
    and invoking it to run the workload. By default, it will look for the ``*.apk`` file
    in the same directory as the .py file for the workload (this can be changed by overriding
    the ``uiauto_file`` property in the subclassing workload).

    To inintiate UI Automation, the fully-qualified name of the Java class and the
    corresponding method name are needed. By default, the package part of the class name
    is derived from the class file, and class and method names are ``UiAutomation``
    and ``runUiAutomaton`` respectively. If you have generated the boilder plate for the
    UiAutomatior code using ``create_workloads`` utility, then everything should be named
    correctly. If you're creating the Java project manually, you need to make sure the names
    match what is expected, or you could override ``uiauto_package``, ``uiauto_class`` and
    ``uiauto_method`` class attributes with the value that match your Java code.

    You can also pass parameters to the APK file. To do this add the parameters to
    ``self.uiauto_params`` dict inside your class's ``__init__`` or ``setup`` methods.

    """

    supported_platforms = ['android']

    uiauto_package = ''
    uiauto_class = 'UiAutomation'
    uiauto_method = 'android.support.test.runner.AndroidJUnitRunner'
    # Can be overidden by subclasses to adjust to run time of specific
    # benchmarks.
    run_timeout = 10 * 60  # seconds
    uninstall_uiauto_apk = True

    def __init__(self, device, _call_super=True, **kwargs):  # pylint: disable=W0613
        if _call_super:
            Workload.__init__(self, device, **kwargs)
        self.uiauto_file = None
        self.command = None
        self.uiauto_params = ParameterDict()

    def init_resources(self, context):
        self.uiauto_file = context.resolver.get(ApkFile(self, uiauto=True))
        if not self.uiauto_file:
            raise ResourceError('No UI automation APK file found for workload {}.'.format(self.name))

        if not self.uiauto_package:
            self.uiauto_package = os.path.splitext(os.path.basename(self.uiauto_file))[0]

    def setup(self, context):
        Workload.setup(self, context)
        params_dict = self.uiauto_params
        params_dict['workdir'] = self.device.working_directory
        params = ''
        for k, v in self.uiauto_params.iter_encoded_items():
            params += ' -e {} "{}"'.format(k, v)

        if self.device.package_is_installed(self.uiauto_package):
            self.device.uninstall(self.uiauto_package)
        self.device.install_apk(self.uiauto_file)

        instrumention_string = 'am instrument -w -r {}  -e class {}.{} {}/{}'
        self.command = instrumention_string.format(params, self.uiauto_package,
                                                   self.uiauto_class, self.uiauto_package,
                                                   self.uiauto_method)
        self.device.killall('uiautomator')

    def run(self, context):
        result = self.device.execute(self.command, self.run_timeout)
        if 'FAILURE' in result:
            raise WorkloadError(result)
        else:
            self.logger.debug(result)
        time.sleep(DELAY)

    def update_result(self, context):
        pass

    def teardown(self, context):
        if self.uninstall_uiauto_apk:
            self.device.uninstall(self.uiauto_package)

    def validate(self):
        if not self.uiauto_file:
            raise WorkloadError('No UI automation APK file found for workload {}.'.format(self.name))
        if not self.uiauto_package:
            raise WorkloadError('No UI automation package specified for workload {}.'.format(self.name))


class ApkWorkload(Workload):
    """
    A workload based on an APK file.

    Defines the following attributes:

    :package: The package name of the app. This is usually a Java-style name of the form
              ``com.companyname.appname``.
    :activity: This is the initial activity of the app. This will be used to launch the
               app during the setup.  Many applications do not specify a launch activity so
               this may be left blank if necessary.
    :view: The class of the main view pane of the app. This needs to be defined in order
           to collect SurfaceFlinger-derived statistics (such as FPS) for the app, but
           may otherwise be left as ``None``.
    :launch_main: If ``False``, the default activity will not be launched (during setup),
                  allowing workloads to start the app with an intent of their choice in
                  the run step. This is useful for apps without a launchable default/main
                  activity or those where it cannot be launched without intent data (which
                  is provided at the run phase).
    :install_timeout: Timeout for the installation of the APK. This may vary wildly based on
                      the size and nature of a specific APK, and so should be defined on
                      per-workload basis.

                      .. note:: To a lesser extent, this will also vary based on the the
                                device and the nature of adb connection (USB vs Ethernet),
                                so, as with all timeouts, so leeway must be included in
                                the specified value.

    :min_apk_version: The minimum supported apk version for this workload. May be ``None``.
    :max_apk_version: The maximum supported apk version for this workload. May be ``None``.

    .. note:: Both package and activity for a workload may be obtained from the APK using
              the ``aapt`` tool that comes with the ADT  (Android Developemnt Tools) bundle.

    """
    package = None
    activity = None
    view = None
    min_apk_version = None
    max_apk_version = None
    supported_platforms = ['android']
    launch_main = True

    parameters = [
        Parameter('install_timeout', kind=int, default=300,
                  description='Timeout for the installation of the apk.'),
        Parameter('check_apk', kind=boolean, default=True,
                  description='''
                  When set to True the APK file on the host will be prefered if
                  it is a valid version and ABI, if not it will fall back to the
                  version on the targer. When set to False the target version is
                  prefered.
                  '''),
        Parameter('force_install', kind=boolean, default=False,
                  description='''
                  Always re-install the APK, even if matching version is found already installed
                  on the device. Runs ``adb install -r`` to ensure existing APK is replaced. When
                  this is set, check_apk is ignored.
                  '''),
        Parameter('uninstall_apk', kind=boolean, default=False,
                  description='If ``True``, will uninstall workload\'s APK as part of teardown.'),
        Parameter('exact_abi', kind=bool, default=False,
                  description='''
                  If ``True``, workload will check that the APK matches the target
                  device ABI, otherwise any APK found will be used.
                  '''),
        Parameter('clear_data_on_reset', kind=bool, default=True,
                  description="""
                  If set to ``False``, this will prevent WA from clearing package
                  data for this workload prior to running it.
                  """),
    ]

    def __init__(self, device, _call_super=True, **kwargs):
        if _call_super:
            Workload.__init__(self, device, **kwargs)
        self.apk_file = None
        self.apk_version = None
        self.logcat_log = None
        self.exact_apk_version = None

    def setup(self, context):  # pylint: disable=too-many-branches
        Workload.setup(self, context)
        self.setup_workload_apk(context)
        self.launch_application()
        self.kill_background()
        self.device.clear_logcat()

    def setup_workload_apk(self, context):
        # Get target version
        target_version = self.device.get_installed_package_version(self.package)
        if target_version:
            target_version = LooseVersion(target_version)
            self.logger.debug("Found version '{}' on target device".format(target_version))

        # Get host version
        self.apk_file = context.resolver.get(ApkFile(self, self.device.abi,
                                                     package=getattr(self, 'package', None)),
                                             version=getattr(self, 'version', None),
                                             variant_name=getattr(self, 'variant_name', None),
                                             strict=False)

        # Get target abi
        target_abi = self.device.get_installed_package_abi(self.package)
        if target_abi:
            self.logger.debug("Found apk with primary abi '{}' on target device".format(target_abi))

        # Get host version, primary abi is first, and then try to find supported.
        for abi in self.device.supported_abi:
            self.apk_file = context.resolver.get(ApkFile(self, abi,
                                                         package=getattr(self, 'package', None)),
                                                 version=getattr(self, 'version', None),
                                                 variant_name=getattr(self, 'variant_name', None),
                                                 strict=False)

            # Stop if apk found, or if exact_abi is set only look for primary abi.
            if self.apk_file or self.exact_abi:
                break

        host_version = self.check_host_version()
        self.verify_apk_version(target_version, target_abi, host_version)

        if self.force_install:
            self.force_install_apk(context, host_version)
        elif self.check_apk:
            self.prefer_host_apk(context, host_version, target_version)
        else:
            self.prefer_target_apk(context, host_version, target_version)

        self.reset(context)
        self.apk_version = self.device.get_installed_package_version(self.package)
        context.add_classifiers(apk_version=self.apk_version)

    def check_host_version(self):
        host_version = None
        if self.apk_file is not None:
            host_version = ApkInfo(self.apk_file).version_name
            if host_version:
                host_version = LooseVersion(host_version)
            self.logger.debug("Found version '{}' on host".format(host_version))
        return host_version

    def verify_apk_version(self, target_version, target_abi, host_version):
        # Error if apk was not found anywhere
        if target_version is None and host_version is None:
            msg = "Could not find APK for '{}' on the host or target device"
            raise ResourceError(msg.format(self.name))

        if self.exact_apk_version is not None:
            if self.exact_apk_version != target_version and self.exact_apk_version != host_version:
                msg = "APK version '{}' not found on the host '{}' or target '{}'"
                raise ResourceError(msg.format(self.exact_apk_version, host_version, target_version))

        # Error if exact_abi and suitable apk not found on host and incorrect version on device
        if self.exact_abi and host_version is None:
            if target_abi != self.device.abi:
                msg = "APK abi '{}' not found on the host and target is '{}'"
                raise ResourceError(msg.format(self.device.abi, target_abi))

    def launch_application(self):
        if self.launch_main:
            self.launch_package()  # launch default activity without intent data

    def kill_background(self):
        self.device.execute('am kill-all')  # kill all *background* activities

    def force_install_apk(self, context, host_version):
        if host_version is None:
            raise ResourceError("force_install is 'True' but could not find APK on the host")
        try:
            self.validate_version(host_version)
        except ResourceError as e:
            msg = "force_install is 'True' but the host version is invalid:\n\t{}"
            raise ResourceError(msg.format(str(e)))
        self.install_apk(context, replace=True)

    def prefer_host_apk(self, context, host_version, target_version):
        msg = "check_apk is 'True' "
        if host_version is None:
            try:
                self.validate_version(target_version)
            except ResourceError as e:
                msg += "but the APK was not found on the host and the target version is invalid:\n\t{}"
                raise ResourceError(msg.format(str(e)))
            else:
                msg += "but the APK was not found on the host, using target version"
                self.logger.debug(msg)
                return
        try:
            self.validate_version(host_version)
        except ResourceError as e1:
            msg += "but the host APK version is invalid:\n\t{}\n"
            if target_version is None:
                msg += "The target does not have the app either"
                raise ResourceError(msg.format(str(e1)))
            try:
                self.validate_version(target_version)
            except ResourceError as e2:
                msg += "The target version is also invalid:\n\t{}"
                raise ResourceError(msg.format(str(e1), str(e2)))
            else:
                msg += "using the target version instead"
                self.logger.debug(msg.format(str(e1)))
        else:  # Host version is valid
            if target_version is not None and target_version == host_version:
                msg += " and a matching version is alread on the device, doing nothing"
                self.logger.debug(msg)
                return
            msg += " and the host version is not on the target, installing APK"
            self.logger.debug(msg)
            self.install_apk(context, replace=True)

    def prefer_target_apk(self, context, host_version, target_version):
        msg = "check_apk is 'False' "
        if target_version is None:
            try:
                self.validate_version(host_version)
            except ResourceError as e:
                msg += "but the app was not found on the target and the host version is invalid:\n\t{}"
                raise ResourceError(msg.format(str(e)))
            else:
                msg += "and the app was not found on the target, using host version"
                self.logger.debug(msg)
                self.install_apk(context)
                return
        try:
            self.validate_version(target_version)
        except ResourceError as e1:
            msg += "but the target app version is invalid:\n\t{}\n"
            if host_version is None:
                msg += "The host does not have the APK either"
                raise ResourceError(msg.format(str(e1)))
            try:
                self.validate_version(host_version)
            except ResourceError as e2:
                msg += "The host version is also invalid:\n\t{}"
                raise ResourceError(msg.format(str(e1), str(e2)))
            else:
                msg += "Using the host APK instead"
                self.logger.debug(msg.format(str(e1)))
                self.install_apk(context, replace=True)
        else:
            msg += "and a valid version of the app is already on the target, using target app"
            self.logger.debug(msg)

    def validate_version(self, version):
        min_apk_version = getattr(self, 'min_apk_version', None)
        max_apk_version = getattr(self, 'max_apk_version', None)

        if min_apk_version is not None and max_apk_version is not None:
            if version < LooseVersion(min_apk_version) or \
                    version > LooseVersion(max_apk_version):
                msg = "version '{}' not supported. " \
                      "Minimum version required: '{}', Maximum version known to work: '{}'"
                raise ResourceError(msg.format(version, min_apk_version, max_apk_version))

        elif min_apk_version is not None:
            if version < LooseVersion(min_apk_version):
                msg = "version '{}' not supported. " \
                      "Minimum version required: '{}'"
                raise ResourceError(msg.format(version, min_apk_version))

        elif max_apk_version is not None:
            if version > LooseVersion(max_apk_version):
                msg = "version '{}' not supported. " \
                      "Maximum version known to work: '{}'"
                raise ResourceError(msg.format(version, max_apk_version))

    def launch_package(self):
        if not self.activity:
            output = self.device.execute('am start -W {}'.format(self.package))
        else:
            output = self.device.execute('am start -W -n {}/{}'.format(self.package, self.activity))
        if 'Error:' in output:
            self.device.execute('am force-stop {}'.format(self.package))  # this will dismiss any erro dialogs
            raise WorkloadError(output)
        self.logger.debug(output)

    def reset(self, context):  # pylint: disable=W0613
        self.device.execute('am force-stop {}'.format(self.package))
        if self.clear_data_on_reset:
            self.device.execute('pm clear {}'.format(self.package))

        # As of android API level 23, apps can request permissions at runtime,
        # this will grant all of them so requests do not pop up when running the app
        # This can also be done less "manually" during adb install using the -g flag
        if self.device.get_sdk_version() >= 23:
            self._grant_requested_permissions()

    def install_apk(self, context, replace=False):
        success = False
        if replace and self.device.package_is_installed(self.package):
            self.device.uninstall(self.package)
        output = self.device.install_apk(self.apk_file, timeout=self.install_timeout,
                                         replace=replace, allow_downgrade=True)
        if 'Failure' in output:
            if 'ALREADY_EXISTS' in output:
                self.logger.warn('Using already installed APK (did not unistall properly?)')
                self.reset(context)
            else:
                raise WorkloadError(output)
        else:
            self.logger.debug(output)
            success = True
        self.do_post_install(context)
        return success

    def _grant_requested_permissions(self):
        dumpsys_output = self.device.execute(command="dumpsys package {}".format(self.package))
        permissions = []
        lines = iter(dumpsys_output.splitlines())
        for line in lines:
            if "requested permissions:" in line:
                break

        for line in lines:
            if "android.permission." in line:
                permissions.append(line.split(":")[0].strip())
            # Matching either of these means the end of requested permissions section
            elif "install permissions:" in line or "runtime permissions:" in line:
                break

        for permission in set(permissions):
            # "Normal" Permisions are automatically granted and cannot be changed
            permission_name = permission.rsplit('.', 1)[1]
            if permission_name not in ANDROID_NORMAL_PERMISSIONS:
                # Some permissions are not allowed to be "changed"
                if permission_name not in ANDROID_UNCHANGEABLE_PERMISSIONS:
                    # On some API 23+ devices, this may fail with a SecurityException
                    # on previously granted permissions. In that case, just skip as it
                    # is not fatal to the workload execution
                    try:
                        self.device.execute("pm grant {} {}".format(self.package, permission))
                    except DeviceError as e:
                        if "changeable permission" in e.message or "Unknown permission" in e.message:
                            self.logger.debug(e)
                        else:
                            raise e

    def do_post_install(self, context):
        """ May be overwritten by derived classes."""
        pass

    def run(self, context):
        pass

    def update_result(self, context):
        self.logcat_log = os.path.join(context.output_directory, 'logcat.log')
        self.device.dump_logcat(self.logcat_log)
        context.add_iteration_artifact(name='logcat',
                                       path='logcat.log',
                                       kind='log',
                                       description='Logact dump for the run.')

    def teardown(self, context):
        self.device.execute('am force-stop {}'.format(self.package))
        if self.uninstall_apk:
            self.device.uninstall(self.package)

AndroidBenchmark = ApkWorkload  # backward compatibility

class AndroidUiAutoBenchmark(UiAutomatorWorkload, AndroidBenchmark):

    supported_platforms = ['android']

    def __init__(self, device, **kwargs):
        UiAutomatorWorkload.__init__(self, device, **kwargs)
        AndroidBenchmark.__init__(self, device, _call_super=False, **kwargs)

    def initialize(self, context):
        UiAutomatorWorkload.initialize(self, context)
        AndroidBenchmark.initialize(self, context)
        self._check_unsupported_packages()

    def init_resources(self, context):
        UiAutomatorWorkload.init_resources(self, context)
        AndroidBenchmark.init_resources(self, context)

    def setup(self, context):
        UiAutomatorWorkload.setup(self, context)
        AndroidBenchmark.setup(self, context)

    def update_result(self, context):
        UiAutomatorWorkload.update_result(self, context)
        AndroidBenchmark.update_result(self, context)

    def teardown(self, context):
        UiAutomatorWorkload.teardown(self, context)
        AndroidBenchmark.teardown(self, context)

    def _check_unsupported_packages(self):
        """
        Check for any unsupported package versions and raise an
        exception if detected.

        """
        for package in UNSUPPORTED_PACKAGES:
            version = self.device.get_installed_package_version(package)
            if version is None:
                continue

            if '-' in version:
                version = version.split('-')[0]  # ignore abi version

            if version in UNSUPPORTED_PACKAGES[package]:
                message = 'This workload does not support version "{}" of package "{}"'
                raise WorkloadError(message.format(version, package))


class AndroidUxPerfWorkloadMeta(ExtensionMeta):
    to_propagate = ExtensionMeta.to_propagate + [('deployable_assets', str, ListCollection)]


class AndroidUxPerfWorkload(AndroidUiAutoBenchmark):
    __metaclass__ = AndroidUxPerfWorkloadMeta

    deployable_assets = []
    parameters = [
        Parameter('markers_enabled', kind=bool, default=False,
                  description="""
                  If ``True``, UX_PERF action markers will be emitted to logcat during
                  the test run.
                  """),
        Parameter('clean_assets', kind=bool, default=False,
                  description="""
                  If ``True`` pushed assets will be deleted at the end of each iteration
                  """),
        Parameter('force_push_assets', kind=bool, default=False,
                  description="""
                  If ``True`` always push assets on each iteration, even if the
                  assets already exists in the device path
                  """),
    ]

    def _path_on_device(self, fpath, dirname=None):
        if dirname is None:
            dirname = self.device.working_directory
        fname = os.path.basename(fpath)
        return self.device.path.join(dirname, fname)

    def push_assets(self, context):
        pushed = False
        file_list = []
        for f in self.deployable_assets:
            fpath = context.resolver.get(File(self, f))
            device_path = self._path_on_device(fpath)
            if self.force_push_assets or not self.device.file_exists(device_path):
                self.device.push_file(fpath, device_path, timeout=300)
                file_list.append(device_path)
                pushed = True
        if pushed:
            self.device.refresh_device_files(file_list)

    def delete_assets(self):
        if self.deployable_assets:
            file_list = []
            for f in self.deployable_assets:
                f = self._path_on_device(f)
                self.device.delete_file(f)
                file_list.append(f)
                self.device.delete_file(f)
            self.device.refresh_device_files(file_list)

    def __init__(self, device, **kwargs):
        super(AndroidUxPerfWorkload, self).__init__(device, **kwargs)
        # Turn class attribute into instance attribute
        self.deployable_assets = list(self.deployable_assets)

    def validate(self):
        super(AndroidUxPerfWorkload, self).validate()
        self.uiauto_params['package_name'] = self.package
        self.uiauto_params['markers_enabled'] = self.markers_enabled

    def setup(self, context):
        super(AndroidUxPerfWorkload, self).setup(context)
        self.push_assets(context)

    def teardown(self, context):
        super(AndroidUxPerfWorkload, self).teardown(context)
        if self.clean_assets:
            self.delete_assets()


class GameWorkload(ApkWorkload, ReventWorkload):
    """
    GameWorkload is the base class for all the workload that use revent files to
    run.

    For more in depth details on how to record revent files, please see
    :ref:`revent_files_creation`. To subclass this class, please refer to
    :ref:`GameWorkload`.

    Additionally, this class defines the following attributes:

    :asset_file: A tarball containing additional assets for the workload. These are the assets
                 that are not part of the APK but would need to be downloaded by the workload
                 (usually, on first run of the app). Since the presence of a network connection
                 cannot be assumed on some devices, this provides an alternative means of obtaining
                 the assets.
    :saved_state_file: A tarball containing the saved state for a workload. This tarball gets
                       deployed in the same way as the asset file. The only difference being that
                       it is usually much slower and re-deploying the tarball should alone be
                       enough to reset the workload to a known state (without having to reinstall
                       the app or re-deploy the other assets).
    :loading_time: Time it takes for the workload to load after the initial activity has been
                   started.

    """

    # May be optionally overwritten by subclasses
    asset_file = None
    saved_state_file = None
    view = 'SurfaceView'
    loading_time = 10
    supported_platforms = ['android']
    setup_required = True

    parameters = [
        Parameter('install_timeout', default=500, override=True),
        Parameter('check_states', kind=bool, default=False, global_alias='check_game_states',
                  description="""Use visual state detection to verify the state of the workload
                  after setup and run"""),
        Parameter('assets_push_timeout', kind=int, default=500,
                  description='Timeout used during deployment of the assets package (if there is one).'),
    ]

    def __init__(self, device, **kwargs):  # pylint: disable=W0613
        ApkWorkload.__init__(self, device, **kwargs)
        ReventWorkload.__init__(self, device, _call_super=False, **kwargs)
        if self.check_states:
            state_detector.check_match_state_dependencies()
        self.logcat_process = None
        self.module_dir = os.path.dirname(sys.modules[self.__module__].__file__)
        self.revent_dir = os.path.join(self.module_dir, 'revent_files')

    def init_resources(self, context):
        ApkWorkload.init_resources(self, context)
        ReventWorkload.init_resources(self, context)
        if self.check_states:
            self._check_statedetection_files(context)

    def setup(self, context):
        ApkWorkload.setup(self, context)
        self.logger.debug('Waiting for the game to load...')
        time.sleep(self.loading_time)
        ReventWorkload.setup(self, context)

        # state detection check if it's enabled in the config
        if self.check_states:
            self.check_state(context, "setup_complete")

    def do_post_install(self, context):
        ApkWorkload.do_post_install(self, context)
        self._deploy_assets(context, self.assets_push_timeout)

    def reset(self, context):
        # If saved state exists, restore it; if not, do full
        # uninstall/install cycle.
        self.device.execute('am force-stop {}'.format(self.package))
        if self.saved_state_file:
            self._deploy_resource_tarball(context, self.saved_state_file)
        else:
            if self.clear_data_on_reset:
                self.device.execute('pm clear {}'.format(self.package))
            self._deploy_assets(context)

    def run(self, context):
        ReventWorkload.run(self, context)

    def teardown(self, context):
        # state detection check if it's enabled in the config
        if self.check_states:
            self.check_state(context, "run_complete")

        if not self.saved_state_file:
            ApkWorkload.teardown(self, context)
        else:
            self.device.execute('am force-stop {}'.format(self.package))
        ReventWorkload.teardown(self, context)

    def _deploy_assets(self, context, timeout=300):
        if self.asset_file:
            self._deploy_resource_tarball(context, self.asset_file, timeout)
        if self.saved_state_file:  # must be deployed *after* asset tarball!
            self._deploy_resource_tarball(context, self.saved_state_file, timeout)

    def _deploy_resource_tarball(self, context, resource_file, timeout=300):
        kind = 'data'
        if ':' in resource_file:
            kind, resource_file = resource_file.split(':', 1)
        ondevice_cache = self.device.path.join(self.device.resource_cache, self.name, resource_file)
        if not self.device.file_exists(ondevice_cache):
            asset_tarball = context.resolver.get(ExtensionAsset(self, resource_file))
            if not asset_tarball:
                message = 'Could not find resource {} for workload {}.'
                raise WorkloadError(message.format(resource_file, self.name))
            # adb push will create intermediate directories if they don't
            # exist.
            self.device.push_file(asset_tarball, ondevice_cache, timeout=timeout)

        device_asset_directory = self.device.path.join(self.device.external_storage_directory, 'Android', kind)
        deploy_command = 'cd {} && {} tar -xzf {}'.format(device_asset_directory,
                                                          self.device.busybox,
                                                          ondevice_cache)
        self.device.execute(deploy_command, timeout=timeout, as_root=True)

    def _check_statedetection_files(self, context):
        try:
            self.statedefs_dir = context.resolver.get(File(self, 'state_definitions'))
        except ResourceError:
            self.logger.warning("State definitions directory not found. Disabling state detection.")
            self.check_states = False # pylint: disable=W0201

    def check_state(self, context, phase):
        try:
            self.logger.info("\tChecking workload state...")
            screenshotPath = os.path.join(context.output_directory, "screen.png")
            self.device.capture_screen(screenshotPath)
            stateCheck = state_detector.verify_state(screenshotPath, self.statedefs_dir, phase)
            if not stateCheck:
                raise WorkloadError("Unexpected state after setup")
        except state_detector.StateDefinitionError as e:
            msg = "State definitions or template files missing or invalid ({}). Skipping state detection."
            self.logger.warning(msg.format(e.message))
