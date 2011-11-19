#!/usr/bin/python
"""netstats - Munin Plugin to monitor network stats.


Requirements
  - netstat command

Wild Card Plugin - No


Multigraph Plugin - Graph Structure
   - netstat_status


Environment Variables

  include_graphs: Comma separated list of enabled graphs.
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.

  Example:
    [netstats]
        env.include_graphs conn_status

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=noautoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.netstat import NetstatInfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninNetstatsPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring Network Stats.

    """
    plugin_name = 'netstats'
    isMultigraph = True

    def __init__(self, argv=(), env={}, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """     
        MuninPlugin.__init__(self, argv, env, debug)
         
        if self.graphEnabled('netstat_status'):
            graph = MuninGraph('Network - Connection Status', 'Network', 
                               info='TCP connection status stats.',
                               args='--base 1000 --lower-limit 0')
            for (fname, fdesc) in (
                ('listen', 'Socket listening for incoming connections.'),
                ('established', 'Socket with established connection.'),
                ('syn_sent', 'Socket actively attempting connection.'),
                ('syn_recv', 'Socket that has received a connection request'
                             ' from network.'),
                ('fin_wait1', 'Connection closed, and connection shutting down.'),
                ('fin_wait2', 'Connection is closed, and the socket is waiting'
                              ' for  a  shutdown from the remote end.'),
                ('time_wait', 'Socket is waiting after close '
                              'to handle packets still in the network.'),
                ('close', 'Socket is not being used.'),
                ('close_wait', 'The remote end has shut down, '
                               'waiting for the socket to close.'),
                ('last_ack', 'The remote end has shut down, and the socket'
                             ' is closed.  Waiting for acknowledgement.'),
                ('closing', 'Both  sockets are shut down'
                            ' but not all data is sent yet.'),
                ('unknown', 'Sockets with unknown state.'),
                ): 
                graph.addField(fname, fname, type='GAUGE', draw='AREA',
                               info=fdesc)
            self.appendGraph('netstat_status', graph)

    def retrieveVals(self):
        """Retrieve values for graphs."""
        net_info = NetstatInfo()
        if self.hasGraph('netstat_status'):
            stats = net_info.getTCPportConnStatus(include_listen=True)
            for fname in ('listen', 'established', 'syn_sent', 'syn_recv',
                          'fin_wait1', 'fin_wait2', 'time_wait', 
                          'close','close_wait', 'last_ack', 'closing', 
                          'unknown',):
                self.setGraphVal('netstat_status', fname, stats.get(fname,0))


if __name__ == "__main__":
    sys.exit(muninMain(MuninNetstatsPlugin))
