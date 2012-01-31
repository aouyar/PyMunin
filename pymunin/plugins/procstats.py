#!/usr/bin/env python
"""procstats - Munin Plugin to monitor process / thread stats.


Requirements
  - ps command

Wild Card Plugin - No


Multigraph Plugin - Graph Structure
   - proc_status
   - proc_priority
   - thread_status
   - thread_priority


Environment Variables

  include_graphs: Comma separated list of enabled graphs.
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.

  Example:
    [procstats]
        env.include_graphs proc_status

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=noautoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.process import ProcessInfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninProcStatsPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring Process Stats.

    """
    plugin_name = 'procstats'
    isMultigraph = True

    def __init__(self, argv=(), env={}, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """     
        MuninPlugin.__init__(self, argv, env, debug)

        for (prefix, title, desc) in (('proc', 'Processes', 'Number of processes'),
                                      ('thread', 'Threads', 'Number of threads')):
            graph_name = '%s_status' % prefix
            graph_title = '%s - Status' % title
            graph_desc = '%s discriminated by status.' % desc 
            if self.graphEnabled(graph_name):
                graph = MuninGraph(graph_title, 'Processes', info=graph_desc,
                    args='--base 1000 --lower-limit 0')
                for (fname, fdesc) in (
                    ('unint_sleep', 'Uninterruptable sleep. (Usually I/O)'),
                    ('stopped', 'Stopped, either by job control signal '
                     'or because it is being traced.'),
                    ('defunct', 'Defunct (zombie) process. '
                                'Terminated but not reaped by parent.'),
                    ('running', 'Running or runnable (on run queue).'),
                    ('sleep', 'Interruptable sleep. '
                              'Waiting for an event to complete.')): 
                    graph.addField(fname, fname, type='GAUGE', draw='AREA',
                                   info=fdesc)
                self.appendGraph(graph_name, graph)
                
            graph_name = '%s_prio' % prefix
            graph_title = '%s - Priority' % title
            graph_desc = '%s discriminated by priority.' % desc 
            if self.graphEnabled(graph_name):
                graph = MuninGraph(graph_title, 'Processes', info=graph_desc,
                    args='--base 1000 --lower-limit 0')
                for (fname, fdesc) in (
                    ('high', 'High priority.'),
                    ('low', 'Low priority.'),
                    ('norm', 'Normal priority.')):
                    graph.addField(fname, fname, type='GAUGE', draw='AREA',
                                   info=fdesc) 
                graph.addField('locked', 'locked', type='GAUGE', draw='LINE2',
                               info='Has pages locked into memory.')
                self.appendGraph(graph_name, graph)

    def retrieveVals(self):
        """Retrieve values for graphs."""
        proc_info = ProcessInfo()
        stats = {}
        for (prefix, is_thread) in (('proc', False), 
                                    ('thread', True)):
            graph_name = '%s_status' % prefix
            if self.hasGraph(graph_name):
                if not stats.has_key(prefix):
                    stats[prefix] = proc_info.getProcStatStatus(is_thread)
                for (fname, stat_key) in (
                    ('unint_sleep', 'uninterruptable_sleep'),
                    ('stopped', 'stopped'),
                    ('defunct', 'defunct'),
                    ('running', 'running'),
                    ('sleep', 'sleep')):
                    self.setGraphVal(graph_name, fname, 
                                     stats[prefix]['status'].get(stat_key))
            graph_name = '%s_prio' % prefix
            if self.hasGraph(graph_name):
                if not stats.has_key(prefix):
                    stats[prefix] = proc_info.getProcStatStatus(is_thread)
                for (fname, stat_key) in (
                    ('high', 'high'),
                    ('low', 'low'),
                    ('norm', 'norm'),
                    ('locked', 'locked_in_mem')):
                    self.setGraphVal(graph_name, fname, 
                                     stats[prefix]['prio'].get(stat_key))
        

def main():
    sys.exit(muninMain(MuninProcStatsPlugin))


if __name__ == "__main__":
    main()
