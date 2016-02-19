.. _workloads:

Workloads
=========

andebench
---------

AndEBench is an industry standard Android benchmark provided by The
Embedded Microprocessor Benchmark Consortium (EEMBC).

http://www.eembc.org/andebench/about.php

From the website:

   - Initial focus on CPU and Dalvik interpreter performance
   - Internal algorithms concentrate on integer operations
   - Compares the difference between native and Java performance
   - Implements flexible multicore performance analysis
   - Results displayed in Iterations per second
   - Detailed log file for comprehensive engineering analysis

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

number_of_threads : integer  
    Number of threads that will be spawned by AndEBench.

single_threaded : boolean  
    If ``true``, AndEBench will run with a single thread. Note: this must
    not be specified if ``number_of_threads`` has been specified.

native_only : boolean  
    If ``true``, AndEBench will execute only the native portion of the benchmark.


androbench
----------

Measures the storage performance of an Android device.

Website: http://www.androbench.org/wiki/AndroBench

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.


angrybirds
----------

Angry Birds game.

A very popular Android 2D game.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``500``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

assets_push_timeout : integer  
    Timeout used during deployment of the assets package (if there is one).

    default: ``500``

clear_data_on_reset : boolean  
    If set to ``False``, this will prevent WA from clearing package
    data for this workload prior to running it.

    default: ``True``


angrybirds_rio
--------------

Angry Birds Rio game.

The sequel to the very popular Android 2D game.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``500``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

assets_push_timeout : integer  
    Timeout used during deployment of the assets package (if there is one).

    default: ``500``

clear_data_on_reset : boolean  
    If set to ``False``, this will prevent WA from clearing package
    data for this workload prior to running it.

    default: ``True``


anomaly2
--------

Anomaly 2 game demo and benchmark.

Plays three scenes from the game, benchmarking each one. Scores reported are intended to
represent overall perceived quality of the game, based not only on raw FPS but also factors
like smoothness.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``500``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

assets_push_timeout : integer  
    Timeout used during deployment of the assets package (if there is one).

    default: ``500``

clear_data_on_reset : boolean  
    If set to ``False``, this will prevent WA from clearing package
    data for this workload prior to running it.

    default: ``True``


antutu
------

AnTuTu Benchmark is an benchmarking tool for Android Mobile Phone/Pad. It
can run a full test of a key project, through the "Memory Performance","CPU
Integer Performance","CPU Floating point Performance","2D 3D Graphics
Performance","SD card reading/writing speed","Database IO" performance
testing, and gives accurate analysis for Andriod smart phones.

http://www.antutulabs.com/AnTuTu-Benchmark

From the website:

AnTuTu Benchmark can support the latest quad-core cpu. In reaching the
overall and individual scores of the hardware, AnTuTu Benchmark could judge
your phone by the scores of the performance of the hardware. By uploading
the scores, Benchmark can view your device in the world rankings, allowing
points to let you know the level of hardware performance equipment.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

version : str  
    Specify the version of AnTuTu to be run. If not specified, the latest available version will be used.

    allowed values: ``'3.3.2'``, ``'4.0.3'``, ``'5.3.0'``, ``'6.0.1'``

    default: ``'6.0.1'``

times : integer  
    The number of times the benchmark will be executed in a row (i.e. without going through the full setup/teardown process). Note: this does not work with versions prior to 4.0.3.

    default: ``1``

enable_sd_tests : boolean  
    If ``True`` enables SD card tests in pre version 4 AnTuTu. These tests were know to cause problems on platforms without an SD card. This parameter will be ignored on AnTuTu version 4 and higher.


applaunch
---------

Measures the time and energy used in launching an application.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

app : str  
    The name of the application to measure.

    allowed values: ``'calculator'``, ``'browser'``, ``'calendar'``

    default: ``'browser'``

set_launcher_affinity : boolean  
    If ``True``, this will explicitly set the affinity of the launcher process to the A15 cluster.

    default: ``True``

times : integer  
    Number of app launches to do on the device.

    default: ``8``

measure_energy : boolean  
    Specfies wether energy measurments should be taken during the run.

    .. note:: This depends on appropriate sensors to be exposed through HWMON.

cleanup : boolean  
    Specifies whether to clean up temporary files on the device.

    default: ``True``


audio
-----

Audio workload plays an MP3 file using the built-in music player. By default,
it plays Canon_in_D_Pieano.mp3 for 30 seconds.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

duration : integer  
    The duration the music will play for in seconds.

    default: ``30``

audio_file : str  
    The (on-host) path to the audio file to be played.

    .. note:: If the default file is not present locally, it will be downloaded.

    default: ``'~/.workload_automation/dependencies/Canon_in_D_Piano.mp3'``

perform_cleanup : boolean  
    If ``True``, workload files on the device will be deleted after execution.

clear_file_cache : boolean  
    Clear the the file cache on the target device prior to running the workload.

    default: ``True``


autotest
--------

Executes tests from ChromeOS autotest suite

.. note:: This workload *must* be run inside a CromeOS SDK chroot.

See: https://www.chromium.org/chromium-os/testing/power-testing

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

test : str (mandatory)
    The test to be run

test_that_args : arguments  
    Extra arguments to be passed to test_that_invocation.

run_timeout : integer  
    Timeout, in seconds, for the test execution.

    default: ``1800``


bbench
------

BBench workload opens the built-in browser and navigates to, and
scrolls through, some preloaded web pages and ends the workload by trying to
connect to a local server it runs after it starts. It can also play the
workload while it plays an audio file in the background.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

with_audio : boolean  
    Specifies whether an MP3 should be played in the background during workload execution.

server_timeout : integer  
    Specifies the timeout (in seconds) before the server is stopped.

    default: ``300``

force_dependency_push : boolean  
    Specifies whether to push dependency files to the device to the device if they are already on it.

audio_file : str  
    The (on-host) path to the audio file to be played. This is only used if ``with_audio`` is ``True``.

    default: ``'~/.workload_automation/dependencies/Canon_in_D_Piano.mp3'``

perform_cleanup : boolean  
    If ``True``, workload files on the device will be deleted after execution.

clear_file_cache : boolean  
    Clear the the file cache on the target device prior to running the workload.

    default: ``True``

browser_package : str  
    Specifies the package name of the device's browser app.

    default: ``'com.android.browser'``

