.. _devices:

Devices
=======

Nexus10
-------

Nexus10 is a 10 inch tablet device, which has dual-core A15.

To be able to use Nexus10 in WA, the following must be true:

    - USB Debugging Mode is enabled.
    - Generate USB debugging authorisation for the host machine

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

core_names : list_of_caseless_strings (mandatory)
    This is a list of all cpu cores on the device with each
    element being the core type, e.g. ``['a7', 'a7', 'a15']``. The
    order of the cores must match the order they are listed in
    ``'/sys/devices/system/cpu'``. So in this case, ``'cpu0'`` must
    be an A7 core, and ``'cpu2'`` an A15.'

    default: ``['A15', 'A15']``

core_clusters : list_of_ints (mandatory)
    This is a list indicating the cluster affinity of the CPU cores,
    each element correponding to the cluster ID of the core coresponding
    to it's index. E.g. ``[0, 0, 1]`` indicates that cpu0 and cpu1 are on
    cluster 0, while cpu2 is on cluster 1. If this is not specified, this
    will be inferred from ``core_names`` if possible (assuming all cores with
    the same name are on the same cluster).

    default: ``[0, 0]``

scheduler : str  
    Specifies the type of multi-core scheduling model utilized in the device. The value
    must be one of the following:

    :unknown: A generic Device interface is used to interact with the underlying device
              and the underlying scheduling model is unkown.
    :smp: A standard single-core or Symmetric Multi-Processing system.
    :hmp: ARM Heterogeneous Multi-Processing system.
    :iks: Linaro In-Kernel Switcher.
    :ea: ARM Energy-Aware scheduler.
    :other: Any other system not covered by the above.

            .. note:: most currently-available systems would fall under ``smp`` rather than
                      this value. ``other`` is there to future-proof against new schemes
                      not yet covered by WA.

    allowed values: ``'unknown'``, ``'smp'``, ``'hmp'``, ``'iks'``, ``'ea'``, ``'other'``

    default: ``'unknown'``

iks_switch_frequency : integer  
    This is the switching frequency, in kilohertz, of IKS devices. This parameter *MUST NOT*
    be set for non-IKS device (i.e. ``scheduler != 'iks'``). If left unset for IKS devices,
    it will default to ``800000``, i.e. 800MHz.

property_files : list_of_strs  
    A list of paths to files containing static OS properties. These will be pulled into the
    __meta directory in output for each run in order to provide information about the platfrom.
    These paths do not have to exist and will be ignored if the path is not present on a
    particular device.

    default: ``['/etc/arch-release', '/etc/debian_version', '/etc/lsb-release', '/proc/config.gz', '/proc/cmdline', '/proc/cpuinfo', '/proc/version', '/proc/zconfig', '/sys/kernel/debug/sched_features', '/sys/kernel/hmp']``

binaries_directory : str  
    Location of executable binaries on this device (must be in PATH).

    default: ``'/data/local/tmp'``

adb_name : str  
    The unique ID of the device as output by "adb devices".

android_prompt : regex  
    The format  of matching the shell prompt in Android.

    default: ``r'^.*(shell|root)@.*:/\S* [#$] '``

working_directory : str  
    Directory that will be used WA on the device for output files etc.

    default: ``'/sdcard/wa-working'``

package_data_directory : str  
    Location of of data for an installed package (APK).

    default: ``'/data/data'``

external_storage_directory : str  
    Mount point for external storage.

    default: ``'/sdcard'``

connection : str  
    Specified the nature of adb connection.

    allowed values: ``'usb'``, ``'ethernet'``

    default: ``'usb'``

logcat_poll_period : integer  
    If specified and is not ``0``, logcat will be polled every
    ``logcat_poll_period`` seconds, and buffered on the host. This
    can be used if a lot of output is expected in logcat and the fixed
    logcat buffer on the device is not big enough. The trade off is that
    this introduces some minor runtime overhead. Not set by default.

enable_screen_check : boolean  
    Specified whether the device should make sure that the screen is on
    during initialization.

swipe_to_unlock : str  
    If set a swipe of the specified direction will be performed.
    This should unlock the screen.

    allowed values: ``None``, ``'horizontal'``, ``'vertical'``


Nexus5
------

Adapter for Nexus 5.

To be able to use Nexus5 in WA, the following must be true:

    - USB Debugging Mode is enabled.
    - Generate USB debugging authorisation for the host machine

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

core_names : list_of_caseless_strings (mandatory)
    This is a list of all cpu cores on the device with each
    element being the core type, e.g. ``['a7', 'a7', 'a15']``. The
    order of the cores must match the order they are listed in
    ``'/sys/devices/system/cpu'``. So in this case, ``'cpu0'`` must
    be an A7 core, and ``'cpu2'`` an A15.'

    default: ``['krait400', 'krait400', 'krait400', 'krait400']``

core_clusters : list_of_ints (mandatory)
    This is a list indicating the cluster affinity of the CPU cores,
    each element correponding to the cluster ID of the core coresponding
    to it's index. E.g. ``[0, 0, 1]`` indicates that cpu0 and cpu1 are on
    cluster 0, while cpu2 is on cluster 1. If this is not specified, this
    will be inferred from ``core_names`` if possible (assuming all cores with
    the same name are on the same cluster).

    default: ``[0, 0, 0, 0]``

scheduler : str  
    Specifies the type of multi-core scheduling model utilized in the device. The value
    must be one of the following:

    :unknown: A generic Device interface is used to interact with the underlying device
              and the underlying scheduling model is unkown.
    :smp: A standard single-core or Symmetric Multi-Processing system.
    :hmp: ARM Heterogeneous Multi-Processing system.
    :iks: Linaro In-Kernel Switcher.
    :ea: ARM Energy-Aware scheduler.
    :other: Any other system not covered by the above.

            .. note:: most currently-available systems would fall under ``smp`` rather than
                      this value. ``other`` is there to future-proof against new schemes
                      not yet covered by WA.

    allowed values: ``'unknown'``, ``'smp'``, ``'hmp'``, ``'iks'``, ``'ea'``, ``'other'``

    default: ``'unknown'``

iks_switch_frequency : integer  
    This is the switching frequency, in kilohertz, of IKS devices. This parameter *MUST NOT*
    be set for non-IKS device (i.e. ``scheduler != 'iks'``). If left unset for IKS devices,
    it will default to ``800000``, i.e. 800MHz.

property_files : list_of_strs  
    A list of paths to files containing static OS properties. These will be pulled into the
    __meta directory in output for each run in order to provide information about the platfrom.
    These paths do not have to exist and will be ignored if the path is not present on a
    particular device.

    default: ``['/etc/arch-release', '/etc/debian_version', '/etc/lsb-release', '/proc/config.gz', '/proc/cmdline', '/proc/cpuinfo', '/proc/version', '/proc/zconfig', '/sys/kernel/debug/sched_features', '/sys/kernel/hmp']``

binaries_directory : str  
    Location of executable binaries on this device (must be in PATH).

    default: ``'/data/local/tmp'``

adb_name : str  
    The unique ID of the device as output by "adb devices".

android_prompt : regex  
    The format  of matching the shell prompt in Android.

    default: ``r'^.*(shell|root)@.*:/\S* [#$] '``

working_directory : str  
    Directory that will be used WA on the device for output files etc.

    default: ``'/sdcard/wa-working'``

package_data_directory : str  
    Location of of data for an installed package (APK).

    default: ``'/data/data'``

external_storage_directory : str  
    Mount point for external storage.

    default: ``'/sdcard'``

