#!/usr/bin/env python
"""nginxstats - Munin Plugin to monitor stats for Nginx Web Server.

Requirements
  - Access to Nginx Web Server server-status page.


Wild Card Plugin - No


Multigraph Plugin - Graph Structure
   - nginx_activeconn
   - nginx_connections
   - nginx_requests
   - nginx_requestsperconn

   
Environment Variables

  host:           Nginx Web Server Host. (Default: 127.0.0.1)
  port:           Nginx Web Server Port. (Default: 80, SSL: 443)
  user:           User in case authentication is required for access to 
                  server-status page.
  password:       Password in case authentication is required for access 
                  to server-status page.
  statuspath:     Path for Nginx Web Server Status Page.
                  (Default: server-status)
  ssl:            Use SSL if yes. (Default: no)
  samples:        Number of samples to collect for calculating running averages.
                  (Six samples for 30 minute running average are stored by 
                  default.)
  include_graphs: Comma separated list of enabled graphs. 
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.

  Example:
    [nginxstats]
        env.include_graphs nginx_activeconn
        env.samples 3

"""
# Munin  - Magic Markers
#%# family=manual
#%# capabilities=noautoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.nginx import NginxInfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.8"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


defaultNumSamples = 6
"""Number of samples to store for calculating the running averages."""


class MuninNginxPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring Nginx Web Server.

    """
    plugin_name = 'nginxstats'
    isMultigraph = True

    def __init__(self, argv=(), env={}, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)
        
        self._host = self.envGet('host')
        self._port = self.envGet('port')
        self._user = self.envGet('user')
        self._password = self.envGet('password')
        self._statuspath = self.envGet('statuspath')
        self._ssl = self.envCheckFlag('ssl', False)
        self._numSamples = self.envGet('samples', defaultNumSamples)  
        
        if self.graphEnabled('nginx_activeconn'):
            graph = MuninGraph('Nginx - Active Connections', 
                'Nginx',
                info='Active connections to Nginx Web Server.',
                args='--base 1000 --lower-limit 0')
            graph.addField('proc', 'proc', draw='AREASTACK', type='GAUGE',
                info="Connections with Nginx reading request body, "
                      "processing request or writing response to client.")
            graph.addField('read', 'read', draw='AREASTACK', type='GAUGE',
                info="Connections with Nginx reading request headers.")
            graph.addField('wait', 'wait', draw='AREASTACK', type='GAUGE',
                info="Keep-alive connections with Nginx in wait state..")
            graph.addField('total', 'total', draw='LINE2', type='GAUGE',
                info="Total active connections.", colour='000000')
            self.appendGraph('nginx_activeconn', graph)
            
        if self.graphEnabled('nginx_connections'):
            graph = MuninGraph('Nginx - Connections per Second', 
                'Nginx',
                info='Connections per second to Nginx Web Server.',
                args='--base 1000 --lower-limit 0')
            graph.addField('handled', 'handled', draw='AREASTACK', type='DERIVE', 
                           min=0, info="Connections handled by Nginx per second.")
            graph.addField('nothandled', 'nothandled', draw='AREASTACK', type='DERIVE', 
                           min=0, info="Connections accepted, but not handled "
                                       "by Nginx per second.")
            self.appendGraph('nginx_connections', graph)
            
        if self.graphEnabled('nginx_requests'):
            graph = MuninGraph('Nginx - Requests per Second', 
                'Nginx',
                info='Requests per second to Nginx Web Server.',
                args='--base 1000 --lower-limit 0')
            graph.addField('requests', 'requests', draw='LINE2', type='DERIVE', 
                           min=0, info="Requests handled by Nginx per second.")
            self.appendGraph('nginx_requests', graph)
            
        if self.graphEnabled('nginx_requestsperconn'):
            graph = MuninGraph('Nginx - Requests per Connection', 
                'Nginx',
                info='Requests per handled connections for Nginx Web Server.',
                args='--base 1000 --lower-limit 0')
            graph.addField('requests', 'requests', draw='LINE2', type='GAUGE', 
                           min=0, info="Average number of requests per"
                                       " connections handled by Nginx.")
            self.appendGraph('nginx_requestsperconn', graph)
            
    def retrieveVals(self):
        """Retrieve values for graphs."""   
        nginxInfo = NginxInfo(self._host, self._port,
                                self._user, self._password, 
                                self._statuspath, self._ssl)
        stats = nginxInfo.getServerStats()
        if stats:
            if self.hasGraph('nginx_activeconn'):
                self.setGraphVal('nginx_activeconn', 'proc', stats['writing'])
                self.setGraphVal('nginx_activeconn', 'read', stats['reading'])
                self.setGraphVal('nginx_activeconn', 'wait', stats['waiting'])
                self.setGraphVal('nginx_activeconn', 'total', 
                                 stats['connections'])
            if self.hasGraph('nginx_connections'):
                self.setGraphVal('nginx_connections', 'handled', stats['handled'])
                self.setGraphVal('nginx_connections', 'nothandled', 
                                 stats['accepts'] - stats['handled'])
            if self.hasGraph('nginx_requests'):
                self.setGraphVal('nginx_requests', 'requests', stats['requests'])
            if self.hasGraph('nginx_requestsperconn'):
                curr_stats = (stats['handled'], stats['requests'])
                hist_stats = self.restoreState()
                if hist_stats:
                    prev_stats = hist_stats[0]
                else:
                    hist_stats = []
                    prev_stats = (0,0)
                conns = max(curr_stats[0] - prev_stats[0], 0)
                reqs = max(curr_stats[1] - prev_stats[1], 0)
                if conns > 0:
                    self.setGraphVal('nginx_requestsperconn', 'requests',
                                     float(reqs) / float(conns))
                else:
                    self.setGraphVal('nginx_requestsperconn', 'requests', 0)
                hist_stats.append(curr_stats)
                self.saveState(hist_stats[-self._numSamples:])
                

def main():
    sys.exit(muninMain(MuninNginxPlugin))

                
if __name__ == "__main__":
    main()
