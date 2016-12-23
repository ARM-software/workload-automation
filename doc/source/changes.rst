=================================
What's New in Workload Automation
=================================
-------------
Version 2.6.0
-------------

 .. note:: Users who are currently using the GitHub master version of WA should
           uninstall the existing version before upgrading to avoid potential issues.

Additions:
##########

Workloads
~~~~~~~~~
- ``AdobeReader``: A workload that carries out following typical productivity
  tasks. These include opening a file, performing various gestures and
  zooms on screen and searching for a predefined set of strings.
- ``octaned8``: A workload to run the binary (non-browser) version of the JS
  benchmark Octane.
- ``GooglePlayBooks``: A workload to perform standard productivity tasks with
  Google Play Books. This workload performs various tasks, such as searching
  for a book title online, browsing through a book, adding and removing notes,
  word searching, and querying information about the book.
- ``GooglePhotos``: A workload to perform standard productivity tasks with
  Google Photos. Carries out various tasks, such as browsing images,
  performing zooms, and post-processing the image.
- ``GoogleSlides``: Carries out various tasks, such as creating a new
  presentation, adding text, images, and shapes, as well as basic editing and
  playing a slideshow.
- ``Youtube``: The workload plays a video, determined by the ``video_source``
  parameter. While the video is playing, some common actions such as video
  seeking, pausing playback and navigating the comments section are performed.
- ``Skype``: Replacement for the ``skypevideo`` workload. Logs into Skype
  and initiates a voice or video call with a contact.

Framework
~~~~~~~~~
- ``AndroidUxPerfWorkload``: Added a new workload class to encapsulate
  functionality common to all uxperf workloads.
- ``UxPerfUiAutomation``: Added class which contains methods specific to
  UX performance
  testing.
- ``get-assets``: Added new script and command to retrieve external assets
  for workloads

Results Processors
~~~~~~~~~~~~~~~~~~~
- ``uxperf``: Parses device logcat for `UX_PERF` markers to produce performance
  metrics for workload actions using specified instrumentation.

Other
~~~~~
- ``State Detection``: Added feature to use visual state detection to
  verify the state of a workload after setup and run.


Fixes/Improvements:
###################

Documentation
~~~~~~~~~~~~~~
- ``Revent``: Added file structure to the documentation.
- Clarified documentation regarding binary dependencies.
- Updated documentation with ``create`` and ``get-assets`` commands.

Instruments
~~~~~~~~~~~~
- ``sysfs_extractor``: Fixed error when `tar.gz` file already existed on device,
  now overwrites.
- ``cpufreq``: Fixed error when `tar.gz` file already existed on device, now
  overwrites.
- ``file-poller``:
    - Improved csv output.
    - Added error checking and reporting.
    - Changed ``files`` to be a mandatory parameter.
- ``fps``:
    - Added a new parameter to fps instrument to specify the time period between
      calls to ``dumpsys SurfaceFlinger --latency`` when collecting frame data.
    - Added gfxinfo methods to obtain fps stats. Auto detects and uses appropriate
      method via android version of device.
    - Fixed issue with regex.
    - Now handles empty frames correctly.
- ``energy_model``: Ensures that the ``ui`` runtime parameter is only set for
  ChromeOS devices.
- ``ftrace``: Added support to handle traces collected by both WA and devlib.
- ``Perf``: Updated 32bit binary file for little endian devices.

Resource Getters
~~~~~~~~~~~~~~~~
- ``http_getter``: Now used to try and find executables files from a
  provided ``remove_assets_url``.

Result Processors
~~~~~~~~~~~~~~~~~
- ``cpu_states``: Fixes using stand-alone script with timeline option.

Workloads
~~~~~~~~~
- ``antutu``: Fixed setting permissions of ``FINE_LOCATION`` on some devices.
- ``bbench`` Fixed handling of missing results.
- ``camerarecord``:
    - Added frame stats collection through dumpsys gfxinfo.
    - Added possibility to select slow_motion recording mode.
- ``Geekbench``:
    - Fixed output file listing causing pull failure.
    - Added support for Geekbench 4.
- ``recentfling``:
    - Fixed issue when binaries were not uninstalled correctly.
    - Scripts are now deployed via ``install()`` to ensure they are executable.
    - Fixed handling of when a PID file is deleted before reaching processing
      results stage.
    - Added parameter to not start any apps before flinging.
- ``rt-app``: Added camera recorder simulation.
- ``sysbench``: Added arm64 binary.
- ``Vellamo``: Fixed capitalization in part of UIAutomation to prevent
  potential issues.
