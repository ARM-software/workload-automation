.. _result_processors:

Result_processors
=================

cpustates
---------

Process power ftrace to produce CPU state and parallelism stats.

Parses trace-cmd output to extract power events and uses those to generate
statistics about parallelism and frequency/idle core residency.

.. note:: trace-cmd instrument must be enabled and configured to collect
          at least ``power:cpu_idle`` and ``power:cpu_frequency`` events.
          Reporting should also be enabled (it is by default) as
          ``cpustate`` parses the text version of the trace.
          Finally, the device should have ``cpuidle`` module installed.

This generates two reports for the run:

*parallel.csv*

Shows what percentage of time was spent with N cores active (for N
from 0 to the total number of cores), for a cluster or for a system as
a whole. It contain the following columns:

    :workload: The workload label
    :iteration: iteration that was run
    :cluster: The cluster for which statics are reported. The value of
              ``"all"`` indicates that this row reports statistics for
              the whole system.
    :number_of_cores: number of cores active. ``0`` indicates the cluster
                      was idle.
    :total_time: Total time spent in this state during workload execution
    :%time: Percentage of total workload execution time spent in this state
    :%running_time: Percentage of the time the cluster was active (i.e.
                    ignoring time the cluster was idling) spent in this
                    state.

*cpustate.csv*

Shows percentage of the time a core spent in a particular power state. The first
column names the state is followed by a column for each core. Power states include
available DVFS frequencies (for heterogeneous systems, this is the union of
frequencies supported by different core types) and idle states. Some shallow
states (e.g. ARM WFI) will consume different amount of power depending on the
current OPP. For such states, there will be an entry for each opp. ``"unknown"``
indicates the percentage of time for which a state could not be established from the
trace. This is usually due to core state being unknown at the beginning of the trace,
but may also be caused by dropped events in the middle of the trace.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

first_cluster_state : integer  
    The first idle state which is common to a cluster.

    default: ``2``

first_system_state : integer  
    The first idle state which is common to all cores.

    default: ``3``

write_iteration_reports : boolean  
    By default, this instrument will generate reports for the entire run
    in the overall output directory. Enabling this option will, in addition,
    create reports in each iteration's output directory. The formats of these
    reports will be similar to the overall report, except they won't mention
    the workload name or iteration number (as that is implied by their location).

use_ratios : boolean  
    By default proportional values will be reported as percentages, if this
    flag is enabled, they will be reported as ratios instead.

create_timeline : boolean  
    Create a CSV with the timeline of core power states over the course of the run
    as well as the usual stats reports.

    default: ``True``


csv
---

Creates a ``results.csv`` in the output directory containing results for
all iterations in CSV format, each line containing a single metric.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

use_all_classifiers : boolean  
    If set to ``True``, this will add a column for every classifier
    that features in at least one collected metric.

    .. note:: This cannot be ``True`` if ``extra_columns`` is set.

extra_columns : list_of_strs  
    List of classifiers to use as columns.

    .. note:: This cannot be set if ``use_all_classifiers`` is ``True``.


dvfs
----

Reports DVFS state residency data form ftrace power events.

This generates a ``dvfs.csv`` in the top-level results directory that,
for each workload iteration, reports the percentage of time each CPU core
spent in each of the DVFS frequency states (P-states), as well as percentage
of the time spent in idle, during the execution of the workload.

.. note:: ``trace-cmd`` instrument *MUST* be enabled in the instrumentation,
          and at least ``'power*'`` events must be enabled.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.


ipynb_exporter
--------------

Generates an IPython notebook from a template with the results and runs it.
Optionally it can show the resulting notebook in a web browser.
It can also generate a PDF from the notebook.

The template syntax is that of `jinja2 <http://jinja.pocoo.org/>`_
and the template should generate a valid ipython notebook. The
templates receives ``result`` and ``context`` which correspond to
the RunResult and ExecutionContext respectively. You can use those
in your ipython notebook template to extract any information you
want to parse or show.

This results_processor depends on ``ipython`` and ``python-jinja2`` being
installed on the system.

For example, a simple template that plots a bar graph of the results is::


 {
  "metadata": {
   "name": ""
  },
  "nbformat": 3,
  "nbformat_minor": 0,
  "worksheets": [
   {
    "cells": [
     {
      "cell_type": "code",
      "collapsed": false,
      "input": [
       "%pylab inline"
      ],
      "language": "python",
      "metadata": {},
      "outputs": [],
      "prompt_number": 1
     },
     {
      "cell_type": "code",
      "collapsed": false,
      "input": [
       "results = {",
       {% for ir in result.iteration_results -%}
         {% for metric in ir.metrics -%}
           {% if metric.name in ir.workload.summary_metrics or not ir.workload.summary_metrics -%}
       "\"{{ ir.spec.label }}_{{ ir.id }}_{{ ir.iteration }}_{{ metric.name }}\": {{ metric.value }}, ",
           {%- endif %}
         {%- endfor %}
       {%- endfor %}
       "}\n",
       "width = 0.7\n",
       "ind = np.arange(len(results))"
      ],
      "language": "python",
      "metadata": {},
      "outputs": [],
      "prompt_number": 2
     },
     {
      "cell_type": "code",
      "collapsed": false,
      "input": [
       "fig, ax = plt.subplots()\n",
       "ax.bar(ind, results.values(), width)\n",
       "ax.set_xticks(ind + width/2)\n",
       "_ = ax.set_xticklabels(results.keys())"
      ],
      "language": "python",
      "metadata": {},
      "outputs": [],
      "prompt_number": 3
     }
    ],
    "metadata": {}
   }
  ]
 }

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

