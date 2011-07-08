#!/usr/bin/python
"""diskiostats - Munin Plugin to monitor Disk I/O.

Requirements - NA


Wild Card Plugin - No


Multigraph Plugin - Graph Structure
    - diskio_disk_requests
    - diskio_disk_bytes
    - diskio_disk_active

   
Environment Variables
  include_graphs:  Comma separated list of enabled graphs. 
                   (All graphs enabled by default.)
  exclude_graphs:  Comma separated list of disabled graphs.


  Example:
    [diskiostats]
        env.exclude_graphs diskinode
        env.exclude_fstype tmpfs

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=noautoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.diskio import DiskIOinfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.7"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninDiskIOplugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring Disk I/O.

    """
    plugin_name = 'diskiostats'
    isMultigraph = True

    def __init__(self, argv = (), env = {}):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv: List of command line arguments.
        @param env:  Dictionary of environment variables.
        
        """
        MuninPlugin.__init__(self, argv, env)
        
        self._statsSpace = None
        self._statsInode = None
        self._info = DiskIOinfo()
        
        name = 'diskio_disk_requests'
        if self.graphEnabled(name):
            graph = MuninGraph('Disk I/O - Disk - Requests', 'Disk I/O',
                info='Disk I/O - Disk Throughput,  Read / write requests per second.',
                args='--base 1000 --lower-limit 0',
                vlabel='reqs/sec read (-) / write (+)')
            for disk in self._info.getDiskList():
                graph.addField(disk + '_read', disk, draw='LINE2', type='DERIVE',
                    min = 0, graph=False)
                graph.addField(disk + '_write', disk, draw='LINE2', type='DERIVE',
                    min = 0, negative = disk + '_read')
            self.appendGraph(name, graph)
        
        name = 'diskio_disk_bytes'
        if self.graphEnabled(name):
            graph = MuninGraph('Disk I/O - Disk - Throughput', 'Disk I/O',
                info='Disk I/O - Disk Throughput, bytes read / written per second.',
                args='--base 1000 --lower-limit 0',
                vlabel='bytes/sec read (-) / write (+)')
            for disk in self._info.getDiskList():
                graph.addField(disk + '_read', disk, draw='LINE2', type='DERIVE',
                    min = 0, graph=False)
                graph.addField(disk + '_write', disk, draw='LINE2', type='DERIVE',
                    min = 0, negative = disk + '_read')
            self.appendGraph(name, graph)
            
        name = 'diskio_disk_active'
        if self.graphEnabled(name):
            graph = MuninGraph('Disk I/O - Disk - Queue Length', 'Disk I/O',
                info='Disk I/O - Number  of I/O Operations in Progress for every disk.',
                args='--base 1000 --lower-limit 0')
            for disk in self._info.getDiskList():
                graph.addField(disk, disk, draw='AREASTACK', type='GAUGE')
            self.appendGraph(name, graph)
                
    def retrieveVals(self):
        """Retrive values for graphs."""
        for disk in self._info.getDiskList():
            stats = self._info.getDiskStats(disk)
            name = 'diskio_disk_requests'
            if self.hasGraph(name):
                self.setGraphVal(name, disk + '_read', stats['rios'])
                self.setGraphVal(name, disk + '_write', stats['wios'])
                name = 'diskio_disk_bytes'
            if self.hasGraph(name):
                self.setGraphVal(name, disk + '_read', stats['rbytes'])
                self.setGraphVal(name, disk + '_write', stats['wbytes'])
            name = 'diskio_disk_active'
            if self.hasGraph(name):
                self.setGraphVal(name, disk, stats['ios_active'])
                

if __name__ == "__main__":
    sys.exit(muninMain(MuninDiskIOplugin))