- ``Spec2000``: Now uses WA deployed version of busybox.
- ``NetStat``: Updated to support new default logcat format in Android 6.
- ``Dex2oat``: Now uses root if available.

Framework
~~~~~~~~~
- ``adb_shell``:
    - Fixed issue when using single quoted command with ``adb_shell``.
    - Correctly forward stderror to the caller for newer version of adb.
- ``revent``
    - Added ``-S`` argument to "record" command to automatically record a
      screen capture after a recording is completed.
    - Fixed issue with multiple iterations of a revent workload.
    - Added ``-s`` option to executable to allow waiting on stdin.
    - Removed timeout in command as ``-s`` is specified.
    - Revent recordings can now be parsed and used within WA.
    - Fixed issue when some recordings wouldn't be retrieved correctly.
    - Timeout is now based on recording duration.
    - Added `magic` and file version to revent files. Revent files should now
      start with ``REVENT`` followed by the file format version.
    - Added support for gamepad recording. This type of recording contains
      only the events from a gamepad device (which is automatically
      identified).
    - A ``mode`` field has been added to the recording format to help
      distinguish between the normal and gamepad recording types.
    - Added ``-g`` option to ``record`` command to expose the gamepad recording
      mode.
    - The structure of revent code has undergone a major overhaul to improve
      maintainability and robustness.
    - More detailed ``info`` command output.
    - Updated Makefile to support debug/production builds.
- ``Android API``: Upgraded Android API level from 17 to 18.
- ``uiautomator``: The window hierarchy is now dumped to a file when WA fails
  on android devices.
- ``AndroidDevice``:
    - Added support for downgrading when installing an APK.
    - Added a ``broadcast_media_mounted`` method to force a re-index of the
      mediaserver cache for a specified directory.
    - Now correctly handles ``None`` output for ``get_pids_of()`` when there are no
      running processes with the specified name.
    - Renamed the capture method from ``capture_view_hierachy`` to
      ``capture_ui_hierarchy``.
    - Changed the file extension of the capture file to ``.uix``
    - Added ``-rf`` to delete_files to be consistent with ``LinuxDevice``.
- ``LinuxDevice``: Now ensures output from both stdout and etderr is propagated in
  the event of a DeviceError.
- ``APKWorkload``:
    - Now ensure APKs are replaced properly when reinstalling.
    - Now checks APK version and ABI when installing.
    - Fixed error on some devices when trying to grant permissions that were
      already granted.
    - Fixed some permissions not being granted.
    - Now allows disabling the main activity launch in setup (required for some
      apps).
    - Added parameter to clear data on reset (default behaviour unchanged).
    - Ignores exception for non-fatal permission grant failure.
    - Fixed issue of multiple versions of the same workload failing to find their APK.
    - Added method to ensure a valid apk version is used within a workload.
    - Updated how APK resolution is performed to maximise likelihood of
      a workload running.
    - When ``check_apk`` is ``True`` will prefer host APK and if no suitable APK
      is found, will use target APK if the correct version is present. When ``False``
      will prefer target apk if it is a valid version otherwise will fallback to
      host APK.
- ``RunConfiguration``: Fixed disabling of instruments in workload specs.
- ``Devices``:
    - Added network connectivity check for devices.
    - Subclasses can now set ``requires_network`` to ``True`` and network
      connectivity check will be performed during ``setup()``.
- ``Workloads``:
    - Added network check methods.
    - Fixed versions to be backwards compatible.
    - Updated workload versions to match APK files.
    - Fixed issues with calling super.
- ``Assets``: Added script to retrieve external assets for workloads.
- ``Execution``: Added a ``clean_up`` global config option to delete WA files from
  devices.
- ``Runner``: No longer takes a screenshot or dump of UI hierarchy for some errors when
  unnecessary, e.g. host errors.
- ``core``: Constraints and allowed values are now checked when set instead of
  when validating.
- ``FpsProcessor``:
    - Added requirement on ``filtered_vsyncs_to_compose`` for ``total_vsync metric``.
    - Removed misleading comment in class description.
- ``BaseUiAutomation``: Added new Marker API so workloads generate start and end
  markers with a string name.
- ``AndroidUiAutoBenchmark``: Automatically checks for known package versions
  that don't work well with AndroidUiAutoBenchmark workloads.

Other
~~~~~
- Updated setup.py url to be a valid URI.
- Fixed workload name in big.Little sample agenda.

Incompatible changes
####################

