#    Copyright 2013-2015 ARM Limited
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

import sys
import argparse
import os
import csv
import re
import collections

from wlauto import ResultProcessor, settings, instrumentation,Parameter
from wlauto.exceptions import ConfigError, ResultProcessorError


####################
class PowerTrace:
    """
    Base class representing a scheduler trace line
    """
    def __init__(self, _cpu,_time):
        """
        Constructor
        """
        self.cpu = int(_cpu)
        self.timestamp = _time

class IdleStartTrace(PowerTrace):
    """
    Class representing a sched_wakeup power trace format using power_start event
    """
    rgx = re.compile('\s*power_start:\s+type=(\d+)\sstate=(\d+)\scpu_id=(\d+)')
    
    def __init__(self, _match,_time,_cpu=None,_state=None,common=False):
        """
        Constructorx
        """
        # parse _comment string for taskname, pid and priority
        if _match:
            self.state = int(_match.group(2))
            _cpu = int(_match.group(3))
        else:
            self.state = _state
            
        PowerTrace.__init__(self,_cpu,_time)
        self.common = common
        self.sleeptime = sys.maxint
        self.temp = 0

    def __repr__(self):
        return self.__str__()
        
    def __str__(self):
        return '>IS C{0} T{1} S{2} CM{3}:\n'.format(
          self.cpu,  self.timestamp,  self.state, self.common)

class IdleStartTraceCpuIdle(IdleStartTrace):
    """
    Class reprenting start of a cpu idle using the cpu_idle trace format, which replaces the power_start format. Basically just builds an object the IdleStartTrace format
    """
    rgx = re.compile('\s*cpu_idle:\s+state=(\d+)\scpu_id=(\d+)')
    
    def __init__(self, _match,_time):
        """
        Constructorx
        """
        # parse _comment string for taskname, pid and priority
        state = int(_match.group(1))
        assert(state!=-1 and state!=4294967295), "matched an idle end trace"
        _cpu = int(_match.group(2))
        IdleStartTrace.__init__(self,None,_time,_cpu,state)

    def __repr__(self):
        return self.__str__()
        
    def __str__(self):
        return IdleStartTrace.__str__(self)


class IdleEndTrace(PowerTrace):
    """
    Class representing end of idle period using power_end format
    """
    rgx = re.compile('\s*power_end:\s+cpu_id=(\d+)')
    
    def __init__(self, _match,_time,_cpu=None):
        """
        Constructor
        """
        # parse _comment string for taskname, pid and priority
        if _match:
            _cpu = int(_match.group(1))
        PowerTrace.__init__(self,_cpu,_time)
        # probably should do this as base class but being lazy
        self.sleeptime = sys.maxint
        self.wakefromcommon = -1
    def __repr__(self):
        return self.__str__()
        
    def __str__(self):
        return '<IE C{0} T{1}: \n'.format(self.cpu,  self.timestamp)

class IdleEndTraceCpuIdle(IdleEndTrace):
    """
    Class representing end of idle period using cpu_idle format, construct a IdleEndTrace object, must be placed in list of objects before IdleStartTraceCpuIdle

    """
    rgx = re.compile('\s*cpu_idle:\s+state=4294967295\s+cpu_id=(\d+)')
    
    def __init__(self, _match,_time,_cpu=None):
        """
        Constructor
        """
        # parse _comment string for taskname, pid and priority
        IdleEndTrace.__init__(self,_match,_time,_cpu) # __match format is the same

    def __repr__(self):
        return self.__str__()
        
    def __str__(self):
        return '<IE C{0} T{1}: \n'.format(self.cpu,  self.timestamp)