connection : str  
    Specified the nature of adb connection.

    allowed values: ``'usb'``, ``'ethernet'``

    default: ``'usb'``

logcat_poll_period : integer  
    If specified and is not ``0``, logcat will be polled every
    ``logcat_poll_period`` seconds, and buffered on the host. This
    can be used if a lot of output is expected in logcat and the fixed
    logcat buffer on the device is not big enough. The trade off is that
    this introduces some minor runtime overhead. Not set by default.

enable_screen_check : boolean  
    Specified whether the device should make sure that the screen is on
    during initialization.

swipe_to_unlock : str  
    If set a swipe of the specified direction will be performed.
    This should unlock the screen.

    allowed values: ``None``, ``'horizontal'``, ``'vertical'``


Note3
-----

Adapter for Galaxy Note 3.

To be able to use Note3 in WA, the following must be true:

    - USB Debugging Mode is enabled.
    - Generate USB debugging authorisation for the host machine

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

core_names : list_of_caseless_strings (mandatory)
    This is a list of all cpu cores on the device with each
    element being the core type, e.g. ``['a7', 'a7', 'a15']``. The
    order of the cores must match the order they are listed in
    ``'/sys/devices/system/cpu'``. So in this case, ``'cpu0'`` must
    be an A7 core, and ``'cpu2'`` an A15.'

    default: ``['A15', 'A15', 'A15', 'A15']``

core_clusters : list_of_ints (mandatory)
    This is a list indicating the cluster affinity of the CPU cores,
    each element correponding to the cluster ID of the core coresponding
    to it's index. E.g. ``[0, 0, 1]`` indicates that cpu0 and cpu1 are on
    cluster 0, while cpu2 is on cluster 1. If this is not specified, this
    will be inferred from ``core_names`` if possible (assuming all cores with
    the same name are on the same cluster).

    default: ``[0, 0, 0, 0]``

scheduler : str  
    Specifies the type of multi-core scheduling model utilized in the device. The value
    must be one of the following:

    :unknown: A generic Device interface is used to interact with the underlying device
              and the underlying scheduling model is unkown.
    :smp: A standard single-core or Symmetric Multi-Processing system.
    :hmp: ARM Heterogeneous Multi-Processing system.
    :iks: Linaro In-Kernel Switcher.
    :ea: ARM Energy-Aware scheduler.
    :other: Any other system not covered by the above.

            .. note:: most currently-available systems would fall under ``smp`` rather than
                      this value. ``other`` is there to future-proof against new schemes
                      not yet covered by WA.

    allowed values: ``'unknown'``, ``'smp'``, ``'hmp'``, ``'iks'``, ``'ea'``, ``'other'``

    default: ``'unknown'``

iks_switch_frequency : integer  
    This is the switching frequency, in kilohertz, of IKS devices. This parameter *MUST NOT*
    be set for non-IKS device (i.e. ``scheduler != 'iks'``). If left unset for IKS devices,
    it will default to ``800000``, i.e. 800MHz.

property_files : list_of_strs  
    A list of paths to files containing static OS properties. These will be pulled into the
    __meta directory in output for each run in order to provide information about the platfrom.
    These paths do not have to exist and will be ignored if the path is not present on a
    particular device.

    default: ``['/etc/arch-release', '/etc/debian_version', '/etc/lsb-release', '/proc/config.gz', '/proc/cmdline', '/proc/cpuinfo', '/proc/version', '/proc/zconfig', '/sys/kernel/debug/sched_features', '/sys/kernel/hmp']``

binaries_directory : str  
    Location of executable binaries on this device (must be in PATH).

    default: ``'/data/local/tmp'``

adb_name : str  
    The unique ID of the device as output by "adb devices".

android_prompt : regex  
    The format  of matching the shell prompt in Android.

    default: ``r'^.*(shell|root)@.*:/\S* [#$] '``

working_directory : str  
    Directory that will be used WA on the device for output files etc.

    default: ``'/storage/sdcard0/wa-working'``

package_data_directory : str  
    Location of of data for an installed package (APK).

    default: ``'/data/data'``

external_storage_directory : str  
    Mount point for external storage.

    default: ``'/sdcard'``

connection : str  
    Specified the nature of adb connection.

    allowed values: ``'usb'``, ``'ethernet'``

    default: ``'usb'``

logcat_poll_period : integer  
    If specified and is not ``0``, logcat will be polled every
    ``logcat_poll_period`` seconds, and buffered on the host. This
    can be used if a lot of output is expected in logcat and the fixed
    logcat buffer on the device is not big enough. The trade off is that
    this introduces some minor runtime overhead. Not set by default.

enable_screen_check : boolean  
    Specified whether the device should make sure that the screen is on
    during initialization.

swipe_to_unlock : str  
    If set a swipe of the specified direction will be performed.
    This should unlock the screen.

    allowed values: ``None``, ``'horizontal'``, ``'vertical'``


TC2
---

TC2 is a development board, which has three A7 cores and two A15 cores.

TC2 has a number of boot parameters which are:

    :root_mount: Defaults to '/media/VEMSD'
    :boot_firmware: It has only two boot firmware options, which are
                    uefi and bootmon. Defaults to 'uefi'.
    :fs_medium: Defaults to 'usb'.
    :device_working_directory: The direcitory that WA will be using to copy
                               files to. Defaults to 'data/local/usecase'
    :serial_device: The serial device which TC2 is connected to. Defaults to
                    '/dev/ttyS0'.
    :serial_baud: Defaults to 38400.
    :serial_max_timeout: Serial timeout value in seconds. Defaults to 600.
    :serial_log: Defaults to standard output.
    :init_timeout: The timeout in seconds to init the device. Defaults set
                   to 30.
    :always_delete_uefi_entry: If true, it will delete the ufi entry.
                               Defaults to True.
    :psci_enable: Enabling the psci. Defaults to True.
    :host_working_directory: The host working directory. Defaults to None.
    :disable_boot_configuration: Disables boot configuration through images.txt and board.txt. When
                                 this is ``True``, those two files will not be overwritten in VEMSD.
                                 This option may be necessary if the firmware version in the ``TC2``
                                 is not compatible with the templates in WA. Please note that enabling
                                 this will prevent you form being able to set ``boot_firmware`` and
                                 ``mode`` parameters. Defaults to ``False``.

TC2 can also have a number of different booting mode, which are:

    :mp_a7_only: Only the A7 cluster.
    :mp_a7_bootcluster: Both A7 and A15 clusters, but it boots on A7
                        cluster.
    :mp_a15_only: Only the A15 cluster.
    :mp_a15_bootcluster: Both A7 and A15 clusters, but it boots on A15
                         clusters.
    :iks_cpu: Only A7 cluster with only 2 cpus.
    :iks_a15: Only A15 cluster.
    :iks_a7: Same as iks_cpu
    :iks_ns_a15: Both A7 and A15 clusters.
    :iks_ns_a7: Both A7 and A15 clusters.

The difference between mp and iks is the scheduling policy.

TC2 takes the following runtime parameters

    :a7_cores: Number of active A7 cores.
    :a15_cores: Number of active A15 cores.
    :a7_governor: CPUFreq governor for the A7 cluster.
    :a15_governor: CPUFreq governor for the A15 cluster.
    :a7_min_frequency: Minimum CPU frequency for the A7 cluster.
    :a15_min_frequency: Minimum CPU frequency for the A15 cluster.
    :a7_max_frequency: Maximum CPU frequency for the A7 cluster.
    :a15_max_frequency: Maximum CPU frequency for the A7 cluster.
    :irq_affinity: lambda x: Which cluster will receive IRQs.
    :cpuidle: Whether idle states should be enabled.
    :sysfile_values: A dict mapping a complete file path to the value that
                     should be echo'd into it. By default, the file will be
                     subsequently read to verify that the value was written
                     into it with DeviceError raised otherwise. For write-only
                     files, this check can be disabled by appending a ``!`` to
                     the end of the file path.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