Framework
~~~~~~~~~
- ``check_abi``: Now renamed to ``exact_abi``, is used to ensure that if enabled,
  only an apk containing no native code or code designed for the devices primary
  abi is use.
- ``AndroidDevice``: Renamed ``supported_eabis`` property to ``supported_abis``
  to be consistent with linux devices.

Workloads
~~~~~~~~~~
- ``skypevideo``: Workload removed and replaced with ``skype`` workload.

-------------
Version 2.5.0
-------------

Additions:
##########

Instruments
~~~~~~~~~~~
- ``servo_power``: Added support for chromebook servo boards.
- ``file_poller``: polls files and outputs a CSV of their values over time.
- ``systrace``: The Systrace tool helps analyze the performance of your
  application by capturing and displaying execution times of your applications
  processes and other Android system processes.

Workloads
~~~~~~~~~
- ``blogbench``: Blogbench is a portable filesystem benchmark that tries to
  reproduce the load of a real-world busy file server.
- ``stress-ng``: Designed to exercise various physical subsystems of a computer
  as well as the various operating system kernel interfaces.
- ``hwuitest``: Uses hwuitest from AOSP to test rendering latency on Android
  devices.
- ``recentfling``: Tests UI jank on android devices.
- ``apklaunch``: installs and runs an arbitrary apk file.
- ``googlemap``: Launches Google Maps and replays previously recorded
  interactions.

Framework
~~~~~~~~~
- ``wlauto.utils.misc``: Added ``memoised`` function decorator that allows
  caching of previous function/method call results.
- Added new ``Device`` APIs:
   - ``lsmod``: lists kernel modules
   - ``insmod``: inserts a kernel module from a ``.ko`` file on the host.
   - ``get_binary_path``: Checks ``binary_directory`` for the wanted binary,
     if it is not found there it will try to use ``which``
   - ``install_if_needed``: Will only install a binary if it is not already
     on the target.
   - ``get_device_model``: Gets the model of the device.
- ``wlauto.core.execution.ExecutionContext``:
   - ``add_classfiers``: Allows adding a classfier to all metrics for the
     current result.

Other
~~~~~
- Commands:
   - ``record``: Simplifies recording revent files.
   - ``replay``: Plays back revent files.

Fixes/Improvements:
###################

Devices
~~~~~~~
- ``juno``:
   - Fixed ``bootargs`` parameter not being passed  to ``_boot_via_uboot``.
   - Removed default ``bootargs``
- ``gem5_linux``:
   - Added ``login_prompt`` and ``login_password_prompt`` parameters.
- ``generic_linux``: ABI is now read from the target device.

Instruments
~~~~~~~~~~~
- ``trace-cmd``:
   - Added the ability to report the binary trace on the target device,
     removing the need for ``trace-cmd`` binary to be present on the host.
   - Updated to handle messages that the trace for a CPU is empty.
   - Made timeout for pulling trace 1 minute at minimum.
- ``perf``: per-cpu statistics now get added as metrics to the results (with a
   classifier used to identify the cpu).
- ``daq``:
   - Fixed bug where an exception would be raised if ``merge_channels=False``
   - No longer allows duplicate channel labels
- ``juno_energy``:
   - Summary metrics are now calculated from the contents of ``energy.csv`` and
     added to the overall results.
   - Added a ``strict`` parameter. When this is set to ``False`` the device
     check during validation is omitted.
- ``sysfs_extractor``: tar and gzip are now performed separately to solve
  permission issues.
- ``fps``:
   - Now only checks for crashed content if ``crash_check`` is ``True``.
   - Can now process multiple ``view`` attributes.
- ``hwmon``: Sensor naming fixed, they are also now added as result classifiers

Resource Getters
~~~~~~~~~~~~~~~~
- ``extension_asset``: Now picks up the path to the mounted filer from the
  ``remote_assets_path`` global setting.

Result Processors
~~~~~~~~~~~~~~~~~
- ``cpustates``:
   - Added the ability to configure how a missing ``START`` marker in the trace
     is handled.
   - Now raises a warning when there is a ``START`` marker in the trace but no
     ``STOP`` marker.
   - Exceptions in PowerStateProcessor no longer stop the processing of the
     rest of the trace.
   - Now ensures a known initial state by nudging each CPU to bring it out of
     idle and writing starting CPU frequencies to the trace.
   - Added the ability to create a CPU utilisation timeline.
   - Fixed issues with getting frequencies of hotplugged CPUs
- ``csv``: Zero-value classifieres are no longer converted to an empty entry.
- ``ipynb_exporter``: Default template no longer shows a blank plot for
  workloads without ``summary_metrics``