class FreqTrace(PowerTrace):
    """
    Class representing a freq trace in power_frequency format
    """
    rgx = re.compile('\s*power_frequency:\s+type=(\d+)\s+state=(\d+)\s+cpu_id=(\d+)')
    
    def __init__(self, _match,_time, _cpu=None,_freq=None):
        """
        Constructor
        """
        # parse _comment string for taskname, pid and priority
        if _match:
            self.freq = int(_match.group(2))
            _cpu = int(_match.group(3))
        else:
            self.freq = _freq
        PowerTrace.__init__(self,_cpu,_time)

    def __repr__(self):
        return self.__str__()
        
    def __str__(self):
        return 'F C{0} T{1} S{2}: \n'.format(self.cpu,  self.timestamp,  self.freq)

class FreqTraceCpu(FreqTrace):
    """
    Class representing a freq trace in cpu_frequency format
    """
    rgx = re.compile('\s*cpu_frequency:\s+state=(\d+)\s+cpu_id=(\d+)')
    
    def __init__(self, _match,_time):
        """
        Constructor
        """
        # parse _comment string for taskname, pid and priority
        _freq = int(_match.group(1))
        _cpu = int(_match.group(2))
        FreqTrace.__init__(self,None,_time,_cpu,_freq)

    def __repr__(self):
        return self.__str__()
        
    def __str__(self):
        return 'F C{0} T{1} S{2}: \n'.format(self.cpu,  self.timestamp,  self.freq)

def cpu_filter(cpul):
    return lambda obj: obj.cpu in cpul

def types_filter(typel):
    return lambda obj: any([isinstance(obj,  t) for t in typel])
    