core_names : list_of_caseless_strings  
    This parameter will be ignored for TC2

core_clusters : list_of_ints  
    This parameter will be ignored for TC2

scheduler : str  
    Specifies the type of multi-core scheduling model utilized in the device. The value
    must be one of the following:

    :unknown: A generic Device interface is used to interact with the underlying device
              and the underlying scheduling model is unkown.
    :smp: A standard single-core or Symmetric Multi-Processing system.
    :hmp: ARM Heterogeneous Multi-Processing system.
    :iks: Linaro In-Kernel Switcher.
    :ea: ARM Energy-Aware scheduler.
    :other: Any other system not covered by the above.

            .. note:: most currently-available systems would fall under ``smp`` rather than
                      this value. ``other`` is there to future-proof against new schemes
                      not yet covered by WA.

    allowed values: ``'unknown'``, ``'smp'``, ``'hmp'``, ``'iks'``, ``'ea'``, ``'other'``

    default: ``'hmp'``

iks_switch_frequency : integer  
    This is the switching frequency, in kilohertz, of IKS devices. This parameter *MUST NOT*
    be set for non-IKS device (i.e. ``scheduler != 'iks'``). If left unset for IKS devices,
    it will default to ``800000``, i.e. 800MHz.

property_files : list_of_strs  
    A list of paths to files containing static OS properties. These will be pulled into the
    __meta directory in output for each run in order to provide information about the platfrom.
    These paths do not have to exist and will be ignored if the path is not present on a
    particular device.

    default: ``['/etc/arch-release', '/etc/debian_version', '/etc/lsb-release', '/proc/config.gz', '/proc/cmdline', '/proc/cpuinfo', '/proc/version', '/proc/zconfig', '/sys/kernel/debug/sched_features', '/sys/kernel/hmp']``

binaries_directory : str  
    Location of executable binaries on this device (must be in PATH).

    default: ``'/data/local/tmp'``

adb_name : str  
    The unique ID of the device as output by "adb devices".

android_prompt : regex  
    The format  of matching the shell prompt in Android.

    default: ``r'^.*(shell|root)@.*:/\S* [#$] '``

working_directory : str  
    Directory that will be used WA on the device for output files etc.

    default: ``'/sdcard/wa-working'``

package_data_directory : str  
    Location of of data for an installed package (APK).

    default: ``'/data/data'``

external_storage_directory : str  
    Mount point for external storage.

    default: ``'/sdcard'``

connection : str  
    Specified the nature of adb connection.

    allowed values: ``'usb'``, ``'ethernet'``

    default: ``'usb'``

logcat_poll_period : integer  
    If specified and is not ``0``, logcat will be polled every
    ``logcat_poll_period`` seconds, and buffered on the host. This
    can be used if a lot of output is expected in logcat and the fixed
    logcat buffer on the device is not big enough. The trade off is that
    this introduces some minor runtime overhead. Not set by default.

enable_screen_check : boolean  
    Specified whether the device should make sure that the screen is on
    during initialization.

swipe_to_unlock : str  
    If set a swipe of the specified direction will be performed.
    This should unlock the screen.

    allowed values: ``None``, ``'horizontal'``, ``'vertical'``


XE503C12
--------

A developer-unlocked Samsung XE503C12 running sshd.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

core_names : list_of_caseless_strings (mandatory)
    This is a list of all cpu cores on the device with each
    element being the core type, e.g. ``['a7', 'a7', 'a15']``. The
    order of the cores must match the order they are listed in
    ``'/sys/devices/system/cpu'``. So in this case, ``'cpu0'`` must
    be an A7 core, and ``'cpu2'`` an A15.'

    default: ``['a15', 'a15', 'a15', 'a15']``

core_clusters : list_of_ints (mandatory)
    This is a list indicating the cluster affinity of the CPU cores,
    each element correponding to the cluster ID of the core coresponding
    to it's index. E.g. ``[0, 0, 1]`` indicates that cpu0 and cpu1 are on
    cluster 0, while cpu2 is on cluster 1. If this is not specified, this
    will be inferred from ``core_names`` if possible (assuming all cores with
    the same name are on the same cluster).

    default: ``[0, 0, 0, 0]``

scheduler : str  
    Specifies the type of multi-core scheduling model utilized in the device. The value
    must be one of the following:

    :unknown: A generic Device interface is used to interact with the underlying device
              and the underlying scheduling model is unkown.
    :smp: A standard single-core or Symmetric Multi-Processing system.
    :hmp: ARM Heterogeneous Multi-Processing system.
    :iks: Linaro In-Kernel Switcher.
    :ea: ARM Energy-Aware scheduler.
    :other: Any other system not covered by the above.

            .. note:: most currently-available systems would fall under ``smp`` rather than
                      this value. ``other`` is there to future-proof against new schemes
                      not yet covered by WA.

    allowed values: ``'unknown'``, ``'smp'``, ``'hmp'``, ``'iks'``, ``'ea'``, ``'other'``

    default: ``'unknown'``

iks_switch_frequency : integer  
    This is the switching frequency, in kilohertz, of IKS devices. This parameter *MUST NOT*
    be set for non-IKS device (i.e. ``scheduler != 'iks'``). If left unset for IKS devices,
    it will default to ``800000``, i.e. 800MHz.

property_files : list_of_strs  
    A list of paths to files containing static OS properties. These will be pulled into the
    __meta directory in output for each run in order to provide information about the platfrom.
    These paths do not have to exist and will be ignored if the path is not present on a
    particular device.

    default: ``['/etc/arch-release', '/etc/debian_version', '/etc/lsb-release', '/proc/config.gz', '/proc/cmdline', '/proc/cpuinfo', '/proc/version', '/proc/zconfig', '/sys/kernel/debug/sched_features', '/sys/kernel/hmp']``

binaries_directory : str  
    Location of executable binaries on this device (must be in PATH).

    default: ``'/home/chronos/bin'``

host : str (mandatory)
    Host name or IP address for the device.

username : str (mandatory)
    User name for the account on the device.

    default: ``'chronos'``

password : str  
    Password for the account on the device (for password-based auth).

keyfile : str  
    Keyfile to be used for key-based authentication.

port : integer  
    SSH port number on the device.

    default: ``22``

password_prompt : str  
    Prompt presented by sudo when requesting the password.

    default: ``'Password:'``

use_telnet : boolean  
    Optionally, telnet may be used instead of ssh, though this is discouraged.

boot_timeout : integer  
    How long to try to connect to the device after a reboot.

    default: ``120``

working_directory : str  
    Working directory to be used by WA. This must be in a location where the specified user
    has write permissions. This will default to /home/<username>/wa (or to /root/wa, if
    username is 'root').


chromeos_test_image
-------------------

Chrome OS test image device. Use this if you are working on a Chrome OS device with a test
image. An off the shelf device will not work with this device interface.

More information on how to build a Chrome OS test image can be found here:

    https://www.chromium.org/chromium-os/developer-guide#TOC-Build-a-disk-image-for-your-board

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

