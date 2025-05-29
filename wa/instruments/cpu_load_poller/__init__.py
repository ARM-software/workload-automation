#    Copyright 2025 ARM Limited
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
# pylint: disable=access-member-before-definition,attribute-defined-outside-init,unused-argument
import os

import pandas as pd

from wa import Instrument, Parameter, Executable
from wa.framework import signal
from wa.framework.exception import InstrumentError
from wa.utils.trace_cmd import TraceCmdParser


class CpuLoadPoller(Instrument):
    name = "cpu_load_poller"
    description = """
    Polls /proc/stat at a set sample interval to calculate per-core CPU load.
    The values are output in CSV format.

    This instrument places a file called cpu_load.csv in each iteration's result directory.
    This file will contain a timestamp column (in seconds since boot) and CPU load
    percentage columns for each core (cpu0_load, cpu1_load, etc.).

    The CPU load represents the percentage of time each core spent doing work
    (non-idle) during the sampling interval.
    """

    parameters = [
        Parameter(
            "sample_interval",
            kind=int,
            default=1000,
            description="""The interval between samples in mS.""",
        ),
        Parameter(
            "align_with_ftrace",
            kind=bool,
            default=False,
            description="""
                  Insert a marker into ftrace that aligns with the first
                  timestamp. During output processing, extract the marker
                  and use its timestamp to adjust the timestamps in the collected
                  csv so that they align with ftrace.
                  """,
        ),
    ]

    def initialize(self, context):
        host_poller = context.get_resource(
            Executable(self, self.target.abi, "cpu_load_poller")
        )
        target_poller = self.target.install(host_poller)

        self.target_output_path = self.target.path.join(
            self.target.working_directory, "cpu_load.csv"
        )
        self.target_log_path = self.target.path.join(
            self.target.working_directory, "cpu_load_poller.log"
        )

        marker_option = ""
        if self.align_with_ftrace:
            marker_option = "-m"
            signal.connect(self._adjust_timestamps, signal.AFTER_JOB_OUTPUT_PROCESSED)

        self.command = "{} {} -t {} > {} 2>{}".format(
            target_poller,
            marker_option,
            self.sample_interval * 1000,
            self.target_output_path,
            self.target_log_path,
        )

    def start(self, context):
        self.target.kick_off(self.command)

    def stop(self, context):
        self.target.killall("cpu_load_poller", signal="TERM")

    def update_output(self, context):
        host_output_file = os.path.join(context.output_directory, "cpu_load.csv")
        self.target.pull(self.target_output_path, host_output_file)
        context.add_artifact("cpu-load-output", host_output_file, kind="data")

        host_log_file = os.path.join(context.output_directory, "cpu_load_poller.log")
        self.target.pull(self.target_log_path, host_log_file)
        context.add_artifact("cpu-load-poller-log", host_log_file, kind="log")

        with open(host_log_file) as fh:
            for line in fh:
                if "ERROR" in line:
                    raise InstrumentError(line.strip())
                if "WARNING" in line:
                    self.logger.warning(line.strip())
                if "Detected" in line:
                    self.logger.info(line.strip())

    def teardown(self, context):
        self.target.remove(self.target_output_path)
        self.target.remove(self.target_log_path)

    def _adjust_timestamps(self, context):
        output_file = context.get_artifact_path("cpu-load-output")
        message = 'Adjusting timestamps inside "{}" to align with ftrace'
        self.logger.debug(message.format(output_file))

        trace_txt = context.get_artifact_path("trace-cmd-txt")
        trace_parser = TraceCmdParser(filter_markers=False)
        marker_timestamp = None
        for event in trace_parser.parse(trace_txt):
            if event.name == "print" and "CPU_POLLER_START" in event.text:
                marker_timestamp = event.timestamp
                break

        if marker_timestamp is None:
            raise InstrumentError("Did not see CPU poller marker in ftrace")

        df = pd.read_csv(output_file)
        df.time -= df.time[0]
        df.time += marker_timestamp
        df.to_csv(output_file, index=False)
