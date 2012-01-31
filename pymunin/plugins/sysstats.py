#!/usr/bin/env python
"""sysstats - Munin Plugin to monitor system resource usage stats.
CPU, memory, processes, forks, interrupts, context switches, paging, 
swapping, etc.

Requirements
  - NA.

Wild Card Plugin - No


Multigraph Plugin - Graph Structure
   - sys_loadavg
   - sys_cpu_util
   - sys_memory_util
   - sys_memory_avail
   - sys_processes
   - sys_forks
   - sys_intr_ctxt
   - sys_vm_paging
   - sys_vm_swapping


Environment Variables

  include_graphs: Comma separated list of enabled graphs.
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.

  Example:
    [sysstats]
        env.exclude_graphs sys_loadavg

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=noautoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.system import SystemInfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninSysStatsPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring System Resource Usage Stats.

    """
    plugin_name = 'sysstats'
    isMultigraph = True

    def __init__(self, argv=(), env={}, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """     
        MuninPlugin.__init__(self, argv, env, debug)
        
        self._sysinfo = SystemInfo()
        self._loadstats = None
        self._cpustats = None
        self._memstats = None
        self._procstats = None
        self._vmstats = None

        if self.graphEnabled('sys_loadavg'):
            graph = MuninGraph('Load Average', 'System',
                info='Load Average (15 min, 5 min, 1 min).',
                args='--base 1000 --lower-limit 0')
            graph.addField('load15min', '15 min', type='GAUGE', draw='AREA')
            graph.addField('load5min', '5 min', type='GAUGE', draw='LINE1')
            graph.addField('load1min', '1 min', type='GAUGE', draw='LINE1')
            self.appendGraph('sys_loadavg', graph)
        
        if self.graphEnabled('sys_cpu_util'):
            self._cpustats = self._sysinfo.getCPUuse()
            graph = MuninGraph('CPU Utilization (%)', 'System',
                info='System CPU Utilization.',
                args='--base 1000 --lower-limit 0')
            for field in ['system', 'user', 'nice', 'idle', 'iowait', 
                          'irq', 'softirq', 'steal', 'guest']:
                if self._cpustats.has_key(field):
                    graph.addField(field, field, type='DERIVE', min=0, 
                                   cdef='%s,10,/' % field, draw='AREASTACK')
            self.appendGraph('sys_cpu_util', graph)
            
        if self.graphEnabled('sys_mem_util'):
            if self._memstats is None:
                self._memstats = self._sysinfo.getMemoryUse()
            self._memstats['MemUsed'] = self._memstats['MemTotal']
            for field in ['MemFree', 'SwapCached', 'Buffers', 'Cached']:
                if self._memstats.has_key(field):
                    self._memstats['MemUsed'] -= self._memstats[field]
            self._memstats['SwapUsed'] = (self._memstats['SwapTotal'] 
                                          - self._memstats['SwapFree'])
            graph = MuninGraph('Memory Utilization (bytes)', 'System',
                info='System Memory Utilization in bytes.',
                args='--base 1000 --lower-limit 0')
            for field in ['MemUsed', 'SwapCached', 'Buffers', 'Cached', 
                          'MemFree', 'SwapUsed']:
                if self._memstats.has_key(field):
                    graph.addField(field, field, type='GAUGE', draw='AREASTACK')
            self.appendGraph('sys_mem_util', graph)
        
        if self.graphEnabled('sys_mem_avail'):
            if self._memstats is None:
                self._memstats = self._sysinfo.getMemoryUse()
            if self._memstats.has_key('Hugepagesize'):
                self._memstats['MemHugePages'] = (self._memstats['HugePages_Total'] 
                                                  * self._memstats['Hugepagesize']) 
            self._memstats['MemKernel'] = self._memstats['MemTotal']
            for field in ['MemHugePages', 'Active', 'Inactive', 'MemFree']:
                if self._memstats.has_key(field):
                    self._memstats['MemKernel'] -= self._memstats[field]
            graph = MuninGraph('Memory Utilization - Active/Inactive (bytes)', 
                'System',
                info='System Memory Utilization (Active/Inactive) in bytes.',
                args='--base 1000 --lower-limit 0')
            for field in ['MemKernel', 'MemHugePages', 'Active', 'Inactive', 
                          'MemFree']:
                if self._memstats.has_key(field):
                    graph.addField(field, field, type='GAUGE', draw='AREASTACK')
            self.appendGraph('sys_mem_avail', graph)
        
        if self.graphEnabled('sys_mem_huge'):
            if self._memstats is None:
                self._memstats = self._sysinfo.getMemoryUse()
            if (self._memstats.has_key('Hugepagesize') 
                and self._memstats['HugePages_Total'] > 0):
                graph = MuninGraph('Memory Utilization - Huge Pages (bytes)', 
                    'System',
                    info='System Memory Huge Pages Utilization in bytes.',
                    args='--base 1000 --lower-limit 0')
                for field in ['Rsvd', 'Surp', 'Free']:
                    fkey = 'HugePages_' + field
                    if self._memstats.has_key(fkey):
                        graph.addField(field, field, type='GAUGE', 
                                       draw='AREASTACK')
                self.appendGraph('sys_mem_huge', graph)
        
        if self.graphEnabled('sys_processes'):
            graph = MuninGraph('Processes', 'System',
                info='Number of processes in running and blocked state.',
                args='--base 1000 --lower-limit 0')
            graph.addField('running', 'running', type='GAUGE', draw='AREASTACK')
            graph.addField('blocked', 'blocked', type='GAUGE', draw='AREASTACK')
            self.appendGraph('sys_processes', graph)
            
        if self.graphEnabled('sys_forks'):
            graph = MuninGraph('Process Forks per Second', 'System',
                info='Process Forks per Second.',
                args='--base 1000 --lower-limit 0')
            graph.addField('forks', 'forks', type='DERIVE', min=0, draw='LINE2')
            self.appendGraph('sys_forks', graph)
            
        if self.graphEnabled('sys_intr_ctxt'):
            if self._procstats is None:
                self._procstats = self._sysinfo.getProcessStats()
            graph = MuninGraph('Interrupts and Context Switches per Second', 
                'System',
                info='Interrupts and Context Switches per Second',
                args='--base 1000 --lower-limit 0')
            labels = ['irq', 'softirq', 'ctxt']
            infos = ['Hardware Interrupts per second',
                    'Software Interrupts per second.',
                    'Context Switches per second.']
            idx = 0
            for field in ['intr', 'softirq', 'ctxt']:
                if self._procstats.has_key(field):
                    graph.addField(field, labels[idx], type='DERIVE', min=0,
                                   draw='LINE2', info=infos[idx])
                    idx += 1
            self.appendGraph('sys_intr_ctxt', graph)
        
        if self.graphEnabled('sys_vm_paging'):
            graph = MuninGraph('VM - Paging', 'System',
                info='Virtual Memory Paging: Pages In (-) / Out (+) per Second.',
                args='--base 1000 --lower-limit 0',
                vlabel='pages in (-) / out (+) per second')
            graph.addField('in', 'pages', type='DERIVE', min=0, draw='LINE2', 
                           graph=False)
            graph.addField('out', 'pages', type='DERIVE', min=0, draw='LINE2', 
                           negative='in')
            self.appendGraph('sys_vm_paging', graph)
        
        if self.graphEnabled('sys_vm_swapping'):
            graph = MuninGraph('VM - Swapping', 'System',
                info='Virtual Memory Swapping: Pages In (-) / Out (+) per Second.',
                args='--base 1000 --lower-limit 0',
                vlabel='pages in (-) / out (+) per second')
            graph.addField('in', 'pages', type='DERIVE', min=0, draw='LINE2', 
                           graph=False)
            graph.addField('out', 'pages', type='DERIVE', min=0, draw='LINE2', 
                           negative='in')
            self.appendGraph('sys_vm_swapping', graph)

    def retrieveVals(self):
        """Retrieve values for graphs."""
        if self.hasGraph('sys_loadavg'):
            self._loadstats = self._sysinfo.getLoadAvg()
            if self._loadstats:
                self.setGraphVal('sys_loadavg', 'load15min', self._loadstats[2])
                self.setGraphVal('sys_loadavg', 'load5min', self._loadstats[1])
                self.setGraphVal('sys_loadavg', 'load1min', self._loadstats[0])
        if self._cpustats and self.hasGraph('sys_cpu_util'):
            for field in self.getGraphFieldList('sys_cpu_util'):
                self.setGraphVal('sys_cpu_util', 
                                 field, int(self._cpustats[field] * 1000))
        if self._memstats:
            if self.hasGraph('sys_mem_util'):
                for field in self.getGraphFieldList('sys_mem_util'):
                    self.setGraphVal('sys_mem_util', 
                                     field, self._memstats[field])
            if self.hasGraph('sys_mem_avail'):
                for field in self.getGraphFieldList('sys_mem_avail'):
                    self.setGraphVal('sys_mem_avail', 
                                     field, self._memstats[field])
            if self.hasGraph('sys_mem_huge'):
                for field in ['Rsvd', 'Surp', 'Free']:
                    fkey = 'HugePages_' + field
                    if self._memstats.has_key(fkey):
                        self.setGraphVal('sys_mem_huge', field, 
                            self._memstats[fkey] * self._memstats['Hugepagesize'])
        if self.hasGraph('sys_processes'):
            if self._procstats is None:
                self._procstats = self._sysinfo.getProcessStats()
            if self._procstats:
                self.setGraphVal('sys_processes', 'running', 
                                 self._procstats['procs_running'])
                self.setGraphVal('sys_processes', 'blocked', 
                                 self._procstats['procs_blocked'])
        if self.hasGraph('sys_forks'):
            if self._procstats is None:
                self._procstats = self._sysinfo.getProcessStats()
            if self._procstats:
                self.setGraphVal('sys_forks', 'forks', 
                                 self._procstats['processes'])
        if self.hasGraph('sys_intr_ctxt'):
            if self._procstats is None:
                self._procstats = self._sysinfo.getProcessStats()
            if self._procstats:
                for field in self.getGraphFieldList('sys_intr_ctxt'):
                    self.setGraphVal('sys_intr_ctxt', field, 
                                     self._procstats[field])
        if self.hasGraph('sys_vm_paging'):
            if self._vmstats is None:
                self._vmstats = self._sysinfo.getVMstats()
            if self._vmstats:
                self.setGraphVal('sys_vm_paging', 'in', 
                                 self._vmstats['pgpgin'])
                self.setGraphVal('sys_vm_paging', 'out', 
                                 self._vmstats['pgpgout'])
        if self.hasGraph('sys_vm_swapping'):
            if self._vmstats is None:
                self._vmstats = self._sysinfo.getVMstats()
            if self._vmstats:
                self.setGraphVal('sys_vm_swapping', 'in', 
                                 self._vmstats['pswpin'])
                self.setGraphVal('sys_vm_swapping', 'out', 
                                 self._vmstats['pswpout'])


def main():
    sys.exit(muninMain(MuninSysStatsPlugin))


if __name__ == "__main__":
    main()