class CpuStateProc:
    def __init__(self):
        self.device = None
        self.infile = None
        self.tracefile = None
        self.outfilep = None   # parallel csv
        self.outfilecs = None   # will add load profile here in future
        self.cpuset = collections.defaultdict(lambda: collections.defaultdict(int))
        self.idleentries = collections.defaultdict(int)
        self.freqentries = collections.defaultdict(int)
        self.trace_dictionary = collections.defaultdict(list)
        self.trace = list()
        self.absentstate = 2  
        self.clusterstate = 2
        self.realfirsttime = -1
        self.droppedtraces = False
        self.initfreq = list()
        

    def initialize(self, context, logger, absentstate=2, clusterstate=2, initfreq=list(), tracefile='trace.txt'):  # pylint: disable=R0912
        self.device = context.device
        self.clusterlist = self.getclusterlist()
        self.logger = logger
        # Things to be defined as parameters

        if len(initfreq)==0:
            self.initfreq = [-1 for i in  self.clusterlist]
        else:
            self.initfreq = initfreq

        self.absentstate = absentstate    
        self.clusterstate = clusterstate
        if not self.device.core_names:
            message = 'Device does not specify its core types (core_names/core_clusters not set in device_config).'
            raise ResultProcessorError(message)
        number_of_clusters = max(self.device.core_clusters) + 1
        
        self.tracefile = tracefile
        # separate out the cores in each cluster
        # It is list of list of cores in cluster
        # print self.absentstate
        # print self.clusterstate
        # print self.initfreq
        # print self.infile
        # print self.outfilep
        # print self.outfilecs
        # print self.clusterlist
        # print self.device.core_names
        # print self.device.core_clusters


    def plotcores(self,trace,plotcores,name):
        import matplotlib.pyplot as py
        import matplotlib.cm as cmx
        fig= py.figure()
        i = 0
        pltrace = filter( cpu_filter(plotcores), trace )
        for c in plotcores:
            ctrace = filter( cpu_filter([c]), pltrace )
            pl = list()
            laststate = -1
            lasttime = 0
            for t in ctrace:
                if isinstance(t,IdleEndTrace) and laststate!=-1:
                    if laststate == 0: laststate = 0.5 # make WFI show up 
                    tt  = (lasttime,t.timestamp-lasttime,laststate)
                    pl.append(tt)
                    laststate = -1
                    lasttime = 0
                elif isinstance(t,IdleStartTrace):
                    lasttime = t.timestamp
                    laststate = t.state
            i+=1
            ax = fig.add_subplot(len(plotcores),1,i)
            ax.set_xlim(self.firsttime,  self.lasttime)
            ax.set_ylabel("CPU "+str(c))
            for item in pl:
                col = cmx.jet(float(item[2])/5)
                xx = [item[0],item[1]]
                yy = [0,item[2]]
                if xx[1]:
                    ax.broken_barh( [xx], yy,alpha=0.8,color=col)
        fig.savefig(name)      


    def debugdmp(self,trace,fname):
        # env variable PDEBUG needs to be set to get this stuff
        dbgpath = os.environ.get('CPUPROCDEBUG')
        plcores = os.environ.get('PLOTCORES')
        if plcores:
            plotcores = [int(s) for s in plcores.split(",")]
        
        if (dbgpath):
            if plcores and len(plotcores):
                self.plotcores(trace,plotcores,os.path.join(dbgpath,fname+".png"))
            f = open(os.path.join(dbgpath,fname+".txt"), 'w')
            for t in trace: f.write(str(t))
            f.close()
        return

    def getclusterix(self,core):
        for clix in range(len(self.clusterlist)):
            for cpix in range(len(self.clusterlist[clix])):
                if core == self.clusterlist[clix][cpix]:
                    return (clix,cpix)

        
    def getclusterlist(self):
        clusterlist = list()
        for i in range(max(self.device.core_clusters)+1):
            cpusincl = list()
            for ix in range(len(self.device.core_clusters)):
                if self.device.core_clusters[ix]==i:
                    cpusincl.append(ix)
            clusterlist.append(cpusincl)
        return clusterlist     

    def pass_final_do_self_trace(self,maxcpu,trace):
        # fix frequency traces, so if any given CPU changes frequency
        # add a trace token for every CPU with the same stamp
        # for the set of cpus that use the same frequency
        # only use if absbreakmp 
        # cpus 0 - absbreakmp-1 have one frequency
        # cpus absbreakmp to max have another
        # ie 4x4 bL could be [[0,1,2,3],[4,5,6,7]]
        # in addition if the change of frequency would cause a cluster change in IKS
        # add a core was idling, add idle traces before and after the frequency
        # for all idling cores
        self.trace = list()
        laststate = [-1 for i in range(0,maxcpu+1)]
        for item in trace:
            self.trace.append(item)
            if isinstance(item,FreqTrace):
                (clix,cpix) = self.getclusterix(item.cpu)
                for c in self.clusterlist[clix]:
                    if c!=item.cpu:
                        newitem = FreqTrace(None,item.timestamp,c,item.freq)
                        self.trace.append(newitem)
        return    
    
    def pass3_common_cluster_states(self,maxcpu,trace):
        '''
        Makes it so that all common states (states >= cluster state) are only marked as common
        when all cpus are in the same state. So for two cpus in cluster, if cluster state is 2
        the sequence like this:
        Time 10: CPU1 goes into state 2
        Time 15: CPU2 goes into state 2
        Time 20: CPU1 wakes up
        is converted to:
        Time 10: CPU1 goes into state 1
        Time 15: CPU2 goes into state 2
        Time 15: CPU1 wakes
        Time 15: CPU1 goes into state 2
        Time 20: CPU1 wakes up
        Time 20: CPU2 wakes up
        Time 20: CPU2 goes into state 1
        the noncommonstate is assumed to be self.clusterstate - 1
        '''
        
        newtrace = list()
        # FIXME support different entry times per cpu type
        laststate = list()
        for l in self.clusterlist:
            laststate.append([-1 for _ in l])
        lastcpu = list()
        newtrace = list()
        cnt = -1
        noncommonstate = self.clusterstate - 1
        for item in trace:
            cnt+=1
            (clix,cpix) = self.getclusterix(item.cpu)
            if isinstance(item,IdleStartTrace) and item.state >= self.clusterstate:
                assert(laststate[clix][cpix]==-1)
                laststate[clix][cpix]=item
                numcpus = sum([s != -1 for s in laststate[clix]])
                if numcpus != len(laststate[clix]): 
                    newtrace.append(item)
                else:
                    # we are entering a real cluster down state
                    # whens the next wakeup?
                    nextwake = -1
                    for k in range(cnt,len(trace)):
                        nextwake = trace[k]
                        if isinstance(nextwake,IdleEndTrace) and nextwake.cpu in self.clusterlist[clix]:
                            break
                    if nextwake == -1:
                        nextwake = IdleEndTrace(None,self.lasttime,item.cpu)
                    #delta = nextwake.timestamp-item.timestamp
                    item.common=True        
                    # for every other core that is in cluster state, mutate that to a noncommonstate
                    # for the portion that is not over
                    targetclusterstate = self.clusterstate
                    nextwake.wakefromcommon = targetclusterstate
                    for oc in laststate[clix]:
                        if oc!=item:
                            # In Ares this will create state 1 (cpu gated) regions for all cores but the last one 
                            # until the entry of the cluster gated state, which will have all cores entering
                            # simulatneously
                            oc.state=noncommonstate
                            newtrace.append(IdleEndTrace(None,item.timestamp,oc.cpu))
                            newtrace.append(IdleStartTrace(None,item.timestamp,oc.cpu,targetclusterstate,True))
                    newtrace.append(item)

            elif isinstance(item,IdleEndTrace):
                laststate[clix][cpix] = -1
                newtrace.append(item)
                if item.wakefromcommon!=-1:
                    # when the first core wakes up from an idle period, there may others that are still reporting
                    # to be in cluster state, because they wake up later. For all of those cores
                    # we insert a wake up from the state, and then reinsert another trace element at noncommonstate
                    # Then update laststate so that those cores are still considered to be requesting self.clusterstate
                    # since the time of the wakeup
                    for c in self.clusterlist[clix]:
                        if c!=item.cpu:
                            (wclix,wcpix) = self.getclusterix(c)
                            newtrace.append(IdleEndTrace(None,item.timestamp,c))
                            newtrace.append(IdleStartTrace(None,item.timestamp,c,noncommonstate,True)) 
                            # using item.wakefromcommon state like this will be if we introduce several levels of cluster depth (but not in Ares and TC2)
                            laststate[wclix][wcpix]=IdleStartTrace(None,item.timestamp,c,item.wakefromcommon) 
                            
            else:
                newtrace.append(item)

