.. _invocation:
.. highlight:: none

========
Commands
========

Installing the wlauto package will add ``wa`` command to your system,
which you can run from anywhere. This has a number of sub-commands, which can
be viewed by executing ::

        wa -h

Individual sub-commands are discussed in detail below.

run
---

The most common sub-command you will use is ``run``. This will run specified
workload(s) and process resulting output. This takes a single mandatory
argument that specifies what you want WA to run. This could be either a
workload name, or a path  to an "agenda" file that allows to specify multiple
workloads as well as a lot additional configuration (see :ref:`agenda`
section for details). Executing ::

        wa run -h

Will display help for this subcommand that will look something like this::

        usage: run [-d DIR] [-f] AGENDA

        Execute automated workloads on a remote device and process the resulting
        output.

        positional arguments:
          AGENDA                Agenda for this workload automation run. This defines
                                which workloads will be executed, how many times, with
                                which tunables, etc. See /usr/local/lib/python2.7
                                /dist-packages/wlauto/agenda-example.csv for an
                                example of how this file should be structured.

        optional arguments:
          -h, --help            show this help message and exit
          -c CONFIG, --config CONFIG
                                specify an additional config.py
          -v, --verbose         The scripts will produce verbose output.
          --version             Output the version of Workload Automation and exit.
          --debug               Enable debug mode. Note: this implies --verbose.
          -d DIR, --output-directory DIR
                                Specify a directory where the output will be
                                generated. If the directory already exists, the script
                                will abort unless -f option (see below) is used,in
                                which case the contents of the directory will be
                                overwritten. If this option is not specified, then
                                wa_output will be used instead.
          -f, --force           Overwrite output directory if it exists. By default,
                                the script will abort in this situation to prevent
                                accidental data loss.
          -i ID, --id ID        Specify a workload spec ID from an agenda to run. If
                                this is specified, only that particular spec will be
                                run, and other workloads in the agenda will be
                                ignored. This option may be used to specify multiple
                                IDs.


Output Directory
~~~~~~~~~~~~~~~~

The exact contents on the output directory will depend on configuration options
used, instrumentation and output processors enabled, etc. Typically, the output
directory will contain a results file at the top level that lists all
measurements that were collected (currently, csv and json formats are
supported), along with a subdirectory for each iteration executed with output
for that specific iteration.

At the top level, there will also be a run.log file containing the complete log
output for the execution. The contents of this file is equivalent to what you
would get in the console when using --verbose option.

Finally, there will be a __meta subdirectory. This will contain a copy of the
agenda file used to run the workloads along with any other device-specific
configuration files used during execution.


create
------

This can be used to create various WA-related objects, currently workloads, packages and agendas.
The full set of options for this command are::

    usage: wa create [-h] [-c CONFIG] [-v] [--debug] [--version]
                     {workload,package,agenda} ...

    positional arguments:
      {workload,package,agenda}
        workload            Create a new workload. By default, a basic workload
                            template will be used but you can use options to
                            specify a different template.
        package             Create a new empty Python package for WA extensions.
                            On installation, this package will "advertise" itself
                            to WA so that Extensions with in it will be loaded by
                            WA when it runs.
        agenda              Create an agenda whit the specified extensions
                            enabled. And parameters set to their default values.

    optional arguments:
      -h, --help            show this help message and exit
      -c CONFIG, --config CONFIG
                            specify an additional config.py
      -v, --verbose         The scripts will produce verbose output.
      --debug               Enable debug mode. Note: this implies --verbose.
      --version             show program's version number and exit

Use "wa create <object> -h" to see all the object-specific arguments. For example::

        wa create agenda -h

will display the relevant options that can be used to create an agenda. 

get-assets
----------