core_names : list_of_caseless_strings (mandatory)
    This is a list of all cpu cores on the device with each
    element being the core type, e.g. ``['a7', 'a7', 'a15']``. The
    order of the cores must match the order they are listed in
    ``'/sys/devices/system/cpu'``. So in this case, ``'cpu0'`` must
    be an A7 core, and ``'cpu2'`` an A15.'

core_clusters : list_of_ints (mandatory)
    This is a list indicating the cluster affinity of the CPU cores,
    each element correponding to the cluster ID of the core coresponding
    to it's index. E.g. ``[0, 0, 1]`` indicates that cpu0 and cpu1 are on
    cluster 0, while cpu2 is on cluster 1. If this is not specified, this
    will be inferred from ``core_names`` if possible (assuming all cores with
    the same name are on the same cluster).

scheduler : str  
    Specifies the type of multi-core scheduling model utilized in the device. The value
    must be one of the following:

    :unknown: A generic Device interface is used to interact with the underlying device
              and the underlying scheduling model is unkown.
    :smp: A standard single-core or Symmetric Multi-Processing system.
    :hmp: ARM Heterogeneous Multi-Processing system.
    :iks: Linaro In-Kernel Switcher.
    :ea: ARM Energy-Aware scheduler.
    :other: Any other system not covered by the above.

            .. note:: most currently-available systems would fall under ``smp`` rather than
                      this value. ``other`` is there to future-proof against new schemes
                      not yet covered by WA.

    allowed values: ``'unknown'``, ``'smp'``, ``'hmp'``, ``'iks'``, ``'ea'``, ``'other'``

    default: ``'unknown'``

iks_switch_frequency : integer  
    This is the switching frequency, in kilohertz, of IKS devices. This parameter *MUST NOT*
    be set for non-IKS device (i.e. ``scheduler != 'iks'``). If left unset for IKS devices,
    it will default to ``800000``, i.e. 800MHz.

property_files : list_of_strs  
    A list of paths to files containing static OS properties. These will be pulled into the
    __meta directory in output for each run in order to provide information about the platfrom.
    These paths do not have to exist and will be ignored if the path is not present on a
    particular device.

    default: ``['/etc/arch-release', '/etc/debian_version', '/etc/lsb-release', '/proc/config.gz', '/proc/cmdline', '/proc/cpuinfo', '/proc/version', '/proc/zconfig', '/sys/kernel/debug/sched_features', '/sys/kernel/hmp']``

binaries_directory : str  
    Location of executable binaries on this device (must be in PATH).

    default: ``'/usr/local/bin'``

host : str (mandatory)
    Host name or IP address for the device.

username : str (mandatory)
    User name for the account on the device.

    default: ``'root'``

password : str  
    Password for the account on the device (for password-based auth).

keyfile : str  
    Keyfile to be used for key-based authentication.

port : integer  
    SSH port number on the device.

    default: ``22``

password_prompt : str  
    Prompt presented by sudo when requesting the password.

    default: ``'Password:'``

use_telnet : boolean  
    Optionally, telnet may be used instead of ssh, though this is discouraged.

boot_timeout : integer  
    How long to try to connect to the device after a reboot.

    default: ``120``

working_directory : str  
    Working directory to be used by WA. This must be in a location where the specified user
    has write permissions. This will default to /home/<username>/wa (or to /root/wa, if
    username is 'root').

    default: ``'/home/root/wa-working'``


gem5_android
------------

Implements gem5 Android device.

This class allows a user to connect WA to a simulation using gem5. The
connection to the device is made using the telnet connection of the
simulator, and is used for all commands. The simulator does not have ADB
support, and therefore we need to fall back to using standard shell
commands.

Files are copied into the simulation using a VirtIO 9P device in gem5. Files
are copied out of the simulated environment using the m5 writefile command
within the simulated system.

When starting the workload run, the simulator is automatically started by
Workload Automation, and a connection to the simulator is established. WA
will then wait for Android to boot on the simulated system (which can take
hours), prior to executing any other commands on the device. It is also
possible to resume from a checkpoint when starting the simulation. To do
this, please append the relevant checkpoint commands from the gem5
simulation script to the gem5_discription argument in the agenda.

Host system requirements:
    * VirtIO support. We rely on diod on the host system. This can be
      installed on ubuntu using the following command:

            sudo apt-get install diod

Guest requirements:
    * VirtIO support. We rely on VirtIO to move files into the simulation.
      Please make sure that the following are set in the kernel
      configuration:

            CONFIG_NET_9P=y

            CONFIG_NET_9P_VIRTIO=y

            CONFIG_9P_FS=y

            CONFIG_9P_FS_POSIX_ACL=y

            CONFIG_9P_FS_SECURITY=y

            CONFIG_VIRTIO_BLK=y

    * m5 binary. Please make sure that the m5 binary is on the device and
      can by found in the path.

parameters
~~~~~~~~~~

gem5_binary : str  
    Command used to execute gem5. Adjust according to needs.

    default: ``'./build/ARM/gem5.fast'``

gem5_args : arguments (mandatory)
    Command line passed to the gem5 simulation. This command line is used to set up the simulated system, and should be the same as used for a standard gem5 simulation without workload automation. Note that this is simulation script specific and will hence need to be tailored to each particular use case.

gem5_vio_args : arguments (mandatory)
    gem5 VirtIO command line used to enable the VirtIO device in the simulated system. At the very least, the root parameter of the VirtIO9PDiod device must be exposed on the command line. Please set this root mount to {}, as it will be replaced with the directory used by Workload Automation at runtime.

    constraint: ``"{}" in str(value)``

temp_dir : str  
    Temporary directory used to pass files into the gem5 simulation. Workload Automation will automatically create a directory in this folder, and will remove it again once the simulation completes.

    default: ``'/tmp'``

checkpoint : boolean  
    This parameter tells Workload Automation to create a checkpoint of the simulated system once the guest system has finished booting. This checkpoint can then be used at a later stage by other WA runs to avoid booting the guest system a second time. Set to True to take a checkpoint of the simulated system post boot.

run_delay : integer  
    This sets the time that the system should sleep in the simulated system prior to running and workloads or taking checkpoints. This allows the system to quieten down prior to running the workloads. When this is combined with the checkpoint_post_boot option, it allows the checkpoint to be created post-sleep, and therefore the set of workloads resuming from this checkpoint will not be required to sleep.

    constraint: ``value >= 0``

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

core_names : list_of_caseless_strings (mandatory)
    This is a list of all cpu cores on the device with each
    element being the core type, e.g. ``['a7', 'a7', 'a15']``. The
    order of the cores must match the order they are listed in
    ``'/sys/devices/system/cpu'``. So in this case, ``'cpu0'`` must
    be an A7 core, and ``'cpu2'`` an A15.'

core_clusters : list_of_ints (mandatory)
    This is a list indicating the cluster affinity of the CPU cores,
    each element correponding to the cluster ID of the core coresponding
    to it's index. E.g. ``[0, 0, 1]`` indicates that cpu0 and cpu1 are on
    cluster 0, while cpu2 is on cluster 1. If this is not specified, this
    will be inferred from ``core_names`` if possible (assuming all cores with
    the same name are on the same cluster).

