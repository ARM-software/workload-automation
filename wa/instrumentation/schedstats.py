#    Copyright 2017 ARM Limited
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

from devlib import SchedstatsInstrument as _Schedstats

from wa import Instrument
from wa.framework.exception import InstrumentError

class SchedstatsInstrument(Instrument):
    name = 'schedstats'

    description = """
    Collects scheduler statistics info and reports them as Metrics

    This uses the devlib schedstats instrument to collect schedstats information
    at the beginning and at the end of the workload. It then reports the delta
    in each statistic as a Metric.

    The metrics are named according to corresponding identifiers in the
    kernel scheduler code. The names for ``sched_domain.lb_*`` stats, which are
    recorded per ``cpu_idle_type`` are suffixed with a ':' followed by the idle
    type, for example ``'lb_balanced:CPU_NEWLY_IDLE'``.

    A classifier called 'node' is used to differentiate between the metrics from
    different sources (each CPU and sched_domain). Therefore you might want to
    make sure your result_processors report that classifier. For the CSV
    processor, for example, the simplest way is to set ``use_all_classifiers``
    to ``True``.
    """

    def initialize(self, context):
        if not self.target.file_exists(_Schedstats.schedstat_path) and \
           not self.target.file_exists(_Schedstats.sysctl_path):
            raise InstrumentError('schedstats not supported by target. '
                                  'Ensure CONFIG_SCHEDSTATS is enabled.')

    def setup(self, context):
        self.instrument = _Schedstats(self.target)
        self.instrument.reset()

    def start(self, context):
        self.before = self.instrument.take_measurement()

    def stop(self, context):
        self.after = self.instrument.take_measurement()

    def update_result(self, context):
        before = {m.channel.label: m for m in self.before}
        after = {m.channel.label: m for m in self.after}

        if set(before.keys()) != set(after.keys()):
            raise InstrumentError('schedstats measurements returned different entries!')

        for label, measurement_after in after.iteritems():
            measurement_before = before[label]
            diff = measurement_after.value - measurement_before.value
            channel = measurement_after.channel
            context.add_metric(channel.kind, diff,
                               classifiers={'node': channel.site})

    def teardown(self, context):
        self.instrument.teardown()

