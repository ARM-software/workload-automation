#pylint: disable=attribute-defined-outside-init
from __future__ import division
import csv
import os
import signal
import time
from fcntl import fcntl, F_GETFL, F_SETFL
from string import Template
from subprocess import Popen, PIPE, STDOUT

from wlauto import Instrument, Parameter
from wlauto.exceptions import HostError
from wlauto.utils.misc import which


IIOCAP_CMD_TEMPLATE = Template("""
${iio_capture} -n ${host} -b ${buffer_size} -c -f ${outfile} ${iio_device}
""")


def _read_nonblock(pipe, size=1024):
    fd = pipe.fileno()
    flags = fcntl(fd, F_GETFL)
    flags |= os.O_NONBLOCK
    fcntl(fd, F_SETFL, flags)

    output = ''
    try:
        while True:
            output += pipe.read(size)
    except IOError:
        pass
    return output


class AcmeCapeInstrument(Instrument):

    name = 'acmecape'
    description = """
    Instrumetnation for the BayLibre ACME cape for power/energy measurment.
    """

    parameters = [
        Parameter('iio-capture', default=which('iio-capture'),
                  description="""
                  Path to the iio-capture binary will be taken from the
                  environment, if not specfied.
                  """),
        Parameter('host', default='baylibre-acme.local',
                  description="""
                  Host name (or IP address) of the ACME cape board.
                  """),
        Parameter('iio-device', default='iio:device0',
                  description="""
                  """),
        Parameter('buffer-size', kind=int, default=256,
                  description="""
                  Size of the capture buffer (in KB).
                  """),
    ]

    def initialize(self, context):
        if self.iio_capture is None:
            raise HostError('Missing iio-capture binary')
        self.command = None
        self.subprocess = None

    def setup(self, context):
        self.outfile = os.path.join(context.output_directory, 'acme-capture.csv')
        params = dict(
            iio_capture=self.iio_capture,
            host=self.host,
            buffer_size=self.buffer_size,
            iio_device=self.iio_device,
            outfile=self.outfile,
        )
        self.command = IIOCAP_CMD_TEMPLATE.substitute(**params)
        self.logger.debug('ACME cape command: {}'.format(self.command))

    def very_fast_start(self, context):  # pylint: disable=unused-argument
        self.subprocess = Popen(self.command.split(), stdout=PIPE, stderr=STDOUT)

    def very_fast_stop(self, context):  # pylint: disable=unused-argument
        self.subprocess.terminate()

    def update_result(self, context):
        timeout_secs = 10
        for _ in xrange(timeout_secs):
            if self.subprocess.poll() is not None:
                break
            time.sleep(1)
        else:
            output = _read_nonblock(self.subprocess.stdout)
            self.subprocess.kill()
            self.logger.error('iio-capture did not terminate gracefully')
            if self.subprocess.poll() is None:
                msg = 'Could not terminate iio-capture:\n{}'
                raise HostError(msg.format(output))
        if not os.path.isfile(self.outfile):
            raise HostError('Output CSV not generated.')

        context.add_iteration_artifact('iio-capture', self.outfile, 'data')
        if os.stat(self.outfile).st_size == 0:
            self.logger.warning('"{}" appears to be empty'.format(self.outfile))
            return
        self._compute_stats(context)

    def _compute_stats(self, context):
        with open(self.outfile, 'rb') as fh:
            reader = csv.reader(fh, skipinitialspace=True)
            header = reader.next()
            power_index = header.index('power mW')
            ts_index = header.index('timestamp ms')

            last_ts = 0.0
            energy_uj = 0
            ave_power_mw = 0.0

            for i, row in enumerate(reader):
                row_power_mw = float(row[power_index])
                row_ts = float(row[ts_index])

                if i == 0:
                    ave_power_mw = row_power_mw
                else:
                    ave_power_mw = ave_power_mw + (row_power_mw - ave_power_mw) / i
                    energy_uj += row_power_mw * (row_ts - last_ts)
                last_ts = row_ts

            context.add_metric('power', ave_power_mw, 'milliwatts')
            context.add_metric('energy', energy_uj / 1000000, 'joules')