Workloads
~~~~~~~~~
- ``vellamo``:
   - Added support for v3.2.4.
   - Fixed getting values from logcat.
- ``cameracapture``: Updated to work with Android M+.
- ``camerarecord``: Updated to work with Android M+.
- ``lmbench``:
   - Added the output file as an artifact.
   - Added taskset support
- ``antutu`` - Added support for v6.0.1
- ``ebizzy``: Fixed use of ``os.path`` to ``self.device.path``.
- ``bbench``: Fixed browser crashes & permissions issues on android M+.
- ``geekbench``:
   - Added check whether device is rooted.
- ``manual``: Now only uses logcat on Android devices.
- ``applaunch``:
   - Fixed ``cleanup`` not getting forwarded to script.
   - Added the ability to stress IO during app launch.
- ``dhrystone``: Now uses WA's resource resolution to find it's binary so it
  uses the correct ABI.
- ``glbench``: Updated for new logcat formatting.

Framework
~~~~~~~~~
- ``ReventWorkload``:
   - Now kills all revent instances on teardown.
   - Device model name is now used when searching for revent files, falling back
     to WA device name.
- ``BaseLinuxDevice``:
   - ``killall`` will now run as root by default if the device
     is rooted.
   - ``list_file_systems`` now handles blank lines.
   - All binaries are now installed into ``binaries_directory`` this allows..
   - Busybox is now deployed on non-root devices.
   - gzipped property files are no zcat'ed
- ``LinuxDevice``:
   - ``kick_off`` no longer requires root.
   - ``kick_off`` will now run as root by default if the device is rooted.
   - No longer raises an exception if a connection was dropped during a reboot.
   - Added a delay before polling for a connection to avoid re-connecting to a
     device that is still in the process of rebooting.
- ``wlauto.utils.types``: ``list_or_string`` now ensures that elements of a list
  are strings.
- ``AndroidDevice``:
   - ``kick_off`` no longer requires root.
   - Build props are now gathered via ``getprop`` rather than trying to parse
     build.prop directly.
   - WA now pushes its own ``sqlite3`` binary.
   - Now uses ``content`` instead of ``settings`` to get ``ANDROID_ID``
   - ``swipe_to_unlock`` parameter is now actually used. It has been changed to
      take a direction to accomodate various devices.
   - ``ensure_screen_is_on`` will now also unlock the screen if swipe_to_unlock
     is set.
   - Fixed use of variables in as_root=True commands.
   - ``get_pids_of`` now used ``busybox grep`` since as of Android M+ ps cannot
     filter by process name anymore.
   - Fixed installing APK files with whitespace in their path/name.
- ``adb_shell``:
   - Fixed handling of line breaks at the end of command output.
   - Newline separator is now detected from the target.
   - As of ADB v1.0.35, ADB returns the return code of the command run. WA now
     handles this correctly.
- ``ApkWorkload``:
   - Now attempts to grant all runtime permissions for devices on Android M+.
   - Can now launch packages that don't have a launch activity defined.
   - Package version is now added to results as a classifier.
   - Now clears app data if an uninstall failed to ensure it starts from a known
     state.
- ``wlauto.utils.ipython``: Updated to work with ipython v5.
- ``Gem5Device``:
   - Added support for deploying the ``m5`` binary.
   - No longer waits for the boot animation to finish if it has been disabled.
   - Fixed runtime error caused by lack of kwargs.
   - No longer depends on ``busybox``.
   - Split out commands to resize shell to ``resize_shell``.
   - Now tries to connect to the shell up to 10 times.
   - No longer renames gzipped files.
- Agendas:
  - Now errors when an agenda key is empty.
- ``wlauto.core.execution.RunInfo``: ``run_name`` will now default to
  ``{output_folder}_{date}_{time}``.
- Extensions:
   - Two different parameters can now have the same global alias as long as they
     their types match.
   - You can no longer ``override`` parameters that are defined at the same
     level.
- ``wlauto.core.entry_point``: Now gives a better error when a config file
  doesn't exist.
- ``wlauto.utils.misc``: Added ``aarch64`` to list for arm64 ABI.
- ``wlauto.core.resolver``: Now shows what version was being search for when a
  resource is not found.
- Will no longer start instruments ect. if a run has no workload specs.
- ``wlauto.utils.uboot``: Now detects uboot version to use correct line endings.
- ``wlauto.utils.trace_cmd``: Added a parser for sched_switch events.

