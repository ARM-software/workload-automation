#    Copyright 2020 ARM Limited
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
import os
import re

import pandas as pd

from wa import Instrument, Parameter, Executable, InstrumentError


class ProcStatCollector(Instrument):
    name = "proc_stat"
    description = """
    Collect CPU load information from /proc/stat.
    """

    parameters = [
        Parameter(
            "period",
            float,
            default=5,
            constraint=lambda x: x > 0,
            description="""
                  Time (in seconds) between collections.
                  """,
        ),
        Parameter(
            "per_core",
            kind=bool,
            default=False,
            description="If true, it also captures per-core stats.",
        ),
        Parameter(
            "use_boottime",
            kind=bool,
            default=False,
            description="""
                If true, boot time will be used for the timestamp instead of " \
                ISO8601 date-time, to match the `poller` instrument.
            """,
        ),
    ]

    def initialize(self, context):
        host_poller = context.get_resource(
            Executable(self, self.target.abi, "proc_stat_poller")
        )
        self.target_poller = self.target.install(host_poller)

        self.target_output = self.target.path.join(
            self.target.working_directory, "cpu_load.csv"
        )
        self.target_log_path = self.target.path.join(
            self.target.working_directory, "proc_stat_poller.log"
        )

        per_core_option = ""
        if self.per_core:
            per_core_option = "-c"

        timestamp_option = ""
        if self.use_boottime:
            timestamp_option = "-b"

        self.command = "{} {} {} -t {} > {} 2>{}".format(
            self.target_poller,
            per_core_option,
            timestamp_option,
            self.period * 1000000,
            self.target_output,
            self.target_log_path,
        )

    def start(self, context):  # pylint: disable=unused-argument
        self.target.kick_off(self.command)

    def stop(self, context):  # pylint: disable=unused-argument
        self.target.killall("proc_stat_poller", signal="TERM")

    def update_output(self, context):
        self.host_output = os.path.join(context.output_directory, "proc-stat-raw.csv")
        self.target.pull(self.target_output, self.host_output)
        context.add_artifact("proc-stat-raw", self.host_output, kind="raw")

        host_log_file = os.path.join(context.output_directory, "proc_stat_poller.log")
        self.target.pull(self.target_log_path, host_log_file)
        context.add_artifact("proc_stat_poller.log", host_log_file, kind="log")

        with open(host_log_file) as fh:
            for line in fh:
                if "ERROR" in line:
                    raise InstrumentError(line.strip())
                if "WARNING" in line:
                    self.logger.warning(line.strip())
                if "Detected" in line:
                    self.logger.info(line.strip())

        df = pd.read_csv(self.host_output)

        cols_types = [
            "user",
            "nice",
            "system",
            "idle",
            "iowait",
            "irq",
            "softirq",
            "steal",
            "guest",
            "guest_nice",
        ]
        cpus = sorted(
            set(
                re.match(r"^(cpu\d*_)", col).group(1)
                for col in df.columns
                if re.match(r"^(cpu\d*_)", col)
            )
        )

        results = {"timestamp": df["timestamp"].iloc[1:].reset_index(drop=True)}
        for cpu in [""] + cpus:
            # Get the CPU data
            cpu_data = df[["{}{}".format(cpu, col) for col in cols_types]]
            deltas = cpu_data.diff()

            total_delta = deltas.sum(axis=1)
            idle_delta = deltas["{}idle".format(cpu)]
            active_delta = total_delta - idle_delta
            utilization = active_delta.div(total_delta).fillna(0) * 100

            if cpu:
                col_name = "{}util".format(cpu)
            else:
                col_name = "cpu_util"
            # Add to results (skip first row due to diff())
            results[col_name] = utilization.iloc[1:].reset_index(drop=True)
        out_df = pd.DataFrame(results)

        self.util_file = os.path.join(context.output_directory, "proc-stat.csv")
        out_df.to_csv(self.util_file, index=False)
        context.add_artifact("proc-stat", self.util_file, kind="data")

    def finalize(self, context):  # pylint: disable=unused-argument
        self.target.remove(self.target_log_path)
        self.target.remove(self.target_output)

        if self.cleanup_assets:
            self.target.remove(self.target_poller)
