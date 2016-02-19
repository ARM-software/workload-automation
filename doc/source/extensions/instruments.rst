.. _instruments:

Instruments
===========

apk_version
-----------

Extracts APK versions for workloads that have them.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.


cci_pmu_logger
--------------

This instrument allows collecting CCI counter data.

It relies on the pmu_logger.ko kernel driver, the source for which is
included with Workload Automation (see inside ``wlauto/external`` directory).
You will need to build this against your specific kernel. Once compiled, it needs
to be placed in the dependencies directory (usually ``~/.workload_uatomation/dependencies``).

.. note:: When compling pmu_logger.ko for a new hardware platform, you may need to
          modify CCI_BASE inside pmu_logger.c to contain the base address of where
          CCI is mapped in memory on your device.

This instrument relies on ``trace-cmd`` instrument to also be enabled. You should enable
at least ``'bprint'`` trace event.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

events : list  
    A list of strings, each representing an event to be counted. The length
    of the list cannot exceed the number of PMU counters available (4 in CCI-400).
    If this is not specified, shareable read transactions and snoop hits on both
    clusters will be counted by default.  E.g. ``['0x63', '0x83']``.

    default: ``['0x63', '0x6A', '0x83', '0x8A']``

event_labels : list  
    A list of labels to be used when reporting PMU counts. If specified,
    this must be of the same length as ``cci_pmu_events``. If not specified,
    events will be labeled "event_<event_number>".

period : integer  
    The period (in jiffies) between counter reads.

    default: ``10``

install_module : boolean  
    Specifies whether pmu_logger has been compiled as a .ko module that needs
    to be installed by the instrument. (.ko binary must be in /work/home/.workload_automation/dependencies). If this is set
    to ``False``, it will be assumed that pmu_logger has been compiled into the kernel,
    or that it has been installed prior to the invocation of WA.

    default: ``True``


coreutil
--------

Measures CPU core activity during workload execution in terms of the percentage of time a number
of cores were utilized above the specfied threshold.

This workload generates ``coreutil.csv`` report in the workload's output directory. The report is
formatted as follows::

    <threshold,1core,2core,3core,4core
    18.098132,38.650248000000005,10.736180000000001,3.6809760000000002,28.834312000000001

Interpretation of the result:

 - 38.65% of total time only single core is running above or equal to threshold value
 - 10.736% of total time two cores are running simultaneously above or equal to threshold value
 - 3.6809% of total time three cores are running simultaneously above or equal to threshold value
 - 28.8314% of total time four cores are running simultaneously above or equal to threshold value
 - 18.098% of time all core are running below threshold value.

..note : This instrument doesn't work on ARM big.LITTLE IKS implementation

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

threshold : integer  
    Cores with percentage utilization above this value will be considered as "utilized". This value may need to be adjusted based on the background activity and the intensity of the workload being instrumented (e.g. it may need to be lowered for low-intensity workloads such as video playback).

    constraint: ``0 < value <= 100``

    default: ``50``


cpufreq
-------

Collects dynamic frequency (DVFS) settings before and after workload execution.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

paths : list_of_strs  
    A list of paths to be pulled from the device. These could be directories
    as well as files.

use_tmpfs : boolean  
    Specifies whether tmpfs should be used to cache sysfile trees and then pull them down
    as a tarball. This is significantly faster then just copying the directory trees from
    the device directly, bur requres root and may not work on all devices. Defaults to
    ``True`` if the device is rooted and ``False`` if it is not.

tmpfs_mount_point : str  
    Mount point for tmpfs partition used to store snapshots of paths.

tmpfs_size : str  
    Size of the tempfs partition.

    default: ``'32m'``


daq
---

DAQ instrument obtains the power consumption of the target device's core
measured by National Instruments Data Acquisition(DAQ) device.

WA communicates with a DAQ device server running on a Windows machine
(Please refer to :ref:`daq_setup`) over a network. You must specify the IP
address and port the server is listening on in the config file as follows ::

    daq_server_host = '10.1.197.176'
    daq_server_port = 45677

These values will be output by the server when you run it on Windows.

You must also specify the values of resistors (in Ohms) across which the
voltages are measured (Please refer to :ref:`daq_setup`). The values should be
specified as a list with an entry for each resistor, e.g.::

    daq_resistor_values = [0.005, 0.005]

