#!/usr/bin/python
"""memcachedstats - Munin Plugin to monitor stats for Memcached Server.

Requirements


Wild Card Plugin - No


Multigraph Plugin - Graph Structure
    - memcached_connections
    - memcached_items
    - memcached_memory
    - memcached_traffic
    - memcached_connrate
    - memcached_reqrate
    - memcached_statget
    - memcached_statset
    - memcached_statdel
    - memcached_statcas
    - memcached_statincrdecr
    - memcached_statevict
    - memcached_statauth
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
        
        self._host = self.envGet('host')
        self._port = self.envGet('port')
        
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
        
        if self.graphEnabled('memcached_memory'):
            graph = MuninGraph('Memcached - Memory Usage', 'Memcached',
                info='Memory used to store items on Memcached Server in bytes.',
                args='--base 1024 --lower-limit 0')
            graph.addField('bytes', 'bytes', draw='LINE2', type='GAUGE')
            self.appendGraph('memcached_memory', graph)
        
        if self.graphEnabled('memcached_connrate'):
            graph = MuninGraph('Memcached - Throughput - Connections', 
                'Memcached',
                info='Connections per ${graph_period}.',
                args='--base 1000 --lower-limit 0')
            graph.addField('conn', 'conn', draw='LINE2', type='DERIVE', min=0)
            self.appendGraph('memcached_connrate', graph)
        
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
            
        if self.graphEnabled('memcached_statget'):
            graph = MuninGraph('Memcached - Stats - Get', 
                'Memcached',
                info='Get requests per ${graph_period}.',
                args='--base 1000 --lower-limit 0')
            graph.addField('hit', 'hit', draw='AREASTACK', type='DERIVE', min=0, 
                info='Get request hits per ${graph_period}.')
            graph.addField('miss', 'miss', draw='AREASTACK', type='DERIVE', min=0, 
                info='Get request misses per ${graph_period}.')
            graph.addField('total', 'total', draw='LINE2', type='DERIVE', min=0,
                colour='000000', 
                info='Total get requests per ${graph_period}.')
            self.appendGraph('memcached_statget', graph)
            
        if self.graphEnabled('memcached_statset'):
            graph = MuninGraph('Memcached - Stats - Set', 
                'Memcached',
                info='Set requests per ${graph_period}.',
                args='--base 1000 --lower-limit 0')
            graph.addField('hit', 'hit', draw='AREASTACK', type='DERIVE', min=0, 
                info='Set request hits per ${graph_period}.')
            graph.addField('miss', 'miss', draw='AREASTACK', type='DERIVE', min=0, 
                info='Set request misses per ${graph_period}.')
            graph.addField('total', 'total', draw='LINE2', type='DERIVE', min=0,
                colour='000000', 
                info='Total set requests per ${graph_period}.')
            self.appendGraph('memcached_statset', graph)
            
        if self.graphEnabled('memcached_statdel'):
            graph = MuninGraph('Memcached - Stats - Delete', 
                'Memcached',
                info='Delete requests per ${graph_period}.',
                args='--base 1000 --lower-limit 0')
            graph.addField('hit', 'hit', draw='AREASTACK', type='DERIVE', min=0, 
                info='Delete request hits per ${graph_period}.')
            graph.addField('miss', 'miss', draw='AREASTACK', type='DERIVE', min=0, 
                info='Delete request misses per ${graph_period}.')
            graph.addField('total', 'total', draw='LINE2', type='DERIVE', min=0,
                colour='000000', 
                info='Total delete requests per ${graph_period}.')
            self.appendGraph('memcached_statdel', graph)
        
        if self.graphEnabled('memcached_statcas'):
            graph = MuninGraph('Memcached - Stats - CAS', 
                'Memcached',
                info='CAS requests per ${graph_period}.',
                args='--base 1000 --lower-limit 0')
            graph.addField('hit', 'hit', draw='AREASTACK', type='DERIVE', min=0, 
                info='CAS request hits per ${graph_period}.')
            graph.addField('miss', 'miss', draw='AREASTACK', type='DERIVE', min=0, 
                info='CAS request misses per ${graph_period}.')
            graph.addField('badval', 'badval', draw='AREASTACK', 
                type='DERIVE', min=0, 
                info='CAS requests hits with bad value per ${graph_period}.')
            graph.addField('total', 'total', draw='LINE2', type='DERIVE', min=0,
                colour='000000', 
                info='Total CAS requests per ${graph_period}.')
            self.appendGraph('memcached_statcas', graph)
            
        if self.graphEnabled('memcached_statincrdecr'):
            graph = MuninGraph('Memcached - Stats - Incr / Decr', 
                'Memcached',
                info='Increment / decrement requests per ${graph_period}.',
                args='--base 1000 --lower-limit 0')
            graph.addField('incr_hit', 'incr_hit', draw='AREASTACK', 
                type='DERIVE', min=0, 
                info='Increment hits per ${graph_period}.')
            graph.addField('decr_hit', 'decr_hit', draw='AREASTACK', 
                type='DERIVE', min=0, 
                info='Decrement hits per ${graph_period}.')
            graph.addField('incr_miss', 'incr_miss', draw='AREASTACK', 
                type='DERIVE', min=0, 
                info='Increment misses per ${graph_period}.')
            graph.addField('decr_miss', 'decr_miss', draw='AREASTACK', 
                type='DERIVE', min=0, 
                info='Decrement misses per ${graph_period}.')
            graph.addField('total', 'total', draw='LINE2', type='DERIVE', min=0,
                colour='000000', 
                info='Total Increment / decrement requests per ${graph_period}.')
            self.appendGraph('memcached_statincrdecr', graph)
        if self.graphEnabled('memcached_statevict'):
            graph = MuninGraph('Memcached - Stats - Evictions', 
                'Memcached',
                info='Cache evictions and reclaims per ${graph_period}.',
                args='--base 1000 --lower-limit 0')
            graph.addField('evict', 'evict', draw='LINE2', type='DERIVE', min=0, 
                info='Items evicted from cache per ${graph_period}.')
            graph.addField('reclaim', 'reclaim', draw='LINE2', type='DERIVE', min=0, 
                info='Items stored over expired entries per ${graph_period}.')
            self.appendGraph('memcached_statevict', graph)
        if self.graphEnabled('memcached_statauth'):
            graph = MuninGraph('Memcached - Stats - Autentication', 
                'Memcached',
                info='Autentication requests per ${graph_period}.',
                args='--base 1000 --lower-limit 0')
            graph.addField('reqs', 'reqs', draw='LINE2', type='DERIVE', min=0, 
                info='Authentication requests per ${graph_period}.')
            graph.addField('errors', 'errors', draw='LINE2', type='DERIVE', min=0, 
                info='Authentication errors per ${graph_period}.')
            self.appendGraph('memcached_statauth', graph)
        
        if self.graphEnabled('memcached_hitpct'):
            graph = MuninGraph('Memcached - Hit Percent', 'Memcached',
                info='Hit percent for memcached requests.',
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
            stats['set_hits'] = stats.get('total_items')
            stats['set_misses'] = (stats.get('cmd_set') 
                                   - stats.get('total_items'))
            if self.hasGraph('memcached_connections'):
                self.setGraphVal('memcached_connections', 'conn', 
                                 stats.get('curr_connections'))
            if self.hasGraph('memcached_items'):
                self.setGraphVal('memcached_items', 'items', 
                                 stats.get('curr_items'))
            if self.hasGraph('memcached_memory'):
                self.setGraphVal('memcached_memory', 'bytes', 
                                 stats.get('bytes'))
            if self.hasGraph('memcached_connrate'):
                self.setGraphVal('memcached_connrate', 'conn', 
                                 stats.get('total_connections'))
            if self.hasGraph('memcached_traffic'):
                self.setGraphVal('memcached_traffic', 'rxbytes', 
                                 stats.get('bytes_read'))
                self.setGraphVal('memcached_traffic', 'txbytes', 
                                 stats.get('bytes_written'))
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
            if self.hasGraph('memcached_statget'):
                self.setGraphVal('memcached_statget', 'hit', 
                                 stats.get('get_hits'))
                self.setGraphVal('memcached_statget', 'miss', 
                                 stats.get('get_misses'))
                self.setGraphVal('memcached_statget', 'total', 
                                 sum([stats.get('get_hits'),
                                      stats.get('get_misses')]))
            if self.hasGraph('memcached_statset'):
                self.setGraphVal('memcached_statset', 'hit', 
                                 stats.get('set_hits'))
                self.setGraphVal('memcached_statset', 'miss', 
                                 stats.get('set_misses'))
                self.setGraphVal('memcached_statset', 'total', 
                                 sum([stats.get('set_hits'),
                                      stats.get('set_misses')]))
            if self.hasGraph('memcached_statdel'):
                self.setGraphVal('memcached_statdel', 'hit', 
                                 stats.get('delete_hits'))
                self.setGraphVal('memcached_statdel', 'miss', 
                                 stats.get('delete_misses'))
                self.setGraphVal('memcached_statdel', 'total', 
                                 sum([stats.get('delete_hits'),
                                      stats.get('delete_misses')]))
            if self.hasGraph('memcached_statcas'):
                self.setGraphVal('memcached_statcas', 'hit', 
                                 stats.get('cas_hits'))
                self.setGraphVal('memcached_statcas', 'miss', 
                                 stats.get('cas_misses'))
                self.setGraphVal('memcached_statcas', 'badval', 
                                 stats.get('cas_badval'))
                self.setGraphVal('memcached_statcas', 'total', 
                                 sum([stats.get('cas_hits'),
                                      stats.get('cas_misses'),
                                      stats.get('cas_badval')]))
            if self.hasGraph('memcached_statincrdecr'):
                self.setGraphVal('memcached_statincrdecr', 'incr_hit', 
                                 stats.get('incr_hits'))
                self.setGraphVal('memcached_statincrdecr', 'decr_hit', 
                                 stats.get('decr_hits'))
                self.setGraphVal('memcached_statincrdecr', 'incr_miss', 
                                 stats.get('incr_misses'))
                self.setGraphVal('memcached_statincrdecr', 'decr_miss', 
                                 stats.get('decr_misses'))
                self.setGraphVal('memcached_statincrdecr', 'total', 
                                 sum([stats.get('incr_hits'),
                                  stats.get('decr_hits'),
                                  stats.get('incr_misses'),
                                  stats.get('decr_misses')]))
                
            if self.hasGraph('memcached_statevict'):
                self.setGraphVal('memcached_statevict', 'evict', 
                                 stats.get('evictions'))
                self.setGraphVal('memcached_statevict', 'reclaim', 
                                 stats.get('reclaimed'))
            if self.hasGraph('memcached_statauth'):
                self.setGraphVal('memcached_statauth', 'reqs', 
                                 stats.get('auth_cmds'))
                self.setGraphVal('memcached_statauth', 'errors', 
                                 stats.get('auth_errors'))
            if self.hasGraph('memcached_hitpct'):
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