browser_activity : str  
    Specifies the startup activity  name of the device's browser app.

    default: ``'.BrowserActivity'``


benchmarkpi
-----------

Measures the time the target device takes to run and complete the Pi
calculation algorithm.

http://androidbenchmark.com/howitworks.php

from the website:

The whole idea behind this application is to use the same Pi calculation
algorithm on every Android Device and check how fast that proccess is.
Better calculation times, conclude to faster Android devices. This way you
can also check how lightweight your custom made Android build is. Or not.

As Pi is an irrational number, Benchmark Pi does not calculate the actual Pi
number, but an approximation near the first digits of Pi over the same
calculation circles the algorithms needs.

So, the number you are getting in miliseconds is the time your mobile device
takes to run and complete the Pi calculation algorithm resulting in a
approximation of the first Pi digits.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.


caffeinemark
------------

CaffeineMark is a series of tests that measure the speed of Java
programs running in various hardware and software configurations.

http://www.benchmarkhq.ru/cm30/info.html

From the website:

CaffeineMark scores roughly correlate with the number of Java instructions
executed per second, and do not depend significantly on the the amount of
memory in the system or on the speed of a computers disk drives or internet
connection.

The following is a brief description of what each test does:

    - Sieve: The classic sieve of eratosthenes finds prime numbers.
    - Loop: The loop test uses sorting and sequence generation as to measure
            compiler optimization of loops.
    - Logic: Tests the speed with which the virtual machine executes
             decision-making instructions.
    - Method: The Method test executes recursive function calls to see how
              well the VM handles method calls.
    - Float: Simulates a 3D rotation of objects around a point.
    - Graphics: Draws random rectangles and lines.
    - Image: Draws a sequence of three graphics repeatedly.
    - Dialog: Writes a set of values into labels and editboxes on a form.

The overall CaffeineMark score is the geometric mean of the individual
scores, i.e., it is the 9th root of the product of all the scores.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.


cameracapture
-------------

Uses in-built Android camera app to take photos.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

no_of_captures : integer  
    Number of photos to be taken.

    default: ``5``

time_between_captures : integer  
    Time, in seconds, between two consecutive camera clicks.

    default: ``5``


camerarecord
------------

Uses in-built Android camera app to record the video for given interval
of time.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

recording_time : integer  
    The video recording time in seconds.

    default: ``60``


castlebuilder
-------------

Castle Builder game.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``500``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

assets_push_timeout : integer  
    Timeout used during deployment of the assets package (if there is one).

    default: ``500``

clear_data_on_reset : boolean  
    If set to ``False``, this will prevent WA from clearing package
    data for this workload prior to running it.

    default: ``True``


castlemaster
------------

Castle Master v1.09 game.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``500``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

assets_push_timeout : integer  
    Timeout used during deployment of the assets package (if there is one).

    default: ``500``

clear_data_on_reset : boolean  
    If set to ``False``, this will prevent WA from clearing package
    data for this workload prior to running it.

    default: ``True``


cfbench
-------

CF-Bench is (mainly) CPU and memory benchmark tool specifically designed to
be able to handle multi-core devices, produce a fairly stable score, and
test both native as well managed code performance.

https://play.google.com/store/apps/details?id=eu.chainfire.cfbench&hl=en

From the website:

It tests specific device properties you do not regularly see tested by other
benchmarks, and runs in a set timeframe.

It does produce some "final" scores, but as with every benchmark, you should
take those with a grain of salt. It is simply not theoretically possible to
produce a single number that accurately describes a device's performance.

.. note:: This workload relies on the device being rooted

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.


citadel
-------

Epic Citadel demo showcasing Unreal Engine 3.

The game has very rich graphics details. The workload only moves around its
environment for the specified time.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``500``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

assets_push_timeout : integer  
    Timeout used during deployment of the assets package (if there is one).

    default: ``500``

clear_data_on_reset : boolean  
    If set to ``False``, this will prevent WA from clearing package
    data for this workload prior to running it.

    default: ``True``

