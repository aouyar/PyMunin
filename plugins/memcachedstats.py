#!/usr/bin/python
"""memcachedstats - Munin Plugin to monitor stats for Memcached Server.

Requirements


Wild Card Plugin - No


Multigraph Plugin - Graph Structure
   - memcached_connections
   - memcached_items
   - memcached_storage
   - memcached_traffic
   - memcached_connrate
   - memcached_reqrate
   - memcached_hitpct

Environment Variables
  host:           Memcached Server IP. (127.0.0.1 by default.)
  port:           Memcached Server Port (11211 by default.)
  include_graphs: Comma separated list of enabled graphs.
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.

  Example:
    [memcachedstats]
        env.exclude_graphs memcached_connrate

"""
# Munin  - Magic Markers
#%# family=manual
#%# capabilities=noautoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.memcached import MemcachedInfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninMemcachedPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring Memcached Server.

    """
    plugin_name = 'memcached'
    isMultigraph = True

    def __init__(self, argv = (), env = {}):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv: List of command line arguments.
        @param env:  Dictionary of environment variables.
        
        """
        MuninPlugin.__init__(self, argv, env)
        
        self._host = self._env.get('host')
        self._port = self._env.get('port')
        
        if self.graphEnabled('memcached_connections'):
            graph = MuninGraph('Memcached - Active Connections', 'Memcached',
                info='Active connections for Memcached Server.',
                args='--base 1000 --lower-limit 0')
            graph.addField('conn', 'conn', draw='LINE2', type='GAUGE')
            self.appendGraph('memcached_connections', graph)
        
        if self.graphEnabled('memcached_items'):
            graph = MuninGraph('Memcached - Items', 'Memcached',
                info='Current number of items stored on Memcached Server.',
                args='--base 1000 --lower-limit 0')
            graph.addField('items', 'items', draw='LINE2', type='GAUGE')
            self.appendGraph('memcached_items', graph)
        
        if self.graphEnabled('memcached_storage'):
            graph = MuninGraph('Memcached - Storage', 'Memcached',
                info='Current space used to store items on Memcached Server in bytes.',
                args='--base 1024 --lower-limit 0')
            graph.addField('bytes', 'bytes', draw='LINE2', type='GAUGE')
            self.appendGraph('memcached_storage', graph)
        
        if self.graphEnabled('memcached_traffic'):
            graph = MuninGraph('Memcached - Throughput - Network', 'Memcached',
                info='Bytes sent (+) / received (-)  by Memcached per ${graph_period}.',
                args='--base 1024 --lower-limit 0',
                vlabel='bytes in (-) / out (+) per second')
            graph.addField('rxbytes', 'bytes', draw='LINE2', type='DERIVE', 
                           min=0, graph=False)
            graph.addField('txbytes', 'bytes', draw='LINE2', type='DERIVE', 
                           min=0, negative='rxbytes')
            self.appendGraph('memcached_traffic', graph)
            
        if self.graphEnabled('memcached_connrate'):
            graph = MuninGraph('Memcached - Throughput - Connections', 
                'Memcached',
                info='Connections per ${graph_period}.',
                args='--base 1000 --lower-limit 0')
            graph.addField('conn', 'conn', draw='LINE2', type='DERIVE', min=0)
            self.appendGraph('memcached_connrate', graph)
            
        if self.graphEnabled('memcached_reqrate'):
            graph = MuninGraph('Memcached - Throughput - Request Rate', 
                'Memcached',
                info='Requests per ${graph_period}.',
                args='--base 1000 --lower-limit 0')
            graph.addField('set', 'set', draw='AREASTACK', type='DERIVE', min=0, 
                info='Set requests per ${graph_period}.')
            graph.addField('get', 'get', draw='AREASTACK', type='DERIVE', min=0, 
                info='Get requests per ${graph_period}.')
            graph.addField('del', 'del', draw='AREASTACK', type='DERIVE', min=0, 
                info='Delete requests per ${graph_period}.')
            graph.addField('cas', 'cas', draw='AREASTACK', type='DERIVE', min=0, 
                info='CAS requests per ${graph_period}.')
            graph.addField('incr', 'incr', draw='AREASTACK', type='DERIVE', min=0, 
                info='Increment requests per ${graph_period}.')
            graph.addField('decr', 'decr', draw='AREASTACK', type='DERIVE', min=0, 
                info='Decrement requests per ${graph_period}.')
            self.appendGraph('memcached_reqrate', graph)
            
        if self.graphEnabled('memcached_hitpct'):
            graph = MuninGraph('Memcached - Miss Percent', 'Memcached',
                info='Miss percent for memcached requests.',
                args='--base 1000 --lower-limit 0')
            graph.addField('set', 'set', draw='LINE2', type='GAUGE', 
                info='Stored items vs. total set requests.')
            graph.addField('get', 'get', draw='LINE2', type='GAUGE', 
                info='Get requests - hits vs total.')
            graph.addField('del', 'del', draw='LINE2', type='GAUGE', 
                info='Delete requests - hits vs. total.')
            graph.addField('cas', 'cas', draw='LINE2', type='GAUGE', 
                info='CAS requests - hits vs. total.')
            graph.addField('incr', 'incr', draw='LINE2', type='GAUGE', 
                info='Increment requests - hits vs. total.')
            graph.addField('decr', 'decr', draw='LINE2', type='GAUGE', 
                info='Decrement requests - hits vs. totals.')
            self.appendGraph('memcached_hitpct', graph)
            
    def retrieveVals(self):
        """Retrive values for graphs."""
        serverInfo = MemcachedInfo(self._host,  self._port)
        stats = serverInfo.getStats()
        if stats:
            if self.hasGraph('memcached_connections'):
                self.setGraphVal('memcached_connections', 'conn', 
                                 stats.get('curr_connections'))
            if self.hasGraph('memcached_items'):
                self.setGraphVal('memcached_items', 'items', 
                                 stats.get('curr_items'))
            if self.hasGraph('memcached_storage'):
                self.setGraphVal('memcached_storage', 'bytes', 
                                 stats.get('bytes'))
            if self.hasGraph('memcached_traffic'):
                self.setGraphVal('memcached_traffic', 'rxbytes', 
                                 stats.get('bytes_read'))
                self.setGraphVal('memcached_traffic', 'txbytes', 
                                 stats.get('bytes_written'))
            if self.hasGraph('memcached_connrate'):
                self.setGraphVal('memcached_connrate', 'conn', 
                                 stats.get('total_connections'))
            if self.hasGraph('memcached_reqrate'):
                self.setGraphVal('memcached_reqrate', 'set', 
                                 stats.get('cmd_set'))
                self.setGraphVal('memcached_reqrate', 'get', 
                                 stats.get('cmd_get'))
                self.setGraphVal('memcached_reqrate', 'del',
                    stats.get('delete_hits') + stats.get('delete_misses'))
                self.setGraphVal('memcached_reqrate', 'cas',
                                 stats.get('cas_hits') + stats.get('cas_misses') 
                                 + stats.get('cas_badval'))
                self.setGraphVal('memcached_reqrate', 'incr',
                    stats.get('incr_hits') + stats.get('incr_misses'))
                self.setGraphVal('memcached_reqrate', 'decr',
                    stats.get('decr_hits') + stats.get('decr_misses'))
            if self.hasGraph('memcached_hitpct'):
                stats['set_hits'] = stats.get('total_items')
                stats['set_misses'] = (stats.get('cmd_set') 
                                       - stats.get('total_items'))
                prev_stats = self.restoreState()
                for (field_name,  field_hits,  field_misses) in (
                        ('set',  'set_hits',  'set_misses'),
                        ('get',  'get_hits',  'get_misses'), 
                        ('del',  'delete_hits',  'delete_misses'), 
                        ('cas',  'cas_hits',  'cas_misses'), 
                        ('incr',  'incr_hits',  'incr_misses'), 
                        ('decr',  'decr_hits',  'decr_misses')
                    ):
                    val = float(100)
                    if prev_stats: 
                        hits = stats.get(field_hits) - prev_stats.get(field_hits)
                        misses = (stats.get(field_misses) 
                                  - prev_stats.get(field_misses))
                        total = hits + misses
                        if total > 0:
                            val = 100.0 * hits / total
                    self.setGraphVal('memcached_hitpct',  field_name, 
                                     round(val,  2))
                self.saveState(stats)



if __name__ == "__main__":
    sys.exit(muninMain(MuninMemcachedPlugin))