This command can download external extension dependencies used by Workload Automation.
It can be used to download assets for all available extensions or those specificity listed. 
The full set of options for this command are::

    usage: wa get-assets [-h] [-c CONFIG] [-v] [--debug] [--version] [-f]
                         [--url URL] (-a | -e EXT [EXT ...])

    optional arguments:
      -h, --help            show this help message and exit
      -c CONFIG, --config CONFIG
                            specify an additional config.py
      -v, --verbose         The scripts will produce verbose output.
      --debug               Enable debug mode. Note: this implies --verbose.
      --version             show program's version number and exit
      -f, --force           Always fetch the assets, even if matching versions
                            exist in local cache.
      --url URL             The location from which to download the files. If not
                            provided, config setting ``remote_assets_url`` will be
                            used if available, else uses the default
                            REMOTE_ASSETS_URL parameter in the script.
      -a, --all             Download assets for all extensions found in the index.
                            Cannot be used with -e.
      -e EXT [EXT ...]      One or more extensions whose assets to download.
                            Cannot be used with --all.


list
----

This lists all extensions of a particular type. For example::

        wa list workloads

will list all workloads currently included in WA. The list will consist of
extension names and short descriptions of the functionality they offer.


show
----

This will show detailed information about an extension, including more in-depth
description and any parameters/configuration that are available.  For example
executing::

        wa show andebench

will produce something like::


        andebench

        AndEBench is an industry standard Android benchmark provided by The Embedded Microprocessor Benchmark Consortium
        (EEMBC).

        parameters:

        number_of_threads
        Number of threads that will be spawned by AndEBench.
                type: int

        single_threaded
        If ``true``, AndEBench will run with a single thread. Note: this must not be specified if ``number_of_threads``
        has been specified.
                type: bool

        http://www.eembc.org/andebench/about.php

        From the website:

        - Initial focus on CPU and Dalvik interpreter performance
        - Internal algorithms concentrate on integer operations
        - Compares the difference between native and Java performance
        - Implements flexible multicore performance analysis
        - Results displayed in Iterations per second
        - Detailed log file for comprehensive engineering analysis

.. _record-command:

record
------

This command simplifies the process of recording an revent file. It
will automatically deploy revent and even has the option of automatically
opening apps. WA uses two parts to the names of revent recordings in the
format, {device_name}.{suffix}.revent. - device_name can either be specified
manually with the ``-d`` argument or it can be automatically determined. On
Android device it will be obtained from ``build.prop``, on Linux devices it is
obtained from ``/proc/device-tree/model``. - suffix is used by WA to determine
which part of the app execution the recording is for, currently these are
either ``setup`` or ``run``. This should be specified with the ``-s``
argument. The full set of options for this command are::

    usage: wa record [-h] [-c CONFIG] [-v] [--debug] [--version] [-d DEVICE]
                 [-s SUFFIX] [-o OUTPUT] [-p PACKAGE] [-g] [-C]

    optional arguments:
      -h, --help            show this help message and exit
      -c CONFIG, --config CONFIG
                            specify an additional config.py
      -v, --verbose         The scripts will produce verbose output.
      --debug               Enable debug mode. Note: this implies --verbose.
      --version             show program's version number and exit
      -d DEVICE, --device DEVICE
                            The name of the device
      -s SUFFIX, --suffix SUFFIX
                            The suffix of the revent file, e.g. ``setup``
      -o OUTPUT, --output OUTPUT
                            Directory to save the recording in
      -p PACKAGE, --package PACKAGE
                            Package to launch before recording
      -g, --gamepad         Record from a gamepad rather than all devices.
      -C, --clear           Clear app cache before launching it

.. _replay-command:

replay
------

Along side ``record`` wa also has a command to playback recorded revent files.
It behaves very similar to the ``record`` command taking many of the same options::

    usage: wa replay [-h] [-c CONFIG] [-v] [--debug] [--version] [-p PACKAGE] [-C]
                 revent

    positional arguments:
      revent                The name of the file to replay

    optional arguments:
      -h, --help            show this help message and exit
      -c CONFIG, --config CONFIG
                            specify an additional config.py
      -v, --verbose         The scripts will produce verbose output.
      --debug               Enable debug mode. Note: this implies --verbose.
      --version             show program's version number and exit
      -p PACKAGE, --package PACKAGE
                            Package to launch before recording
      -C, --clear           Clear app cache before launching it
