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
    - redis_hits_misses
    - redis_keys_expired
    - redis_keys_evicted
    - redis_subscriptions
    - redis_rdb_changes
    - redis_rdb_dumptime
    - redis_aof_filesize
    - redis_aof_bufflen
    - redis_aof_rewrite_bufflen
    - redis_aof_rewritetime
    - redis_db_totals
    - redis_db_keys
    - redis_db_expires


Environment Variables

  host:             Redis Server Host. (127.0.0.1 by default.)
  port:             Redis Server Port. (6379  by default.)
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
__version__ = "0.9.21"
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
        
        cmd_list = []
        db_list = []
        for k in self._stats.keys():
            if k.startswith('cmdstat_'):
                cmd_list.append(k[len('cmdstat_'):])
            elif k.startswith('db'):
                db_list.append(k)
        db_list.sort()
        cmd_list.sort()
        graphs = [
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
            ('redis_conn_rate', 'Client Connections per Sec',
             'Connections accepted / rejected per second by the Redis Server.',
             (('rejected_connections', 'reject', 'AREASTACK', 'DERIVE',
               'Number of connections rejected by the server.'),
              ('total_connections_received', 'accept', 'AREASTACK', 'DERIVE',
               'Number of connections accepted by the server.'),)
            ),
            ('redis_cmd_rate', 'Commands Processed per Sec',
             'Number of commands processed per second by the Redis Server.',
             (('total_commands_processed', 'cmds', 'LINE2', 'DERIVE',
               'Number of commands processed by the Redis Server.'),)
            ),
            ('redis_memory', 'Memory Usage (bytes)', 'Memory usage of Redis Server.',
             (('used_memory_rss', 'rss', 'AREASTACK', 'GAUGE',
               'Resident Memory space (bytes) allocated to Redis by the OS for '
               'storing data.'),
              ('used_memory_lua', 'lua', 'AREASTACK', 'GAUGE',
               'Memory space (bytes) used by the Lua Engine.'),
              ('used_memory', 'mem', 'LINE2', 'GAUGE',
               'Memory space (bytes) allocated by Redis Allocator for storing data.'),)
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
             (('used_cpu_sys', 'srv_sys', 'AREASTACK', 'DERIVE',
               'System CPU Time consumed by the server.'),
              ('used_cpu_user', 'srv_user', 'AREASTACK', 'DERIVE',
               'User CPU Time consumed by the server.'),
              ('used_cpu_sys_children', 'child_sys', 'AREASTACK', 'DERIVE',
               'System CPU Time consumed by the background processes.'),
              ('used_cpu_user_children', 'child_user', 'AREASTACK', 'DERIVE',
               'User CPU Time consumed by the background processes.'),)
            ),
            ('redis_hits_misses', 'Hits/Misses per Sec',
             'Hits vs. misses in main dictionary lookup by Redis Server.',
             (('keyspace_hits', 'hit', 'AREASTACK', 'DERIVE',
               'Number of hits in main dictionary lookup.'),
              ('keyspace_misses', 'miss', 'AREASTACK', 'DERIVE',
               'Number of misses in main dictionary lookup.'),)
            ),
            ('redis_keys_expired', 'Expired Keys per Sec',
             'Number of keys expired by the Redis Server.',
             (('expired_keys', 'keys', 'LINE2', 'DERIVE',
               'Number of keys expired.'),)
            ),
            ('redis_keys_evicted', 'Evicted Keys per Sec',
             'Number of keys evicted by the Redis Server due to memory limits.',
             (('evicted_keys', 'keys', 'LINE2', 'DERIVE',
               'Number of keys evicted.'),)
            ),
            ('redis_subscriptions', 'Subscriptions',
             'Channels or patterns with subscribed clients.',
             (('pubsub_patterns', 'patterns', 'AREASTACK', 'GAUGE',
               'Global number of pub/sub patterns with client subscriptions.'),
              ('pubsub_channels', 'channels', 'AREASTACK', 'GAUGE',
               'Global number of pub/sub channels with client subscriptions.'),)
            ),
            ('redis_rdb_changes', 'RDB Pending Changes', 
             'Number of pending changes since last RDB Dump of Redis Server.',
             (('rdb_changes_since_last_save', 'changes', 'LINE2', 'GAUGE',
               'Number of changes since last RDB Dump.'),)
            ),
            ('redis_rdb_dumptime', 'RDB Dump Duration (sec)', 
             'Duration of the last RDB Dump of Redis Server in seconds.',
             (('rdb_last_bgsave_time_sec', 'duration', 'LINE2', 'GAUGE',
               'Duration of the last RDB Dump in seconds.'),)
            ),
        ]
        
        if self._stats.get('aof_enabled', 0) > 0:
            graphs.extend((
                ('redis_aof_filesize', 'AOF File Size (bytes)', 
                 'Redis Server AOF File Size in bytes.',
                 (('aof_current_size', 'size', 'LINE2', 'GAUGE',
                   'AOF File Size in bytes.'),)
                ),
                ('redis_aof_bufflen', 'AOF Buffer Length (bytes)', 
                 'Redis Server AOF Buffer Length in bytes.',
                 (('aof_buffer_length', 'len', 'LINE2', 'GAUGE',
                   'AOF Buffer Length in bytes.'),)
                ),
                ('redis_aof_rewrite_bufflen', 'AOF Rewrite Buffer Length (bytes)', 
                 'Redis Server AOF Rewrite Buffer Length in bytes.',
                 (('aof_rewrite_buffer_length', 'len', 'LINE2', 'GAUGE',
                   'AOF Rewrite Buffer Length in bytes.'),)
                ),
                ('redis_aof_rewritetime', 'AOF Rewrite Duration (sec)', 
                 'Duration of the last AOF Rewrite of Redis Server in seconds.',
                 (('aof_last_rewrite_time_sec', 'duration', 'AREA', 'GAUGE',
                   'Duration of the last AOF Rewrite in seconds.'),)
                ),             
            ))
        
        for graph_name, graph_title, graph_info, graph_fields in graphs:
            if self.graphEnabled(graph_name):
                graph = MuninGraph("Redis - %s" % graph_title, self._category, 
                                   info=graph_info, 
                                   args='--base 1000 --lower-limit 0')
                for fname, flabel, fdraw, ftype, finfo in graph_fields:
                    if self._stats.has_key(fname):
                        graph.addField(fname, flabel, draw=fdraw, type=ftype, 
                                       min=0, info=finfo)
                if graph.getFieldCount() > 0:
                    self.appendGraph(graph_name, graph)
        
        self._stats['db_total_keys'] = 0
        self._stats['db_total_expires'] = 0
        if self.graphEnabled('redis_db_totals'):
            for db in db_list:
                fname_keys = "%s_keys" % db
                fname_expires = "%s_expires" % db
                num_keys = self._stats[db].get('keys', 0)
                num_expires = self._stats[db].get('expires', 0)
                self._stats[fname_keys] = num_keys
                self._stats[fname_expires] = num_expires
                self._stats['db_total_keys'] += num_keys
                self._stats['db_total_expires'] += num_expires
            self._stats['db_total_persists'] = (self._stats['db_total_keys']
                                                - self._stats['db_total_expires'])
        
        graph_name = 'redis_db_totals'
        if self.graphEnabled(graph_name) and len(db_list) > 0:
            graph = MuninGraph("Redis - Number of Keys", self._category,
                               info="Number of keys stored by Redis Server",
                               args='--base 1000 --lower-limit 0')
            graph.addField('db_total_expires', 'expire', 'GAUGE', 'AREASTACK', 
                           min=0, info="Total number of keys with expiration.")
            graph.addField('db_total_persists', 'persist', 'GAUGE', 'AREASTACK', 
                           min=0, info="Total number of keys without expiration.")
            graph.addField('db_total_keys', 'total', 'GAUGE', 'LINE2', 
                           min=0, info="Total number of keys.", colour='000000')
            self.appendGraph(graph_name, graph)
                
        graph_name = 'redis_db_keys'
        if self.graphEnabled(graph_name) and len(db_list) > 0:
            graph = MuninGraph("Redis - Number of Keys per DB", self._category,
                               info="Number of keys stored in each DB by Redis Server",
                               args='--base 1000 --lower-limit 0')
            for db in db_list:
                fname = "%s_keys" % db
                graph.addField(fname, db, 'GAUGE', 'AREASTACK', min=0, 
                               info="Number of keys stored in %s." % db)
            self.appendGraph(graph_name, graph)
        
        graph_name = 'redis_db_expires'
        if self.graphEnabled(graph_name) and len(db_list) > 0:
            graph = MuninGraph("Redis - Number of Keys with Expiration per DB", 
                               self._category,
                               info="Number of keys stored in each DB by Redis Server",
                               args='--base 1000 --lower-limit 0')
            for db in db_list:
                fname = "%s_expires" % db
                graph.addField(fname, db, 'GAUGE', 'AREASTACK', min=0, 
                               info="Number of keys with expiration stored in %s." % db)
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