#         # take out non-common entries and change state into non-common state
        for item in newtrace:
            if isinstance(item,IdleStartTrace) and item.state >= self.clusterstate and not item.common:
                    item.state = noncommonstate

        return newtrace

    def pass2_initfreqs_notrace_cpus(self,maxcpu,trace):
        # print warning if you we didn't see traces from a cpu when maxcpu is passed
        # also add init freqs
        #import pdb ; pdb.set_trace()
        for c in range(maxcpu+1):
            tracesforc = sum([self.cpuset[c][t] for t in self.cpuset[c].keys()])
            if tracesforc==0: # no traces for c at all
                self.logger.warning('No traces observed for CPU %d' % (c))
                # if this is the case, add a trace begining and end of idle start and stop
                trace.insert(0,IdleStartTrace(None,self.firsttime,c,absentstate))
                trace.append(IdleEndTrace(None,self.lasttime,c))
        for clix in range(len(self.clusterlist)):
            c = self.clusterlist[clix][0]
            newitemf = FreqTrace(None,self.firsttime,c,self.initfreq[clix])  # this is broadcast to other CPU below
            trace.insert(0,newitemf)
                
        
    def pass1_start_end_idle(self,maxcpu,trace):
        # fix traces for each CPU so that idle is accounted for correctly
        # if first idle trace is a trace end or if last idle trace is an idle start
        #        import pdb ; pdb.set_trace()
        for k in range(maxcpu+1):
        # fix the trace so we have an idle state 0 at beginning if core
        # was already idle at start of trace, or if the trace finishes with
        # an unmatched idle start
            for item  in trace: 
                if item.cpu == k:
                    if isinstance(item,IdleStartTrace):
                        break # first found was idle start
                    if isinstance(item,IdleEndTrace):
                        newitem = IdleStartTrace(None,self.firsttime,k,self.absentstate)
                        trace.insert(0,newitem)
                        break
        
            i = len(trace)-1
            while (i>=0):
                item = trace[i]
                if item.cpu == k:
                    if isinstance(item,IdleEndTrace):
                        # put an idle start trace at the end all parsing functions assume a cores ends with idle traces
                        # are present at end of trace
                        newitem = IdleStartTrace(None,self.lasttime,k,0)
                        trace.append(newitem)
                        break
                    if isinstance(item,IdleStartTrace):
                        newitem = IdleEndTrace(None,self.lasttime,k)
                        trace.append(newitem)
                        break
                i-=1
        return        

    def addifnonzero(self,l,tt):
        if tt[1]!=0: l.append(tt)
        return
    
    def addifnonzerof(self,d,f,tt):
        if tt[1]!=0: d[f].append(tt)
        return

    def parserunning(self):
        """
        creates square waves per CPU per states along the lines of
        {cpuidex={freq=[(time of entry, time spent)(time of entry, time spent) ....]}
        where special freq -1 is for unknown time until first frequency trace
        """
        self.running = collections.defaultdict(lambda: collections.defaultdict(list))
        
        newfreq = -1
        
        for k,ttraces in self.trace_dictionary.items():
            lastentrytime = self.firsttime
            lastfreq = self.initfreqs[k]
            running = True
            
            for item in ttraces:
                if isinstance(item,IdleStartTrace):
                    assert(running)
                    running = False
                    a = (lastentrytime,item.timestamp-lastentrytime)
                    self.addifnonzerof(self.running[k],lastfreq,a)
              
                if isinstance(item,IdleEndTrace):
                    assert(not running)
                    running = True
                    lastentrytime = item.timestamp
                    if newfreq!=-1:
                        lastfreq = newfreq
                        newfreq = -1
 
                if isinstance(item,FreqTrace):
                    self.freqentries[item.freq]+=1
                    if running:
                        a = (lastentrytime,item.timestamp-lastentrytime)
                        self.addifnonzerof(self.running[k],lastfreq,a)
                        lastentrytime = item.timestamp
                        lastfreq = item.freq
                    else:
                        newfreq = item.freq # sometimes we get a new freq trace when still idle
            if running:
                a = (lastentrytime,self.lasttime-lastentrytime)
                self.addifnonzerof(self.running[k],lastfreq,a)
        return


    def parseidlestates(self):
        """
        populates self.idlestates square waves per CPU per states along the lines of
        {cpuidex={state=[(time of entry, time spent,freq)(time of entry, time spent,freq) ....]}
        where special state -2 has all traces of idleness for a given core
        if a CPU trace starts with a power_end
        """
        self.idlestates = collections.defaultdict(lambda: collections.defaultdict(list))
        
        for k in self.trace_dictionary.keys():
            trace = self.trace_dictionary[k]
            laststateitem = -0xd1e
            lastfreq  = self.initfreqs[k]
            for item in trace:
                if isinstance(item,IdleStartTrace):
                    self.idleentries[item.state]+=1
                    assert(laststateitem == -0xd1e),"last item %r item %r" % (laststateitem,item)
                    laststateitem = item

                if isinstance(item,IdleEndTrace):
                    assert(laststateitem != -0xd1e), "last item %r item %r" % (laststateitem,item)
                    delta = item.timestamp-laststateitem.timestamp
                    a = (laststateitem.timestamp,delta,lastfreq)
                    self.addifnonzero(self.idlestates[k][laststateitem.state],a)
                    laststateitem = -0xd1e

                if isinstance(item,FreqTrace):
                  lastfreq = item.freq
        return
    
                
    def idle_parse_common(self,cpulist,state=[]):
        """
        assumes index is linear, ie cpus between mix and max
        returns a square wave for states where 0,1, up to N cpus are runing
        at the same time
        ret = {nactivecpus:[(t,delta),....],nactivecpus:[....]}
        where ncpu is the number of active CPUs in the sample
        if state != [] only include records where the requested idle state == state
        in other words if state is not in list supplied then cpu is considered 
        as running
        """
        ret = collections.defaultdict(list)   

        # traces are fixed so all cores start active
        laststate = [-0xd1e for i in cpulist]
        
        tracelist = list()

        lastentrytime = self.firsttime


        for item in self.trace:
            if item.cpu not in cpulist:
                continue
            idx = cpulist.index(item.cpu)
        

            if isinstance(item,IdleStartTrace) and (state==[] or item.state in state):
                assert(laststate[idx] == -0xd1e)
                # cpu idx is going idle
                nactivecpus = sum([s == -0xd1e for s in laststate])
                delta = item.timestamp-lastentrytime
                if delta > 0: ret[nactivecpus].append((lastentrytime,delta))
                laststate[idx] = item.state
                lastentrytime = item.timestamp
                
            if isinstance(item,IdleEndTrace) and (state==[] or laststate[idx] in state):
                assert(laststate[idx] != -0xd1e)
                nactivecpus = sum([s == -0xd1e for s in laststate])
                # cpu idx is waking
                delta = item.timestamp-lastentrytime
                if delta > 0: ret[nactivecpus].append((lastentrytime,delta))
                lastentrytime = item.timestamp                                      
                laststate[idx] = -0xd1e
            
        return ret


    def parseline(self,  _line):
        mm = CpuState.rgx.match(_line)
        if mm:
          timestamp = int(mm.group(1))*1000000+int(mm.group(2))
          self.lasttime = timestamp
          if self.firsttime < 0 : self.firsttime = self.lasttime
          for c in CpuState.classes:
            m = c.rgx.match(mm.group(3))
            if (m): 
              return c(m,timestamp)
        return None


    def trace_first_pass(self,fh):
        ''' do a first pass and check for TRACE_MARKER and 
           dropped traces '''
        self.realfirsttime = -1
        self.droppedtraces = False
        lastgoodpos = fh.tell()
        for line in fh:
            mm = CpuState.rgx.match(line)
            if mm:
                timestamp = int(mm.group(1))*1000000+int(mm.group(2))
                if self.realfirsttime < 0 : self.realfirsttime = timestamp
            if 'EVENTS DROPPED'  in line:
                self.logger.warning('There are dropped events we will skip traces')
                self.droppedtraces = True
                lastgoodpos = lastpos
            if 'TRACE_MARKER_START'  in line:
                lastgoodpos = lastpos
            lastpos = fh.tell()
        fh.seek(lastgoodpos)
    
    def parse(self,context):
        """
        """
        self.infile = os.path.join(context.output_directory, self.tracefile)
        self.outfilep = os.path.join(context.output_directory, 'parallel.csv')
        self.outfilecs = os.path.join(context.output_directory, 'corestates.csv')

        fh=open(self.infile,  'r')
      
        trace = list()
        maxcpu = len(self.device.core_names)-1
        linenum=0
        self.trace_first_pass(fh)
        line = fh.readline()
        self.firsttime = -1
        self.initfreqs = [-1 for i in range(maxcpu+1)]
        self.trace = list()
        firstcpu=[0]
        lastcpu = list()
        freqstraces = list()
        lastfreqchange = list()
        # must strip header lines out of file
        item = self.parseline(line)
        self.firsttime = -1
        self.initfreqs = [-1 for i in range(maxcpu+1)]
        
        firstcpu=[0]
        lastcpu = list()
        freqstraces = list()
        lastfreqchange = list()
        while line:
            linenum += 1
            if 'TRACE_MARKER_STOP' in line:
                break;

            item = self.parseline(line)
            if (item): 
                trace.append(item)
                ix = 0
                if isinstance(item,IdleEndTrace): ix=1
                if isinstance(item,FreqTrace): ix=2
                self.cpuset[item.cpu][ix]+=1
                
            line = fh.readline()

        fh.close()        
        self.debugdmp(trace,"0_raw_trace")
        self.pass1_start_end_idle(maxcpu,trace)
        self.debugdmp(trace,"1_fixup_start_end_idles")
        self.pass2_initfreqs_notrace_cpus(maxcpu,trace)
        self.debugdmp(trace,"2_pass2_initfreqs_notrace_cpus")
        trace = self.pass3_common_cluster_states(maxcpu,trace)
        self.debugdmp(trace,"3_fixup_cluster_commons")
        self.pass_final_do_self_trace(maxcpu,trace)     
        self.debugdmp(self.trace,"4_final")

        for c in range(maxcpu+1):
            for item in self.trace:
                if item.cpu==c: 
                    self.trace_dictionary[c].append(item)

        self.parseidlestates()
        self.parserunning()
        return


    def parallel_report(self,clix,fh):
        maxcpu = len(self.device.core_names)-1
        corelist = range(maxcpu+1)
        cl = 'all'
        if (clix < len(self.clusterlist)):
            corelist = self.clusterlist[clix]
            cl = str(clix)
            
        ret = self.idle_parse_common(corelist)

        totaltime = self.lasttime-self.firsttime
        s =  "report for cluster:,"+cl+", cores:,"
        for c in corelist: s+=str(c)+' '
        s+=','
        fh.write("%s\n" % (s))
        fh.write("numcores,totaltime,%time,%running time\n")
        totalrunningtime = 0
        for n in range(len(corelist)+1):
            tt = sum([s[1] for s in ret[n]])
            if n==0:
                totalrunningtime=totaltime-tt
                fh.write("%d,%d,%f,%f\n" % (n,tt,float(tt)*100.0/totaltime,0.0))
            else:
                fh.write("%d,%d,%f,%f\n" % (n,tt,float(tt)*100.0/totaltime,
                                            float(tt)*100.0/totalrunningtime))

            
    def cpu_state_report(self,c,fh):
        ss = self.device.core_names[c]+'_'+str(c)+','
        sss = ss+'State_or_freq,time,%time,\n'
        fh.write(sss)
        totaltime = self.lasttime-self.firsttime
        tt = 0
        for f in sorted(self.freqentries.keys()):
            tl = self.running[c][f]
            sss = ss+str(f)+','
            if len(tl):
                t = sum([i[1] for i in tl])
                tt+=t
                sss+='%d,%f,'%(t,float(t)*100.0/totaltime)
            else:
                sss+='0,0,'
            fh.write(sss+'\n')

        for s in sorted(self.idleentries.keys()):
            tl = self.idlestates[c][s]
            sss = ss+str(s)+','
            if len(tl):
                t = sum([i[1] for i in tl])
                tt+=t
                sss+='%d,%f,'%(t,float(t)*100.0/totaltime)
            else:
                sss+='0,0,'
            fh.write(sss+'\n')
        fh.write(ss+',%d,%d,\n'%(tt,totaltime))
        return

    def addwarning(self,fh):
        if self.droppedtraces:
            missingtime = 'uknown'
            if self.realfirsttime != -1:
                realtotaltime = self.lasttime-self.realfirsttime
                tracedtime = self.lasttime-self.firsttime
                missingtime  = '%d us %f%% of total' % (realtotaltime - tracedtime,
                                                          100.0*float(realtotaltime - tracedtime)/realtotaltime)
            fh.write('warning: lost traces missing %s time\n' % (missingtime))                                                   
        
    def produce_report(self):
        fh=open(self.outfilep,  'w')
        self.addwarning(fh)                                                  
        nclusters = len(self.clusterlist)
        if nclusters > 1:
            for ix in range(nclusters): 
                self.parallel_report(ix,fh)
        self.parallel_report(nclusters,fh)  # calling with index set to max+1 generates report for all cores
        fh.close()    
        fh=open(self.outfilecs,  'w')
        self.addwarning(fh)                                                  
        for c in range(len(self.device.core_names)):
            self.cpu_state_report(c,fh)
        fh.close()


