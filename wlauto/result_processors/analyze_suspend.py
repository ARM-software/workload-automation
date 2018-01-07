#    Copyright 2013-2015 ARM Limited
#
#    Author: arnoldlu@qq.com
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


# pylint: disable=R0201
import os
import time
import csv
import logging
from wlauto import ResultProcessor
import sleepgraph as sglib
import traceback

logger = logging.getLogger('SuspendResult')

class AnalyzeSuspend(ResultProcessor):
    name = 'analyze_suspend'
    description = '''
    Use sleepgraph.py to analyze the suspend/resume.
    Output an html file.
    '''

    def process_run_result(self, result, context):
        html_name = 'output.html'
        suspend_data = [['Test ID', 'suspend(ms)', 'resume(ms)', 'total(ms)']]

        '''
        Iterate all output folder, using sleepgraph.py to generate output.html.
        '''
        for result in result.iteration_results:
            workload_id_interation = result.workload.name + '_' + str(result.id) + '_' + str(result.iteration)
            result_folder = os.path.join(context.run_output_directory, workload_id_interation+'/')
            ftrace_file = os.path.join(result_folder, 'ftrace.txt')
            dmesg_file = os.path.join(result_folder, 'dmesg.txt')

            sglib.sysvals.notestrun = True
            #sglib. sysvals.verbose = True
            sglib.sysvals.ftracelog = True
            sglib.sysvals.ftracefile = ftrace_file
            sglib.sysvals.dmesgfile = dmesg_file
            sglib.sysvals.dmesglog = True
            #sglib.sysvals.result = 'summary.txt'
            try:
                stamp = sglib.rerunTest()
                sglib.sysvals.outputResult(stamp)
            except:
                logger.error('Processing {} failed!'.format(result_folder))
                traceback.print_exc()
            else:
                '''
                Process output.html to get suspend/resume duration.
                '''
                html_file = open(html_name, 'r').read(10000)
                suspend = sglib.find_in_html(html_file, ['Kernel Suspend: ', 'Kernel Suspend Time: '])
                resume = sglib.find_in_html(html_file, ['Kernel Resume: ', 'Kernel Resume Time: '])
                suspend_data.append([workload_id_interation, suspend, resume, float(suspend)+float(resume)])

                os.system('mv {} {}'.format(html_name, result_folder))
                logger.debug('Processing {} sucessfully!'.format(result_folder))

        '''
        Save test data to summary.csv for an overview.
        '''
        summary_csv = open('{}/summary.csv'.format(context.run_output_directory), 'wb')
        summary_writer = csv.writer(summary_csv)
        for data in suspend_data:
            summary_writer.writerow([data[0], data[1], data[2], data[3]])
        summary_csv.close()
