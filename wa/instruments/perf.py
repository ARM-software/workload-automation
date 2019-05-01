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

import collections
import os

from devlib.utils.cli import Command
from devlib.trace.perf import PerfCollector
from wa import Instrument, Parameter
from wa.utils.types import list_or_string, list_of_strs

__all__ = [
    'PerfInstrument',
]


class YamlCommandDescriptor(collections.OrderedDict):

    def __init__(self, yaml_dict):
        super(YamlCommandDescriptor, self).__init__()
        if isinstance(yaml_dict, YamlCommandDescriptor):
            for k, v in yaml_dict.items():
                self[k] = v
            return
        yaml_dict_copy = yaml_dict.copy()
        for label, parameters in yaml_dict_copy.items():
            self[label] = str(Command(kwflags_join=',',
                                      kwflags_sep='=',
                                      end_of_options='--',
                                      **parameters))


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
        Parameter('pre_commands', kind=YamlCommandDescriptor, default=None,
                  description="""
                  Dictionary of commands to be run before the workloads run
                  (same format as ``commands``).
                 """),
        Parameter('commands', kind=YamlCommandDescriptor, default=None,
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
        Parameter('post_commands', kind=YamlCommandDescriptor, default=None,
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

            self.commands = YamlCommandDescriptor({
                label: {
                    'command': 'stat',
                    'kwflags': {'event': self.events},
                    'options': options,
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
        # pylint: disable=unused-argument
        self.collector.reset()

    def start(self, context):
        # pylint: disable=unused-argument
        self.collector.start()

    def stop(self, context):
        # pylint: disable=unused-argument
        self.collector.stop()

    def update_output(self, context):
        outdir = os.path.join(context.output_directory, 'perf')
        self.collector.get_traces(outdir)
        # HUGE TODO: add parsers for supported post_commands
        #    (or should these be in devlib?)

    def teardown(self, context):
        # pylint: disable=unused-argument
        self.collector.reset()
