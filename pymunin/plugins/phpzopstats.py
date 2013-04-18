#!/usr/bin/env python
"""phpzopstats - Munin Plugin for monitoring PHP APC Cache.


Requirements

  - The PHP script zopinfo.php must be placed in the document root and have 
    access permissions from localhost.


Wild Card Plugin - No


Multigraph Plugin - Graph Structure

   - php_zop_memory
   - php_zop_opcache_statistics
   - php_zop_key_status

   
Environment Variables

  host:           Web Server Host. (Default: 127.0.0.1)
  port:           Web Server Port. (Default: 80, SSL: 443)
  user:           User in case authentication is required for access to 
                  APC Status page.
  password:       Password in case authentication is required for access to 
                  APC Status page.
  monpath:        APC status script path relative to Document Root.
                  (Default: zopinfo.php)
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
    [phpzopstats]
        env.exclude_graphs php_zop_key

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=autoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.phpzop import ZOPinfo

__author__ = "Preston M."
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9.24"
__maintainer__ = "Preston M."
__email__ = "pentie at gmail.com"
__status__ = "Development"


class MuninPHPZopPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring APC PHP Cache.

    """
    plugin_name = 'phpzopstats'
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
        
        graph_name = 'php_zop_memory'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('PHP Zend Optimizor+ - Memory Usage (bytes)', self._category,
                info='Memory usage of Zend Optimizor+ in bytes.',
                args='--base 1024 --lower-limit 0')
            graph.addField('used_memory', 'Used Memory', draw='AREASTACK', 
                           type='GAUGE')
            graph.addField('wasted_memory', 'Wasted Memory', draw='AREASTACK', 
                           type='GAUGE')
            graph.addField('free_memory', 'Free Memory', draw='AREASTACK', type='GAUGE')
            graph.addField('total', 'total', draw='LINE2', type='GAUGE', colour='000000')

            self.appendGraph(graph_name, graph)
        
        graph_name = 'php_zop_opcache_statistics'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('PHP Zend Optimizor+ - Opcache Statistics', self._category,
                info='Hits and Misses of Zend Optimizor+ Opcache.',
                args='--base 1000 --lower-limit 0')
            graph.addField('hits', 'hits', draw='AREASTACK', 
                           type='DERIVE', min=0)
            graph.addField('misses', 'misses', draw='AREASTACK',
                           type='DERIVE', min=0)
            self.appendGraph(graph_name, graph)

        graph_name = 'php_zop_key_status'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('PHP Zend Optimizor+ - Key Statistics', self._category,
                info='Key usage of Zend Optimizor+ Opcache.',
                args='--base 1000 --lower-limit 0')
            graph.addField('max_cached_keys', 'Max Cached Keys', draw='AREASTACK', 
                           type='DERIVE', min=0)
            graph.addField('num_cached_keys', 'Cached Keys', draw='AREASTACK',
                           type='DERIVE', min=0)
            self.appendGraph(graph_name, graph)
        
    def retrieveVals(self):
        """Retrieve values for graphs."""
        zopinfo = ZOPinfo(self._host, self._port, self._user, self._password, 
                          self._monpath, self._ssl)
        stats = zopinfo.getAllStats()
        
        if self.hasGraph('php_zop_memory') and stats:
            mem = stats['memory_usage']
            self.setGraphVal('php_zop_memory', 'used_memory', mem['used_memory'])
            self.setGraphVal('php_zop_memory', 'wasted_memory', mem['wasted_memory'])
            self.setGraphVal('php_zop_memory', 'free_memory', mem['free_memory'])

            self.setGraphVal('php_zop_memory', 'total',
                    sum((mem['used_memory'], mem['wasted_memory'], mem['free_memory'])))

        if self.hasGraph('php_zop_opcache_statistics') and stats:
            st = stats['opcache_statistics']
            self.setGraphVal('php_zop_opcache_statistics', 'hits', 
                             st['hits'])
            self.setGraphVal('php_zop_opcache_statistics', 'misses', 
                             st['misses'])

        if self.hasGraph('php_zop_key_status') and stats:
            st = stats['opcache_statistics']
            self.setGraphVal('php_zop_key_status', 'max_cached_keys', 
                             st['max_cached_keys'])
            self.setGraphVal('php_zop_key_status', 'num_cached_keys', 
                             st['num_cached_keys'])
    
    def autoconf(self):
        """Implements Munin Plugin Auto-Configuration Option.
        
        @return: True if plugin can be  auto-configured, False otherwise.
                 
        """
        zopinfo = ZOPinfo(self._host, self._port, self._user, self._password, 
                          self._monpath, self._ssl)
        return zopinfo is not None

            
def main():
    sys.exit(muninMain(MuninPHPZopPlugin))


if __name__ == "__main__":
    main()
