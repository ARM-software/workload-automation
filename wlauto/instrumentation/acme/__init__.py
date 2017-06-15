import json
import os
import psutil
from subprocess import Popen, PIPE, STDOUT
import shutil
from time import sleep

from wlauto import Instrument, Parameter
from wlauto.exceptions import HostError
from wlauto.utils.types import list_of_strs
from wlauto.utils.misc import which

class ACME(Instrument):
    name = 'acme'

    parameters = [
        Parameter('host', kind=str, default='baylibre-acme.local',
                  description="""Hostname or IP address of ACME board"""),
        Parameter('iio_channels', kind=list_of_strs, default=['iio:device0'],
                  description="""IIO channels to collect from"""),
    ]

    def validate(self):
        self._iiocapturebin = which('iio-capture')
        if not self._iiocapturebin:
            raise Hosterror('No iio-capture in $PATH')

    def start(self, context):
        """
        Reset energy meter and start sampling from channels specified in the
        target configuration.
        """
        self._res_dir = os.path.join(context.output_directory, 'acme')
        os.makedirs(self._res_dir)

        self._processes = {}

        # Start iio-capture for all channels required
        for channel in self.iio_channels:
            # Setup CSV file to collect samples for this channel
            csv_file = '{}/{}'.format(
                self._res_dir,
                'samples_{}.csv'.format(channel)
            )

            # Start a dedicated iio-capture instance for this channel
            self._processes[channel] = Popen(
                [self._iiocapturebin, '-n', self.acme_host, '-o', '-c',
                 '-f', csv_file, channel],
                stdout=PIPE, stderr=STDOUT)

        # Wait few milliseconds before to check if there is any output
        sleep(1)

        # Check that all required channels have been started
        for channel in self.iio_channels:
            self._processes[channel].poll()
            if self._processes[channel].returncode:
                self.logger.error('Failed to run %s for %s',
                                 self._iiocapturebin, channel)
                self.logger.warning('\n\n'\
                    '  Make sure there are no iio-capture processes\n'\
                    '  connected to %s and device %s\n',
                    self.acme_host)
                out, _ = self._processes[channel].communicate()
                self.logger.error('Output: [%s]', out.strip())
                self._processes[channel] = None
                raise RuntimeError('iio-capture connection error')

    def stop(self, context):
        for channel in self.iio_channels:
            self._processes[channel].poll()
            if self._processes[channel].returncode:
                # returncode not None means that iio-capture has terminated
                # already, so there must have been an error
                self.logger.error('%s terminated for %s',
                                  self._iiocapturebin, channel)
                out, _ = self._processes[channel].communicate()
                self.logger.error('[%s]', out)
                continue

            # kill process - will get the output in update_result.
            self._processes[channel].terminate()

    def update_result(self, context):
        channels_nrg = {}
        channels_stats = {}

        for channel in self.iio_channels:
            out, _ = self._processes[channel].communicate()
            self._processes[channel].wait()

            self.logger.debug('Completed IIOCapture for %s...',
                            channel)

            # iio-capture return "energy=value", add a simple format check
            if '=' not in out:
                self.logger.error('Bad output format for %s:', channel)
                self.logger.error('[%s]', out)
                continue

            # Build energy counter object
            nrg = {}
            for kv_pair in out.split():
                key, val = kv_pair.partition('=')[::2]
                nrg[key] = float(val)
            channels_stats[channel] = nrg

            self.logger.debug(channel)
            self.logger.debug(nrg)

            # Add channel's energy to return results
            channels_nrg['{}'.format(channel)] = nrg['energy']

        # Dump energy data
        with open(os.path.join(self._res_dir, 'energy.json'), 'w') as f:
            json.dump(channels_nrg, f, sort_keys=True, indent=4)

        # Dump energy stats
        with open(os.path.join(self._res_dir, 'energy_stats.json'), 'w') as f:
            json.dump(channels_stats, f, sort_keys=True, indent=4)
