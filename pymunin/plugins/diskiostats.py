#!/usr/bin/python
"""diskiostats - Munin Plugin to monitor Disk I/O.

Requirements - NA


Wild Card Plugin - No


Multigraph Plugin - Graph Structure
    - diskio_disk_requests
    - diskio_disk_bytes
    - diskio_disk_active
    - diskio_part_requests
    - diskio_part_bytes
    - diskio_part_active
    - diskio_md_requests
    - diskio_md_bytes
    - diskio_md_active
    - diskio_lv_requests
    - diskio_lv_bytes
    - diskio_lv_active
    - diskio_fs_requests
    - diskio_fs_bytes
    - diskio_fs_active

   
Environment Variables
  include_graphs:  Comma separated list of enabled graphs. 
                   (All graphs enabled by default.)
  exclude_graphs:  Comma separated list of disabled graphs.


  Example:
    [diskiostats]
        env.include_graphs diskio_disk_requests, diskio_disk_bytes


"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=noautoconf nosuggest

import sys
from pymunin import (MuninGraph, MuninPlugin, muninMain, 
                     fixLabel, maxLabelLenGraphSimple, maxLabelLenGraphDual)
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

    def __init__(self, argv=(), env={}, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)

        self._info = DiskIOinfo()
        
        self._labelDelim = { 'fs': '/', 'lv': '-'}
        
        self._diskList = self._info.getDiskList()
        if self._diskList:
            self._diskList.sort()
            self._configDevRequests('disk', 'Disk', self._diskList)
            self._configDevBytes('disk', 'Disk', self._diskList)
            self._configDevActive('disk', 'Disk', self._diskList)
            
        self._mdList = self._info.getMDlist()
        if self._mdList:
            self._mdList.sort()
            self._configDevRequests('md', 'MD', self._mdList)
            self._configDevBytes('md', 'MD', self._mdList)
            self._configDevActive('md', 'MD', self._mdList)
            
        devlist = self._info.getPartitionList()
        if devlist:
            devlist.sort()
            self._partList = [x[1] for x in devlist]
            self._configDevRequests('part', 'Partition', self._partList)
            self._configDevBytes('part', 'Partition', self._partList)
            self._configDevActive('part', 'Partition', self._partList)
        else:
            self._partList = None
            
        devlist = self._info.getLVlist()
        if devlist:
            devlist.sort()
            self._lvList = ["-".join(x) for x in devlist]
            self._configDevRequests('lv', 'LV', self._lvList)
            self._configDevBytes('lv', 'LV', self._lvList)
            self._configDevActive('lv', 'LV', self._lvList)
        else:
            self._lvList = None
        
        self._fsList = self._info.getFilesystemList()
        self._fsList.sort()
        self._configDevRequests('fs', 'Filesystem', self._fsList)
        self._configDevBytes('fs', 'Filesystem', self._fsList)
        self._configDevActive('fs', 'Filesystem', self._fsList)
        
                
    def retrieveVals(self):
        """Retrieve values for graphs."""
        if self._diskList:
            self._fetchDevAll('disk', self._diskList, 
                              self._info.getDiskStats)
        if self._mdList:
            self._fetchDevAll('md', self._mdList, 
                              self._info.getMDstats)
        if self._partList:
            self._fetchDevAll('part', self._partList, 
                              self._info.getPartitionStats) 
        if self._lvList:
            self._fetchDevAll('lv', self._lvList, 
                              self._info.getLVstats)
        self._fetchDevAll('fs', self._fsList, 
                          self._info.getFilesystemStats)
                
    def _configDevRequests(self, namestr, titlestr, devlist):
        """Generate configuration for I/O Request stats.
        
        @param namestr:  Field name component indicating device type.
        @param titlestr: Title component indicating device type.
        @param devlist:  List of devices.
        
        """
        name = 'diskio_%s_requests' % namestr
        if self.graphEnabled(name):
            graph = MuninGraph('Disk I/O - %s - Requests' % titlestr, 'Disk I/O',
                info='Disk I/O - %s Throughput, Read / write requests per second.' 
                     % titlestr,
                args='--base 1000 --lower-limit 0',
                vlabel='reqs/sec read (-) / write (+)', printf='%6.1lf',
                autoFixNames = True)
            for dev in devlist:
                graph.addField(dev + '_read',
                               fixLabel(dev, maxLabelLenGraphDual, 
                                        repl = '..', truncend=False,
                                        delim = self._labelDelim.get(namestr)), 
                               draw='LINE2', type='DERIVE', min=0, graph=False)
                graph.addField(dev + '_write',
                               fixLabel(dev, maxLabelLenGraphDual, 
                                        repl = '..', truncend=False,
                                        delim = self._labelDelim.get(namestr)),
                               draw='LINE2', type='DERIVE', min=0, 
                               negative=(dev + '_read'),info=dev)
            self.appendGraph(name, graph)

    def _configDevBytes(self, namestr, titlestr, devlist):
        """Generate configuration for I/O Throughput stats.
        
        @param namestr:  Field name component indicating device type.
        @param titlestr: Title component indicating device type.
        @param devlist:  List of devices.
        
        """
        name = 'diskio_%s_bytes' % namestr
        if self.graphEnabled(name):
            graph = MuninGraph('Disk I/O - %s - Throughput' % titlestr, 'Disk I/O',
                info='Disk I/O - %s Throughput, bytes read / written per second.'
                     % titlestr,
                args='--base 1000 --lower-limit 0', printf='%6.1lf',
                vlabel='bytes/sec read (-) / write (+)',
                autoFixNames = True)
            for dev in devlist:
                graph.addField(dev + '_read', 
                               fixLabel(dev, maxLabelLenGraphDual, 
                                        repl = '..', truncend=False,
                                        delim = self._labelDelim.get(namestr)),
                               draw='LINE2', type='DERIVE', min=0, graph=False)
                graph.addField(dev + '_write', 
                               fixLabel(dev, maxLabelLenGraphDual, 
                                        repl = '..', truncend=False,
                                        delim = self._labelDelim.get(namestr)),
                               draw='LINE2', type='DERIVE', min=0, 
                               negative=(dev + '_read'), info=dev)
            self.appendGraph(name, graph)
            
    def _configDevActive(self, namestr, titlestr, devlist):
        """Generate configuration for I/O Queue Length.
        
        @param namestr:  Field name component indicating device type.
        @param titlestr: Title component indicating device type.
        @param devlist:  List of devices.
        
        """
        name = 'diskio_%s_active' % namestr
        if self.graphEnabled(name):
            graph = MuninGraph('Disk I/O - %s - Queue Length' % titlestr, 
                'Disk I/O',
                info='Disk I/O - Number  of I/O Operations in Progress for every %s.'
                     % titlestr,
                args='--base 1000 --lower-limit 0', printf='%6.1lf',
                autoFixNames = True)
            for dev in devlist:
                graph.addField(dev, 
                               fixLabel(dev, maxLabelLenGraphSimple, 
                                        repl = '..', truncend=False,
                                        delim = self._labelDelim.get(namestr)), 
                               draw='AREASTACK', type='GAUGE', info=dev)
            self.appendGraph(name, graph)

    def _fetchDevAll(self, namestr, devlist, statsfunc):
        """Initialize I/O stats for devices.
        
        @param namestr:   Field name component indicating device type.
        @param devlist:   List of devices.
        @param statsfunc: Function for retrieving stats for device.
        
        """
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
        

def main():
    sys.exit(muninMain(MuninDiskIOplugin))


if __name__ == "__main__":
    main()