duration : integer  
    Duration, in seconds, of the run (may need to be adjusted for different devices.

    default: ``60``


cyclictest
----------

Measures the amount of time that passes between when a timer expires and
when the thread which set the timer actually runs.

Cyclic test works by taking a time snapshot just prior to waiting for a specific
time interval (t1), then taking another time snapshot after the timer
finishes (t2), then comparing the theoretical wakeup time with the actual
wakeup time (t2 -(t1 + sleep_time)). This value is the latency for that
timers wakeup.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

clock : str  
    specify the clock to be used during the test.

    allowed values: ``'monotonic'``, ``'realtime'``

    default: ``'realtime'``

duration : integer  
    Specify the length for the test to run in seconds.

    default: ``30``

quiet : boolean  
    Run the tests quiet and print only a summary on exit.

    default: ``True``

thread : integer  
    Set the number of test threads

    default: ``8``

latency : integer  
    Write the value to /dev/cpu_dma_latency

    default: ``1000000``

extra_parameters : str  
    Any additional command line parameters to append to the existing parameters above. A list can be found at https://rt.wiki.kernel.org/index.php/Cyclictest or in the help page ``cyclictest -h``

clear_file_cache : boolean  
    Clear file caches before starting test

    default: ``True``

screen_off : boolean  
    If true it will turn the screen off so that onscreen graphics do not effect the score. This is predominantly for devices without a GPU

    default: ``True``


dex2oat
-------

Benchmarks the execution time of dex2oat (a key part of APK installation process).

ART is a new Android runtime in KitKat, which replaces Dalvik VM. ART uses Ahead-Of-Time
compilation. It pre-compiles ODEX files used by Dalvik using dex2oat tool as part of APK
installation process.

This workload benchmarks the time it take to compile an APK using dex2oat, which has a
significant impact on the total APK installation time, and therefore  user experience.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

instruction_set : str  
    Specifies the instruction set to compile for.  Only options supported by
    the target device can be used.

    allowed values: ``'arm'``, ``'arm64'``, ``'x86'``, ``'x86_64'``, ``'mips'``

    default: ``'arm64'``


dhrystone
---------

Runs the Dhrystone benchmark.

Original source from::

    http://classes.soe.ucsc.edu/cmpe202/benchmarks/standard/dhrystone.c

This version has been modified to configure duration and the number of
threads used.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

duration : integer  
    The duration, in seconds, for which dhrystone will be executed. Either this or ``mloops`` should be specified but not both.

mloops : integer  
    Millions of loops to run. Either this or ``duration`` should be specified, but not both. If neither is specified, this will default to ``100``

threads : integer  
    The number of separate dhrystone "threads" that will be forked.

    default: ``4``

delay : integer  
    The delay, in seconds, between kicking off of dhrystone threads (if ``threads`` > 1).

taskset_mask : integer  
    The processes spawned by sysbench will be pinned to cores as specified by this parameter


dungeondefenders
----------------

Dungeon Defenders game.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``500``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

assets_push_timeout : integer  
    Timeout used during deployment of the assets package (if there is one).

    default: ``500``

clear_data_on_reset : boolean  
    If set to ``False``, this will prevent WA from clearing package
    data for this workload prior to running it.

    default: ``True``


ebizzy
------

ebizzy is designed to generate a workload resembling common web
application server workloads.  It is highly threaded, has a large in-memory
working set with low locality, and allocates and deallocates memory frequently.
When running most efficiently, it will max out the CPU.

ebizzy description taken from the source code at
https://github.com/linux-test-project/ltp/tree/master/utils/benchmark/ebizzy-0.3

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

threads : integer  
    Number of threads to execute.

    default: ``2``

seconds : integer  
    Number of seconds.

    default: ``10``

chunks : integer  
    Number of memory chunks to allocate.

    default: ``10``

extra_params : str  
    Extra parameters to pass in (e.g. -M to disable mmap). See ebizzy -? for full list of options.


facebook
--------

Uses com.facebook.patana apk for facebook workload.
This workload does the following activities in facebook

    Login to facebook account.
    Send a message.
    Check latest notification.
    Search particular user account and visit his/her facebook account.
    Find friends.
    Update the facebook status

[NOTE:  This workload starts disableUpdate workload as a part of setup to
disable online updates, which helps to tackle problem of uncertain
behavier during facebook workload run.]

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.


geekbench
---------

Geekbench provides a comprehensive set of benchmarks engineered to quickly
and accurately measure processor and memory performance.

http://www.primatelabs.com/geekbench/

From the website:

Designed to make benchmarks easy to run and easy to understand, Geekbench
takes the guesswork out of producing robust and reliable benchmark results.

Geekbench scores are calibrated against a baseline score of 1,000 (which is
the score of a single-processor Power Mac G5 @ 1.6GHz). Higher scores are
better, with double the score indicating double the performance.

The benchmarks fall into one of four categories:

    - integer performance.
    - floating point performance.
    - memory performance.
    - stream performance.

Geekbench benchmarks: http://www.primatelabs.com/geekbench/doc/benchmarks.html

Geekbench scoring methedology:
http://support.primatelabs.com/kb/geekbench/interpreting-geekbench-scores

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

version : str  
    Specifies which version of the workload should be run.

    allowed values: ``'2'``, ``'3'``

    default: ``'3'``

times : integer  
    Specfies the number of times the benchmark will be run in a "tight loop", i.e. without performaing setup/teardown inbetween.

    default: ``1``


glb_corporate
-------------

GFXBench GL (a.k.a. GLBench) v3.0 Corporate version.

This is a version of GLBench available through a corporate license (distinct
from the version available in Google Play store).

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

times : integer  
    Specifies the number of times the benchmark will be run in a "tight loop", i.e. without performaing setup/teardown inbetween.

    constraint: ``value > 0``

    default: ``1``

resolution : str  
    Explicitly specifies the resultion under which the benchmark will be run. If not specfied, device's native resoution will used.

    allowed values: ``'720p'``, ``'1080p'``, ``'720'``, ``'1080'``

test_id : str  
    ID of the GFXBench test to be run.

    allowed values: ``'gl_alu'``, ``'gl_alu_off'``, ``'gl_blending'``, ``'gl_blending_off'``, ``'gl_driver'``, ``'gl_driver_off'``, ``'gl_fill'``, ``'gl_fill_off'``, ``'gl_manhattan'``, ``'gl_manhattan_off'``, ``'gl_trex'``, ``'gl_trex_battery'``, ``'gl_trex_off'``, ``'gl_trex_qmatch'``, ``'gl_trex_qmatch_highp'``

    default: ``'gl_manhattan_off'``

run_timeout : integer  
    Time out for workload execution. The workload will be killed if it hasn't completed
    withint this period.

    default: ``600``


glbenchmark
-----------

Measures the graphics performance of Android devices by testing
the underlying OpenGL (ES) implementation.

http://gfxbench.com/about-gfxbench.jsp

From the website:

    The benchmark includes console-quality high-level 3D animations
    (T-Rex HD and Egypt HD) and low-level graphics measurements.

    With high vertex count and complex effects such as motion blur, parallax
    mapping and particle systems, the engine of GFXBench stresses GPUs in order
    provide users a realistic feedback on their device.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

version : str  
    Specifies which version of the benchmark to run (different versions support different use cases).

    allowed values: ``'2.7.0'``, ``'2.5.1'``

    default: ``'2.7.0'``

use_case : str  
    Specifies which usecase to run, as listed in the benchmark menu; e.g.
    ``'GLBenchmark 2.5 Egypt HD'``. For convenience, two aliases are provided
    for the most common use cases: ``'egypt'`` and ``'t-rex'``. These could
    be use instead of the full use case title. For version ``'2.7.0'`` it defaults
    to ``'t-rex'``, for version ``'2.5.1'`` it defaults to ``'egypt-classic'``.

variant : str  
    Specifies which variant of the use case to run, as listed in the benchmarks
    menu (small text underneath the use case name); e.g. ``'C24Z16 Onscreen Auto'``.
    For convenience, two aliases are provided for the most common variants:
    ``'onscreen'`` and ``'offscreen'``. These may be used instead of full variant
    names.

    default: ``'onscreen'``

times : integer  
    Specfies the number of times the benchmark will be run in a "tight loop", i.e. without performaing setup/teardown inbetween.

    default: ``1``

timeout : integer  
    Specifies how long, in seconds, UI automation will wait for results screen to
    appear before assuming something went wrong.

    default: ``200``


gunbros2
--------

Gun Bros. 2 game.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``500``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

assets_push_timeout : integer  
    Timeout used during deployment of the assets package (if there is one).

    default: ``500``

clear_data_on_reset : boolean  
    If set to ``False``, this will prevent WA from clearing package
    data for this workload prior to running it.

    default: ``True``


hackbench
---------

Hackbench runs a series of tests for the Linux scheduler.

For details, go to:
https://github.com/linux-test-project/ltp/

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

datasize : integer  
    Message size in bytes.

    default: ``100``

groups : integer  
    Number of groups.

    default: ``10``

loops : integer  
    Number of loops.

    default: ``100``

fds : integer  
    Number of file descriptors.

    default: ``40``

extra_params : str  
    Extra parameters to pass in. See the hackbench man page or type `hackbench --help` for list of options.

duration : integer  
    Test duration in seconds.

    default: ``30``


homescreen
----------

A workload that goes to the home screen and idles for the the
specified duration.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

duration : integer  
    Specifies the duration, in seconds, of this workload.

    default: ``20``


hwuitest
--------

Tests UI rendering latency on android devices

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

test : caseless_string  
    The test to run:
    - ``'shadowgrid'``: creates a grid of rounded rects that
      cast shadows, high CPU & GPU load
    - ``'rectgrid'``: creates a grid of 1x1 rects
    - ``'oval'``: draws 1 oval

    allowed values: ``'shadowgrid'``, ``'rectgrid'``, ``'oval'``

    default: ``'shadowgrid'``

loops : integer  
    The number of test iterations.

    default: ``3``

frames : integer  
    The number of frames to run the test over.

    default: ``150``


idle
----

Do nothing for the specified duration.

On android devices, this may optionally stop the Android run time, if
``stop_android`` is set to ``True``.

.. note:: This workload requires the device to be rooted.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

duration : integer  
    Specifies the duration, in seconds, of this workload.

    default: ``20``

stop_android : boolean  
    Specifies whether the Android run time should be stopped. (Can be set only for Android devices).


iozone
------

Iozone is a filesystem benchmark that runs a series of disk
I/O performance tests.

Here is a list of tests that you can run in the iozone
workload. The descriptions are from the official iozone
document.

0  - Write Test
     Measure performance of writing a new file. Other
     tests rely on the file written by this, so it must
     always be enabled (WA will automatically neable this
     if not specified).

1  - Rewrite Test
     Measure performance of writing an existing file.

2  - Read Test
     Measure performance of reading an existing file.

3  - Reread Test
     Measure performance of rereading an existing file.

4  - Random Read Test
     Measure performance of reading a file by accessing
     random locations within the file.

5  - Random Write Test
     Measure performance of writing a file by accessing
     random locations within the file.

6  - Backwards Read Test
     Measure performance of reading a file backwards.

7  - Record Rewrite Test
     Measure performance of writing and rewriting a
     particular spot within the file.

8  - Strided Read Test
     Measure performance of reading a file with strided
     access behavior.

9  - Fwrite Test
     Measure performance of writing a file using the
     library function fwrite() that performances
     buffered write operations.

10 - Frewrite Test
     Measure performance of writing a file using the
     the library function fwrite() that performs
     buffered and blocked write operations.

11 - Fread Test
     Measure performance of reading a file using the
     library function fread() that performs buffered
     and blocked read operations.

12 - Freread Test
     Same as the Fread Test except the current file
     being read was read previously sometime in the
     past.

By default, iozone will run all tests in auto mode. To run
specific tests, they must be written in the form of:

[0,1,4,5]

Please enable classifiers in your agenda or config file
in order to display the results properly in the results.csv
file.

The official website for iozone is at www.iozone.org.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

tests : list_of_ints  
    List of performance tests to run.

    allowed values: ``0``, ``1``, ``2``, ``3``, ``4``, ``5``, ``6``, ``7``, ``8``, ``9``, ``10``, ``11``, ``12``

auto_mode : boolean  
    Run tests in auto mode.

    default: ``True``

timeout : integer  
    Timeout for the workload.

    default: ``14400``

file_size : integer  
    Fixed file size.

record_length : integer  
    Fixed record length.

threads : integer  
    Number of threads

other_params : str  
    Other parameter. Run iozone -h to see list of options.


ironman3
--------

Iron Man 3 game.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``500``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

assets_push_timeout : integer  
    Timeout used during deployment of the assets package (if there is one).

    default: ``500``

clear_data_on_reset : boolean  
    If set to ``False``, this will prevent WA from clearing package
    data for this workload prior to running it.

    default: ``True``


krazykart
---------

Krazy Kart Racing game.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``500``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

assets_push_timeout : integer  
    Timeout used during deployment of the assets package (if there is one).

    default: ``500``

clear_data_on_reset : boolean  
    If set to ``False``, this will prevent WA from clearing package
    data for this workload prior to running it.

    default: ``True``


linpack
-------

The LINPACK Benchmarks are a measure of a system's floating point computing
power.

http://en.wikipedia.org/wiki/LINPACK_benchmarks

From the article:

Introduced by Jack Dongarra, they measure how fast a computer solves
a dense n by n system of linear equations Ax = b, which is a common task in
engineering.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

output_file : str  
    On-device output file path.


linpack-cli
-----------

linpack benchmark with a command line interface

Benchmarks FLOPS (floating point operations per second).

This is the oldschool version of the bencmark. Source may be viewed here:

    http://www.netlib.org/benchmark/linpackc.new

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

array_size : integer  
    size of arrays to be used by the benchmark.

    default: ``200``


lmbench
-------

Run a subtest from lmbench, a suite of portable ANSI/C microbenchmarks for UNIX/POSIX.

In general, lmbench measures two key features: latency and bandwidth. This workload supports a subset
of lmbench tests. lat_mem_rd can be used to measure latencies to memory (including caches). bw_mem
can be used to measure bandwidth to/from memory over a range of operations.

Further details, and source code are available from:
http://sourceforge.net/projects/lmbench/.
See lmbench/bin/README for license details.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

test : str  
    Specifies an lmbench test to run.

    allowed values: ``'lat_mem_rd'``, ``'bw_mem'``

    default: ``'lat_mem_rd'``

stride : list_or_type  
    Stride for lat_mem_rd test. Workload will iterate over one or more integer values.

    default: ``[128]``

thrash : boolean  
    Sets -t flag for lat_mem_rd_test

    default: ``True``

size : list_or_string  
    Data set size for lat_mem_rd bw_mem tests.

    default: ``'4m'``

mem_category : list_or_string  
    List of memory catetories for bw_mem test.

    default: ``('rd', 'wr', 'cp', 'frd', 'fwr', 'fcp', 'bzero', 'bcopy')``

parallelism : integer  
    Parallelism flag for tests that accept it.

warmup : integer  
    Warmup flag for tests that accept it.

repetitions : integer  
    Repetitions flag for tests that accept it.

force_abi : str  
    Override device abi with this value. Can be used to force arm32 on 64-bit devices.

run_timeout : integer  
    Timeout for execution of the test.

    default: ``900``

times : integer  
    Specifies the number of times the benchmark will be run in a "tight loop",
    i.e. without performaing setup/teardown inbetween. This parameter is distinct from
    "repetitions", as the latter takes place within the benchmark and produces a single result.

    constraint: ``value > 0``

    default: ``1``


manual
------

Yields control to the user, either for a fixed period or based on user input, to perform
custom operations on the device, about which workload automation does not know of.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

duration : integer  
    Control of the devices is yielded for the duration (in seconds) specified. If not specified, ``user_triggered`` is assumed.

user_triggered : boolean  
    If ``True``, WA will wait for user input after starting the workload;
    otherwise fixed duration is expected. Defaults to ``True`` if ``duration``
    is not specified, and ``False`` otherwise.

view : str  
    Specifies the View of the workload. This enables instruments that require a
    View to be specified, such as the ``fps`` instrument.

    default: ``'SurfaceView'``

enable_logcat : boolean  
    If ``True``, ``manual`` workload will collect logcat as part of the results.

    default: ``True``


memcpy
------

Runs memcpy in a loop.

This will run memcpy in a loop for a specified number of times on a buffer
of a specified size. Additionally, the affinity of the test can be set to one
or more specific cores.

This workload is single-threaded. It genrates no scores or metrics by itself.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

buffer_size : integer  
    Specifies the size, in bytes, of the buffer to be copied.

    default: ``5242880``

iterations : integer  
    Specfies the number of iterations that will be performed.

    default: ``1000``

cpus : list  
    A list of integers specifying ordinals of cores to which the affinity
    of the test process should be set. If not specified, all avaiable cores
    will be used.


nenamark
--------

NenaMark is an OpenGL-ES 2.0 graphics performance benchmark for Android
devices.

http://nena.se/nenamark_story

From the website:

The NenaMark2 benchmark scene averages about 45k triangles, with a span
between 26k and 68k triangles. It averages 96 batches per frame and contains
about 15 Mb of texture data (non-packed).

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

duration : integer  
    Number of seconds to wait before considering the benchmark
    finished

    default: ``120``


peacekeeper
-----------

Peacekeeper is a free and fast browser test that measures a browser's speed.

.. note::

   This workload requires a network connection as well as support for
   one of the two currently-supported browsers. Moreover, TC2 has
   compatibility issue with chrome

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

browser : str  
    The browser to be benchmarked.

    allowed values: ``'firefox'``, ``'chrome'``

    default: ``'firefox'``

output_file : str  
    The result URL of peacekeeper benchmark will be written
    into this file on device after completion of peacekeeper benchmark.
    Defaults to peacekeeper.txt in the device's ``working_directory``.

peacekeeper_url : str  
    The URL to run the peacekeeper benchmark.

    default: ``'http://peacekeeper.futuremark.com/run.action'``


power_loadtest
--------------

power_LoadTest (part of ChromeOS autotest suite) continuously cycles through a set of
browser-based activities and monitors battery drain on a device.

.. note:: This workload *must* be run inside a CromeOS SDK chroot.

See: https://www.chromium.org/chromium-os/testing/power-testing

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

board : str  
    The name of the board to be used for the test. If this is not specified,
    BOARD environment variable will be used.

variant : str  
    The variant of the test to run; If not specified, the full power_LoadTest will
    run (until the device battery is drained). The only other variant available in the
    vanilla test is "1hour", but further variants may be added by providing custom
    control files.

test_that_args : arguments  
    Extra arguments to be passed to test_that_invocation.

run_timeout : integer  
    Timeout, in seconds, for the test execution.

    default: ``86400``


quadrant
--------

Quadrant is a benchmark for mobile devices, capable of measuring CPU, memory,
I/O and 3D graphics performance.

http://www.aurorasoftworks.com/products/quadrant

From the website:
Quadrant outputs a score for the following categories: 2D, 3D, Mem, I/O, CPU
, Total.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.


real-linpack
------------

This version of `Linpack <http://en.wikipedia.org/wiki/LINPACK_benchmarks>`
was developed by Dave Butcher. RealLinpack tries to find the number of threads
that give you the maximum linpack score.

RealLinpack runs 20 runs of linpack for each number of threads and
calculates the mean and confidence.  It stops when the
score's confidence interval drops below the current best score
interval.  That is, when (current_score + confidence) < (best_score -
best_score_confidence)

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

max_threads : integer  
    The maximum number of threads that real linpack will try.

    constraint: ``value > 0``

    default: ``16``


realracing3
-----------

Real Racing 3 game.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``500``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

assets_push_timeout : integer  
    Timeout used during deployment of the assets package (if there is one).

    default: ``500``

clear_data_on_reset : boolean  
    If set to ``False``, this will prevent WA from clearing package
    data for this workload prior to running it.

    default: ``True``


recentfling
-----------

Tests UI jank on android devices.

For this workload to work, ``recentfling.sh`` and ``defs.sh`` must be placed
in ``~/.workload_automation/dependencies/recentfling/``. These can be found
in the [AOSP Git repository](https://android.googlesource.com/platform/system/extras/+/master/tests/).

To change the apps that are opened at the start of the workload you will need
to modify the ``defs.sh`` file. You will need to add your app to ``dfltAppList``
and then add a variable called ``{app_name}Activity`` with the name of the
activity to launch (where ``{add_name}`` is the name you put into ``dfltAppList``).

You can get a list of activities available on your device by running
``adb shell pm list packages -f``

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

loops : integer  
    The number of test iterations.

    default: ``3``


rt-app
------

A test application that simulates cofigurable real-time periodic load.

rt-app is a test application that starts multiple periodic threads in order to
simulate a real-time periodic load. It supports SCHED_OTHER, SCHED_FIFO,
SCHED_RR as well as the AQuoSA framework and SCHED_DEADLINE.

The load is described using JSON-like config files. Below are a couple of simple
examples.

.. code-block:: json

    {
        /*
        * Simple use case which creates a thread that run 1ms then sleep 9ms
        * until the use case is stopped with Ctrl+C
        */
        "tasks" : {
            "thread0" : {
                "loop" : -1,
                "run" :   20000,
                "sleep" : 80000
            }
        },
        "global" : {
            "duration" : 2,
            "calibration" : "CPU0",
            "default_policy" : "SCHED_OTHER",
            "pi_enabled" : false,
            "lock_pages" : false,
            "logdir" : "./",
            "log_basename" : "rt-app1",
            "ftrace" : false,
            "gnuplot" : true,
        }
    }

.. code-block:: json

    {
        /*
        * Simple use case with 2 threads that runs for 10 ms and wake up each
        * other until the use case is stopped with Ctrl+C
        */
        "tasks" : {
            "thread0" : {
                "loop" : -1,
                "run" :     10000,
                "resume" : "thread1",
                "suspend" : "thread0"
            },
            "thread1" : {
                "loop" : -1,
                "run" :     10000,
                "resume" : "thread0",
                "suspend" : "thread1"
            }
        }
    }

Please refer to the exising configs in ``/work/home/seb_wa/workload-automation/wlauto/workloads/rt_app/use_cases`` for more examples.

The version of rt-app currently used with this workload contains enhancements and
modifications done by Linaro. The source code for this version may be obtained here:

http://git.linaro.org/power/rt-app.git

The upstream version of rt-app is hosted here:

https://github.com/scheduler-tools/rt-app

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

config : str  
    Use case configuration file to run with rt-app. This may be
    either the name of one of the "standard" configuratons included
    with the workload. or a path to a custom JSON file provided by
    the user. Either way, the ".json" plugin is implied and will
    be added automatically if not specified in the argument.

    The following is th list of standard configuraionts currently
    included with the workload: browser-long.json, taskset.json, spreading-tasks.json, mp3-short.json, video-short.json, browser-short.json, mp3-long.json, video-long.json

    default: ``'taskset'``

duration : integer  
    Duration of the workload execution in Seconds. If specified, this
    will override the corresponing parameter in the JSON config.

taskset_mask : integer  
    Constrain execution to specific CPUs.

uninstall_on_exit : boolean  
    If set to ``True``, rt-app binary will be uninstalled from the device
    at the end of the run.

force_install : boolean  
    If set to ``True``, rt-app binary will always be deployed to the
    target device at the begining of the run, regardless of whether it
    was already installed there.


shellscript
-----------

Runs an arbitrary shellscript on the device.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

script_file : str (mandatory)
    The path (on the host) to the shell script file. This must be an absolute path (though it may contain ~).

argstring : str  
    A string that should contain arguments passed to the script.

timeout : integer  
    Timeout, in seconds, for the script run time.

    default: ``60``


skypevideo
----------

Initiates Skype video call to a specified contact for a pre-determined duration.
(Note: requires Skype to be set up appropriately).

This workload is intended for monitoring the behaviour of a device while a Skype
video call is in progress (a common use case). It does not produce any score or
metric and the intention is that some addition instrumentation is enabled while
running this workload.

This workload, obviously, requires a network connection (ideally, wifi).

This workload accepts the following parameters:


**Skype Setup**

   - You should install Skype client from Google Play Store on the device
     (this was tested with client version 4.5.0.39600; other recent versions
     should also work).
   - You must have an account set up and logged into Skype on the device.
   - The contact to be called must be added (and has accepted) to the
     account. It's possible to have multiple contacts in the list, however
     the contact to be called *must* be visible on initial navigation to the
     list.
   - The contact must be able to received the call. This means that there
     must be  a Skype client running (somewhere) with the contact logged in
     and that client must have been configured to auto-accept calls from the
     account on the device (how to set this varies between different versions
     of Skype and between platforms -- please search online for specific
     instructions).
     https://support.skype.com/en/faq/FA3751/can-i-automatically-answer-all-my-calls-with-video-in-skype-for-windows-desktop

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

duration : integer  
    Duration of the video call in seconds.

    default: ``300``

contact : str (mandatory)
    The name of the Skype contact to call. The contact must be already
    added (see below). *If use_gui is set*, then this must be the skype
    ID of the contact, *otherwise*, this must be the name of the
    contact as it appears in Skype client's contacts list. In the latter case
    it *must not* contain underscore characters (``_``); it may, however, contain
    spaces. There is no default, you **must specify the name of the contact**.

    .. note:: You may alternatively specify the contact name as
              ``skype_contact`` setting in your ``config.py``. If this is
              specified, the ``contact`` parameter is optional, though
              it may still be specified (in which case it will override
              ``skype_contact`` setting).

use_gui : boolean  
    Specifies whether the call should be placed directly through a
    Skype URI, or by navigating the GUI. The URI is the recommended way
    to place Skype calls on a device, but that does not seem to work
    correctly on some devices (the URI seems to just start Skype, but not
    place the call), so an alternative exists that will start the Skype app
    and will then navigate the UI to place the call (incidentally, this method
    does not seem to work on all devices either, as sometimes Skype starts
    backgrounded...). Please note that the meaning of ``contact`` prameter
    is different depending on whether this is set.  Defaults to ``False``.

    .. note:: You may alternatively specify this as ``skype_use_gui`` setting
              in your ``config.py``.


smartbench
----------

Smartbench is a multi-core friendly benchmark application that measures the
overall performance of an android device. It reports both Productivity and
Gaming Index.

https://play.google.com/store/apps/details?id=com.smartbench.twelve&hl=en

From the website:

It will be better prepared for the quad-core world. Unfortunately this also
means it will run slower on older devices. It will also run slower on
high-resolution tablet devices. All 3D tests are now rendered in full native
resolutions so naturally it will stress hardware harder on these devices.
This also applies to higher resolution hand-held devices.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.


spec2000
--------

SPEC2000 benchmarks measuring processor, memory and compiler.

http://www.spec.org/cpu2000/

From the web site:

SPEC CPU2000 is the next-generation industry-standardized CPU-intensive benchmark suite. SPEC
designed CPU2000 to provide a comparative measure of compute intensive performance across the
widest practical range of hardware. The implementation resulted in source code benchmarks
developed from real user applications. These benchmarks measure the performance of the
processor, memory and compiler on the tested system.

.. note:: At the moment, this workload relies on pre-built SPEC binaries (included in an
          asset bundle). These binaries *must* be built according to rules outlined here::

              http://www.spec.org/cpu2000/docs/runrules.html#toc_2.0

          in order for the results to be valid SPEC2000 results.

.. note:: This workload does not attempt to generate results in an admissible SPEC format. No
          metadata is provided (though some, but not all, of the required metdata is colleted
          by WA elsewhere). It is upto the user to post-process results to generated
          SPEC-admissible results file, if that is their intention.

*base vs peak*

SPEC2000 defines two build/test configuration: base and peak. Base is supposed to use basic
configuration (e.g. default compiler flags) with no tuning, and peak is specifically optimized for
a system. Since this workload uses externally-built binaries, there is no way for WA to be sure
what configuration is used -- the user is expected to keep track of that. Be aware that
base/peak also come with specfic requirements for the way workloads are run (e.g. how many instances
on multi-core systems)::

    http://www.spec.org/cpu2000/docs/runrules.html#toc_3

These are not enforced by WA, so it is again up to the user to ensure that correct workload
parameters are specfied inthe agenda, if they intend to collect "official" SPEC results. (Those
interested in collecting official SPEC results should also note that setting runtime parameters
would violate SPEC runs rules that state that no configuration must be done to the platform
after boot).

*bundle structure*

This workload expects the actual benchmark binaries to be provided in a tarball "bundle" that has
a very specific structure. At the top level of the tarball, there should be two directories: "fp"
and "int" -- for each of the SPEC2000 categories. Under those, there is a sub-directory per benchmark.
Each benchmark sub-directory contains three sub-sub-directorie:

- "cpus" contains a subdirector for each supported cpu (e.g. a15) with a single executable binary
  for that cpu, in addition to a "generic" subdirectory that has not been optimized for a specific
  cpu and should run on any ARM system.
- "data" contains all additional files (input, configuration, etc) that  the benchmark executable
  relies on.
- "scripts" contains one or more one-liner shell scripts that invoke the benchmark binary with
  appropriate command line parameters. The name of the script must be in the format
  <benchmark name>[.<variant name>].sh, i.e. name of benchmark, optionally followed by variant
  name, followed by ".sh" plugin. If there is more than one script, then all of them must
  have  a variant; if there is only one script the it should not cotain a variant.

A typical bundle may look like this::

    |- fp
    |  |-- ammp
    |  |   |-- cpus
    |  |   |   |-- generic
    |  |   |   |   |-- ammp
    |  |   |   |-- a15
    |  |   |   |   |-- ammp
    |  |   |   |-- a7
    |  |   |   |   |-- ammp
    |  |   |-- data
    |  |   |   |-- ammp.in
    |  |   |-- scripts
    |  |   |   |-- ammp.sh
    |  |-- applu
    .  .   .
    .  .   .
    .  .   .
    |- int
    .

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

benchmarks : list_or_string  
    Specfiles the SPEC benchmarks to run.

mode : str  
    SPEC benchmarks can report either speed to execute or throughput/rate. In the latter case, several "threads" will be spawned.

    allowed values: ``'speed'``, ``'rate'``

    default: ``'speed'``

number_of_threads : integer  
    Specify the number of "threads" to be used in 'rate' mode. (Note: on big.LITTLE systems this is the number of threads, for *each cluster*).

force_extract_assets : boolean  
    if set to ``True``, will extract assets from the bundle, even if they are already extracted. Note: this option implies ``force_push_assets``.

force_push_assets : boolean  
    If set to ``True``, assets will be pushed to device even if they're already present.

timeout : integer  
    Timemout, in seconds, for the execution of single spec test.

    default: ``1200``


sqlitebm
--------

Measures the performance of the sqlite database. It determines within
what time the target device processes a number of SQL queries.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.


stream
------

Measures memory bandwidth.

The original source code be found on:
https://www.cs.virginia.edu/stream/FTP/Code/

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

threads : integer  
    The number of threads to execute if OpenMP is enabled


sysbench
--------

SysBench is a modular, cross-platform and multi-threaded benchmark tool
for evaluating OS parameters that are important for a system running a
database under intensive load.

The idea of this benchmark suite is to quickly get an impression about
system performance without setting up complex database benchmarks or
even without installing a database at all.

**Features of SysBench**

   * file I/O performance
   * scheduler performance
   * memory allocation and transfer speed
   * POSIX threads implementation performance
   * database server performance


See: https://github.com/akopytov/sysbench

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

timeout : integer  
    timeout for workload execution (adjust from default if running on a slow device and/or specifying a large value for ``max_requests``

    default: ``300``

test : str  
    sysbench test to run

    allowed values: ``'fileio'``, ``'cpu'``, ``'memory'``, ``'threads'``, ``'mutex'``

    default: ``'cpu'``

threads : integer  
    The number of threads sysbench will launch

    default: ``8``

num_threads : integer  
    The number of threads sysbench will launch, overrides  ``threads`` (old parameter name)

max_requests : integer  
    The limit for the total number of requests.

max_time : integer  
    The limit for the total execution time. If neither this nor
    ``max_requests`` is specified, this will default to 30 seconds.

file_test_mode : str  
    File test mode to use. This should only be specified if ``test`` is ``"fileio"``; if that is the case and ``file_test_mode`` is not specified, it will default to ``"seqwr"`` (please see sysbench documentation for explanation of various modes).

    allowed values: ``'seqwr'``, ``'seqrewr'``, ``'seqrd'``, ``'rndrd'``, ``'rndwr'``, ``'rndrw'``

cmd_params : str  
    Additional parameters to be passed to sysbench as a single stiring

force_install : boolean  
    Always install binary found on the host, even if already installed on device

    default: ``True``

taskset_mask : integer  
    The processes spawned by sysbench will be pinned to cores as specified by this parameter


telemetry
---------

Executes Google's Telemetery benchmarking framework

Url: https://www.chromium.org/developers/telemetry

From the web site:

Telemetry is Chrome's performance testing framework. It allows you to
perform arbitrary actions on a set of web pages and report metrics about
it. The framework abstracts:

  - Launching a browser with arbitrary flags on any platform.
  - Opening a tab and navigating to the page under test.
  - Fetching data via the Inspector timeline and traces.
  - Using Web Page Replay to cache real-world websites so they don't
    change when used in benchmarks.

Design Principles

  - Write one performance test that runs on all platforms - Windows, Mac,
    Linux, Chrome OS, and Android for both Chrome and ContentShell.
  - Runs on browser binaries, without a full Chromium checkout, and without
    having to build the browser yourself.
  - Use WebPageReplay to get repeatable test results.
  - Clean architecture for writing benchmarks that keeps measurements and
    use cases separate.
  - Run on non-Chrome browsers for comparative studies.

This instrument runs  telemetry via its ``run_benchmark`` script (which
must be in PATH or specified using ``run_benchmark_path`` parameter) and
parses metrics from the resulting output.

**device setup**

The device setup will depend on whether you're running a test image (in
which case little or no setup should be necessary)

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

run_benchmark_path : str  
    This is the path to run_benchmark script which runs a
    Telemetry benchmark. If not specified, WA will look for Telemetry in its
    dependencies; if not found there, Telemetry will be downloaded.

test : str  
    Specifies the telemetry test to run.

    default: ``'page_cycler.top_10_mobile'``

run_benchmark_params : str  
    Additional paramters to be passed to ``run_benchmark``.

run_timeout : integer  
    Timeout for execution of the test.

    default: ``900``

extract_fps : boolean  
    if ``True``, FPS for the run will be computed from the trace (must be enabled).

target_config : str  
    Manually specify target configuration for telemetry. This must contain
    --browser option plus any addition options Telemetry requires for a particular
    target (e.g. --device or --remote)


templerun
---------

Templerun game.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``500``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

assets_push_timeout : integer  
    Timeout used during deployment of the assets package (if there is one).

    default: ``500``

clear_data_on_reset : boolean  
    If set to ``False``, this will prevent WA from clearing package
    data for this workload prior to running it.

    default: ``True``


thechase
--------

The Chase demo showcasing the capabilities of Unity game engine.

This demo, is a static video-like game demo, that demonstrates advanced features
of the unity game engine. It loops continuously until terminated.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

duration : integer  
    Duration, in seconds, note that the demo loops the same (roughly) 60 second sceene until stopped.

    default: ``70``


truckerparking3d
----------------

Trucker Parking 3D game.

(yes, apparently that's a thing...)

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``500``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

assets_push_timeout : integer  
    Timeout used during deployment of the assets package (if there is one).

    default: ``500``

clear_data_on_reset : boolean  
    If set to ``False``, this will prevent WA from clearing package
    data for this workload prior to running it.

    default: ``True``


vellamo
-------

Android benchmark designed by Qualcomm.

Vellamo began as a mobile web benchmarking tool that today has expanded
to include three primary chapters. The Browser Chapter evaluates mobile
web browser performance, the Multicore chapter measures the synergy of
multiple CPU cores, and the Metal Chapter measures the CPU subsystem
performance of mobile processors. Through click-and-go test suites,
organized by chapter, Vellamo is designed to evaluate: UX, 3D graphics,
and memory read/write and peak bandwidth performance, and much more!

Note: Vellamo v3.0 fails to run on Juno

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

version : str  
    Specify the version of Vellamo to be run. If not specified, the latest available version will be used.

    allowed values: ``'2.0.3'``, ``'3.0'``

    default: ``'3.0'``

benchmarks : list_of_strs  
    Specify which benchmark sections of Vellamo to be run. Only valid on version 3.0 and newer.
    NOTE: Browser benchmark can be problematic and seem to hang,just wait and it will progress after ~5 minutes

    allowed values: ``'Browser'``, ``'Metal'``, ``'Multi'``

    default: ``['Browser', 'Metal', 'Multi']``

browser : integer  
    Specify which of the installed browsers will be used for the tests. The number refers to the order in which browsers are listed by Vellamo. E.g. ``1`` will select the first browser listed, ``2`` -- the second, etc. Only valid for version ``3.0``.

    default: ``1``


video
-----

Plays a video file using the standard android video player for a predetermined duration.

The video can be specified either using ``resolution`` workload parameter, in which case
`Big Buck Bunny`_ MP4 video of that resolution will be downloaded and used, or using
``filename`` parameter, in which case the video file specified will be used.


.. _Big Buck Bunny: http://www.bigbuckbunny.org/

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

play_duration : integer  
    Playback duration of the video file. This become the duration of the workload.

    default: ``20``

resolution : str  
    Specifies which resolution video file to play.

    allowed values: ``'480p'``, ``'720p'``, ``'1080p'``

    default: ``'720p'``

filename : str  
    The name of the video file to play. This can be either a path
    to the file anywhere on your file system, or it could be just a
    name, in which case, the workload will look for it in
    ``~/.workloads_automation/dependency/video``
    *Note*: either resolution or filename should be specified, but not both!

force_dependency_push : boolean  
    If true, video will always be pushed to device, regardless
    of whether the file is already on the device.  Default is ``False``.


videostreaming
--------------

Uses the FREEdi video player to search, stream and play the specified
video content from YouTube.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

install_timeout : integer  
    Timeout for the installation of the apk.

    default: ``300``

check_apk : boolean  
    Discover the APK for this workload on the host, and check that
    the version matches the one on device (if already installed).

    default: ``True``

force_install : boolean  
    Always re-install the APK, even if matching version is found
    on already installed on the device.

uninstall_apk : boolean  
    If ``True``, will uninstall workload's APK as part of teardown.

video_name : str  
    Name of the video to be played.

resolution : str  
    Resolution of the video to be played. If video_name is setthis setting will be ignored

    allowed values: ``'320p'``, ``'720p'``, ``'1080p'``

    default: ``'320p'``

sampling_interval : integer  
    Time interval, in seconds, after which the status of the video playback to
    be monitoreThe elapsed time of the video playback is
    monitored after after every ``sampling_interval`` seconds and
    compared against the actual time elapsed and the previous
    sampling point. If the video elapsed time is less that
    (sampling time - ``tolerance``) , then the playback is aborted as
    the video has not been playing continuously.

    default: ``20``

tolerance : integer  
    Specifies the amount, in seconds, by which sampling time is
    allowed to deviate from elapsed video playback time. If the delta
    is greater than this value (which could happen due to poor network
    connection), workload result will be invalidated.

    default: ``3``

run_timeout : integer  
    The duration in second for which to play the video

    default: ``200``


