#    Copyright 2013-2019 ARM Limited
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

import itertools
import os
import re
import shlex

from devlib.trace.perf import PerfCollector, PerfCommandDict
from wa import Instrument, Parameter
from wa.utils.types import list_or_string, list_of_strs

__all__ = [
    'PerfInstrument',
]

DEFAULT_EVENTS = ['migration', 'cs']
DEFAULT_OPTIONSTRING = '-a'


class PerfInstrument(Instrument):

    name = 'perf'
    description = """
    Perf is a Linux profiling tool based on performance counters.

    Performance counters are typically CPU hardware registers (found in the
    Performance Monitoring Unit) that count hardware events such as
    instructions executed, cache-misses suffered, or branches mispredicted.
    Because each ``event`` corresponds to a hardware counter, the maximum
    number of events that can be tracked is imposed by the available hardware.

    By extension, performance counters, in the context of ``perf``, also refer
    to so-called "software counters" representing events that can be tracked by
    the OS kernel (e.g. context switches). As these are software events, the
    counters are kept in RAM and the hardware virtually imposes no limit on the
    number that can be used.

    This instrument allows a straight-forward way of calling ``perf stat``
    through the named parameters ``optionstring`` and ``events``, which is the
    default behaviour (see the defaults of these parameters).  However, it can
    also be used through the more advanced ``commands`` dictionary which
    provides a flexible access to all ways ``perf`` can be used.

    In both cases, if a ``stat`` command is issued, this workload will
    automatically parse its output into run ``metrics``. For this reason,
    please avoid the ``-x`` ``stat`` flag.

    The ``pre_commands`` and ``post_commands`` are provided to suit those
    ``perf`` commands that don't actually capture data (``list``, ``config``,
    ``report``, ...).

    Commands are tagged with _labels_ which are used to define in which
    directory they run. Therefore, a pair of commands (_e.g._ a `record`
    followed by a `report`) sharing the same label can access the same files
    while commands with different labels can use the same filename with the
    guarantee of avoiding clashes.

    Depending on the subcommand used, ``perf`` might require setting:

        - ``/proc/sys/kernel/printk`` to ``4``
        - ``/proc/sys/kernel/kptr_restrict`` to ``0``

    Please refer to the ``sysfile_values`` runtime parameter to do so from an
    agenda.

    When running ``perf stat``, this instrument reports the captured
    counters as unitless :class:`Metrics` with the following classifiers:

    - ``'name'``: The name of the event as reported by ``perf``. This name
      may not be unique when aggregation is disabled as the same counter is
      then captured for multiple hardware threads;
    - ``'label'``: Label given to the run of ``perf stat``;
    - ``'target'``: The target ``perf`` reports for the captured events.
      This is shared across all events of a run and is further specialized
      by ``'hw_thread'``, ``'core'`` and ``'cluster'`` if applicable;
    - ``'duration'``, ``'duration_units'``: duration of the ``perf`` run;
    - ``'count_error'``: A string containing the error corresponding that
      prevented the counter from being captured. Only available if an error
      occured. In this case the value of the metric is always ``0``;
    - ``'hw_thread_count'``: Number of **hardware** threads that were
      contributing to the counter. Only available when the automatic
      aggregation done by ``perf stat`` is disabled. See ``'hw_thread'``,
      ``'core'`` and ``'cluster'``;
    - ``'hw_thread'``: When the ``--no-aggr`` option is used, holds the
      index of the hardware thread that incremented the counter. In this
      case, ``'hw_thread_count'`` is always ``1``. For backward
      compatibility, the ``'cpu'`` classifier is provided as a synonym of
      ``'hw_thread'`` (unlike what its name might suggest, on systems
      supporting hardware multithreading, ``'cpu'`` is not a synonym of
      ``'core'``!);
    - ``'cluster'``: When the ``--per-socket`` option is used, holds the
      index of the cluster (_i.e._ "socket" in ``perf`` terminology) that
      incremented the counter and ``'hw_thread_count'`` holds the number of
      hardware threads in the cluster. When the ``--per-core`` option is
      used, this classifier gives the index of the cluster of the core.
    - ``'core'``: When the ``--per-core`` option is used, holds the index
      (within its cluster) of the core that incremented the counter and
      ``'hw_thread_count'`` holds the number of hardware threads in the
      core.
    - ``'enabled'``: When ``perf`` needs to capture more hardware events
      than there are hardware counters, it shares the hardware counters
      among the events through time-slicing. This classifier holds the
      fraction (between ``0.0`` and ``100.0``) of the run that a hardware
      counter was allocated to the the event. Available only for hardware
      events and only when time-slicing was required.
    - ``'comment_value'``, ``'comment_units'``: Some counters may come with
      an extra "comment" (following a ``#``) added by ``perf``. The
      ``'comment_value'`` holds the numeric (``int`` or ``float``) value of
      the comment while ``'comment_units'`` holds the rest of the comment
      (typically the units). Only available for the events for which
      ``perf`` added a comment.
    """

    parameters = [
        Parameter('force_install', kind=bool, default=False,
                  description="""
                  Always install ``perf`` binary even if ``perf`` is already
                  present on the device.
                  """),
        Parameter('events', kind=list_of_strs, default=None,
                  description="""
                  List of events the default ``perf stat`` should capture.
                  Valid events can be obtained from ``perf list`` and
                  ``perf --help``.
                  This parameter is ignored if ``commands`` is passed.

                  default: {}
                  """.format(
                      ','.join('``{}``'.format(e) for e in DEFAULT_EVENTS))
                  ),
        Parameter('optionstring', kind=list_or_string, default=None,
                  description="""
                  String of options the default ``perf stat`` should use.
                  For backward compatibility, this may be be a list of strings.
                  In that case, a ``perf stat`` command will be launched for
                  each string. This parameter is ignored if ``commands`` is
                  passed.
                  This parameter is ignored if ``commands`` is passed.

                  default: ``{}``
                  """.format(DEFAULT_OPTIONSTRING)
                  ),
        Parameter('labels', kind=list_of_strs, default=None,
                  description=r"""
                  These labels act like the keys of the ``commands`` parameter.
                  They are provided for backward compatibility. If specified,
                  the number of labels must match the number of
                  ``optionstring``\ s. This parameter is ignored if
                  ``commands`` is passed.
                  """),
        Parameter('pre_commands', kind=PerfCommandDict, default=None,
                  description="""
                  Dictionary of commands to be run before the workloads run
                  (same format as ``commands``).
                 """),
        Parameter('commands', kind=PerfCommandDict, default=None,
                  description="""
                  Dictionary in which keys are considered as *labels* and
                  values are themselves dictionaries with the following
                  entries:

                      - ``command`` (``str``): The ``perf`` subcommand
                        (``stat``, ``record``, ...);
                      - ``flags`` (``str`` or ``list``): Switch flags without
                        their leading hyphens (``no-inherit``, ``all-cpus``,
                        ``a``, ...);
                      - ``kwflags`` (``dict``): Dictionary of flag names (no
                        hyphen) as keys and their corresponding values.
                        These values can be ``list``s for flags taking CSV
                        inputs (``event``, ``pid``, ...);
                      - ``args`` (``str`` or valid command): the post-``--``
                        arguments. This is typically the command ``perf`` will
                        launch and monitor. Therefore, a valid command
                        dictionary (same as this one) is accepted;

                  As an example, the default behaviour can be replicated
                  through::

                      :language: yaml

                      perf:
                          commands:
                              default_behaviour:
                                  command: stat
                                  flags:
                                      - all-cpus
                                  kwflags:
                                      event:
                                          - migrations
                                          - cs
                                  args:
                                      command: sleep
                                      args: 1000
                                  stderr: '&1'
                                  stdout: stat.out
                 """),
        Parameter('post_commands', kind=PerfCommandDict, default=None,
                  description="""
                  Dictionary of commands to be run after the workloads run
                  (same format as ``commands``).
                 """),
    ]

    def __init__(self, target, **kwargs):
        super(PerfInstrument, self).__init__(target, **kwargs)
        self.collector = None

    def initialize(self, context):
        # pylint: disable=unused-argument
        # pylint: disable=access-member-before-definition
        # pylint: disable=attribute-defined-outside-init
        if self.pre_commands is None:
            self.pre_commands = PerfCommandDict({})
        if self.post_commands is None:
            self.post_commands = PerfCommandDict({})
        if self.commands is None:
            if self.optionstring is None:
                self.optionstring = DEFAULT_OPTIONSTRING

            if self.events is None:
                self.events = DEFAULT_EVENTS

            if isinstance(self.optionstring, str):
                self.optionstring = [self.optionstring]

            if not self.labels:
                self.labels = ['default{}'.format(i)
                               for i, _ in enumerate(self.optionstring)]
            elif isinstance(self.labels, str):
                self.labels = [self.labels]

            if len(self.labels) != len(self.optionstring):
                raise ValueError('Lengths of labels and optionstring differ')

            self.commands = PerfCommandDict({
                label: {
                    'command': 'stat',
                    'kwflags': {'event': self.events},
                    'options': shlex.split(options),
                    'args': {
                        'command': 'sleep',
                        'args': 1000,
                    },
                    'stderr': '&1',
                    'stdout': 'stat.out',
                }
                for label, options in zip(self.labels, self.optionstring)
            })
        else:
            for name in ['optionstring', 'events', 'labels']:
                if self.__dict__[name] is not None:
                    raise ValueError(
                        '{} should not be passed if commands is'.format(name))

        self.collector = PerfCollector(self.target,
                                       self.force_install,
                                       self.pre_commands,
                                       self.commands,
                                       self.post_commands)

    def setup(self, context):
        self.collector.reset()
        version = self.collector.execute('--version').strip()
        context.update_metadata('versions', self.name, version)

    def start(self, context):
        # pylint: disable=unused-argument
        self.collector.start()

    def stop(self, context):
        # pylint: disable=unused-argument
        self.collector.stop()

    def update_output(self, context):
        outdir = os.path.join(context.output_directory, self.name)
        self.collector.get_traces(outdir)
        all_commands = itertools.chain(self.pre_commands.items(),
                                       self.commands.items(),
                                       self.post_commands.items())
        for label, cmd in all_commands:
            if 'stat' in cmd.command:
                # perf stat supports redirecting its stdout to --output/-o:
                stat_file = (cmd.kwflags.get('o', None) or
                             cmd.kwflags.get('output', None) or
                             cmd.stdout)
                with open(os.path.join(outdir, label, stat_file)) as f:
                    for metric in self._extract_stat_metrics(label, f.read()):
                        context.add_metric(**metric)

    def teardown(self, context):
        # pylint: disable=unused-argument
        self.collector.reset()

    @classmethod
    def _extract_stat_metrics(cls, label, stdout):
        match = cls._stat_regex.search(stdout)
        if match is None:
            return
        base_classifiers = {
            'label': label,
            'target': match['target'],
            'duration': float(match['duration'].replace(',', '')),
            'duration_units': match['duration_units'],
        }
        for m in cls._stat_counter_regex.finditer(match['counters']):
            classifiers = base_classifiers.copy()
            name, count = cls._extract_stat_count(m, classifiers)
            yield {
                'name': name,
                'units': None,
                'value': count,
                'classifiers': classifiers,
            }

    _stat_regex = re.compile(
        r'Performance counter stats for (?P<target>.*?)\s*:\s*$'
        r'^(?P<counters>.*)$'
        r'^\s*(?P<duration>[0-9.,]+)\s*(?P<duration_units>\S+)\s*time elapsed',
        flags=(re.S | re.M))

    _stat_counter_regex = re.compile(
        r'^\s*{aggr}?\s*{count}\s*{name}\s*{comment}?(?:{enabled}|$)'.format(
            aggr=r'(?:{hw_thread}|(?:{cluster}{core}?\s*{thread_cnt}))'.format(
                hw_thread=r'(?:CPU-?(?P<hw_thread>\d+))',
                cluster=r'S(?P<cluster>\d+)',
                core=r'(?:-C(?P<core>\d+))',
                thread_cnt=r'(?P<hw_thread_count>\d+)'),
            count=r'(?P<count>[0-9.,]+|\<not supported\>|\<not counted\>)',
            name=r'(?P<name>.*?)',
            comment=r'(?:#\s*{value}\s*{units}\s*)'.format(
                value=r'(?P<comment_value>[0-9,.]+)',
                units=r'(?P<comment_units>.*?)'),
            enabled=r'(?:[\[\(](?P<enabled>[0-9.]+)%[\)\]])'),
        flags=re.M)

    @staticmethod
    def _extract_stat_count(match, classifiers):
        """Extracts the counter classifiers and count from a counter_match.

        Parameters:
            match        A :class:`re.Match` from :attr:`_stat_counter_regex`
            classifiers  A dictionary to be completed for the matched counter

        Returns:
            A (name, value) tuple for the matched counter (value is 0 if an
            error occurred).
        """
        name = '{}_{}'.format(classifiers['label'],
                              match['name']).replace(' ', '_')
        classifiers['name'] = match['name']
        # But metrics need a unique name (classifiers not enough) so this
        # name might be specialized by the following:
        try:
            count = int(match['count'].replace(',', ''))
        except ValueError:
            try:
                # some "counters" return a float (e.g. "task-clock"):
                count = float(match['count'].replace(',', ''))
            except ValueError:
                # perf may report "not supported" or "not counted":
                count = 0  # as metrics have to be numeric, can't use None
                classifiers['count_error'] = match['count']
        if match['hw_thread']:  # --no-aggr
            classifiers['hw_thread'] = int(match['hw_thread'])
            classifiers['hw_thread_count'] = 1
            classifiers['cpu'] = int(match['hw_thread'])  # deprecated!
            name += '_T{}'.format(classifiers["hw_thread"])
        elif match['cluster']:  # --per-core or --per-socket
            classifiers['cluster'] = int(match['cluster'])
            classifiers['hw_thread_count'] = int(match['hw_thread_count'])
            name += '_S{}'.format(classifiers["cluster"])
            if match['core']:  # --per-core
                classifiers['core'] = int(match['core'])
                name += '_C{}'.format(classifiers["core"])
        if match['comment_value']:
            try:
                classifiers['comment_value'] = int(match['comment_value'])
            except ValueError:
                classifiers['comment_value'] = float(match['comment_value'])
        if match['comment_units']:
            classifiers['comment_units'] = match['comment_units']
        if match['enabled']:
            classifiers['enabled'] = float(match['enabled'])
        return (name, count)