scheduler : str  
    Specifies the type of multi-core scheduling model utilized in the device. The value
    must be one of the following:

    :unknown: A generic Device interface is used to interact with the underlying device
              and the underlying scheduling model is unkown.
    :smp: A standard single-core or Symmetric Multi-Processing system.
    :hmp: ARM Heterogeneous Multi-Processing system.
    :iks: Linaro In-Kernel Switcher.
    :ea: ARM Energy-Aware scheduler.
    :other: Any other system not covered by the above.

            .. note:: most currently-available systems would fall under ``smp`` rather than
                      this value. ``other`` is there to future-proof against new schemes
                      not yet covered by WA.

    allowed values: ``'unknown'``, ``'smp'``, ``'hmp'``, ``'iks'``, ``'ea'``, ``'other'``

    default: ``'unknown'``

iks_switch_frequency : integer  
    This is the switching frequency, in kilohertz, of IKS devices. This parameter *MUST NOT*
    be set for non-IKS device (i.e. ``scheduler != 'iks'``). If left unset for IKS devices,
    it will default to ``800000``, i.e. 800MHz.

property_files : list_of_strs  
    A list of paths to files containing static OS properties. These will be pulled into the
    __meta directory in output for each run in order to provide information about the platfrom.
    These paths do not have to exist and will be ignored if the path is not present on a
    particular device.

    default: ``['/etc/arch-release', '/etc/debian_version', '/etc/lsb-release', '/proc/config.gz', '/proc/cmdline', '/proc/cpuinfo', '/proc/version', '/proc/zconfig', '/sys/kernel/debug/sched_features', '/sys/kernel/hmp']``

binaries_directory : str  
    Location of executable binaries on this device (must be in PATH).

    default: ``'/data/local/tmp'``

adb_name : str  
    The unique ID of the device as output by "adb devices".

android_prompt : regex  
    The format  of matching the shell prompt in Android.

    default: ``r'^.*(shell|root)@.*:/\S* [#$] '``

working_directory : str  
    Directory that will be used WA on the device for output files etc.

    default: ``'/sdcard/wa-working'``

package_data_directory : str  
    Location of of data for an installed package (APK).

    default: ``'/data/data'``

external_storage_directory : str  
    Mount point for external storage.

    default: ``'/sdcard'``

connection : str  
    Specified the nature of adb connection.

    allowed values: ``'usb'``, ``'ethernet'``

    default: ``'usb'``

logcat_poll_period : integer  
    If specified and is not ``0``, logcat will be polled every
    ``logcat_poll_period`` seconds, and buffered on the host. This
    can be used if a lot of output is expected in logcat and the fixed
    logcat buffer on the device is not big enough. The trade off is that
    this introduces some minor runtime overhead. Not set by default.

enable_screen_check : boolean  
    Specified whether the device should make sure that the screen is on
    during initialization.

swipe_to_unlock : str  
    If set a swipe of the specified direction will be performed.
    This should unlock the screen.

    allowed values: ``None``, ``'horizontal'``, ``'vertical'``


gem5_linux
----------

Implements gem5 Linux device.

This class allows a user to connect WA to a simulation using gem5. The
connection to the device is made using the telnet connection of the
simulator, and is used for all commands. The simulator does not have ADB
support, and therefore we need to fall back to using standard shell
commands.

Files are copied into the simulation using a VirtIO 9P device in gem5. Files
are copied out of the simulated environment using the m5 writefile command
within the simulated system.

When starting the workload run, the simulator is automatically started by
Workload Automation, and a connection to the simulator is established. WA
will then wait for Android to boot on the simulated system (which can take
hours), prior to executing any other commands on the device. It is also
possible to resume from a checkpoint when starting the simulation. To do
this, please append the relevant checkpoint commands from the gem5
simulation script to the gem5_discription argument in the agenda.

Host system requirements:
    * VirtIO support. We rely on diod on the host system. This can be
      installed on ubuntu using the following command:

            sudo apt-get install diod

Guest requirements:
    * VirtIO support. We rely on VirtIO to move files into the simulation.
      Please make sure that the following are set in the kernel
      configuration:

            CONFIG_NET_9P=y

            CONFIG_NET_9P_VIRTIO=y

            CONFIG_9P_FS=y

            CONFIG_9P_FS_POSIX_ACL=y

            CONFIG_9P_FS_SECURITY=y

            CONFIG_VIRTIO_BLK=y

    * m5 binary. Please make sure that the m5 binary is on the device and
      can by found in the path.

parameters
~~~~~~~~~~

gem5_binary : str  
    Command used to execute gem5. Adjust according to needs.

    default: ``'./build/ARM/gem5.fast'``

gem5_args : arguments (mandatory)
    Command line passed to the gem5 simulation. This command line is used to set up the simulated system, and should be the same as used for a standard gem5 simulation without workload automation. Note that this is simulation script specific and will hence need to be tailored to each particular use case.

gem5_vio_args : arguments (mandatory)
    gem5 VirtIO command line used to enable the VirtIO device in the simulated system. At the very least, the root parameter of the VirtIO9PDiod device must be exposed on the command line. Please set this root mount to {}, as it will be replaced with the directory used by Workload Automation at runtime.

    constraint: ``"{}" in str(value)``

temp_dir : str  
    Temporary directory used to pass files into the gem5 simulation. Workload Automation will automatically create a directory in this folder, and will remove it again once the simulation completes.

    default: ``'/tmp'``

checkpoint : boolean  
    This parameter tells Workload Automation to create a checkpoint of the simulated system once the guest system has finished booting. This checkpoint can then be used at a later stage by other WA runs to avoid booting the guest system a second time. Set to True to take a checkpoint of the simulated system post boot.

run_delay : integer  
    This sets the time that the system should sleep in the simulated system prior to running and workloads or taking checkpoints. This allows the system to quieten down prior to running the workloads. When this is combined with the checkpoint_post_boot option, it allows the checkpoint to be created post-sleep, and therefore the set of workloads resuming from this checkpoint will not be required to sleep.

    constraint: ``value >= 0``

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

core_names : list_of_caseless_strings (mandatory)
    This is a list of all cpu cores on the device with each
    element being the core type, e.g. ``['a7', 'a7', 'a15']``. The
    order of the cores must match the order they are listed in
    ``'/sys/devices/system/cpu'``. So in this case, ``'cpu0'`` must
    be an A7 core, and ``'cpu2'`` an A15.'

core_clusters : list_of_ints (mandatory)
    This is a list indicating the cluster affinity of the CPU cores,
    each element correponding to the cluster ID of the core coresponding
    to it's index. E.g. ``[0, 0, 1]`` indicates that cpu0 and cpu1 are on
    cluster 0, while cpu2 is on cluster 1. If this is not specified, this
    will be inferred from ``core_names`` if possible (assuming all cores with
    the same name are on the same cluster).

scheduler : str  
    Specifies the type of multi-core scheduling model utilized in the device. The value
    must be one of the following:

    :unknown: A generic Device interface is used to interact with the underlying device
              and the underlying scheduling model is unkown.
    :smp: A standard single-core or Symmetric Multi-Processing system.
    :hmp: ARM Heterogeneous Multi-Processing system.
    :iks: Linaro In-Kernel Switcher.
    :ea: ARM Energy-Aware scheduler.
    :other: Any other system not covered by the above.

            .. note:: most currently-available systems would fall under ``smp`` rather than
                      this value. ``other`` is there to future-proof against new schemes
                      not yet covered by WA.

    allowed values: ``'unknown'``, ``'smp'``, ``'hmp'``, ``'iks'``, ``'ea'``, ``'other'``

    default: ``'unknown'``

iks_switch_frequency : integer  
    This is the switching frequency, in kilohertz, of IKS devices. This parameter *MUST NOT*
    be set for non-IKS device (i.e. ``scheduler != 'iks'``). If left unset for IKS devices,
    it will default to ``800000``, i.e. 800MHz.

