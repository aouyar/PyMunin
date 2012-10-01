#!/usr/bin/env python
"""phpapcstats - Munin Plugin for monitoring PHP APC Cache.

Requirements
  - The PHP script apcinfo.php must be placed in the document root and have 
    access permissions from localhost.


Wild Card Plugin - No


Multigraph Plugin - Graph Structure
   - php_apc_memory
   - php_apc_items
   - php_apc_reqs_filecache
   - php_apc_reqs_usercache
   - php_apc_expunge

   
Environment Variables

  host:           Web Server Host. (Default: 127.0.0.1)
  port:           Web Server Port. (Default: 80, SSL: 443)
  user:           User in case authentication is required for access to 
                  APC Status page.
  password:       Password in case authentication is required for access to 
                  APC Status page.
  monpath:        APC status script path relative to Document Root.
                  (Default: apcinfo.php)
  ssl:            Use SSL if yes. (Default: no)
  include_graphs: Comma separated list of enabled graphs. 
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.

Environment Variables for Multiple Instances of Plugin (Omitted by default.)
  instance_name:         Name of instance.
  instance_label:        Graph title label for instance.
                         (Default is the same as instance name.)
  instance_label_format: One of the following values:
                         - suffix (Default)
                         - prefix
                         - none 

  Example:
    [phpapcstats]
        env.exclude_graphs php_apc_items,php_apc_expunge

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=autoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.phpapc import APCinfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9.20"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninPHPapcPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring APC PHP Cache.

    """
    plugin_name = 'phpapcstats'
    isMultigraph = True
    isMultiInstance = True

    def __init__(self, argv=(), env=None, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)
        
        self._host = self.envGet('host')
        self._port = self.envGet('port', None, int)
        self._user = self.envGet('user')
        self._monpath = self.envGet('monpath')
        self._password = self.envGet('password')
        self._ssl = self.envCheckFlag('ssl', False)
        self._category = 'PHP'
        
        if self.graphEnabled('php_apc_memory'):
            graph = MuninGraph('PHP APC Cache - Memory Utilization (bytes)', self._category,
                info='Memory Utilization of PHP APC Cache in bytes.',
                args='--base 1000 --lower-limit 0')
            graph.addField('filecache', 'File Cache', draw='AREASTACK', 
                           type='GAUGE')
            graph.addField('usercache', 'User Cache', draw='AREASTACK', 
                           type='GAUGE')
            graph.addField('other', 'Other', draw='AREASTACK', 
                           type='GAUGE')
            graph.addField('free', 'Free', draw='AREASTACK', type='GAUGE')
            self.appendGraph('php_apc_memory', graph)
        
        if self.graphEnabled('php_apc_items'):
            graph = MuninGraph('PHP APC Cache - Cached Items', self._category,
                info='Number of items (files, user data) in PHP APC Cache.',
                args='--base 1000 --lower-limit 0')
            graph.addField('filecache', 'File Cache', draw='AREASTACK', 
                           type='GAUGE')
            graph.addField('usercache', 'User Cache', draw='AREASTACK', 
                           type='GAUGE')
            self.appendGraph('php_apc_items', graph)
        
        if self.graphEnabled('php_apc_reqs_filecache'):
            graph = MuninGraph('PHP APC - File Cache Requests per second', self._category,
                info='PHP APC File Cache Requests (Hits and Misses) per second.',
                args='--base 1000 --lower-limit 0')
            graph.addField('hits', 'hits', draw='AREASTACK', 
                           type='DERIVE', min=0)
            graph.addField('misses', 'misses', draw='AREASTACK',
                           type='DERIVE', min=0)
            graph.addField('inserts', 'inserts', draw='LINE2',
                           type='DERIVE', min=0)
            self.appendGraph('php_apc_reqs_filecache', graph)
        
        if self.graphEnabled('php_apc_reqs_usercache'):
            graph = MuninGraph('PHP APC - User Cache Requests per second', self._category,
                info='PHP APC User Cache Requests (Hits and Misses) per second.',
                args='--base 1000 --lower-limit 0')
            graph.addField('hits', 'hits', draw='AREASTACK', 
                           type='DERIVE', min=0)
            graph.addField('misses', 'misses', draw='AREASTACK',
                           type='DERIVE', min=0)
            graph.addField('inserts', 'inserts', draw='LINE2',
                           type='DERIVE', min=0)
            self.appendGraph('php_apc_reqs_usercache', graph)
            
        if self.graphEnabled('php_apc_expunge'):
            graph = MuninGraph('PHP APC - Cache Expunge Runs per second', self._category,
                info='PHP APC File and User Cache Expunge Runs per second.',
                args='--base 1000 --lower-limit 0')
            graph.addField('filecache', 'File Cache', draw='LINE2', 
                           type='DERIVE', min=0)
            graph.addField('usercache', 'User Cache', draw='LINE2', 
                           type='DERIVE', min=0)
            self.appendGraph('php_apc_expunge', graph)
        
    def retrieveVals(self):
        """Retrieve values for graphs."""
        apcinfo = APCinfo(self._host, self._port, self._user, self._password, 
                          self._monpath, self._ssl)
        stats = apcinfo.getAllStats()
        
        if self.hasGraph('php_apc_memory') and stats:
            filecache = stats['cache_sys']['mem_size']
            usercache = stats['cache_user']['mem_size']
            total = stats['memory']['seg_size'] * stats['memory']['num_seg']
            free = stats['memory']['avail_mem']
            other = total - free - filecache - usercache 
            self.setGraphVal('php_apc_memory', 'filecache', filecache)
            self.setGraphVal('php_apc_memory', 'usercache', usercache)
            self.setGraphVal('php_apc_memory', 'other', other)
            self.setGraphVal('php_apc_memory', 'free', free)
        if self.hasGraph('php_apc_items') and stats:
            self.setGraphVal('php_apc_items', 'filecache', 
                             stats['cache_sys']['num_entries'])
            self.setGraphVal('php_apc_items', 'usercache', 
                             stats['cache_user']['num_entries'])
        if self.hasGraph('php_apc_reqs_filecache') and stats:
            self.setGraphVal('php_apc_reqs_filecache', 'hits', 
                             stats['cache_sys']['num_hits'])
            self.setGraphVal('php_apc_reqs_filecache', 'misses', 
                             stats['cache_sys']['num_misses'])
            self.setGraphVal('php_apc_reqs_filecache', 'inserts', 
                             stats['cache_sys']['num_inserts'])
        if self.hasGraph('php_apc_reqs_usercache') and stats:
            self.setGraphVal('php_apc_reqs_usercache', 'hits', 
                             stats['cache_user']['num_hits'])
            self.setGraphVal('php_apc_reqs_usercache', 'misses', 
                             stats['cache_user']['num_misses'])
            self.setGraphVal('php_apc_reqs_usercache', 'inserts', 
                             stats['cache_user']['num_inserts'])
        if self.hasGraph('php_apc_expunge') and stats:
            self.setGraphVal('php_apc_expunge', 'filecache', 
                             stats['cache_sys']['expunges'])
            self.setGraphVal('php_apc_expunge', 'usercache', 
                             stats['cache_user']['expunges'])
    
    def autoconf(self):
        """Implements Munin Plugin Auto-Configuration Option.
        
        @return: True if plugin can be  auto-configured, False otherwise.
                 
        """
        apcinfo = APCinfo(self._host, self._port, self._user, self._password, 
                          self._monpath, self._ssl)
        return apcinfo is not None

            
def main():
    sys.exit(muninMain(MuninPHPapcPlugin))


if __name__ == "__main__":
    main()