In addition to this mandatory configuration, you can also optionally specify the
following::

    :daq_labels: Labels to be used for ports. Defaults to ``'PORT_<pnum>'``, where
                 'pnum' is the number of the port.
    :daq_device_id: The ID under which the DAQ is registered with the driver.
                    Defaults to ``'Dev1'``.
    :daq_v_range: Specifies the voltage range for the SOC voltage channel on the DAQ
                  (please refer to :ref:`daq_setup` for details). Defaults to ``2.5``.
    :daq_dv_range: Specifies the voltage range for the resistor voltage channel on
                   the DAQ (please refer to :ref:`daq_setup` for details).
                   Defaults to ``0.2``.
    :daq_sampling_rate: DAQ sampling rate. DAQ will take this many samples each
                        second. Please note that this maybe limitted by your DAQ model
                        and then number of ports you're measuring (again, see
                        :ref:`daq_setup`). Defaults to ``10000``.
    :daq_channel_map: Represents mapping from  logical AI channel number to physical
                      connector on the DAQ (varies between DAQ models). The default
                      assumes DAQ 6363 and similar with AI channels on connectors
                      0-7 and 16-23.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

server_host : str  
    The host address of the machine that runs the daq Server which the insturment communicates with.

    default: ``'localhost'``

server_port : integer  
    The port number for daq Server in which daq insturment communicates with.

    default: ``45677``

device_id : str  
    The ID under which the DAQ is registered with the driver.

    default: ``'Dev1'``

v_range : float  
    Specifies the voltage range for the SOC voltage channel on the DAQ (please refer to :ref:`daq_setup` for details).

    default: ``2.5``

dv_range : float  
    Specifies the voltage range for the resistor voltage channel on the DAQ (please refer to :ref:`daq_setup` for details).

    default: ``0.2``

sampling_rate : integer  
    DAQ sampling rate. DAQ will take this many samples each second. Please note that this maybe limitted by your DAQ model and then number of ports you're measuring (again, see :ref:`daq_setup`)

    default: ``10000``

resistor_values : list (mandatory)
    The values of resistors (in Ohms) across which the voltages are measured on each port.

channel_map : list_of_ints  
    Represents mapping from  logical AI channel number to physical connector on the DAQ (varies between DAQ models). The default assumes DAQ 6363 and similar with AI channels on connectors 0-7 and 16-23.

    default: ``(0, 1, 2, 3, 4, 5, 6, 7, 16, 17, 18, 19, 20, 21, 22, 23)``

labels : list_of_strs  
    List of port labels. If specified, the lenght of the list must match the length of ``resistor_values``. Defaults to "PORT_<pnum>", where "pnum" is the number of the port.

negative_samples : str  
    Specifies how negative power samples should be handled. The following
    methods are possible:

      :keep: keep them as they are
      :zero: turn negative values to zero
      :drop: drop samples if they contain negative values. *warning:* this may result in
             port files containing different numbers of samples
      :abs: take the absoulte value of negave samples

    allowed values: ``'keep'``, ``'zero'``, ``'drop'``, ``'abs'``

    default: ``'keep'``

gpio_sync : integer  
    If specified, the instrument will simultaneously set the
    specified GPIO pin high and put a marker into ftrace. This is
    to facillitate syncing kernel trace events to DAQ power
    trace.

    constraint: ``value > 0``

merge_channels : dict_or_bool  
    If set to ``True``, channels with consecutive letter suffixes will be summed.
    e.g. If you have channels A7a, A7b, A7c, A15a, A15b they will be summed to A7, A15

    You can also manually specify the name of channels to be merged and the name of the
    result like so:

    merge_channels:
         A15: [A15dvfs, A15ram]
         NonCPU: [GPU, RoS, Mem]

    In the above exaples the DAQ channels labeled A15a and A15b will be summed together
    with the results being saved as 'channel' ''a''. A7, GPU and RoS will be summed to 'c'


delay
-----

This instrument introduces a delay before executing either an iteration
or all iterations for a spec.

The delay may be specified as either a fixed period or a temperature
threshold that must be reached.

Optionally, if an active cooling solution is employed to speed up temperature drop between
runs, it may be controlled using this instrument.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

temperature_file : str  
    Full path to the sysfile on the device that contains the device's
    temperature.

    default: ``'/sys/devices/virtual/thermal/thermal_zone0/temp'``