class CpuState(ResultProcessor):
    name = 'cpustate'
    description = '''
                  CPU state utilises power ftraces to generate parallelism metrics 
                  and state residency numbers of each cpu. 
                  The processor will generate files parallel.csv and corestates.csv
                  '''

    parameters = [
        Parameter('initfreq', kind=list, default=list(),
                  description='Initial frequences for each cluster'),
        Parameter('absentstate',kind=int,default=2,
                  description='''Idle state assumed for period where idle state is unknown 
                  because the core was already idle at the start of the trace'''),
        Parameter('clusterstate',kind=int,default=2,
                  description='''first cluster level idle state''')
    ]
    # classesoldformat = [IdleStartTrace,IdleEndTrace,FreqTrace] if ever we need to go back to 3.4
    classesnewformat = [IdleEndTraceCpuIdle,IdleStartTraceCpuIdle,FreqTraceCpu]
    classes = classesnewformat
    rgx = re.compile('.+\[\d+\].*\s+(\d+).(\d+):(\s+\S+:.*)')

    def __init__(self, **kwargs):
        super(CpuState, self).__init__(**kwargs)
        self.cpustateproc = CpuStateProc()

    def validate(self):
        if not instrumentation.instrument_is_installed('trace-cmd'):
            raise ConfigError('"dvfs" works only if "trace_cmd" in enabled in instrumentation')

    def initialize(self, context):  # pylint: disable=R0912
        self.cpustateproc.initialize(context,self.logger,self.absentstate,self.clusterstate,self.initfreq)
    
    def process_iteration_result(self, result, context):
        self.cpustateproc.parse(context)
        self.cpustateproc.produce_report()
    