Other
~~~~~
- Updated to pylint v1.5.1
- Rebuilt ``busybox`` binaries to prefer built-in applets over system binaries.
- ``BaseUiAutomation``: Added functions for checking version strings.

Incompatible changes
####################

Instruments
~~~~~~~~~~~
- ``apk_version``: Removed, use result classifiers instead.

Framework
~~~~~~~~~
- ``BaseLinuxDevice``: Removed ``is_installed`` use ``install_if_needed`` and
  ``get_binary_path`` instead.
- ``LinuxDevice``: Removed ``has_root`` method, use ``is_rooted`` instead.
- ``AndroidDevice``: ``swipe_to_unlock`` method replaced with
  ``perform_unlock_swipe``.

-------------
Version 2.4.0
-------------

Additions:
##########

Devices
~~~~~~~~
- ``gem5_linux`` and ``gem5_android``: Interfaces for Gem5 simulation
  environment running Linux and Android respectively.
- ``XE503C1211``: Interface for Samsung XE503C12 Chromebooks.
- ``chromeos_test_image``: Chrome OS test image device. An off the shelf
  device will not work with this device interface.

Instruments
~~~~~~~~~~~~
- ``freq_sweep``: Allows "sweeping" workloads across multiple CPU frequencies.
- ``screenon``: Ensures screen is on, before each iteration, or periodically
  on Android devices.
- ``energy_model``: This instrument can be used to generate an energy model
  for a device based on collected power and performance measurments.
- ``netstats``:  Allows monitoring data sent/received by applications on an
  Android device.

Modules
~~~~~~~
- ``cgroups``: Allows query and manipulation of cgroups controllers on a Linux
  device. Currently, only cpusets controller is implemented.
- ``cpuidle``: Implements cpuidle state discovery, query and manipulation for
  a Linux device. This replaces the more primitive get_cpuidle_states method
  of LinuxDevice.
- ``cpufreq`` has now been split out into a device module

Reasource Getters
~~~~~~~~~~~~~~~~~
- ``http_assets``:  Downloads resources from a web server.

Results Processors
~~~~~~~~~~~~~~~~~~~
- ``ipynb_exporter``: Generates an IPython notebook from a template with the
  results and runs it.
- ``notify``: Displays a desktop notification when a run finishes
  (Linux only).
- ``cpustates``: Processes power ftrace to produce CPU state and parallelism
  stats. There is also a script to invoke this outside of WA.

Workloads
~~~~~~~~~
- ``telemetry``: Executes Google's Telemetery benchmarking framework
- ``hackbench``: Hackbench runs tests on the Linux scheduler
- ``ebizzy``: This workload resembles common web server application workloads.
- ``power_loadtest``: Continuously cycles through a set of browser-based
  activities and monitors battery drain on a device (part of ChromeOS autotest
  suite).
- ``rt-app``: Simulates configurable real-time periodic load.
- ``linpack-cli``:  Command line version of linpack benchmark.
- ``lmbench``: A suite of portable ANSI/C microbenchmarks for UNIX/POSIX.
- ``stream``: Measures memory bandwidth.
- ``iozone``: Runs a series of disk I/O performance tests.
- ``androbench``:  Measures the storage performance of device.
- ``autotest``:  Executes tests from ChromeOS autotest suite.

Framework
~~~~~~~~~
- ``wlauto.utils``:
   - Added ``trace_cmd``, a generic trace-cmd paraser.
   - Added ``UbootMenu``, allows navigating Das U-boot menu over serial.
- ``wlauto.utils.types``:
   - ``caseless_string``: Behaves exactly like a string, except this ignores
     case in comparisons. It does, however, preserve case.
   - ``list_of``: allows dynamic generation of type-safe list types based on
     an existing type.
   - ``arguments``: represents arguments that are passed on a command line to
     an application.
   - ``list-or``: allows dynamic generation of types that accept either a base
     type or a list of base type. Using this ``list_or_integer``,
     ``list_or_number`` and ``list_or_bool`` were also added.
- ``wlauto.core.configuration.WorkloadRunSpec``:
   - ``copy``: Allows making duplicates of ``WorkloadRunSpec``'s
- ``wlatuo.utils.misc``:
   - ``list_to_ranges`` and ``ranges_to_list``: convert between lists of
     integers and corresponding range strings, e.g. between [0,1,2,4] and
     '0-2,4'
   - ``list_to_mask`` and ``mask_to_list``: convert between lists of integers
     and corresponding integer masks, e.g. between [0,1,2,4] and 0x17