temperature_timeout : integer  
    The timeout after which the instrument will stop waiting even if the specified threshold
    temperature is not reached. If this timeout is hit, then a warning will be logged stating
    the actual temperature at which the timeout has ended.

    default: ``600``

temperature_poll_period : integer  
    How long to sleep (in seconds) between polling current device temperature.

    default: ``5``

temperature_between_specs : integer  
    Temperature (in device-specific units) the device must cool down to before
    the iteration spec will be run.

    .. note:: This cannot be specified at the same time as ``fixed_between_specs``

temperature_between_iterations : integer  
    Temperature (in device-specific units) the device must cool down to before
    the next spec will be run.

    .. note:: This cannot be specified at the same time as ``fixed_between_iterations``

temperature_before_start : integer  
    Temperature (in device-specific units) the device must cool down to just before
    the actual workload execution (after setup has been performed).

    .. note:: This cannot be specified at the same time as ``fixed_between_iterations``

fixed_between_specs : integer  
    How long to sleep (in seconds) after all iterations for a workload spec have
    executed.

    .. note:: This cannot be specified at the same time as ``temperature_between_specs``

fixed_between_iterations : integer  
    How long to sleep (in seconds) after each iterations for a workload spec has
    executed.

    .. note:: This cannot be specified at the same time as ``temperature_between_iterations``

fixed_before_start : integer  
    How long to sleep (in seconds) after setup for an iteration has been perfromed but
    before running the workload.

    .. note:: This cannot be specified at the same time as ``temperature_before_start``

active_cooling : boolean  
    This instrument supports an active cooling solution while waiting for the device temperature
    to drop to the threshold. The solution involves an mbed controlling a fan. The mbed is signaled
    over a serial port. If this solution is present in the setup, this should be set to ``True``.


dmesg
-----

Collected dmesg output before and during the run.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

loglevel : integer  
    Set loglevel for console output.

    allowed values: ``0``, ``1``, ``2``, ``3``, ``4``, ``5``, ``6``, ``7``


energy_model
------------



parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

device_name : caseless_string  
    The name of the device to be used in  generating the model. If not specified,
    ``device.name`` will be used.

big_core : caseless_string  
    The name of the "big" core in the big.LITTLE system; must match
    one of the values in ``device.core_names``.

performance_metric : caseless_string (mandatory)
    Metric to be used as the performance indicator.

power_metric : list_or_caseless_string  
    Metric to be used as the power indicator. The value may contain a
    ``{core}`` format specifier that will be replaced with names of big
    and little cores to drive the name of the metric for that cluster.
    Ether this or ``energy_metric`` must be specified but not both.

energy_metric : list_or_caseless_string  
    Metric to be used as the energy indicator. The value may contain a
    ``{core}`` format specifier that will be replaced with names of big
    and little cores to drive the name of the metric for that cluster.
    this metric will be used to derive power by deviding through by
    execution time. Either this or ``power_metric`` must be specified, but
    not both.

power_scaling_factor : float  
    Power model specfies power in milliWatts. This is a scaling factor that
    power_metric values will be multiplied by to get milliWatts.

    default: ``1.0``

big_frequencies : list_of_ints  
    List of frequencies to be used for big cores. These frequencies must
    be supported by the cores. If this is not specified, all available
    frequencies for the core (as read from cpufreq) will be used.

little_frequencies : list_of_ints  
    List of frequencies to be used for little cores. These frequencies must
    be supported by the cores. If this is not specified, all available
    frequencies for the core (as read from cpufreq) will be used.

idle_workload : str  
    Workload to be used while measuring idle power.

    default: ``'idle'``

idle_workload_params : dict  
    Parameter to pass to the idle workload.

first_cluster_idle_state : integer  
    The index of the first cluster idle state on the device. Previous states
    are assumed to be core idles. The default is ``-1``, i.e. only the last
    idle state is assumed to affect the entire cluster.

    default: ``-1``

no_hotplug : boolean  
    This options allows running the instrument without hotpluging cores on and off.
    Disabling hotplugging will most likely produce a less accurate power model.

num_of_freqs_to_thermal_adjust : integer  
    The number of frequencies begining from the highest, to be adjusted for
    the thermal effect.

big_opps : opp_table  
    OPP table mapping frequency to voltage (kHz --> mV) for the big cluster.

