#!/usr/bin/env python
"""redisstats - Munin Plugin to monitor stats for Redis Server.

Requirements


Wild Card Plugin - No


Multigraph Plugin - Graph Structure
    - redis_ping
    - redis_conn_client
    - redis_memory
    

Environment Variables

  host:             Redis Server Host.  (127.0.0.1 by default.)
  port:             Redis Server Port.  (6379  by default.)
  db:               Redis DB ID. (0 by default.)
  password:         Redis Password (Optional)
  socket_timeout:   Redis Socket Timeout (Default: OS Default.)
  unix_socket_path: Socket File Path for UNIX Socket connections.
                    (Not required unless connection to Redis is through named socket.)
  include_graphs:   Comma separated list of enabled graphs.
                    (All graphs enabled by default.)
  exclude_graphs:   Comma separated list of disabled graphs.

Environment Variables for Multiple Instances of Plugin (Omitted by default.)
  instance_name:         Name of instance.
  instance_label:        Graph title label for instance.
                         (Default is the same as instance name.)
  instance_label_format: One of the following values:
                         - suffix (Default)
                         - prefix
                         - none 

  Example:
    [redisstats]
        env.exclude_graphs redis_ping

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=autoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.redisdb import RedisInfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9.20"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class RedisPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring Memcached Server.

    """
    plugin_name = 'redisstats'
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
        self._port = self.envGet('port')
        self._db = self.envGet('db')
        self._password = self.envGet('password')
        self._socket_timeout = self.envGet('socket_timeout', None, float)
        self._unix_socket_path = self.envGet('unix_socket_path')
        self._category = 'Redis'
        
        self._serverInfo = RedisInfo(self._host, self._port, self._db, 
                                     self._password, self._socket_timeout,
                                     self._unix_socket_path)
       
        if self.graphEnabled('redis_ping'):
            graph = MuninGraph('Redis - Ping Latency (secs)', self._category,
                info='Round Trip Time in seconds for Redis Ping.',
                args='--base 1000 --lower-limit 0')
            graph.addField('rtt', 'rtt', draw='LINE2', type='GAUGE')
            self.appendGraph('redis_ping', graph)
            
        if self.graphEnabled('redis_conn_client'):
            graph = MuninGraph('Redis - Client Connections', self._category,
                info='Number of connections to Redis Server.',
                args='--base 1000 --lower-limit 0')
            graph.addField('clients', 'clients', draw='AREA', type='GAUGE',
                           info='Total number of clients connected to server.')
            graph.addField('blocked', 'blocked', draw='LINE2', type='GAUGE',
                           info='Number of clients pending on a blocking call.')
            self.appendGraph('redis_conn_client', graph)
        
        if self.graphEnabled('redis_memory'):
            graph = MuninGraph('Redis - Memory Usage (bytes)', self._category,
                info='Memory (RAM) usage of Redis Server.',
                args='--base 1000 --lower-limit 0')
            graph.addField('mem', 'mem', draw='AREA', type='GAUGE',
                           info='Total number of bytes allocated by Redis Allocator.')
            graph.addField('rss', 'rss', draw='LINE2', type='GAUGE',
                           info='Number of bytes that Redis allocated as seen '
                                'by the operating system.')
            self.appendGraph('redis_memory', graph)
            
    def retrieveVals(self):
        """Retrieve values for graphs."""
        stats = self._serverInfo.getStats()
        if self.hasGraph('redis_ping'):
            rtt = self._serverInfo.ping()
            self.setGraphVal('redis_ping', 'rtt', rtt)
        if self.hasGraph('redis_conn_client'):
            self.setGraphVal('redis_conn_client', 'clients', 
                             stats.get('connected_clients'))
            self.setGraphVal('redis_conn_client', 'blocked', 
                             stats.get('blocked_clients'))
        if self.hasGraph('redis_memory'):
            self.setGraphVal('redis_memory', 'mem', stats.get('used_memory'))
            self.setGraphVal('redis_memory', 'rss', stats.get('used_memory_rss'))
                        
    def autoconf(self):
        """Implements Munin Plugin Auto-Configuration Option.
        
        @return: True if plugin can be  auto-configured, False otherwise.
                 
        """
        self._serverInfo.ping()
        return True


def main():
    sys.exit(muninMain(RedisPlugin))


if __name__ == "__main__":
    main()