- ``wlauto.instrumentation``:
   - ``instrument_is_enabled``: Returns whether or not an instrument is
     enabled for the current job.
- ``wlauto.core.result``:
   - Added "classifiers" field to Metric objects. This is a dict mapping
     classifier names (arbitrary strings) to corresponding values for that
     specific metrics. This is to allow extensions to add extension-specific
     annotations to metric that could be handled in a generic way (e.g. by
     result processors). They can also be set in agendas.
- Failed jobs will now be automatically retired
- Implemented dynamic device modules that may be loaded automatically on
  device initialization if the device supports them.
- Added support for YAML configs.
- Added ``initialze`` and ``finalize`` methods to workloads.
- ``wlauto.core.ExecutionContext``:
   - Added ``job_status`` property that returns the status of the currently
     running job.

Fixes/Improvements
##################

Devices
~~~~~~~~
- ``tc2``: Workaround for buffer overrun when loading large initrd blob.
- ``juno``:
     - UEFI config can now be specified as a parameter.
     - Adding support for U-Boot booting.
     - No longer auto-disconnects ADB at the end of a run.
     - Added ``actually_disconnect`` to restore old disconnect behaviour
     - Now passes ``video`` command line to Juno kernel to work around a known
       issue where HDMI loses sync with monitors.
     - Fixed flashing.

Instruments
~~~~~~~~~~~
- ``trace_cmd``:
     - Fixed ``buffer_size_file`` for non-Android devices
     - Reduce starting priority.
     - Now handles trace headers and thread names with spaces
- ``energy_probe``: Added ``device_entry`` parameter.
- ``hwmon``:
     - Sensor discovery is now done only at the start of a run.
     - Now prints both before/after and mean temperatures.
- ``daq``:
     - Now reports energy
     - Fixed file descriptor leak
     - ``daq_power.csv`` now matches the order of labels (if specified).
     - Added ``gpio_sync``. When enabled, this wil cause the instrument to
       insert a marker into ftrace, while at the same time setting a GPIO pin
       high.
     - Added ``negative_values`` parameter. which can be used to specify how
       negative values in the samples should be handled.
     - Added ``merge_channels`` parameter. When set DAQ channel will be summed
       together.
     - Workload labels, rather than names, are now used in the "workload"
       column.
- ``cpufreq``:
     - Fixes missing directories problem.
     - Refined the availability check not to rely on the top-level cpu/cpufreq
       directory
     - Now handles non-integer output in ``get_available_frequencies``.
- ``sysfs_extractor``:
     - No longer raises an error when both device and host paths are empty.
     - Fixed pulled files verification.
- ``perf``:
     - Updated binaries.
     - Added option to force install.
     - ``killall`` is now run as root on rooted Android devices.
- ``fps``:
     - now generates detailed FPS traces as well as report average FPS.
     - Updated jank calcluation to only count "large" janks.
     - Now filters out bogus ``actual-present`` times and ignore janks above
       ``PAUSE_LATENCY``
- ``delay``:
     - Added ``fixed_before_start`` parameter.
     - Changed existing ``*_between_specs`` and ``*_between_iterations``
       callbacks to be ``very_slow``
- ``streamline``:
     - Added Linux support
     - ``gatord`` is now only started once at the start of the run.

modules
~~~~~~~
- ``flashing``:
     - Fixed vexpress flashing
     - Added an option to keep UEFI entry

Result Processors
~~~~~~~~~~~~~~~~~
- ``cpustate``:
     - Now generates a timeline csv as well as stats.
     - Adding ID to overall cpustate reports.
- ``csv``: (partial) ``results.csv`` will now be written after each iteration
  rather than at the end of the run.

Workloads
~~~~~~~~~
- ``glb_corporate``: clears logcat to prevent getting results from previous
  run.
- ``sysbench``:
     - Updated sysbench binary to a statically linked verison
     - Added ``file_test_mode parameter`` - this is a mandatory argumet if
       ``test`` is ``"fileio"``.
     - Added ``cmd_params`` parameter to pass options directily to sysbench
       invocation.
     - Removed Android browser launch and shutdown from workload (now runs on
       both Linux and Android).
     - Now works with unrooted devices.
     - Added the ability to run based on time.
     - Added a parameter to taskset to specific core(s).
     - Added ``threads`` parameter to be consistent with dhrystone.
     - Fixed case where default ``timeout`` < ``max_time``.
- ``Dhrystone``:
     - added ``taskset_mask`` parameter to allow pinning to specific cores.
     - Now kills any running instances during setup (also handles CTRL-C).