class simplelogger:
    def warning(self,s):
        sys.stderr.write('warning: %s\n' % (s))        
    def debug(self,s):
        sys.stdout.write('debug: %s\n' % (s))        

class fakedevice:
    pass

class fakecontext:
    def __init__(self, **kwargs):
        self.output_directory = '.'
        self.device = fakedevice()


def run():
    parser = argparse.ArgumentParser(description='Produce CPU power activity data from power trace.')
    parser.add_argument('infile', help='filename of trace file (text format)')
    parser.add_argument('--clusterstate', default=2, help='first cluster gating state')    
    parser.add_argument('--absentstate', default=2, help='state to use as starting state if a cpu was idle from start of trace and for cpus where there is no trace at all')    
    parser.add_argument('--corenames', required = True, default="", help='comma separated core names eg A7,A7,A15,A15')    
    parser.add_argument('--coreclusters', required = True, default="", help='comma separated list of cluster id per core eg 0,0,1,1')  
    parser.add_argument('--initfreq', required = True, default="", help='comma separated list of initial frequencies eg 10,10')    

    args = parser.parse_args()
    fk = fakecontext()
    fk.device.core_names = args.corenames.split(",")
    fk.device.core_clusters = [int(i) for i in args.coreclusters.split(",")]
    if len(fk.device.core_names)!=len(fk.device.core_clusters):
        sys.stderr.write('error: corenames (%d) and corecluster (%d) parameters must be same length \n' % 
                         (len(fk.device.core_names),len(fk.device.core_clusters)))
        parser.print_help() 
        sys.exit(2)

    initfreq = [int(i) for i in args.initfreq.split(",")]
    if len(initfreq)!=len(set(fk.device.core_clusters)):
        sys.stderr.write('error: there must be one freq for each cluster \n')
        sys.stderr.write('error: you have %d freqs and %d clusters \n' % 
                         (len(initfreq),len(set(fk.device.core_clusters))))
        parser.print_help() 
        sys.exit(2)

    sl = simplelogger()
    cpustateproc = CpuStateProc()
    cpustateproc.initialize(fk,sl,int(args.absentstate),int(args.clusterstate),initfreq,args.infile)
    cpustateproc.parse(fk)
    cpustateproc.produce_report()
        
    
if __name__ == '__main__':
    run()
