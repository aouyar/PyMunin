#!/usr/bin/python
#
# sysstats - Munin Plugin to monitor system resource usage (cpu, memory, etc.) stats.
#
# Requirements
#   - NA.
#
# Wild Card Plugin - No
#
#
# Multigraph Plugin - Graph Structure
#    - sys_loadavg
#    - sys_cpu
#    - sys_memory
#
#
# Environment Variables
#
#   include_graphs: Comma separated list of enabled graphs.
#                   (All graphs enabled by default.)
#   exclude_graphs: Comma separated list of disabled graphs.
#
#   Example:
#     [ntpstats]
#         env.exclude_graphs sys_loadavg
#
#
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=noautoconf nosuggest

__author__="Ali Onur Uyar"
__date__ ="$Jun 12, 2011 14:51:57 PM$"


import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.system import SystemInfo



class MuninSysStatsPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring NTP Peer.

    """
    plugin_name = 'sysstats'
    isMultigraph = True

    def __init__(self, argv = (), env = {}):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv: List of command line arguments.
        @param env:  Dictionary of environment variables.
        
        """      
        MuninPlugin.__init__(self, argv, env)
        
        self._sysinfo = SystemInfo()
        self._cpustats = None
        self._memstats = None

        if self.graphEnabled('sys_loadavg'):
            graph = MuninGraph('Load Average', 'System',
                info='Load Average (15 min, 5 min, 1 min).',
                args='--base 1000 --lower-limit 0')
            graph.addField('load15min', '15 min', type='GAUGE', draw='AREA')
            graph.addField('load5min', '5 min', type='GAUGE', draw='LINE2')
            graph.addField('load1min', '1 min', type='GAUGE', draw='LINE2')
            self.appendGraph('sys_loadavg', graph)
        
        if self.graphEnabled('sys_cpu_util'):
            self._cpustats = self._sysinfo.getCPUuse()
            graph = MuninGraph('CPU Utilization (%)', 'System',
                info='System CPU Utilization.',
                args='--base 1000 --lower-limit 0')
            for field in ['system', 'user', 'nice', 'idle', 'iowait', 'irq', 'softirq', 'steal', 'guest']:
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
            self._memstats['SwapUsed'] = self._memstats['SwapTotal'] - self._memstats['SwapFree']
            graph = MuninGraph('Memory Utilization (bytes)', 'System',
                info='System Memory Utilization in bytes.',
                args='--base 1000 --lower-limit 0')
            for field in ['MemUsed', 'SwapCached', 'Buffers', 'Cached', 'MemFree', 'SwapUsed']:
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
            graph = MuninGraph('Memory Utilization - Active/Inactive (bytes)', 'System',
                info='System Memory Utilization (Active/Inactive) in bytes.',
                args='--base 1000 --lower-limit 0')
            for field in ['MemKernel', 'MemHugePages', 'Active', 'Inactive', 'MemFree']:
                if self._memstats.has_key(field):
                    graph.addField(field, field, type='GAUGE', draw='AREASTACK')
            self.appendGraph('sys_mem_avail', graph)
        
        if self.graphEnabled('sys_mem_huge'):
            if self._memstats is None:
                self._memstats = self._sysinfo.getMemoryUse()
            if self._memstats.has_key('Hugepagesize') and self._memstats['HugePages_Total'] > 0:
                graph = MuninGraph('Memory Utilization - Huge Pages (bytes)', 'System',
                    info='System Memory Huge Pages Utilization in bytes.',
                    args='--base 1000 --lower-limit 0')
                for field in ['Rsvd', 'Surp', 'Free']:
                    fkey = 'HugePages_' + field
                    if self._memstats.has_key(fkey):
                        graph.addField(field, field, type='GAUGE', draw='AREASTACK')
                self.appendGraph('sys_mem_huge', graph)
        

    def retrieveVals(self):
        """Retrive values for graphs."""
        stats = self._sysinfo.getLoadAvg()
        if stats:
            if self.graphEnabled('sys_loadavg'):
                self.setGraphVal('sys_loadavg', 'load15min', stats[2])
                self.setGraphVal('sys_loadavg', 'load5min', stats[1])
                self.setGraphVal('sys_loadavg', 'load1min', stats[0])
        if self._cpustats:
            for field in ['system', 'user', 'nice', 'idle', 'iowait', 'irq', 'softirq', 'steal', 'guest']:
                if self._cpustats.has_key(field):
                    self.setGraphVal('sys_cpu_util', field, int(self._cpustats[field] * 1000))
        if self._memstats:
            if self.graphEnabled('sys_mem_util'):
                for field in ['MemUsed', 'SwapCached', 'Buffers', 'Cached', 'MemFree', 'SwapUsed']:
                    if self._memstats.has_key(field):
                        self.setGraphVal('sys_mem_util', field, self._memstats[field])
            if self.graphEnabled('sys_mem_avail'):
                for field in ['MemKernel', 'MemHugePages', 'Active', 'Inactive', 'MemFree']:
                    if self._memstats.has_key(field):
                        self.setGraphVal('sys_mem_avail', field, self._memstats[field])
            if self._memstats.has_key('Hugepagesize') and self._memstats['HugePages_Total'] > 0:
                for field in ['Rsvd', 'Surp', 'Free']:
                    fkey = 'HugePages_' + field
                    if self._memstats.has_key(fkey):
                        self.setGraphVal('sys_mem_huge', field, 
                                         self._memstats[fkey] * self._memstats['Hugepagesize'])
                

if __name__ == "__main__":
    sys.exit(muninMain(MuninSysStatsPlugin))