- ``sysfs_extractor``: Added parameter to explicitly enable/disable tempfs
  caching.
- ``antutu``:
     - Fixed multi-``times`` playback for v5.
     - Updated result parsing to handle Android M logcat output.
- ``geekbench``: Increased timout to cater for slower devices.
- ``idle``: Now works on Linux devices.
- ``manhattan``: Added ``run_timemout`` parameter.
- ``bbench``: Now works when binaries_directory is not in path.
- ``nemamark``: Made duration configurable.

Framework
~~~~~~~~~~
- ``BaseLinuxDevice``:
     - Now checks that at least one core is enabled on another cluster before
       attempting to set number of cores on a cluster to ``0``.
     - No longer uses ``sudo`` if already logged in as ``root``.
     - Now saves ``dumpsys window`` output to the ``__meta`` directory.
     - Now takes ``password_prompt`` as a parameter for devices with a non
       standard ``sudo`` password prompt.
     - No longer raises an error if ``keyfile`` or ``password`` are not
       provided when they are not necessary.
     - Added new cpufreq APIs:
        - ``core`` APIs take a core name as the parameter (e.g. "a15")
        - ``cluster`` APIs take a numeric cluster ID (eg. 0)
        - ``cpu`` APIs take a cpufreq cpu ID as a parameter.
     - ``set_cpu_frequency`` now has a ``exact`` parameter. When true (the
       default) it will produce an error when the specified frequency is not
       supported by the cpu, otherwise cpufreq will decide what to do.
     - Added ``{core}_frequency`` runtime parameter to set cluster frequency.
     - Added ``abi`` property.
     - ``get_properties`` moved from ``LinuxDevice``, meaning ``AndroidDevice``
       will try to pull the same files. Added more paths to pull by default
       too.
     - fixed ``list_file_systems`` for Android M and Linux devices.
     - Now sets ``core_clusters`` from ``core_names`` if not explicitly
       specified.
     - Added ``invoke`` method that allows invoking an executable on the device
       under controlled contions (e.g. within a particular directory, or
       taskset to specific CPUs).
     - No longer attempts to ``get_sysfile_value()`` as root on unrooted
       devices.
- ``LinuxDevice``:
     - Now creates ``binaries_directory`` path if it doesn't exist.
     - Fixed device reset
     - Fixed ``file_exists``
     - implemented ``get_pid_of()`` and ``ps()``. Existing implementation
       relied on Android version of ps.
     - ``listdir`` will now return an empty list for an empty directory
       instead of a list containing a single empty string.
- ``AndroidDevice``:
     - Executable (un)installation now works on unrooted devices.
     - Now takes into account ``binar_directory`` when setting up busybox path.
     - update ``android_prompt`` so that it works even if is not ``"/"``
     - ``adb_connect``: do not assume port 5555 anymore.
     - Now always deploys busybox on rooted devices.
     - Added ``swipe_to_unlock`` method.
- Fixed initialization of ``~/.workload_automation.``.
- Fixed replaying events using revent on 64 bit platforms.
- Improved error repoting when loading extensions.
- ``result`` objects now track their output directories.
- ``context.result`` will not result in ``context.run_result`` when not
  executing a job.
- ``wlauto.utils.ssh``:
     - Fixed key-based authentication.
     - Fixed carriage return stripping in ssh.
     - Now takes ``password_prompt`` as a parameter for non standard ``sudo``
       password prompts.
     - Now with 100% more thread safety!
     - If a timeout condition is hit, ^C is now sent to kill the current
       foreground process and make the shell available for subsequent commands.
     - More robust ``exit_code`` handling for ssh interface
     - Now attempts to deal with dropped connections
     - Fixed error reporting on failed exit code extraction.
     - Now handles backspaces in serial output
     - Added ``port`` argument for telnet connections.
     - Now allows telnet connections without a password.
- Fixed config processing for extensions with non-identifier names.
- Fixed ``get_meansd`` for numbers < 1
- ``wlatuo.utils.ipython``:
     - Now supports old versions of IPython
     - Updated version check to only initialize ipython utils if version is
       < 4.0.0. Version 4.0.0 changes API and breaks WA's usage of it.
- Added ``ignore`` parameter to ``check_output``
- Agendas:
     - Now raise an error if an agenda contains duplicate keys
     - Now raise an error if config section in an agenda is not dict-like
     - Now properly handles ``core_names`` and ``core_clusters``
     - When merging list parameters from different sources, duplicates are no
       longer removed.
