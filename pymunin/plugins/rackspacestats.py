#!/usr/bin/env python
"""rackspacestats - Munin Plugin to monitor stats for Rackspace cloud usage.

Requirements

python-cloudfiles

Wild Card Plugin - No

Multigraph Plugin - Graph Structure
    - rackspace_containersize
    - rackspace_containercount

Environment Variables

  container:          Rackspace CDN container name
  username:           Rackspace username
  api_key:            Rackspace api_key

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=autoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.rackspace import RackspaceContainerInfo

__author__ = "Ben Welsh"
__copyright__ = "Copyright 2012, Ben Welsh"
__credits__ = []
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Ben Welsh"
__email__ = "ben.welsh@gmail.com"
__status__ = "Development"


class MuninRackspacePlugin(MuninPlugin):
    """
    Multigraph Munin Plugin for monitoring Rackspace cloud usage
    """
    plugin_name = 'rackspace'
    isMultigraph = True
    
    def __init__(self, argv=(), env={}, debug=False):
        """
        Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)
        
        self._container = self.envGet('container')
        self._username = self.envGet('username')
        self._api_key = self.envGet('api_key')
        
        self._stats = None
        self._prev_stats = self.restoreState()
        if self._prev_stats is None:
            cdnInfo = RackspaceContainerInfo(
                self._container,
                self._username, 
                self._api_key
            )
            self._stats = cdnInfo.getStats()
            stats = self._stats
        else:
            stats = self._prev_stats
        if stats is None:
            raise Exception("Undetermined error accessing stats.")
        
        if stats.has_key('rackspace_containersize'):
            graph = MuninGraph('Rackspace - Container Size', 'Rackspace',
                info='The total size of files contained in a Rackspace CDN container',
                vlabel='bytes', args='--base 1024 --lower-limit 0')
            graph.addField('size', 'size', draw='AREASTACK', type='GAUGE')
            self.appendGraph('rackspace_containersize', graph)
        
        if stats.has_key('rackspace_containercount'):
            graph = MuninGraph('Rackspace - Container Count', 'Rackspace',
                info='The total number of files contained in a Rackspace CDN container',
                vlabel='objects', args='--base 1000 --lower-limit 0')
            graph.addField('count', 'count', draw='AREASTACK', type='GAUGE')
            self.appendGraph('rackspace_containercount', graph)

    def retrieveVals(self):
        """
        Retrieve values for graphs.
        """
        if self._stats is None:
            cdnInfo = RackspaceContainerInfo(
                self._container,
                self._username, 
                self._api_key
            )
            stats = cdnInfo.getStats()
        else:
            stats = self._stats
        
        if stats is None:
            raise Exception("Undetermined error accessing stats.")
        
        self.saveState(stats)
        
        if self.hasGraph('rackspace_containersize'):
            self.setGraphVal(
                'rackspace_containersize',
                'size', 
                stats.get('rackspace_containersize')
            )
        
        if self.hasGraph('rackspace_containercount'):
            self.setGraphVal(
                'rackspace_containercount',
                'count', 
                stats.get('rackspace_containercount')
            )


def main():
    sys.exit(muninMain(MuninRackspacePlugin))


if __name__ == "__main__":
    main()
