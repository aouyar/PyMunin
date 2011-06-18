#!/usr/bin/python
"""diskusagestats - Munin Plugin to monitor disk space and inode usage of 
filesystems.

Requirements
  - Root user privileges may be requiered to access stats for filesystems 
  without any read access for munin user.


Wild Card Plugin - No


Multigraph Plugin - Graph Structure
   - diskspace
   - diskinode

   
Environment Variables
  include_graphs:  Comma separated list of enabled graphs. 
                   (All graphs enabled by default.)
  exclude_graphs:  Comma separated list of disabled graphs.
  include_fspaths: Comma separated list of filesystems to include in monitoring.
                   (All enabled by default.)
  exclude_fspaths: Comma separated list of filesystems to exclude from monitoring.
  include_fstypes: Comma separated list of filesystem types to include in 
                   monitoring. (All enabled by default.)
  exclude_fstypes: Comma separated list of filesystem types to exclude from 
                   monitoring.


  Example:
    [diskusagestats]
        env.exclude_graphs diskinode
        env.exclude_fstype tmpfs

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=noautoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.diskusage import DiskUsageInfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninDiskUsagePlugin(MuninPlugin):
    """Multigraph Munin Plugin for Disk Usage of filesystems.

    """
    plugin_name = 'diskusagestats'
    isMultigraph = True

    def __init__(self, argv = (), env = {}):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv: List of command line arguments.
        @param env:  Dictionary of environment variables.
        
        """
        MuninPlugin.__init__(self, argv, env)
        
        self.registerFilter('fspaths', '[\w\-\/]+$')
        self.registerFilter('fstypes', '\w+$')
        
        self._statsSpace = None
        self._statsInode = None
        self._info = DiskUsageInfo()
        
        name = 'diskspace'
        if self.graphEnabled(name):
            self._statsSpace = self._info.getSpaceUse()
            graph = MuninGraph('Disk Space Usage (%)', 'Disk Usage',
                info='Disk space usage of filesystems.',
                args='--base 1000 --lower-limit 0')
            for (fspath, stats) in self._statsSpace.iteritems():
                if self.fsPathEnabled(fspath) and self.fsTypeEnabled(stats['type']):
                    fname = self._getFieldName(fspath)
                    graph.addField(fname, fspath, draw='LINE2', type='GAUGE',
                        info="Disk space usage for filesystem: %s" % fspath)
            self.appendGraph(name, graph)
        
        name = 'diskinode'
        if self.graphEnabled(name):
            self._statsInode = self._info.getInodeUse()
            graph = MuninGraph('Inode Usage (%)', 'Disk Usage',
                info='Inode usage of filesystems.',
                args='--base 1000 --lower-limit 0')
            for (fspath, stats) in self._statsInode.iteritems():
                if self.fsPathEnabled(fspath) and self.fsTypeEnabled(stats['type']):
                    fname = self._getFieldName(fspath)
                    graph.addField(fname, fspath, draw='LINE2', type='GAUGE',
                        info="Inode usage for filesystem: %s" % fspath)
            self.appendGraph(name, graph)
        
    def retrieveVals(self):
        """Retrive values for graphs."""
        name = 'diskspace'
        if self.hasGraph(name):
            for (fspath, stats) in self._statsSpace.iteritems():
                if self.fsPathEnabled(fspath) and self.fsTypeEnabled(stats['type']):
                    fname = self._getFieldName(fspath)
                    self.setGraphVal(name, fname, stats['inuse_pcent'])
        name = 'diskinode'
        if self.hasGraph(name):
            for (fspath, stats) in self._statsInode.iteritems():
                if self.fsPathEnabled(fspath) and self.fsTypeEnabled(stats['type']):
                    fname = self._getFieldName(fspath)
                    self.setGraphVal(name, fname, stats['inuse_pcent'])

    def fsPathEnabled(self, fspath):
        """Utility method to check if a filesystem path is included in monitoring.
        
        @param fspath: Filesystem path.
        @return:       Returns True if included in graphs, False otherwise.
            
        """
        return self.checkFilter('fspaths', fspath)

    def fsTypeEnabled(self, fstype):
        """Utility method to check if a filesystem type is included in monitoring.
        
        @param fstype: Filesystem type.
        @return:       Returns True if included in graphs, False otherwise.
            
        """
        return self.checkFilter('fstypes', fstype)
    
    def _getFieldName(self, fspath):
        """Generate a valid field name from the filesystem path.
        
        @param fspath: Filesystem path.
        @return:       Field name.
        
        """
        if fspath == '/':
            return 'rootfs'
        else:
            return(fspath[1:].replace('/', '_'))
            


if __name__ == "__main__":
    sys.exit(muninMain(MuninDiskUsagePlugin))