property_files : list_of_strs  
    A list of paths to files containing static OS properties. These will be pulled into the
    __meta directory in output for each run in order to provide information about the platfrom.
    These paths do not have to exist and will be ignored if the path is not present on a
    particular device.

    default: ``['/etc/arch-release', '/etc/debian_version', '/etc/lsb-release', '/proc/config.gz', '/proc/cmdline', '/proc/cpuinfo', '/proc/version', '/proc/zconfig', '/sys/kernel/debug/sched_features', '/sys/kernel/hmp']``

binaries_directory : str  
    Location of executable binaries on this device (must be in PATH).

host : str (mandatory)
    Host name or IP address for the device.

    default: ``'localhost'``

username : str (mandatory)
    User name for the account on the device.

password : str  
    Password for the account on the device (for password-based auth).

keyfile : str  
    Keyfile to be used for key-based authentication.

port : integer  
    SSH port number on the device.

    default: ``22``

password_prompt : str  
    Prompt presented by sudo when requesting the password.

    default: ``'[sudo] password'``

use_telnet : boolean  
    Optionally, telnet may be used instead of ssh, though this is discouraged.

boot_timeout : integer  
    How long to try to connect to the device after a reboot.

    default: ``120``

working_directory : str  
    Working directory to be used by WA. This must be in a location where the specified user
    has write permissions. This will default to /home/<username>/wa (or to /root/wa, if
    username is 'root').

login_prompt : list_of_strs  


    default: ``['login:', 'AEL login:', 'username:']``

login_password_prompt : list_of_strs  


    default: ``['password:']``


generic_android
---------------

A generic Android device interface. Use this if you do not have an interface
for your device.

This should allow basic WA functionality on most Android devices using adb over
USB. Some additional configuration may be required for some WA plugins
(e.g. configuring ``core_names`` and ``core_clusters``).

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

core_names : list_of_caseless_strings (mandatory)
    This is a list of all cpu cores on the device with each
    element being the core type, e.g. ``['a7', 'a7', 'a15']``. The
    order of the cores must match the order they are listed in
    ``'/sys/devices/system/cpu'``. So in this case, ``'cpu0'`` must
    be an A7 core, and ``'cpu2'`` an A15.'

core_clusters : list_of_ints (mandatory)
    This is a list indicating the cluster affinity of the CPU cores,
    each element correponding to the cluster ID of the core coresponding
    to it's index. E.g. ``[0, 0, 1]`` indicates that cpu0 and cpu1 are on
    cluster 0, while cpu2 is on cluster 1. If this is not specified, this
    will be inferred from ``core_names`` if possible (assuming all cores with
    the same name are on the same cluster).

scheduler : str  
    Specifies the type of multi-core scheduling model utilized in the device. The value
    must be one of the following:

    :unknown: A generic Device interface is used to interact with the underlying device
              and the underlying scheduling model is unkown.
    :smp: A standard single-core or Symmetric Multi-Processing system.
    :hmp: ARM Heterogeneous Multi-Processing system.
    :iks: Linaro In-Kernel Switcher.
    :ea: ARM Energy-Aware scheduler.
    :other: Any other system not covered by the above.

            .. note:: most currently-available systems would fall under ``smp`` rather than
                      this value. ``other`` is there to future-proof against new schemes
                      not yet covered by WA.

    allowed values: ``'unknown'``, ``'smp'``, ``'hmp'``, ``'iks'``, ``'ea'``, ``'other'``

    default: ``'unknown'``

iks_switch_frequency : integer  
    This is the switching frequency, in kilohertz, of IKS devices. This parameter *MUST NOT*
    be set for non-IKS device (i.e. ``scheduler != 'iks'``). If left unset for IKS devices,
    it will default to ``800000``, i.e. 800MHz.

property_files : list_of_strs  
    A list of paths to files containing static OS properties. These will be pulled into the
    __meta directory in output for each run in order to provide information about the platfrom.
    These paths do not have to exist and will be ignored if the path is not present on a
    particular device.

    default: ``['/etc/arch-release', '/etc/debian_version', '/etc/lsb-release', '/proc/config.gz', '/proc/cmdline', '/proc/cpuinfo', '/proc/version', '/proc/zconfig', '/sys/kernel/debug/sched_features', '/sys/kernel/hmp']``

binaries_directory : str  
    Location of executable binaries on this device (must be in PATH).

    default: ``'/data/local/tmp'``

adb_name : str  
    The unique ID of the device as output by "adb devices".

android_prompt : regex  
    The format  of matching the shell prompt in Android.

    default: ``r'^.*(shell|root)@.*:/\S* [#$] '``

working_directory : str  
    Directory that will be used WA on the device for output files etc.

    default: ``'/sdcard/wa-working'``

package_data_directory : str  
    Location of of data for an installed package (APK).

    default: ``'/data/data'``

external_storage_directory : str  
    Mount point for external storage.

    default: ``'/sdcard'``

connection : str  
    Specified the nature of adb connection.

    allowed values: ``'usb'``, ``'ethernet'``

    default: ``'usb'``

logcat_poll_period : integer  
    If specified and is not ``0``, logcat will be polled every
    ``logcat_poll_period`` seconds, and buffered on the host. This
    can be used if a lot of output is expected in logcat and the fixed
    logcat buffer on the device is not big enough. The trade off is that
    this introduces some minor runtime overhead. Not set by default.

enable_screen_check : boolean  
    Specified whether the device should make sure that the screen is on
    during initialization.

swipe_to_unlock : str  
    If set a swipe of the specified direction will be performed.
    This should unlock the screen.

    allowed values: ``None``, ``'horizontal'``, ``'vertical'``


generic_linux
-------------

A generic Linux device interface. Use this if you do not have an interface
for your device.

This should allow basic WA functionality on most Linux devices with SSH access
configured. Some additional configuration may be required for some WA plugins
(e.g. configuring ``core_names`` and ``core_clusters``).

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

core_names : list_of_caseless_strings (mandatory)
    This is a list of all cpu cores on the device with each
    element being the core type, e.g. ``['a7', 'a7', 'a15']``. The
    order of the cores must match the order they are listed in
    ``'/sys/devices/system/cpu'``. So in this case, ``'cpu0'`` must
    be an A7 core, and ``'cpu2'`` an A15.'

core_clusters : list_of_ints (mandatory)
    This is a list indicating the cluster affinity of the CPU cores,
    each element correponding to the cluster ID of the core coresponding
    to it's index. E.g. ``[0, 0, 1]`` indicates that cpu0 and cpu1 are on
    cluster 0, while cpu2 is on cluster 1. If this is not specified, this
    will be inferred from ``core_names`` if possible (assuming all cores with
    the same name are on the same cluster).

scheduler : str  
    Specifies the type of multi-core scheduling model utilized in the device. The value
    must be one of the following:

    :unknown: A generic Device interface is used to interact with the underlying device
              and the underlying scheduling model is unkown.
    :smp: A standard single-core or Symmetric Multi-Processing system.
    :hmp: ARM Heterogeneous Multi-Processing system.
    :iks: Linaro In-Kernel Switcher.
    :ea: ARM Energy-Aware scheduler.
    :other: Any other system not covered by the above.

            .. note:: most currently-available systems would fall under ``smp`` rather than
                      this value. ``other`` is there to future-proof against new schemes
                      not yet covered by WA.

    allowed values: ``'unknown'``, ``'smp'``, ``'hmp'``, ``'iks'``, ``'ea'``, ``'other'``

    default: ``'unknown'``

