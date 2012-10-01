#!/usr/bin/env python
"""lighttpdstats - Munin Plugin to monitor stats for Lighttpd Web Server.

Requirements
  - Access to Lighttpd Web Server server-status page.


Wild Card Plugin - No


Multigraph Plugin - Graph Structure
   - lighttpd_access
   - lighttpd_bytes
   - lighttpd_servers

   
Environment Variables
  host:           Lighttpd Web Server Host. (Default: 127.0.0.1)
  port:           Lighttpd Web Server Port. (Default: 80, SSL: 443)
  user:           User in case authentication is required for access to 
                  server-status page.
  password:       Password in case authentication is required for access 
                  to server-status page.
  statuspath:     Path for Lighttpd Web Server Status Page.
                  (Default: server-status)
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
    [lighttpdstats]
        env.exclude_graphs lighttpd_access,lighttpd_load

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=autoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.lighttpd import LighttpdInfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9.20"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninLighttpdPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring Lighttpd Web Server.

    """
    plugin_name = 'lighttpdstats'
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
        self._password = self.envGet('password')
        self._statuspath = self.envGet('statuspath')
        self._ssl = self.envCheckFlag('ssl', False)
        self._category = 'Lighttpd'
        
        if self.graphEnabled('lighttpd_access'):
            graph = MuninGraph('Lighttpd Web Server - Throughput (Requests / sec)', 
                self._category,
                info='Throughput in Requests per second for Lighttpd Web Server.',
                args='--base 1000 --lower-limit 0')
            graph.addField('reqs', 'reqs', draw='LINE2', type='DERIVE', min=0,
                info="Requests per second.")
            self.appendGraph('lighttpd_access', graph)
        
        if self.graphEnabled('lighttpd_bytes'):
            graph = MuninGraph('Lighttpd Web Server - Througput (bytes/sec)', 
                self._category,
                info='Throughput in bytes per second for Lighttpd Web Server.',
                args='--base 1024 --lower-limit 0')
            graph.addField('bytes', 'bytes', draw='LINE2', type='DERIVE', min=0)
            self.appendGraph('lighttpd_bytes', graph)
                
        if self.graphEnabled('lighttpd_servers'):
            graph = MuninGraph('Lighttpd Web Server - Servers', self._category,
                info='Server utilization stats for Lighttpd Web server.',
                args='--base 1000 --lower-limit 0')
            graph.addField('busy', 'busy', draw='AREASTACK', type='GAUGE',
                info="Number of busy servers.")
            graph.addField('idle', 'idle', draw='AREASTACK', type='GAUGE',
                info="Number of idle servers.")
            graph.addField('max', 'max', draw='LINE2', type='GAUGE',
                info="Maximum number of servers permitted.",
                colour='FF0000')
            self.appendGraph('lighttpd_servers', graph)
        
    def retrieveVals(self):
        """Retrieve values for graphs."""
        lighttpdInfo = LighttpdInfo(self._host, self._port,
                                self._user, self._password, 
                                self._statuspath, self._ssl)
        stats = lighttpdInfo.getServerStats()
        if self.hasGraph('lighttpd_access'):
            self.setGraphVal('lighttpd_access', 'reqs', stats['Total Accesses'])
        if self.hasGraph('lighttpd_bytes'):
            self.setGraphVal('lighttpd_bytes', 'bytes', 
                             stats['Total kBytes'] * 1000)
        if self.hasGraph('lighttpd_servers'):
            self.setGraphVal('lighttpd_servers', 'busy', stats['BusyServers'])
            self.setGraphVal('lighttpd_servers', 'idle', stats['IdleServers'])
            self.setGraphVal('lighttpd_servers', 'max', stats['MaxServers'])
            
    def autoconf(self):
        """Implements Munin Plugin Auto-Configuration Option.
        
        @return: True if plugin can be  auto-configured, False otherwise.
                 
        """
        lighttpdInfo = LighttpdInfo(self._host, self._port,
                                self._user, self._password, 
                                self._statuspath, self._ssl)
        return lighttpdInfo is not None


def main():
    sys.exit(muninMain(MuninLighttpdPlugin))


if __name__ == "__main__":
    main()
