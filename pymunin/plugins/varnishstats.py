#!/usr/bin/env python
"""varnishstats - Munin Plugin to monitor stats for Varnish Cache.


Requirements

  - Access to varnishstat executable for retrieving stats.


Wild Card Plugin - No


Multigraph Plugin - Graph Structure

    - varnish_client_conn
    - varnish_client_requests
    - varnish_backend_conn
    - varnish_backend_requests
    - varnish_traffic
    - varnish_workers
    - varnish_hits


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
__credits__ = []
__license__ = "GPL"
__version__ = "0.9.20"
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

        graph_name = 'varnish_client_conn'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('Varnish - Client Connections / sec',
                self._category,
                info='Client connections per second for Varnish Cache.',
                args='--base 1000 --lower-limit 0')
            graph.addField('client_conn', 'conn', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('client_conn'))
            graph.addField('client_drop', 'drop', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('client_drop'))
            graph.addField('client_req', 'reqs', draw='LINE2', type='DERIVE',
                           min=0, info=self._desc.get('client_req'))
            self.appendGraph(graph_name, graph)

        graph_name = 'varnish_backend_conn'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('Varnish - Backend Connections / sec',
                self._category,
                info='Connections per second from Varnish Cache to backends.',
                args='--base 1000 --lower-limit 0')
            graph.addField('backend_conn', 'backend_conn', draw='LINE2', type='DERIVE',
                           min=0, info=self._desc.get('backend_conn'))
            graph.addField('backend_fail', 'fail', draw='LINE2', type='DERIVE',
                           min=0, info=self._desc.get('backend_fail'))
            graph.addField('backend_reuse', 'reuse', draw='LINE2', type='DERIVE',
                           min=0, info=self._desc.get('backend_reuse'))
            self.appendGraph(graph_name, graph)

        graph_name = 'varnish_objects'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('Varnish - Objects',
                self._category,
                info='number of cached objects.',
                args='--base 1000 --lower-limit 0')
            graph.addField('n_object', 'objs', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('n_object'))
            graph.addField('n_vampireobject', 'vampire', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('n_vampireobject'))
            graph.addField('n_objectcore', 'core', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('n_objectcore'))
            graph.addField('n_objecthead', 'head', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('n_objecthead'))
            graph.addField('n_expired', 'expired', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('n_expired'))
            graph.addField('n_objoverflow', 'overflow', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('n_objoverflow'))
            self.appendGraph(graph_name, graph)

        graph_name = 'varnish_traffic'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('Varnish - Traffic (bytes/sec)',
                self._category,
                info='HTTP Header and Body traffic. '
                     '(TCP/IP overhead not included.)',
                args='--base 1000 --lower-limit 0')
            graph.addField('s_hdrbytes', 'header', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('s_hdrbytes'))
            graph.addField('s_bodybytes', 'body', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('s_bodybytes'))
            self.appendGraph(graph_name, graph)

        graph_name = 'varnish_threads'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('Varnish - Worker Threads',
                self._category,
                info='Number of worker threads.',
                args='--base 1000 --lower-limit 0')
            graph.addField('n_wrk', 'threads', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('n_wrk'))
            graph.addField('n_wrk_create', 'thrd-created', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('n_wrk_create'))
            graph.addField('n_wrk_failed', 'thrd-failed', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('n_wrk_failed'))
            self.appendGraph(graph_name, graph)

        graph_name = 'varnish_work_requests'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('Varnish - Work Requests',
                self._category,
                info='Number of requests being proccessed.',
                args='--base 1000 --lower-limit 0')
            graph.addField('n_wrk_queued', 'worker-queued', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('n_wrk_queued'))
            graph.addField('n_wrk_drop', 'worker-droped', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('n_wrk_drop'))
            self.appendGraph(graph_name, graph)

        graph_name = 'varnish_hits'
        if self.graphEnabled(graph_name):
            graph = MuninGraph('Varnish - Cache Hits vs. Misses',
                self._category,
                info='Number of Cache Hits and Misses per second.',
                args='--base 1000 --lower-limit 0')
            graph.addField('cache_hit', 'hit', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('cache_hit'))
            graph.addField('cache_hitpass', 'pass', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('cache_hitpass'))
            graph.addField('cache_miss', 'miss', draw='AREASTACK', type='DERIVE',
                           min=0, info=self._desc.get('cache_miss'))
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