little_opps : opp_table  
    OPP table mapping frequency to voltage (kHz --> mV) for the little cluster.

big_leakage : integer  
    Leakage factor for the big cluster (this is specific to a particular core implementation).

    default: ``120``

little_leakage : integer  
    Leakage factor for the little cluster (this is specific to a particular core implementation).

    default: ``60``


energy_probe
------------

Collects power traces using the ARM energy probe.

 This instrument requires ``caiman`` utility to be installed in the workload automation
 host and be in the PATH. Caiman is part of DS-5 and should be in ``/path/to/DS-5/bin/`` .
 Energy probe can simultaneously collect energy from up to 3 power rails.

 To connect the energy probe on a rail, connect the white wire to the pin that is closer to the
 Voltage source and the black wire to the pin that is closer to the load (the SoC or the device
 you are probing). Between the pins there should be a shunt resistor of known resistance in the
 range of 5 to 20 mOhm. The resistance of the shunt resistors is a mandatory parameter
 ``resistor_values``.

.. note:: This instrument can process results a lot faster if python pandas is installed.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

resistor_values : list_of_numbers  
    The value of shunt resistors. This is a mandatory parameter.

labels : list  
    Meaningful labels for each of the monitored rails.

device_entry : str  
    Path to /dev entry for the energy probe (it should be /dev/ttyACMx)

    default: ``'/dev/ttyACM0'``


execution_time
--------------

Measure how long it took to execute the run() methods of a Workload.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.


fps
---

Measures Frames Per Second (FPS) and associated metrics for a workload's main View.

.. note:: This instrument depends on pandas Python library (which is not part of standard
          WA dependencies), so you will need to install that first, before you can use it.