iks_switch_frequency : integer  
    This is the switching frequency, in kilohertz, of IKS devices. This parameter *MUST NOT*
    be set for non-IKS device (i.e. ``scheduler != 'iks'``). If left unset for IKS devices,
    it will default to ``800000``, i.e. 800MHz.

property_files : list_of_strs  
    A list of paths to files containing static OS properties. These will be pulled into the
    __meta directory in output for each run in order to provide information about the platfrom.
    These paths do not have to exist and will be ignored if the path is not present on a
    particular device.

    default: ``['/etc/arch-release', '/etc/debian_version', '/etc/lsb-release', '/proc/config.gz', '/proc/cmdline', '/proc/cpuinfo', '/proc/version', '/proc/zconfig', '/sys/kernel/debug/sched_features', '/sys/kernel/hmp']``

binaries_directory : str  
    Location of executable binaries on this device (must be in PATH).

host : str (mandatory)
    Host name or IP address for the device.

username : str (mandatory)
    User name for the account on the device.

password : str  
    Password for the account on the device (for password-based auth).

keyfile : str  
    Keyfile to be used for key-based authentication.

port : integer  
    SSH port number on the device.

    default: ``22``

password_prompt : str  
    Prompt presented by sudo when requesting the password.

    default: ``'[sudo] password'``

use_telnet : boolean  
    Optionally, telnet may be used instead of ssh, though this is discouraged.

boot_timeout : integer  
    How long to try to connect to the device after a reboot.

    default: ``120``

working_directory : str  
    Working directory to be used by WA. This must be in a location where the specified user
    has write permissions. This will default to /home/<username>/wa (or to /root/wa, if
    username is 'root').


juno
----

ARM Juno next generation big.LITTLE development platform.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

core_names : list_of_caseless_strings (mandatory)
    This is a list of all cpu cores on the device with each
    element being the core type, e.g. ``['a7', 'a7', 'a15']``. The
    order of the cores must match the order they are listed in
    ``'/sys/devices/system/cpu'``. So in this case, ``'cpu0'`` must
    be an A7 core, and ``'cpu2'`` an A15.'

    default: ``['a53', 'a53', 'a53', 'a53', 'a57', 'a57']``

core_clusters : list_of_ints (mandatory)
    This is a list indicating the cluster affinity of the CPU cores,
    each element correponding to the cluster ID of the core coresponding
    to it's index. E.g. ``[0, 0, 1]`` indicates that cpu0 and cpu1 are on
    cluster 0, while cpu2 is on cluster 1. If this is not specified, this
    will be inferred from ``core_names`` if possible (assuming all cores with
    the same name are on the same cluster).

    default: ``[0, 0, 0, 0, 1, 1]``

scheduler : str  
    Specifies the type of multi-core scheduling model utilized in the device. The value
    must be one of the following:

    :unknown: A generic Device interface is used to interact with the underlying device
              and the underlying scheduling model is unkown.
    :smp: A standard single-core or Symmetric Multi-Processing system.
    :hmp: ARM Heterogeneous Multi-Processing system.
    :iks: Linaro In-Kernel Switcher.
    :ea: ARM Energy-Aware scheduler.
    :other: Any other system not covered by the above.

            .. note:: most currently-available systems would fall under ``smp`` rather than
                      this value. ``other`` is there to future-proof against new schemes
                      not yet covered by WA.

    allowed values: ``'unknown'``, ``'smp'``, ``'hmp'``, ``'iks'``, ``'ea'``, ``'other'``

    default: ``'hmp'``

iks_switch_frequency : integer  
    This is the switching frequency, in kilohertz, of IKS devices. This parameter *MUST NOT*
    be set for non-IKS device (i.e. ``scheduler != 'iks'``). If left unset for IKS devices,
    it will default to ``800000``, i.e. 800MHz.

property_files : list_of_strs  
    A list of paths to files containing static OS properties. These will be pulled into the
    __meta directory in output for each run in order to provide information about the platfrom.
    These paths do not have to exist and will be ignored if the path is not present on a
    particular device.

    default: ``['/etc/arch-release', '/etc/debian_version', '/etc/lsb-release', '/proc/config.gz', '/proc/cmdline', '/proc/cpuinfo', '/proc/version', '/proc/zconfig', '/sys/kernel/debug/sched_features', '/sys/kernel/hmp']``

binaries_directory : str  
    Location of executable binaries on this device (must be in PATH).

    default: ``'/data/local/tmp'``

adb_name : str  
    The unique ID of the device as output by "adb devices".

android_prompt : regex  
    The format  of matching the shell prompt in Android.

    default: ``r'^.*(shell|root)@.*:/\S* [#$] '``

working_directory : str  
    Directory that will be used WA on the device for output files etc.

    default: ``'/sdcard/wa-working'``

package_data_directory : str  
    Location of of data for an installed package (APK).

    default: ``'/data/data'``

external_storage_directory : str  
    Mount point for external storage.

    default: ``'/sdcard'``

connection : str  
    Specified the nature of adb connection.

    allowed values: ``'usb'``, ``'ethernet'``

    default: ``'usb'``

logcat_poll_period : integer  
    If specified and is not ``0``, logcat will be polled every
    ``logcat_poll_period`` seconds, and buffered on the host. This
    can be used if a lot of output is expected in logcat and the fixed
    logcat buffer on the device is not big enough. The trade off is that
    this introduces some minor runtime overhead. Not set by default.

enable_screen_check : boolean  
    Specified whether the device should make sure that the screen is on
    during initialization.

swipe_to_unlock : str  
    If set a swipe of the specified direction will be performed.
    This should unlock the screen.

    allowed values: ``None``, ``'horizontal'``, ``'vertical'``

retries : integer  
    Specifies the number of times the device will attempt to recover
    (normally, with a hard reset) if it detects that something went wrong.

    default: ``2``

microsd_mount_point : str  
    Location at which the device's MicroSD card will be mounted.

    default: ``'/media/JUNO'``

port : str  
    Serial port on which the device is connected.

    default: ``'/dev/ttyS0'``

baudrate : integer  
    Serial connection baud.

    default: ``115200``

timeout : integer  
    Serial connection timeout.

    default: ``300``

bootloader : str  
    Bootloader used on the device.

    allowed values: ``'uefi'``, ``'u-boot'``

    default: ``'uefi'``

actually_disconnect : boolean  
    Actually perfom "adb disconnect" on closing the connection to the device.

uefi_entry : str  
    The name of the entry to use (will be created if does not exist).

    default: ``'WA'``

uefi_config : UefiConfig  
    Specifies the configuration for the UEFI entry for his device. In an
    entry specified by ``uefi_entry`` parameter doesn't exist in UEFI menu,
    it will be created using this config. This configuration will also be
    used, when flashing new images.

    default: ``{'fdt_support': True, 'image_name': 'Image', 'image_args': None}``

bootargs : str  
    Default boot arguments to use when boot_arguments were not.

    default: ``'console=ttyAMA0,115200 earlyprintk=pl011,0x7ff80000 verbose debug init=/init root=/dev/sda1 rw ip=dhcp rootwait video=DVI-D-1:1920x1080R@60'``


odroidxu3
---------

HardKernel Odroid XU3 development board.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

core_names : list_of_caseless_strings (mandatory)
    This is a list of all cpu cores on the device with each
    element being the core type, e.g. ``['a7', 'a7', 'a15']``. The
    order of the cores must match the order they are listed in
    ``'/sys/devices/system/cpu'``. So in this case, ``'cpu0'`` must
    be an A7 core, and ``'cpu2'`` an A15.'

    default: ``['a7', 'a7', 'a7', 'a7', 'a15', 'a15', 'a15', 'a15']``

