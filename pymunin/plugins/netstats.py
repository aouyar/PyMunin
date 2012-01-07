#!/usr/bin/python
"""netstats - Munin Plugin to monitor network stats.


Requirements
  - netstat command

Wild Card Plugin - No


Multigraph Plugin - Graph Structure
   - netstat_conn_status
   - netstat_conn_server


Environment Variables

  include_graphs:    Comma separated list of enabled graphs.
                     (All graphs enabled by default.)
  exclude_graphs:    Comma separated list of disabled graphs.
  list_server_ports: Comma separated list of Name:PortNumber tuples for services
                     that are to be monitored in the netstat_server_conn graph.
                     A service can be associated to multiple port numbers
                     separated by colon.

  Example:
    [netstats]
        env.include_graphs netstat_conn_server
        env.server_ports www:80:443,mysql:3306

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
         
        if self.graphEnabled('netstat_conn_status'):
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
            self.appendGraph('netstat_conn_status', graph)
            
        if self.graphEnabled('netstat_server_conn'):
            self._srv_dict = {}
            self._srv_list = []
            self._port_list = []
            for srv_str in self.envGetList('server_ports', '(\w+)(:\d+)+$'):
                elems = srv_str.split(':')
                if len(elems) > 1:
                    srv = elems[0]
                    ports = elems[1:]
                    self._srv_list.append(srv)
                    self._srv_dict[srv] = ports
                    self._port_list.extend(ports)      
            self._srv_list.sort()
            if len(self._srv_list) > 0:
                graph = MuninGraph('Network - Server Connections', 'Network', 
                                   info='Number of TCP connections to server ports.',
                                   args='--base 1000 --lower-limit 0')
                for srv in self._srv_list:
                    graph.addField(srv, srv, type='GAUGE', draw='AREA', 
                        info=('Number of connections for service %s on ports: %s' 
                              % (srv, ','.join(self._srv_dict[srv]))))
                self.appendGraph('netstat_conn_server', graph)

    def retrieveVals(self):
        """Retrieve values for graphs."""
        net_info = NetstatInfo()
        if self.hasGraph('netstat_conn_status'):
            stats = net_info.getTCPportConnStatus(include_listen=True)
            for fname in ('listen', 'established', 'syn_sent', 'syn_recv',
                          'fin_wait1', 'fin_wait2', 'time_wait', 
                          'close','close_wait', 'last_ack', 'closing', 
                          'unknown',):
                self.setGraphVal('netstat_conn_status', fname, 
                                 stats.get(fname,0))
        if self.hasGraph('netstat_conn_server'):
            stats = net_info.getTCPportConnCount(localport=self._port_list)
            for srv in self._srv_list:
                numconn = 0
                for port in self._srv_dict[srv]:
                    numconn += stats.get(port, 0)
                self.setGraphVal('netstat_conn_server', srv, numconn)


def main():
    sys.exit(muninMain(MuninNetstatsPlugin))


if __name__ == "__main__":
    main()
