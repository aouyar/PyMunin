#!/usr/bin/env python
"""redisstats - Munin Plugin to monitor stats for Redis Server.

Requirements


Wild Card Plugin - No


Multigraph Plugin - Graph Structure
    - redis_ping
    - redis_conn_client
    - redis_conn_rate
    - redis_cmd_rate
    - redis_memory
    - redis_memory_fragmentation
    - redis_cpu_util
    

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
        self._stats = self._serverInfo.getStats()
        self._stats['rtt'] = self._serverInfo.ping()
        
        for graph_name, graph_title, graph_info, graph_fields in (
            ('redis_ping', 'Ping Latency (secs)',
             'Round Trip Time in seconds for Redis Ping.',
             (('rtt', 'rtt', 'LINE2', 'GAUGE', 'Round trip time.'),)
            ),
            ('redis_conn_client', 'Active Client Connections',
             'Number of connections to Redis Server.',
             (('connected_clients', 'clients', 'AREA', 'GAUGE',
               'Number of clients connected to server.'),
              ('blocked_clients', 'blocked', 'LINE2', 'GAUGE',
               'Number of clients pending on a blocking call.'),)
            ),
            ('redis_conn_rate', 'Client Connections per Second',
             'Connections accepted / rejected per second by the Redis Server.',
             (('rejected_connections', 'reject', 'AREASTACK', 'DERIVE',
               'Number of connections rejected by the server.'),
              ('total_connections_received', 'accept', 'AREASTACK', 'DERIVE',
               'Number of connections accepted by the server.'),)
            ),
            ('redis_cmd_rate', 'Commands Processed per Second',
             'Number of commands processed per second by the Redis Server.',
             (('total_commands_processed', 'cmds', 'LINE2', 'DERIVE',
               'Number of commands processed by the Redis Server.'),)
            ),
            ('redis_memory', 'Memory Usage (bytes)', 'Memory usage of Redis Server.',
             (('used_memory_rss', 'rss', 'AREA', 'GAUGE',
               'Number of RAM (RSS) in bytes allocated to Redis by the OS.'),
              ('used_memory', 'mem', 'LINE2', 'GAUGE',
               'Total number memory in bytes allocated by Redis Allocator.'),)
            ),
            ('redis_memory_fragmentation', 'Memory Fragmentation Ratio',
             'Ratio between RSS and virtual memory use for Redis Server. '
             'Values much higher than 1 imply fragmentation. Values less '
             'than 1 imply that memory has been swapped out by OS.',
             (('mem_fragmentation_ratio', 'ratio', 'LINE2', 'GAUGE',
               'Ratio between RSS and virtual memory use.'),)
            ),
            ('redis_cpu_util', 'CPU Utilization',
             'Processor time utilized by Redis Server.',
             (('used_cpu_sys_children', 'child_sys', 'AREASTACK', 'DERIVE',
               'System CPU Time consumed by the background processes.'),
              ('used_cpu_user_children', 'child_user', 'AREASTACK', 'DERIVE',
               'User CPU Time consumed by the background processes.'),
              ('used_cpu_sys', 'srv_sys', 'AREASTACK', 'DERIVE',
               'System CPU Time consumed by the server.'),
              ('used_cpu_user', 'srv_user', 'AREASTACK', 'DERIVE',
               'User CPU Time consumed by the server.'),)
            ),
            ):
            if self.graphEnabled(graph_name):
                graph = MuninGraph("Redis - %s" % graph_title, self._category, 
                                   info=graph_info, 
                                   args='--base 1000 --lower-limit 0')
                for fname, flabel, fdraw, ftype, finfo in graph_fields:
                    graph.addField(fname, flabel, draw=fdraw, type=ftype, min=0,
                                   info=finfo)
                if graph.getFieldCount() > 0:
                    self.appendGraph(graph_name, graph)
            
    def retrieveVals(self):
        """Retrieve values for graphs."""
        for graph_name in self.getGraphList():
            for field_name in self.getGraphFieldList(graph_name):
                self.setGraphVal(graph_name, field_name, self._stats.get(field_name))
                        
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
