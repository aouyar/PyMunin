#!/usr/bin/env python
"""varnishstats - Munin Plugin to monitor stats for Varnish Cache.


Requirements

  - Access to varnishstat executable for retrieving stats.


Wild Card Plugin - No


Multigraph Plugin - Graph Structure

    - varnish_requests
    - varnish_hits
    - varnish_client_conn
    - varnish_backend_conn
    - varnish_traffic
    - varnish_workers
    - varnish_work_queue
    - varnish_memory
    - varnish_expire_purge


Environment Variables

  instance:       Name  of the Varnish Cache instance.
                  (Defaults to hostname.) 
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
    [varnishstats]
        env.exclude_graphs varnish_workers

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=autoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.varnish import VarnishInfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = ["Preston Mason (https://github.com/pentie)",]
__license__ = "GPL"
__version__ = "0.9.22"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninVarnishPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring Varnish Cache.

    """
    plugin_name = 'varnishstats'
    isMultigraph = True
    isMultiInstance = True

    def __init__(self, argv=(), env=None, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)
        
        self._instance = self.envGet('instance')
        self._category = 'Varnish'
        varnish_info = VarnishInfo(self._instance)
        self._stats = varnish_info.getStats()
        self._desc = varnish_info.getDescDict()
        
        graph_name = 'varnish_requests'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('Varnish - Client/Backend Requests / sec', 
                self._category,
                info='Number of client and backend requests per second for Varnish Cache.',
                args='--base 1000 --lower-limit 0')
            for flabel in ('client', 'backend',):
                fname = '%s_req' % flabel
                finfo = self._desc.get(fname, '')
                graph.addField(fname, flabel, draw='LINE2', type='DERIVE', 
                               min=0, info=finfo)
            self.appendGraph(graph_name, graph)
        
        graph_name = 'varnish_hits'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('Varnish - Cache Hits vs. Misses (%)', 
                self._category,
                info='Number of Cache Hits and Misses per second.',
                args='--base 1000 --lower-limit 0')
            for flabel, fname in (('hit', 'cache_hit'), 
                                  ('pass', 'cache_hitpass'),
                                  ('miss', 'cache_miss')):
                finfo = self._desc.get(fname, '')
                graph.addField(fname, flabel, draw='AREASTACK', type='DERIVE', 
                               min=0, info=finfo)
            self.appendGraph(graph_name, graph)
        
        graph_name = 'varnish_client_conn'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('Varnish - Client Connections / sec', 
                self._category,
                info='Client connections per second for Varnish Cache.',
                args='--base 1000 --lower-limit 0')
            for flabel in ('conn', 'drop',):
                fname = 'client_%s' % flabel
                finfo = self._desc.get(fname, '') 
                graph.addField(fname, flabel, draw='AREASTACK', type='DERIVE', 
                               min=0, info=finfo)
            self.appendGraph(graph_name, graph)
        
        graph_name = 'varnish_backend_conn'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('Varnish - Backend Connections / sec', 
                self._category,
                info='Connections per second from Varnish Cache to backends.',
                args='--base 1000 --lower-limit 0')
            for flabel in ('conn', 'reuse', 'busy', 'fail', 'retry', 'unhealthy',):
                fname = 'backend_%s' % flabel
                finfo = self._desc.get(fname, '')
                graph.addField(fname, flabel, draw='AREASTACK', type='DERIVE', 
                               min=0, info=finfo)
            self.appendGraph(graph_name, graph)
            
        graph_name = 'varnish_traffic'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('Varnish - Traffic (bytes/sec)', 
                self._category,
                info='HTTP Header and Body traffic. '
                     '(TCP/IP overhead not included.)',
                args='--base 1024 --lower-limit 0')
            for flabel, fname in (('header', 's_hdrbytes'), 
                                  ('body', 's_bodybytes'),):
                finfo = self._desc.get(fname, '')
                graph.addField(fname, flabel, draw='AREASTACK', type='DERIVE', 
                           min=0, info=self._desc.get('s_hdrbytes'))
            self.appendGraph(graph_name, graph)

        graph_name = 'varnish_workers'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('Varnish - Worker Threads', 
                self._category,
                info='Number of worker threads.',
                args='--base 1000 --lower-limit 0')
            graph.addField('n_wrk', 'req', draw='LINE2', type='GAUGE', 
                           min=0, info=self._desc.get('n_wrk'))
            self.appendGraph(graph_name, graph)
            
        graph_name = 'varnish_work_queue'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('Varnish - Queued/Dropped Work Requests / sec', 
                self._category,
                info='Requests queued for waiting for a worker thread to become '
                     'available and requests dropped because of overflow of queue.',
                args='--base 1000 --lower-limit 0')
            for flabel, fname in (('queued', 'n_wrk_queued'), 
                                  ('dropped', 'n_wrk_drop')):
                finfo = self._desc.get(fname, '')
                graph.addField(fname, flabel, draw='LINE2', type='DERIVE', 
                               min=0, info=finfo)
            self.appendGraph(graph_name, graph)
            
        graph_name = 'varnish_memory'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('Varnish - Cache Memory Usage (bytes)', 
                self._category,
                info='Varnish cache memory usage in bytes.',
                args='--base 1000 --lower-limit 0')
            for flabel, fname in (('used', 'SMA.s0.g_bytes'), 
                                  ('free', 'SMA.s0.g_space')):
                finfo = self._desc.get(fname, '')
                graph.addField(fname, flabel, draw='AREASTACK', type='GAUGE', 
                               min=0, info=finfo)
            self.appendGraph(graph_name, graph)
            
        graph_name = 'varnish_expire_purge'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('Varnish - Expired/Purged Objects / sec', 
                self._category,
                info='Expired objects and LRU purged objects per second.',
                args='--base 1000 --lower-limit 0')
            for flabel, fname in (('expire', 'n_expired'), 
                                  ('purge', 'n_lru_nuked')):
                finfo = self._desc.get(fname, '')
                graph.addField(fname, flabel, draw='LINE2', type='DERIVE', 
                               min=0, info=finfo)
            self.appendGraph(graph_name, graph)
        
    def retrieveVals(self):
        """Retrieve values for graphs."""
        for graph_name in  self.getGraphList():
            for field_name in self.getGraphFieldList(graph_name):
                self.setGraphVal(graph_name, field_name, 
                                 self._stats.get(field_name))
    
    def autoconf(self):
        """Implements Munin Plugin Auto-Configuration Option.
        
        @return: True if plugin can be  auto-configured, False otherwise.
                 
        """
        return len(self._stats) > 0


def main():
    sys.exit(muninMain(MuninVarnishPlugin))


if __name__ == "__main__":
    main()