- The ``INITIAL_BOOT`` signal is now sent went performing a hard reset during
  intial boot
- updated ``ExecutionContext`` to keep a reference to the ``runner``. This
  will enable Extenstions to do things like modify the job queue.
- Parameter now automatically convert int and boot kinds to integer and
  boolean respectively, this behavior can be supressed by specifying
  ``convert_types``=``False`` when defining the parameter.
- Fixed resource resolution when dependency location does not exist.
- All device ``push`` and ``pull`` commands now raise ``DeviceError`` if they
  didn't succeed.
- Fixed showing Parameter default of ``False`` for boolean values.
- Updated csv result processor with the option to use classifiers to
  add columns to ``results.csv``.
- ``wlauto.utils.formatter``: Fix terminal size discovery.
- The extension loader will now follow symlinks.
- Added arm64-v8a to ABI map
- WA now reports syntax errors in a more informative way.
- Resource resolver: now prints the path of the found resource to the log.
- Resource getter: look for executable in the bin/ directory under resource
  owner's dependencies directory as well as general dependencies bin.
- ``GamingWorkload``:
     - Added an option to prevent clearing of package data before execution.
     - Added the ability to override the timeout of deploying the assets
       tarball.
- ``ApkWorkload``: Added an option to skip host-side APK check entirely.
- ``utils.misc.normalize``: only normalize string keys.
- Better error reporting for subprocess.CalledProcessError
- ``boolean`` now interprets ``'off'`` as ``False``
- ``wlauto.utils.uefi``: Added support for debug builds.
- ``wlauto.utils.serial_port``: Now supports fdexpect versions > 4.0.0
- Semanatics for ``initialize``/``finalize`` for *all* Extensions are changed
  so that now they will always run at most once per run. They will not be
  executed twice even if invoked via instances of different subclasses (if
  those subclasses defined their own verions, then their versions will be
  invoked once each, but the base version will only get invoked once).
- Pulling entries from procfs does not work on some platforms. WA now tries
  to cat the contents of a property_file and write it to a output file on the
  host.

Documentation
~~~~~~~~~~~~~
- ``installation``:
     - Added ``post install`` section which lists workloads that require
       additional external dependencies.
     - Added the ``uninstall`` and ``upgrade`` commands for users to remove or
       upgrade Workload Automation.
     - Added documentation explaining how to use ``remote_assets_path``
       setting.
     - Added warning about potential permission issues with pip.
- ``quickstart``: Added steps for setting up WA to run on Linux devices.
- ``device_setup``: fixed ``generic_linux`` ``device_config`` example.
- ``contributing``: Clarified style guidelines
- ``daq_device_setup``: Added an illustration for DAQ wiring.
- ``writing_extensions``: Documented the Workload initialize and finalize
  methods.
- Added descriptions to extension that didn't have one.

Other
~~~~~
- ``daq_server``:
     - Fixed showing available devices.
     - Now works with earlier versions of the DAQmx driver.thus you can now run
       the server on Linux systems.
     - DAQ error messages are now properly propaged to the client.
     - Server will now periodically clean up uncollected files.
     - fixed not being able to resolve IP address for hostname
       (report "localhost" in that case).
     - Works with latest version of twisted.
- ``setup.py``: Fixed paths to work with Mac OS X.
- ``summary_csv`` is no longer enabled by default.
- ``status`` result processor is now enabled by default.
- Commands:
     - ``show``:
         - Now shows what platform extensions support.
         - Will no longer try to use a pager if ``PAGER=''`` in the environment.
     - ``list``:
         - Added ``"-p"`` option to filter results by supported platforms.
         - Added ``"--packaged-only"`` option to only list extensions packaged
           with WA.
     - ``run``: Added ``"--disable"`` option to diable instruments.
     - ``create``:
         - Added ``agenda`` sub-command to generate agendas for a set of
           extensions.
         - ``create workload`` now gives more informative errors if Android SDK
           installed but no platform has been downloaded.

Incompatible changes
####################

Framework
~~~~~~~~~
- ``BaseLinuxDevice``:
     - Renamed ``active_cpus`` to ``online_cpus``
     - Renamed ``get_cluster_cpu`` to ``get_cluster_active_cpu``
     - Renamed ``get_core_cpu`` to ``get_core_online_cpu``
- All extension's ``initialize`` function now takes one (and only one)
  parameter, ``context``.
- ``wlauto.core.device``: Removed ``init`` function. Replaced with
  ``initialize``

-------------
Version 2.3.0
-------------

- First publicly-released version.
