#!/usr/bin/env python
"""rackspacestats - Munin Plugin to monitor stats for Rackspace Cloud..

Requirements
  - Valid username and api_key for accessing Rackspace Cloud.

Wild Card Plugin - No

Multigraph Plugin - Graph Structure
    - rackspace_cloudfiles_count
    - rackspace_cloudfiles_size

Environment Variables
  username:   Rackspace Cloud username.
  api_key:    Rackspace Cloud api_key.
  region:     Rackspace Auth Server Region.
              (US Auth Server is used by default.)
              Examples:
                - us: USA
                - uk: United Kingdom.
  servicenet: Enable (on) / disable (off) using the Rackspace ServiceNet for
              accessing the cloud. 
              (Disabled by default.)
  include_container: Comma separated list of containers to include in graphs.
                     (All enabled by default.)
  exclude_container: Comma separated list of containers to exclude from graphs.
  include_graphs:    Comma separated list of enabled graphs. 
                     (All graphs enabled by default.)
  exclude_graphs:    Comma separated list of disabled graphs.

Environment Variables for Multiple Instances of Plugin (Omitted by default.)
  instance_name:         Name of instance.
  instance_label:        Graph title label for instance.
                         (Default is the same as instance name.)
  instance_label_format: One of the following values:
                         - suffix (Default)
                         - prefix
                         - none 

  Example:
  
    [rackspacestats]
      env.username joe
      env.api_key ********************************
      env.region uk
      env.include_container test1,test3

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=autoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.rackspace import CloudFilesInfo

__author__ = "Ben Welsh"
__copyright__ = "Copyright 2012, Ben Welsh"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9.20"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninRackspacePlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring Rackspace Cloud Usage.
    
    """
    plugin_name = 'rackspacestats'
    isMultigraph = True
    isMultiInstance = True
    
    def __init__(self, argv=(), env=None, debug=False):
        """
        Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)
        
        self.envRegisterFilter('container', '^\w+$')
        self._username = self.envGet('username')
        self._api_key = self.envGet('api_key')
        self._region = self.envGet('region')
        self._servicenet = self.envCheckFlag('servicenet', False)
        self._category = 'Rackspace'
        
        self._fileInfo = CloudFilesInfo(username=self._username,
                                        api_key=self._api_key,
                                        region=self._region,
                                        servicenet=self._servicenet)
        self._fileContList = [name for name in self._fileInfo.getContainerList()
                                   if self.containerIncluded(name)]
        
        if self.graphEnabled('rackspace_cloudfiles_container_size'):
            graph = MuninGraph('Rackspace Cloud Files - Container Size (bytes)', 
                               self._category,
                info='The total size of files for each Rackspace Cloud Files container.',
                args='--base 1024 --lower-limit 0', autoFixNames=True)
            for contname in self._fileContList:
                    graph.addField(contname, contname, draw='AREASTACK', 
                                   type='GAUGE')
            self.appendGraph('rackspace_cloudfiles_container_size', graph)
        
        if self.graphEnabled('rackspace_cloudfiles_container_count'):
            graph = MuninGraph('Rackspace Cloud Files - Container Object Count', 
                               self._category,
                info='The total number of files for each Rackspace Cloud Files container.',
                args='--base 1024 --lower-limit 0', autoFixNames=True)
            for contname in self._fileContList:
                    graph.addField(contname, contname, draw='AREASTACK', 
                                   type='GAUGE')
            self.appendGraph('rackspace_cloudfiles_container_count', graph)

    def retrieveVals(self):
        """Retrieve values for graphs."""
        file_stats = self._fileInfo.getContainerStats()
        for contname in self._fileContList:
            stats = file_stats.get(contname)
            if stats is not None:
                if self.hasGraph('rackspace_cloudfiles_container_size'):
                    self.setGraphVal('rackspace_cloudfiles_container_size', contname,
                                     stats.get('size'))
                if self.hasGraph('rackspace_cloudfiles_container_count'):
                    self.setGraphVal('rackspace_cloudfiles_container_count', contname,
                                     stats.get('count'))
    
    def containerIncluded(self, name):
        """Utility method to check if database is included in graphs.
        
        @param name: Name of container.
        @return:     Returns True if included in graphs, False otherwise.
            
        """
        return self.envCheckFilter('container', name)


def main():
    sys.exit(muninMain(MuninRackspacePlugin))


if __name__ == "__main__":
    main()