core_clusters : list_of_ints (mandatory)
    This is a list indicating the cluster affinity of the CPU cores,
    each element correponding to the cluster ID of the core coresponding
    to it's index. E.g. ``[0, 0, 1]`` indicates that cpu0 and cpu1 are on
    cluster 0, while cpu2 is on cluster 1. If this is not specified, this
    will be inferred from ``core_names`` if possible (assuming all cores with
    the same name are on the same cluster).

    default: ``[0, 0, 0, 0, 1, 1, 1, 1]``

scheduler : str  
    Specifies the type of multi-core scheduling model utilized in the device. The value
    must be one of the following:

    :unknown: A generic Device interface is used to interact with the underlying device
              and the underlying scheduling model is unkown.
    :smp: A standard single-core or Symmetric Multi-Processing system.
    :hmp: ARM Heterogeneous Multi-Processing system.
    :iks: Linaro In-Kernel Switcher.
    :ea: ARM Energy-Aware scheduler.
    :other: Any other system not covered by the above.

            .. note:: most currently-available systems would fall under ``smp`` rather than
                      this value. ``other`` is there to future-proof against new schemes
                      not yet covered by WA.

    allowed values: ``'unknown'``, ``'smp'``, ``'hmp'``, ``'iks'``, ``'ea'``, ``'other'``

    default: ``'unknown'``

iks_switch_frequency : integer  
    This is the switching frequency, in kilohertz, of IKS devices. This parameter *MUST NOT*
    be set for non-IKS device (i.e. ``scheduler != 'iks'``). If left unset for IKS devices,
    it will default to ``800000``, i.e. 800MHz.

property_files : list_of_strs  
    A list of paths to files containing static OS properties. These will be pulled into the
    __meta directory in output for each run in order to provide information about the platfrom.
    These paths do not have to exist and will be ignored if the path is not present on a
    particular device.

    default: ``['/etc/arch-release', '/etc/debian_version', '/etc/lsb-release', '/proc/config.gz', '/proc/cmdline', '/proc/cpuinfo', '/proc/version', '/proc/zconfig', '/sys/kernel/debug/sched_features', '/sys/kernel/hmp']``

binaries_directory : str  
    Location of executable binaries on this device (must be in PATH).

    default: ``'/data/local/tmp'``

adb_name : str  
    The unique ID of the device as output by "adb devices".

    default: ``'BABABEEFBABABEEF'``

android_prompt : regex  
    The format  of matching the shell prompt in Android.

    default: ``r'^.*(shell|root)@.*:/\S* [#$] '``

working_directory : str  
    Directory that will be used WA on the device for output files etc.

    default: ``'/data/local/wa-working'``

package_data_directory : str  
    Location of of data for an installed package (APK).

    default: ``'/data/data'``

external_storage_directory : str  
    Mount point for external storage.

    default: ``'/sdcard'``

connection : str  
    Specified the nature of adb connection.

    allowed values: ``'usb'``, ``'ethernet'``

    default: ``'usb'``

logcat_poll_period : integer  
    If specified and is not ``0``, logcat will be polled every
    ``logcat_poll_period`` seconds, and buffered on the host. This
    can be used if a lot of output is expected in logcat and the fixed
    logcat buffer on the device is not big enough. The trade off is that
    this introduces some minor runtime overhead. Not set by default.

enable_screen_check : boolean  
    Specified whether the device should make sure that the screen is on
    during initialization.

swipe_to_unlock : str  
    If set a swipe of the specified direction will be performed.
    This should unlock the screen.

    allowed values: ``None``, ``'horizontal'``, ``'vertical'``

port : str  
    Serial port on which the device is connected

    default: ``'/dev/ttyUSB0'``

baudrate : integer  
    Serial connection baud rate

    default: ``115200``


odroidxu3_linux
---------------

HardKernel Odroid XU3 development board (Ubuntu image).

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

core_names : list_of_caseless_strings (mandatory)
    This is a list of all cpu cores on the device with each
    element being the core type, e.g. ``['a7', 'a7', 'a15']``. The
    order of the cores must match the order they are listed in
    ``'/sys/devices/system/cpu'``. So in this case, ``'cpu0'`` must
    be an A7 core, and ``'cpu2'`` an A15.'

    default: ``['a7', 'a7', 'a7', 'a7', 'a15', 'a15', 'a15', 'a15']``

core_clusters : list_of_ints (mandatory)
    This is a list indicating the cluster affinity of the CPU cores,
    each element correponding to the cluster ID of the core coresponding
    to it's index. E.g. ``[0, 0, 1]`` indicates that cpu0 and cpu1 are on
    cluster 0, while cpu2 is on cluster 1. If this is not specified, this
    will be inferred from ``core_names`` if possible (assuming all cores with
    the same name are on the same cluster).

    default: ``[0, 0, 0, 0, 1, 1, 1, 1]``

scheduler : str  
    Specifies the type of multi-core scheduling model utilized in the device. The value
    must be one of the following:

    :unknown: A generic Device interface is used to interact with the underlying device
              and the underlying scheduling model is unkown.
    :smp: A standard single-core or Symmetric Multi-Processing system.
    :hmp: ARM Heterogeneous Multi-Processing system.
    :iks: Linaro In-Kernel Switcher.
    :ea: ARM Energy-Aware scheduler.
    :other: Any other system not covered by the above.

            .. note:: most currently-available systems would fall under ``smp`` rather than
                      this value. ``other`` is there to future-proof against new schemes
                      not yet covered by WA.

    allowed values: ``'unknown'``, ``'smp'``, ``'hmp'``, ``'iks'``, ``'ea'``, ``'other'``

    default: ``'unknown'``

iks_switch_frequency : integer  
    This is the switching frequency, in kilohertz, of IKS devices. This parameter *MUST NOT*
    be set for non-IKS device (i.e. ``scheduler != 'iks'``). If left unset for IKS devices,
    it will default to ``800000``, i.e. 800MHz.

property_files : list_of_strs  
    A list of paths to files containing static OS properties. These will be pulled into the
    __meta directory in output for each run in order to provide information about the platfrom.
    These paths do not have to exist and will be ignored if the path is not present on a
    particular device.

    default: ``['/etc/arch-release', '/etc/debian_version', '/etc/lsb-release', '/proc/config.gz', '/proc/cmdline', '/proc/cpuinfo', '/proc/version', '/proc/zconfig', '/sys/kernel/debug/sched_features', '/sys/kernel/hmp']``

binaries_directory : str  
    Location of executable binaries on this device (must be in PATH).

host : str (mandatory)
    Host name or IP address for the device.

username : str (mandatory)
    User name for the account on the device.

password : str  
    Password for the account on the device (for password-based auth).

keyfile : str  
    Keyfile to be used for key-based authentication.

port : integer  
    SSH port number on the device.

    default: ``22``

password_prompt : str  
    Prompt presented by sudo when requesting the password.

    default: ``'[sudo] password'``

use_telnet : boolean  
    Optionally, telnet may be used instead of ssh, though this is discouraged.

boot_timeout : integer  
    How long to try to connect to the device after a reboot.

    default: ``120``

working_directory : str  
    Working directory to be used by WA. This must be in a location where the specified user
    has write permissions. This will default to /home/<username>/wa (or to /root/wa, if
    username is 'root').


