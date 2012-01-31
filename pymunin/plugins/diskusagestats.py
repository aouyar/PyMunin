#!/usr/bin/env python
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

  include_fspaths: Comma separated list of filesystems to include in monitoring.
                   (All enabled by default.)
  exclude_fspaths: Comma separated list of filesystems to exclude from monitoring.
  include_fstypes: Comma separated list of filesystem types to include in 
                   monitoring. (All enabled by default.)
  exclude_fstypes: Comma separated list of filesystem types to exclude from 
                   monitoring.
  include_graphs:  Comma separated list of enabled graphs. 
                   (All graphs enabled by default.)
  exclude_graphs:  Comma separated list of disabled graphs.


  Example:
    [diskusagestats]
        env.exclude_graphs diskinode
        env.exclude_fstype tmpfs

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=noautoconf nosuggest

import sys
from pymunin import (MuninGraph, MuninPlugin, muninMain, 
                     fixLabel, maxLabelLenGraphSimple)
from pysysinfo.filesystem import FilesystemInfo

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

    def __init__(self, argv=(), env={}, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)
        
        self.envRegisterFilter('fspaths', '^[\w\-\/]+$')
        self.envRegisterFilter('fstypes', '^\w+$')
        
        self._statsSpace = None
        self._statsInode = None
        self._info = FilesystemInfo()
        
        self._fslist = [fs for fs in self._info.getFSlist()
                        if (self.fsPathEnabled(fs) 
                            and self.fsTypeEnabled(self._info.getFStype(fs)))]
        self._fslist.sort()
        
        name = 'diskspace'
        if self.graphEnabled(name):
            self._statsSpace = self._info.getSpaceUse()
            graph = MuninGraph('Disk Space Usage (%)', 'Disk Usage',
                info='Disk space usage of filesystems.',
                args='--base 1000 --lower-limit 0', printf='%6.1lf',
                autoFixNames=True)
            for fspath in self._fslist:
                if self._statsSpace.has_key(fspath):
                    graph.addField(fspath, 
                        fixLabel(fspath, maxLabelLenGraphSimple, 
                                 delim='/', repl='..', truncend=False), 
                        draw='LINE2', type='GAUGE',
                        info="Disk space usage for: %s" % fspath)
            self.appendGraph(name, graph)
        
        name = 'diskinode'
        if self.graphEnabled(name):
            self._statsInode = self._info.getInodeUse()
            graph = MuninGraph('Inode Usage (%)', 'Disk Usage',
                info='Inode usage of filesystems.',
                args='--base 1000 --lower-limit 0', printf='%6.1lf',
                autoFixNames=True)
            for fspath in self._fslist:
                if self._statsInode.has_key(fspath):
                    graph.addField(fspath,
                        fixLabel(fspath, maxLabelLenGraphSimple, 
                                 delim='/', repl='..', truncend=False), 
                        draw='LINE2', type='GAUGE',
                        info="Inode usage for: %s" % fspath)
            self.appendGraph(name, graph)
        
    def retrieveVals(self):
        """Retrieve values for graphs."""
        name = 'diskspace'
        if self.hasGraph(name):
            for fspath in self._fslist:
                if self._statsSpace.has_key(fspath):
                    self.setGraphVal(name, fspath, 
                                     self._statsSpace[fspath]['inuse_pcent'])
        name = 'diskinode'
        if self.hasGraph(name):
            for fspath in self._fslist:
                if self._statsInode.has_key(fspath):
                    self.setGraphVal(name, fspath, 
                                     self._statsInode[fspath]['inuse_pcent'])

    def fsPathEnabled(self, fspath):
        """Utility method to check if a filesystem path is included in monitoring.
        
        @param fspath: Filesystem path.
        @return:       Returns True if included in graphs, False otherwise.
            
        """
        return self.envCheckFilter('fspaths', fspath)

    def fsTypeEnabled(self, fstype):
        """Utility method to check if a filesystem type is included in monitoring.
        
        @param fstype: Filesystem type.
        @return:       Returns True if included in graphs, False otherwise.
            
        """
        return self.envCheckFilter('fstypes', fstype)


def main():
    sys.exit(muninMain(MuninDiskUsagePlugin))
            

if __name__ == "__main__":
    main()
