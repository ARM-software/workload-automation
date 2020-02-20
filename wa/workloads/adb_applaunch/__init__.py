import os
import re
import time

from wa import Parameter, Workload, WorkloadError, File
from wa.utils.types import list_or_string

LAUNCH_TIME_TYPE_DISPLAYED = 'displayed'
LAUNCH_TIME_TYPE_FULLY_DRAWN = 'fully_drawn'

COMMON_APPS = {'camera' : 'com.google.android.GoogleCamera',
               'reddit' : 'com.reddit.frontpage',
               'youtube' : 'com.google.android.youtube',
               'gmail' : 'com.google.android.gm',
               'photos' : 'com.google.android.apps.photos',
               'googledrive' : 'com.google.android.apps.docs',
               'adobereader' : 'com.adobe.reader',
               'chrome' : 'com.android.chrome',
               'maps' : 'com.google.android.maps',
               'slides' : 'com.google.android.apps.docs.editors.slides'}

class AdbApplaunch(Workload):

    name = 'adb_applaunch'
    description = '''
                  This workload measures the cold start of applications and ativities.
                  If loading a specific apk onto phone is required, place apk at:
                  ~/.<workload_atomation_folder>/dependencies/adb_applaunch/<full package name eg. com.adobe.reader>/base.apk
                  '''
    
    parameters = [
        Parameter('packages', kind=list_or_string, default='com.google.android.gm', 
        	      description='Package name of the application to launch'),
        Parameter('activities', kind=list_or_string, default=None, mandatory=False,
                  description ='''Optional parameter, workload will launch specific activities specified here.
                                  Format is <package_name>/<activity>,
                                  eg. com.google.android.apps.photos/com.google.android.apps.photos.home.HomeActivity.'''),
        Parameter('sleep_time', kind=int, default=2, description='Sleep time after launch to wait for application to load.'),
        Parameter('install_packages', kind=str, default='if_missing', allowed_values=['always', 'never', 'if_missing'], 
                  description=''' If set to always, workload will uninstall package from device and reinstall from dependencies folder.
                                  If set to never, workload will always use package on device and throw warning or error if missing.
                                  If set to if_missing, workload will only install package on device if it is not already installed''')
    ]

    def __init__(self, target, **kwargs):
        super(AdbApplaunch, self).__init__(target, **kwargs)
        if isinstance(self.packages, str):
        	self.packages = [self.packages]
        if isinstance(self.activities, str):
        	self.activities = [self.activities]
        self.package_version_name = {}
        self.package_launch_activity = {}

    def initialize(self, context):
        super(AdbApplaunch, self).initialize(context)        
        self._validate_packages(context)
        self._validate_activities()

    def run(self, context):
        super(AdbApplaunch, self).run(context)
        for package in self.packages:
            command = 'monkey -p {} -c android.intent.category.LAUNCHER 1'.format(package)
            host_ouput_path = os.path.join(context.output_directory, '{}_logcat.log'.format(package))
            self._launch_app(command, host_ouput_path, package)
        if self.activities:
            for activity in self.activities:
                package_name = activity.split('/')[0]
                command = 'am start-activity -S -W {}'.format(activity)
                activity_name = activity.split('/')[1]
                host_ouput_path = os.path.join(context.output_directory, '{}_logcat.log'.format(activity_name))
                self._launch_app(command, host_ouput_path, package_name)

    def update_output(self, context):
        super(AdbApplaunch, self).update_output(context)   
        for package in self.packages:    
            logcat_file = os.path.join(context.output_directory, '{}_logcat.log'.format(package))
            context.add_artifact('{}_launch_log'.format(package), logcat_file, 'raw')
            self._parse_launch_time(context, logcat_file, package, self.package_launch_activity[package])
        if self.activities:
            for activity in self.activities:
                activity_name = activity.split('/')[1]
                logcat_file = os.path.join(context.output_directory, '{}_logcat.log'.format(activity_name))
                context.add_artifcat(logcat_file)
                package_name = activity.split('/')[0]
                self._parse_launch_time(context, logcat_file, package_name, activity_name)

    def teardown(self, context):
        super(AdbApplaunch, self).teardown(context)
        for package in self.packages:
            self._stop_app_and_clear_logcat(package)

    def _validate_packages(self, context):
        self.packages = [COMMON_APPS[package] if package in COMMON_APPS else package for package in self.packages]
        self._install_packages(context)
        invalid_packages = [package for package in self.packages if not self.target.is_installed(package)]
        for package in invalid_packages:
            self.packages.remove(package)
            self.logger.warning('Package {} is not installed on device'.format(package))
        if len(self.packages) == 0:
            raise WorkloadError('There are no packages available to launch')
        for package in self.packages:
            self.package_version_name[package] = self.target.get_package_version(package)
            self.package_launch_activity[package] = self._get_main_launch_activity(package)

    def _install_packages(self, context):
        if self.install_packages == 'never':
            return
        if self.install_packages == 'if_missing':
            for package in self.packages:
                if not self.target.is_installed(package):
                    self._install_package_from_dependencies(context, package)
        if self.install_packages == 'always':
            for package in self.packages:
                apk = context.get_resource(File(self, os.path.join(package, 'base.apk')))
                # Some apps on some devices will be system apps and will have to be uninstalled manualy
                system_app = self.target.execute('pm list package -s | grep {}'.format(package))
                if system_app:
                    print('system app... skipping')
                    continue
                self.target.uninstall(package)
                self.target.install(apk)

    def _install_package_from_dependencies(self, context, package):
        apk = context.get_resource(File(self, os.path.join(package, 'base.apk')), strict=False)
        self.target.install(apk)

    def _validate_activities(self):
        if not self.activities:
    	    return
        invalid_activities = []     	
        for activity in self.activities:
            try:
                self.target.execute('dumpsys package | grep -Eo "^[[:space:]]+[0-9a-f]+[[:space:]]+{}"'.format(activity))
            except:
                self.logger.warning('Activity {} cannot be found'.format(activity))
                invalid_activities.append(activity)
        for invalid_activity in invalid_activities:
            self.activities.remove(invalid_activity)

    def _stop_app_and_clear_logcat(self, package):
        self.target.execute('am force-stop {}'.format(package))
        self.target.execute('echo 3 > /proc/sys/vm/drop_caches', check_exit_code=False)        
        self.target.clear_logcat()

    def _launch_app(self, launch_command, output_path, package_name):
        self._stop_app_and_clear_logcat(package_name)
        self.target.execute(launch_command)
        time.sleep(self.sleep_time)
        self.target.dump_logcat(output_path, filter='I ActivityManager')
        self.target.execute('am force-stop {}'.format(package_name))

    def _get_main_launch_activity(self, package):
        return self.target.execute('cmd package resolve-activity --brief {} | tail -n 1'.format(package))

    def _parse_launch_time(self, context, logcat_file, package_name, activity_name):
        launch_time = self._parse_launch_time_fully_drawn(logcat_file, package_name)
        if launch_time:
            self._add_launch_time_metric(context, LAUNCH_TIME_TYPE_FULLY_DRAWN, launch_time, package_name, activity_name)
            return
        launch_time = self._parse_launch_time_display(logcat_file, package_name)
        if launch_time:
            self._add_launch_time_metric(context, LAUNCH_TIME_TYPE_DISPLAYED, launch_time, package_name, activity_name)
        else:
            raise WorkloadError('Launch time could not be found for {}'.format(package_name))

    def _add_launch_time_metric(self, context, launch_time_type, time_seconds, package, activity_name):
        classifiers = {'package' : package,
                       'package_version' : self.package_version_name[package],
                       'launch_activity_name' : activity_name}
        
        context.add_metric('launch_time_{}'.format(launch_time_type), 
                                                    time_seconds, 
                                                    'seconds', 
                                                    classifiers=classifiers, 
                                                    lower_is_better=True)

    @staticmethod
    def _parse_launch_time_fully_drawn(logcat_file, package_name):
        with open(logcat_file) as fh:
            for line in reversed(fh.readlines()):
                match = re.search(r'Fully drawn {}\/.*: \+(?:(\d+)s)?(\d+)ms'.format(package_name), line)
                if match:
                    (sec, msec) = match.groups()
                    sec = 0 if sec is None else float(sec)
                    return sec + (float(msec) / 1000.)
            return None

    @staticmethod 
    def _parse_launch_time_display(logcat_file, package_name):
        with open(logcat_file) as fh:
            for line in reversed(fh.readlines()):
                match = re.search(r'Displayed {}\/.*: \+(?:(\d+)s)?(\d+)ms'.format(package_name), line)
                if match:
                    (sec, msec) = match.groups()
                    sec = 0 if sec is None else float(sec)
                    return sec + (float(msec) / 1000.)
            return None
