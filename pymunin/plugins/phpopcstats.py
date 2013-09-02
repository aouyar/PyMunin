#!/usr/bin/env python
"""phpopcstats - Munin Plugin for monitoring PHP Zend-OPCache.


Requirements

  - The PHP script opcinfo.php must be placed in the document root and have 
    access permissions from localhost.


Wild Card Plugin - No


Multigraph Plugin - Graph Structure

   - php_opc_memory
   - php_opc_key_status
   - php_opc_opcache_statistics
   - php_opc_opcache_hitrate

   
Environment Variables

  host:           Web Server Host. (Default: 127.0.0.1)
  port:           Web Server Port. (Default: 80, SSL: 443)
  user:           User in case authentication is required for access to 
                  APC Status page.
  password:       Password in case authentication is required for access to 
                  APC Status page.
  monpath:        APC status script path relative to Document Root.
                  (Default: opcinfo.php)
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
    [phpopcstats]
        env.exclude_graphs php_opc_key_status,php_opc_opcache_statistics

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=autoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.phpopc import OPCinfo

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
    plugin_name = 'phpopcstats'
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
        
        graph_name = 'php_opc_memory'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('PHP Zend OPCache - Memory Usage (bytes)', self._category,
                info='Memory usage of Zend OPCache in bytes.',
                total='Total Memory',
                args='--base 1024 --lower-limit 0')
            graph.addField('used_memory', 'Used Memory', draw='AREASTACK', 
                           type='GAUGE',colour='FFCC33')
            graph.addField('wasted_memory', 'Wasted Memory', draw='AREASTACK', 
                           type='GAUGE', colour='FF3333')
            graph.addField('free_memory', 'Free Memory', draw='AREASTACK',
                            type='GAUGE', colour='3790E8')

            self.appendGraph(graph_name, graph)
        
        graph_name = 'php_opc_opcache_statistics'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('PHP Zend OPCache - Opcache Statistics', self._category,
                info='Hits and Misses of Zend OPCache Opcache.',
                args='--base 1000 --lower-limit 0')
            graph.addField('hits', 'hits', draw='AREASTACK', 
                           type='DERIVE', min=0, colour='3790E8')
            graph.addField('misses', 'misses', draw='AREASTACK',
                           type='DERIVE', min=0, colour='FF3333')
            self.appendGraph(graph_name, graph)

        graph_name = 'php_opc_opcache_hitrate'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('PHP Zend OPCache - Hit Percent', self._category,
                info='Hit percent for PHP Zend OPCache.',
                vlabel='%', args='--base 1000 --lower-limit 0')
            graph.addField('opcache_hit_rate', 'Hit Percentage', draw='LINE2', type='GAUGE',
                           info='Hit Percentage', min=0)

            self.appendGraph(graph_name, graph)


        graph_name = 'php_opc_key_status'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('PHP Zend OPCache - Key Statistics', self._category,
                info='Key usage of Zend OPCache Opcache.',
                total='Total Keys',
                args='--base 1000 --lower-limit 0')
            graph.addField('num_cached_scripts', 'Used Key (for scripts)', draw='AREASTACK',
                           type='GAUGE', min=0, colour='FFCC33')
            graph.addField('num_wasted_keys', 'Wasted Key', draw='AREASTACK',
                           type='GAUGE', colour='FF3333')
            graph.addField('num_free_keys', 'Free Key', draw='AREASTACK',
                            type='GAUGE', colour='3790E8')

            self.appendGraph(graph_name, graph)
        
    def retrieveVals(self):
        """Retrieve values for graphs."""
        opcinfo = OPCinfo(self._host, self._port, self._user, self._password, 
                          self._monpath, self._ssl)
        stats = opcinfo.getAllStats()
        
        if self.hasGraph('php_opc_memory') and stats:
            mem = stats['memory_usage']
            keys = ('used_memory', 'wasted_memory', 'free_memory')
            map(lambda k:self.setGraphVal('php_opc_memory',k,mem[k]), keys)

        if self.hasGraph('php_opc_opcache_statistics') and stats:
            st = stats['opcache_statistics']
            self.setGraphVal('php_opc_opcache_statistics', 'hits', 
                             st['hits'])
            self.setGraphVal('php_opc_opcache_statistics', 'misses', 
                             st['misses'])

        if self.hasGraph('php_opc_opcache_hitrate') and stats:
            st = stats['opcache_statistics']
            self.setGraphVal('php_opc_opcache_hitrate', 'opcache_hit_rate',
                             st['opcache_hit_rate'])

        if self.hasGraph('php_opc_key_status') and stats:
            st = stats['opcache_statistics']
            wasted = st['num_cached_keys'] - st['num_cached_scripts']
            free = st['max_cached_keys'] - st['num_cached_keys']
            self.setGraphVal('php_opc_key_status', 'num_cached_scripts', st['num_cached_scripts'])
            self.setGraphVal('php_opc_key_status', 'num_wasted_keys', wasted)
            self.setGraphVal('php_opc_key_status', 'num_free_keys', free)
    
    def autoconf(self):
        """Implements Munin Plugin Auto-Configuration Option.
        
        @return: True if plugin can be  auto-configured, False otherwise.
                 
        """
        opcinfo = OPCinfo(self._host, self._port, self._user, self._password, 
                          self._monpath, self._ssl)
        return opcinfo is not None

            
def main():
    sys.exit(muninMain(MuninPHPZopPlugin))


if __name__ == "__main__":
    main()
