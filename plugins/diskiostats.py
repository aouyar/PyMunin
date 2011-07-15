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

        self._info = DiskIOinfo()
        
        disklist = self._info.getDiskList()
        self._configDevRequests('disk', 'Disk', disklist)
        self._configDevBytes('disk', 'Disk', disklist)
        self._configDevActive('disk', 'Disk', disklist)
        
        fslist = self._info.getFilesystemList()
        self._configDevRequests('fs', 'Filesystem', fslist)
        self._configDevBytes('fs', 'Filesystem', fslist)
        self._configDevActive('fs', 'Filesystem', fslist)
                
    def retrieveVals(self):
        """Retrive values for graphs."""
        devlist = self._info.getDiskList()
        statsfunc = self._info.getDiskStats
        self._fetchDevAll('disk', devlist, statsfunc)
        devlist = self._info.getFilesystemList()
        statsfunc = self._info.getFilesystemStats
        self._fetchDevAll('fs', devlist, statsfunc)
                
    def _configDevRequests(self, namestr, titlestr, devlist):
        name = 'diskio_%s_requests' % namestr
        if self.graphEnabled(name):
            graph = MuninGraph('Disk I/O - %s - Requests' % titlestr, 'Disk I/O',
                info='Disk I/O - %s Throughput, Read / write requests per second.' 
                     % titlestr,
                args='--base 1000 --lower-limit 0',
                vlabel='reqs/sec read (-) / write (+)')
            for dev in devlist:
                graph.addField(dev + '_read', namestr, draw='LINE2', 
                               type='DERIVE', min=0, graph=False)
                graph.addField(dev + '_write', namestr, draw='LINE2', 
                               type='DERIVE', min=0, negative=(dev + '_read'))
            self.appendGraph(name, graph)

    def _configDevBytes(self, namestr, titlestr, devlist):
        name = 'diskio_%s_bytes' % namestr
        if self.graphEnabled(name):
            graph = MuninGraph('Disk I/O - %s - Throughput' % titlestr, 'Disk I/O',
                info='Disk I/O - %s Throughput, bytes read / written per second.'
                     % titlestr,
                args='--base 1000 --lower-limit 0',
                vlabel='bytes/sec read (-) / write (+)')
            for dev in devlist:
                graph.addField(dev + '_read', dev, draw='LINE2', type='DERIVE',
                    min=0, graph=False)
                graph.addField(dev + '_write', dev, draw='LINE2', type='DERIVE',
                    min=0, negative=(dev + '_read'))
            self.appendGraph(name, graph)
            
    def _configDevActive(self, namestr, titlestr, devlist):
        name = 'diskio_%s_active' % namestr
        if self.graphEnabled(name):
            graph = MuninGraph('Disk I/O - %s - Queue Length' % titlestr, 
                'Disk I/O',
                info='Disk I/O - Number  of I/O Operations in Progress for every %s.'
                     % titlestr,
                args='--base 1000 --lower-limit 0')
            for dev in devlist:
                graph.addField(dev, dev, draw='AREASTACK', type='GAUGE')
            self.appendGraph(name, graph)

    def _fetchDevAll(self, namestr, devlist, statsfunc):
        for dev in devlist:
            stats = statsfunc(dev)
            name = 'diskio_%s_requests' % namestr
            if self.hasGraph(name):
                self.setGraphVal(name, dev + '_read', stats['rios'])
                self.setGraphVal(name, dev + '_write', stats['wios'])
            name = 'diskio_%s_bytes' % namestr
            if self.hasGraph(name):
                self.setGraphVal(name, dev + '_read', stats['rbytes'])
                self.setGraphVal(name, dev + '_write', stats['wbytes'])
            name = 'diskio_%s_active' % namestr
            if self.hasGraph(name):
                self.setGraphVal(name, dev, stats['ios_active'])
        
        
if __name__ == "__main__":
    sys.exit(muninMain(MuninDiskIOplugin))