The view is specified by the workload as ``view`` attribute. This defaults
to ``'SurfaceView'`` for game workloads, and ``None`` for non-game
workloads (as for them FPS mesurement usually doesn't make sense).
Individual workloads may override this.

This instrument adds four metrics to the results:

    :FPS: Frames Per Second. This is the frame rate of the workload.
    :frames: The total number of frames rendered during the execution of
             the workload.
    :janks: The number of "janks" that occured during execution of the
            workload. Janks are sudden shifts in frame rate. They result
            in a "stuttery" UI. See http://jankfree.org/jank-busters-io
    :not_at_vsync: The number of frames that did not render in a single
                   vsync cycle.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

drop_threshold : numeric  
    Data points below this FPS will be dropped as they do not constitute "real" gameplay. The assumption being that while actually running, the FPS in the game will not drop below X frames per second, except on loading screens, menus, etc, which should not contribute to FPS calculation.

    default: ``5``

keep_raw : boolean  
    If set to ``True``, this will keep the raw dumpsys output in the results directory (this is maily used for debugging) Note: frames.csv with collected frames data will always be generated regardless of this setting.

generate_csv : boolean  
    If set to ``True``, this will produce temporal fps data in the results directory, in a file named fps.csv Note: fps data will appear as discrete step-like values in order to produce a more meainingfull representation,a rolling mean can be applied.

    default: ``True``

crash_check : boolean  
    Specifies wither the instrument should check for crashed content by examining
    frame data. If this is set, ``execution_time`` instrument must also be installed.
    The check is performed by using the measured FPS and exection time to estimate the expected
    frames cound and comparing that against the measured frames count. The the ratio of
    measured/expected is too low, then it is assumed that the content has crashed part way
    during the run. What is "too low" is determined by ``crash_threshold``.

    .. note:: This is not 100\% fool-proof. If the crash occurs sufficiently close to
              workload's termination,  it may not be detected. If this is expected, the
              threshold may be adjusted up to compensate.

    default: ``True``

crash_threshold : float  
    Specifies the threshold used to decided whether a measured/expected frames ration indicates
    a content crash. E.g. a value of ``0.75`` means the number of actual frames counted is a
    quarter lower than expected, it will treated as a content crash.

    default: ``0.7``


freq_sweep
----------

Sweeps workloads through all available frequencies on a device.

When enabled this instrument will take all workloads specified in an agenda
and run them at all available frequencies for all clusters.

Recommendations:
    - Setting the runner to 'by_spec' increases the chance of successfully
      completing an agenda without encountering hotplug issues
    - If possible disable dynamic hotplug on the target device

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

sweeps : list  
     By default this instrument will sweep across all available
     frequencies for all available clusters. If you wish to only
     sweep across certain frequencies on particular clusters you
     can do so by specifying this parameter.

     Sweeps should be a lists of dictionaries that can contain:
       - Cluster (mandatory): The name of the cluster this sweep will be
                              performed on. E.g A7
       - Frequencies: A list of frequencies (in KHz) to use. If this is
                      not provided all frequencies available for this
                      cluster will be used.
                      E.g: [800000, 900000, 100000]
       - label: Workload specs will be named '{spec id}_{label}_{frequency}'.
                If a label is not provided it will be named 'sweep{sweep No.}'

    Example sweep specification:

        freq_sweep:
            sweeps:
                - cluster: A53
                  label: littles
                  frequencies: [800000, 900000, 100000]
                - cluster: A57
                  label: bigs


hwmon
-----

Hardware Monitor (hwmon) is a generic Linux kernel subsystem,
providing access to hardware monitoring components like temperature or
voltage/current sensors.

The following web page has more information:

    http://blogs.arm.com/software-enablement/925-linux-hwmon-power-management-and-arm-ds-5-streamline/

You can specify which sensors HwmonInstrument looks for by specifying
hwmon_sensors in your config.py, e.g. ::

    hwmon_sensors = ['energy', 'temp']

If this setting is not specified, it will look for all sensors it knows about.
Current valid values are::

    :energy: Collect energy measurements and report energy consumed
             during run execution (the diff of before and after readings)
             in Joules.
    :temp: Collect temperature measurements and report the before and
           after readings in degrees Celsius.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

sensors : list_of_strs  
    The kinds of sensors hwmon instrument will look for

    default: ``['energy', 'temp']``


interrupts
----------

Pulls the ``/proc/interrupts`` file before and after workload execution and diffs them
to show what interrupts  occurred during that time.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.


juno_energy
-----------

Collects internal energy meter measurements from Juno development board.

This instrument was created because (at the time of creation) Juno's energy
meter measurements aren't exposed through HWMON or similar standardized mechanism,
necessitating  a dedicated instrument to access them.

This instrument, and the ``readenergy`` executable it relies on are very much tied
to the Juno platform and are not expected to work on other boards.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

period : float  
    Specifies the time, in Seconds, between polling energy counters.

    default: ``0.1``

strict : boolean  
    Setting this to ``False`` will omit the check that the ``device`` is
    ``"juno"``. This is useful if the underlying board is actually Juno
    but WA connects via a different interface (e.g. ``generic_linux``).

    default: ``True``


netstats
--------

Measures transmit/receive network traffic on an Android divice on per-package
basis.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

packages : list_of_strs  
    List of Android packages who's traffic will be monitored. If
    unspecified, all packages in the device will be monitorred.

period : integer  
    Polling period for instrumentation on the device. Traffic statistics
    will be updated every ``period`` seconds.

    default: ``5``

force_reinstall : boolean  
    If ``True``, instrumentation APK will always be re-installed even if
    it already installed on the device.

uninstall_on_completion : boolean  
    If ``True``, instrumentation will be uninstalled upon run completion.


perf
----

Perf is a Linux profiling with performance counters.

Performance counters are CPU hardware registers that count hardware events
such as instructions executed, cache-misses suffered, or branches
mispredicted. They form a basis for profiling applications to trace dynamic
control flow and identify hotspots.

pref accepts options and events. If no option is given the default '-a' is
used. For events, the default events are migrations and cs. They both can
be specified in the config file.

Events must be provided as a list that contains them and they will look like
this ::

    perf_events = ['migrations', 'cs']

Events can be obtained by typing the following in the command line on the
device ::

    perf list

Whereas options, they can be provided as a single string as following ::

    perf_options = '-a -i'

Options can be obtained by running the following in the command line ::

    man perf-record

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

events : list_of_strs  
    Specifies the events to be counted.

    constraint: ``must not be empty.``

    default: ``['migrations', 'cs']``

optionstring : list_or_string  
    Specifies options to be used for the perf command. This
    may be a list of option strings, in which case, multiple instances of perf
    will be kicked off -- one for each option string. This may be used to e.g.
    collected different events from different big.LITTLE clusters.

    default: ``'-a'``

labels : list_of_strs  
    Provides labels for pref output. If specified, the number of
    labels must match the number of ``optionstring``\ s.

force_install : boolean  
    always install perf binary even if perf is already present on the device.


screenon
--------

Ensure screen is on before each iteration on Android devices.

A very basic instrument that checks that the screen is on on android devices. Optionally,
it call poll the device periodically to ensure that the screen is still on.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

polling_period : integer  
    Set this to a non-zero value to enable periodic (every
    ``polling_period`` seconds) polling of the screen on
    the device to ensure it is on during a run.


streamline
----------

Collect Streamline traces from the device.

.. note:: This instrument supports streamline that comes with DS-5 5.17 and later
          earlier versions of streamline  may not work correctly (or at all).

This Instrument allows collecting streamline traces (such as PMU counter values) from
the device. It assumes you have DS-5 (which Streamline is part of) installed on your
system, and that streamline command is somewhere in PATH.

Streamline works by connecting to gator service on the device. gator comes in two parts
a driver (gator.ko) and daemon (gatord). The driver needs to be compiled against your
kernel and both driver and daemon need to be compatible with your version of Streamline.
The best way to ensure compatibility is to build them from source which came with your
DS-5. gator source can be found in ::

    /usr/local/DS-5/arm/gator

(the exact path may vary depending of where you have installed DS-5.) Please refer to the
README the accompanies the source for instructions on how to build it.

Once you have built the driver and the daemon, place the binaries into your
~/.workload_automation/streamline/ directory (if you haven't tried running WA with
this instrument before, the streamline/ subdirectory might not exist, in which
case you will need to create it.

In order to specify which events should be captured, you need to provide a
configuration.xml for the gator. The easiest way to obtain this file is to export it
from event configuration dialog in DS-5 streamline GUI. The file should be called
"configuration.xml" and it be placed in the same directory as the gator binaries.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

port : str  
    Specifies the port on which streamline will connect to gator

    default: ``'8080'``

configxml : str  
    streamline configuration XML file to be used. This must be an absolute path, though it may count the user home symbol (~)

report : boolean  
    Specifies whether a report should be generated from streamline data.

report_options : str  
    A string with options that will be added to streamline -report command.

    default: ``'-format csv'``


sysfs_extractor
---------------

Collects the contest of a set of directories, before and after workload execution
and diffs the result.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

paths : list_of_strs (mandatory)
    A list of paths to be pulled from the device. These could be directories
    as well as files.

use_tmpfs : boolean  
    Specifies whether tmpfs should be used to cache sysfile trees and then pull them down
    as a tarball. This is significantly faster then just copying the directory trees from
    the device directly, bur requres root and may not work on all devices. Defaults to
    ``True`` if the device is rooted and ``False`` if it is not.

tmpfs_mount_point : str  
    Mount point for tmpfs partition used to store snapshots of paths.

tmpfs_size : str  
    Size of the tempfs partition.

    default: ``'32m'``


systrace
--------

This instrument uses systrace.py from the android SDK to dump atrace
output.

Note: This is unlikely to work on devices that have an android build built
      before 15-May-2015. Before this date there was a bug with running
      atrace asynchronously.

From developer.android.com:
The Systrace tool helps analyze the performance of your application by
capturing and displaying execution times of your applications processes
and other Android system processes. The tool combines data from the
Android kernel such as the CPU scheduler, disk activity, and application
threads to generate an HTML report that shows an overall picture of an
Android device's system processes for a given period of time.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

buffer_size : integer  
    Use a trace buffer size of N kilobytes. This option lets you
    limit the total size of the data collected during a trace.

    default: ``1024``

use_circular_buffer : boolean  
    When true trace data will be put into a circular buffer such
    that when it overflows it will start overwriting the beginning
    of the buffer.

kernel_functions : list_of_strs  
    Specify the names of kernel functions to trace.

categories : list_of_strs  
    A list of the categories you wish to trace.

    default: ``['freq', 'sched']``

app_names : list_of_strs  
    Enable tracing for applications, specified as a
    comma-separated list of package names. The apps must contain
    tracing instrumentation calls from the Trace class. For more
    information, see
    http://developer.android.com/tools/debugging/systrace.html#app-trace

ignore_signals : boolean  
    This will cause atrace to ignore ``SIGHUP``, ``SIGINT``,
    ``SIGQUIT`` and ``SIGTERM``.

compress_trace : boolean  
    Compresses atrace output. This *greatly* decreases the time
    it takes to pull results from a device but the resulting txt
    file is not human readable.

    default: ``True``


trace-cmd
---------

trace-cmd is an instrument which interacts with Ftrace Linux kernel internal
tracer

From trace-cmd man page:

trace-cmd command interacts with the Ftrace tracer that is built inside the
Linux kernel. It interfaces with the Ftrace specific files found in the
debugfs file system under the tracing directory.

trace-cmd reads a list of events it will trace, which can be specified in
the config file as follows ::

    trace_events = ['irq*', 'power*']

If no event is specified in the config file, trace-cmd traces the following events:

    - sched*
    - irq*
    - power*
    - cpufreq_interactive*

The list of available events can be obtained by rooting and running the following
command line on the device ::

   trace-cmd list

You may also specify ``trace_buffer_size`` setting which must be an integer that will
be used to set the ftrace buffer size. It will be interpreted as KB::

    trace_cmd_buffer_size = 8000

The maximum buffer size varies from device to device, but there is a maximum and trying
to set buffer size beyound that will fail. If you plan on collecting a lot of trace over
long periods of time, the buffer size will not be enough and you will only get trace for
the last portion of your run. To deal with this you can set the ``trace_mode`` setting to
``'record'`` (the default is ``'start'``)::

    trace_cmd_mode = 'record'

This will cause trace-cmd to trace into file(s) on disk, rather than the buffer, and so the
limit for the max size of the trace is set by the storage available on device. Bear in mind
that ``'record'`` mode *is* more instrusive than the default, so if you do not plan on
generating a lot of trace, it is best to use the default ``'start'`` mode.

.. note:: Mode names correspend to the underlying trace-cmd exectuable's command used to
          implement them. You can find out more about what is happening in each case from
          trace-cmd documentation: https://lwn.net/Articles/341902/.

This instrument comes with an Android trace-cmd binary that will be copied and used on the
device, however post-processing will be done on-host and you must have trace-cmd installed and
in your path. On Ubuntu systems, this may be done with::

    sudo apt-get install trace-cmd

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

events : list  
    Specifies the list of events to be traced. Each event in the list will be passed to
    trace-cmd with -e parameter and must be in the format accepted by trace-cmd.

    default: ``['sched*', 'irq*', 'power*', 'cpufreq_interactive*']``

mode : str  
    Trace can be collected using either 'start' or 'record' trace-cmd
    commands. In 'start' mode, trace will be collected into the ftrace buffer;
    in 'record' mode, trace will be written into a file on the device's file
    system. 'start' mode is (in theory) less intrusive than 'record' mode, however
    it is limited by the size of the ftrace buffer (which is configurable --
    see ``buffer_size`` -- but only up to a point) and that may overflow
    for long-running workloads, which will result in dropped events.

    allowed values: ``'start'``, ``'record'``

    default: ``'start'``

buffer_size : integer  
    Attempt to set ftrace buffer size to the specified value (in KB). Default buffer size
    may need to be increased for long-running workloads, or if a large number
    of events have been enabled. Note: there is a maximum size that the buffer can
    be set, and that varies from device to device. Attempting to set buffer size higher
    than this will fail. In that case, this instrument will set the size to the highest
    possible value by going down from the specified size in ``buffer_size_step`` intervals.

buffer_size_step : integer  
    Defines the decremental step used if the specified ``buffer_size`` could not be set.
    This will be subtracted form the buffer size until set succeeds or size is reduced to
    1MB.

    default: ``1000``

buffer_size_file : str  
    Path to the debugs file that may be used to set ftrace buffer size. This should need
    to be modified for the vast majority devices.

    default: ``'/sys/kernel/debug/tracing/buffer_size_kb'``

report : boolean  
    Specifies whether reporting should be performed once the binary trace has been generated.

    default: ``True``

no_install : boolean  
    Do not install the bundled trace-cmd  and use the one on the device instead. If there is
    not already a trace-cmd on the device, an error is raised.

report_on_target : boolean  
    When enabled generation of reports will be done host-side because the generated file is
    very large. If trace-cmd is not available on the host device this setting and be disabled
    and the report will be generated on the target device.

    .. note:: This requires the latest version of trace-cmd to be installed on the host (the
              one in your distribution's repos may be too old).