notebook_template : str  
    Filename of the ipython notebook template.  If
    no `notebook_template` is specified, the example template
    above is used.

    default: ``'template.ipynb'``

notebook_name_prefix : str  
    Prefix of the name of the notebook. The date,
    time and ``.ipynb`` are appended to form the notebook filename.
    E.g. if notebook_name_prefix is ``result_`` then a run on 13th
    April 2015 at 9:54 would generate a notebook called
    ``result_150413-095400.ipynb``. When generating a PDF,
    the resulting file will have the same name, but
    ending in ``.pdf``.

    default: ``'result_'``

show_notebook : boolean  
    Open a web browser with the resulting notebook.

notebook_directory : str  
    Path to the notebooks directory served by the
    ipython notebook server. You must set it if
    ``show_notebook`` is selected. The ipython notebook
    will be copied here if specified.

notebook_url : str  
    URL of the notebook on the IPython server. If
    not specified, it will be assumed to be in the root notebooks
    location on localhost, served on port 8888. Only needed if
    ``show_notebook`` is selected.

    .. note:: the URL should not contain the final part (the notebook name) which will be populated automatically.

    default: ``'http://localhost:8888/notebooks'``

convert_to_html : boolean  
    Convert the resulting notebook to HTML.

show_html : boolean  
    Open the exported html notebook at the end of
    the run. This can only be selected if convert_to_html has
    also been selected.

convert_to_pdf : boolean  
    Convert the resulting notebook to PDF.

show_pdf : boolean  
    Open the pdf at the end of the run. This can
    only be selected if convert_to_pdf has also been selected.


json
----

Creates a ``results.json`` in the output directory containing results for
all iterations in JSON format.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.


mongodb
-------

Uploads run results to a MongoDB instance.

MongoDB is a popular document-based data store (NoSQL database).

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

uri : str  
    Connection URI. If specified, this will be used for connecting
    to the backend, and host/port parameters will be ignored.

host : str (mandatory)
    IP address/name of the machinge hosting the MongoDB server.

    default: ``'localhost'``

port : integer (mandatory)
    Port on which the MongoDB server is listening.

    default: ``27017``

db : str (mandatory)
    Database on the server used to store WA results.

    default: ``'wa'``

extra_params : dict  
    Additional connection parameters may be specfied using this (see
    pymongo documentation.

authentication : dict  
    If specified, this will be passed to db.authenticate() upon connection;
    please pymongo documentaion authentication examples for detail.


notify
------

Display a desktop notification when the run finishes

Notifications only work in linux systems. It uses the generic
freedesktop notification specification. For this results processor
to work, you need to have python-notify installed in your system.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.


sqlite
------

Stores results in an sqlite database.

This may be used accumulate results of multiple runs in a single file.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

database : str  
    Full path to the sqlite database to be used.  If this is not specified then
    a new database file will be created in the output directory. This setting can be
    used to accumulate results from multiple runs in a single database. If the
    specified file does not exist, it will be created, however the directory of the
    file must exist.

    .. note:: The value must resolve to an absolute path,
                relative paths are not allowed; however the
                value may contain environment variables and/or
                the home reference ~.

overwrite : boolean  
    If ``True``, this will overwrite the database file
    if it already exists. If ``False`` (the default) data
    will be added to the existing file (provided schema
    versions match -- otherwise an error will be raised).


standard
--------

Creates a ``result.txt`` file for every iteration that contains metrics
for that iteration.

The metrics are written in ::

    metric = value [units]

format.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.


status
------

Outputs a txt file containing general status information about which runs
failed and which were successful

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.


summary_csv
-----------

Similar to csv result processor, but only contains workloads' summary metrics.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.


syeg_csv
--------

Generates a CSV results file in the format expected by SYEG toolchain.

Multiple iterations get parsed into columns, adds additional columns for mean
and standard deviation, append number of threads to metric names (where
applicable) and add some metadata based on external mapping files.

parameters
~~~~~~~~~~

modules : list  
    Lists the modules to be loaded by this plugin. A module is a plug-in that
    further extends functionality of an plugin.

outfile : str  
    The name of the output CSV file.

    default: ``'syeg_out.csv'``


