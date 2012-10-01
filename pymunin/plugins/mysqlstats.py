#!/usr/bin/env python
"""mysqlstats - Munin Plugin to monitor stats for MySQL Database Server.

Requirements
  - Access permissions for MySQL Database.


Wild Card Plugin - No


Multigraph Plugin - Graph Structure
    - mysql_connections
    - mysql_traffic
    - mysql_slowqueries
    - mysql_rowmodifications
    - mysql_rowreads
    - mysql_tablelocks
    - mysql_threads
    - mysql_proc_states
    - mysql_proc_db
    - mysql_commits_rollbacks
    - mysql_qcache_memory
    - mysql_qcache_hits
    - mysql_qcache_prunes
    - mysql_myisam_key_buffer_util
    - mysql_myisam_key_read_reqs
    - mysql_innodb_buffer_pool_util
    - mysql_innodb_buffer_pool_activity
    - mysql_innodb_buffer_pool_read_reqs
    - mysql_innodb_row_ops


Environment Variables

  host:           MySQL Server IP. 
                  (Defaults to UNIX socket if not provided.)
  port:           MySQL Server Port
                  (Defaults to 3306 for network connections.)
  database:       MySQL Database
  user:           Database User Name
  password:       Database User Password
  include_engine: Comma separated list of storage engines to include graphs.
                  (All enabled by default.)
  exclude_engine: Comma separated list of storage engines to exclude from graphs.
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
    [mysqlstats]
        user root
        env.exclude_graphs mysql_threads
        env.include_engine innodb

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=autoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.mysql import MySQLinfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = ["Kjell-Magne Oierud (kjellm at GitHub)"]
__license__ = "GPL"
__version__ = "0.9.20"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninMySQLplugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring MySQL Database Server.

    """
    plugin_name = 'pgstats'
    isMultigraph = True
    isMultiInstance = True

    def __init__(self, argv=(), env=None, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)
        
        self.envRegisterFilter('engine', '^\w+$')
        
        self._host = self.envGet('host')
        self._port = self.envGet('port', None, int)
        self._database = self.envGet('database')
        self._user = self.envGet('user')
        self._password = self.envGet('password')
        self._category = 'MySQL'
        
        self._engines = None
        self._genStats = None
        self._genVars = None
        self._dbList = None
        self._dbconn = MySQLinfo(self._host, self._port, self._database, 
                              self._user, self._password)
        
        if self.graphEnabled('mysql_connections'):
            graph = MuninGraph('MySQL - Connections per second', 
                self._category,
                info='MySQL Server new and aborted connections per second.',
                args='--base 1000 --lower-limit 0')
            graph.addField('conn', 'conn', draw='LINE2', 
                type='DERIVE', min=0,
                info='The number of connection attempts to the MySQL server.')
            graph.addField('abort_conn', 'abort_conn', draw='LINE2', 
                type='DERIVE', min=0,
                info='The number of failed attempts to connect to the MySQL server.')
            graph.addField('abort_client', 'abort_client', draw='LINE2', 
                type='DERIVE', min=0,
                info='The number of connections that were aborted, because '
                     'the client died without closing the connection properly.')
            self.appendGraph('mysql_connections', graph)
        
        if self.graphEnabled('mysql_traffic'):
            graph = MuninGraph('MySQL - Network Traffic (bytes/sec)', 
                self._category,
                info='MySQL Server Network Traffic in bytes per second.',
                args='--base 1000 --lower-limit 0',
                vlabel='bytes in (-) / out (+) per second')
            graph.addField('rx', 'bytes', draw='LINE2', type='DERIVE', 
                           min=0, graph=False)
            graph.addField('tx', 'bytes', draw='LINE2', type='DERIVE', 
                           min=0, negative='rx',
                    info="Bytes In (-) / Out (+) per second.")
            self.appendGraph('mysql_traffic', graph)
            
        if self.graphEnabled('mysql_slowqueries'):
            graph = MuninGraph('MySQL - Slow Queries per second', 
                self._category,
                info='The number of queries that have taken more than '
                     'long_query_time seconds.',
                args='--base 1000 --lower-limit 0')
            graph.addField('queries', 'queries', draw='LINE2', 
                           type='DERIVE', min=0)
            self.appendGraph('mysql_slowqueries', graph)
            
        if self.graphEnabled('mysql_rowmodifications'):
            graph = MuninGraph('MySQL - Row Insert, Delete, Updates per second', 
                self._category,
                info='MySQL Server Inserted, Deleted, Updated Rows per second.',
                args='--base 1000 --lower-limit 0')
            graph.addField('insert', 'insert', draw='AREASTACK', 
                type='DERIVE', min=0,
                info='The number of requests to insert a rows into tables.')
            graph.addField('update', 'update', draw='AREASTACK', 
                type='DERIVE', min=0,
                info='The number of requests to update a rows in a tables.')
            graph.addField('delete', 'delete', draw='AREASTACK', 
                type='DERIVE', min=0,
                info='The number of requests to delete rows from tables.')
            self.appendGraph('mysql_rowmodifications', graph)
            
        if self.graphEnabled('mysql_rowreads'):
            graph = MuninGraph('MySQL - Row Reads per second', 
                self._category,
                info='MySQL Server Row Reads per second.',
                args='--base 1000 --lower-limit 0')
            for (field, desc) in (('first', 
                                   'Requests to read first entry in index.'),
                                  ('key', 
                                   'Requests to read a row based on a key.'),
                                  ('next', 
                                   'Requests to read the next row in key order.'),
                                  ('prev', 
                                   'Requests to read the previous row in key order.'),
                                  ('rnd', 
                                   'Requests to read a row based on a fixed position.'),
                                  ('rnd_next', 
                                   'Requests to read the next row in the data file.'),):
                graph.addField(field, field, draw='AREASTACK', 
                    type='DERIVE', min=0, info=desc)
            self.appendGraph('mysql_rowreads', graph)
            
        if self.graphEnabled('mysql_tablelocks'):
            graph = MuninGraph('MySQL - Table Locks per second', 
                self._category,
                info='MySQL Server Table Locks per second.',
                args='--base 1000 --lower-limit 0')
            graph.addField('waited', 'waited', draw='AREASTACK', 
                type='DERIVE', min=0,
                info='The number of times that a request for a table lock '
                     'could not be granted immediately and a wait was needed.')
            graph.addField('immediate', 'immediate', draw='AREASTACK', 
                type='DERIVE', min=0,
                info='The number of times that a request for a table lock '
                     'could be granted immediately.')
            self.appendGraph('mysql_tablelocks', graph)
        
        if self.graphEnabled('mysql_threads'):
            graph = MuninGraph('MySQL - Threads', 
                self._category,
                info='Number of active and idle threads for MySQL Server.',
                args='--base 1000 --lower-limit 0')
            graph.addField('running', 'running', draw='AREASTACK', type='GAUGE', 
                info="Number of threads executing queries.")
            graph.addField('idle', 'idle', draw='AREASTACK', type='GAUGE', 
                info="Number of idle threads with connected clients.")
            graph.addField('cached', 'cached', draw='AREASTACK', type='GAUGE', 
                info="Number of cached threads without connected clients.")
            graph.addField('total', 'total', draw='LINE2', type='GAUGE', 
                           colour='000000',
                           info="Total number of threads.")
            self.appendGraph('mysql_threads', graph)
            
        if self.graphEnabled('mysql_proc_status'):
            graph = MuninGraph('MySQL - Process Status', 
                self._category,
                info='Number of threads discriminated by process status.',
                args='--base 1000 --lower-limit 0')
            for (field, label, desc) in (
                ('locked', 'locked', 
                 'The query is locked by another query.'),
                ('sending_data', 'sending', 
                 'The thread is processing rows for a SELECT statement and also'
                 ' is sending data to the client.'),
                ('updating', 'updating',
                 'The thread is searching for rows to update and is updating them.'),
                ('sorting_result', 'sorting',
                 'For a SELECT statement, this is similar to Creating sort'
                 ' index, but for non-temporary tables.'),
                ('closing_tables', 'closing',
                 'The thread is flushing the changed table data to disk and'
                 ' closing the used tables.'),
                ('copying_to_tmp_table', 'copying',
                 'The thread is processing an ALTER TABLE statement. This state'
                 ' occurs after the table with the new structure has been'
                 ' created but before rows are copied into it.'), 
                ('preparing', 'preparing',
                 'This state occurs during query optimization.'),
                ('statistics', 'statistics',
                 'The server is calculating statistics to develop a query'
                 ' execution plan. If a thread is in this state for a long'
                 ' time, the server is probably disk-bound performing other work.'),
                ('reading_from_net', 'net_read',
                 'The server is reading a packet from the network.'),
                ('writing_to_net', 'net_write',
                 'The server is writing a packet to the network.'),
                ('login', 'login',
                 'The initial state for a connection thread until the client'
                 ' has been authenticated successfully.'),
                ('init', 'init',
                 'This occurs before the initialization of ALTER TABLE, DELETE,'
                 ' INSERT, SELECT, or UPDATE statements.'),
                ('end', 'end',
                 'This occurs at the end but before the cleanup of ALTER TABLE,'
                 ' CREATE VIEW, DELETE, INSERT, SELECT, or UPDATE statements.'),
                ('freeing_items', 'freeing',
                 'The thread has executed a command. This state is usually'
                 ' followed by cleaning up.'),
                ('other', 'other',
                 'Other valid state.'),
                ('unknown', 'unknown',
                 'State not recognized by the monitoring application.'),
                ('idle', 'idle',
                 'Idle threads.'),):
                graph.addField(field, label, draw='AREASTACK', type='GAUGE', 
                               info=desc)
            self.appendGraph('mysql_proc_status', graph)
        
        if self.graphEnabled('mysql_proc_db'):
            if self._dbList is None:
                self._dbList = self._dbconn.getDatabases()
                self._dbList.sort()
            graph = MuninGraph('MySQL - Processes per Database', 
                self._category,
                info='Number of Threads discriminated by database.',
                args='--base 1000 --lower-limit 0', autoFixNames=True)
            for db in self._dbList:
                graph.addField(db, db, draw='AREASTACK', type='GAUGE', 
                info="Number of threads attending connections for database %s." % db)
            self.appendGraph('mysql_proc_db', graph)
                
        if self.graphEnabled('mysql_commits_rollbacks'):
            graph = MuninGraph('MySQL - Commits and Rollbacks', 
                self._category,
                info='MySQL Server Commits and Rollbacks per second.',
                args='--base 1000 --lower-limit 0')
            graph.addField('commit', 'commit', draw='LINE2', 
                type='DERIVE', min=0,
                info='The number of commits per second.')
            graph.addField('rollback', 'rollback', draw='LINE2', 
                type='DERIVE', min=0,
                info='The number of rollbacks per second.')
            self.appendGraph('mysql_commits_rollbacks', graph)
            
        if self.graphEnabled('mysql_qcache_memory'):
            graph = MuninGraph('MySQL - Query Cache - Memory Use (bytes)', 
                self._category,
                info='Memory utilization for MySQL Server Query Cache.',
                args='--base 1000 --lower-limit 0')
            graph.addField('used', 'used', draw='AREASTACK', type='GAUGE', 
                info="Used space (bytes) in Query Cache.")
            graph.addField('free', 'free', draw='AREASTACK', type='GAUGE', 
                info="Free space (bytes) in Query Cache.")
            self.appendGraph('mysql_qcache_memory', graph)
            
        if self.graphEnabled('mysql_qcache_hits'):
            graph = MuninGraph('MySQL - Query Cache - Hits', 
                self._category,
                info='MySQL Server Query Cache Hits vs. Select Queries.',
                args='--base 1000 --lower-limit 0')
            graph.addField('hits', 'hits', draw='AREASTACK', 
                type='DERIVE', min=0,
                info='Hits - Number of select queries responded from query cache.')
            graph.addField('misses', 'misses', draw='AREASTACK', 
                type='DERIVE', min=0,
                info='Misses - Number of select queries executed.')
            self.appendGraph('mysql_qcache_hits', graph)
            
        if self.graphEnabled('mysql_qcache_prunes'):
            graph = MuninGraph('MySQL - Query Cache - Inserts/Prunes per second', 
                self._category,
                info='MySQL Server Query Cache Inserts and Low Memory Prune'
                     ' operations per second.',
                args='--base 1000 --lower-limit 0')
            graph.addField('insert', 'insert', draw='LINE2', 
                type='DERIVE', min=0,
                info='Number of queries added to the query cache.')
            graph.addField('prune', 'prune', draw='LINE2', 
                type='DERIVE', min=0,
                info='The number of queries that were deleted from the'
                     ' query cache because of low memory.')
            self.appendGraph('mysql_qcache_prunes', graph)
            
        if self.engineIncluded('myisam'):
            
            if self.graphEnabled('mysql_myisam_key_buffer_util'):
                graph = MuninGraph('MyISAM - Key Buffer Utilization (bytes)', 
                    self._category,
                    info='MySQL Server MyISAM Key Buffer Utilization'
                         ' in bytes.',
                    args='--base 1000 --lower-limit 0')
                graph.addField('dirty', 'dirty', draw='AREASTACK', type='GAUGE', 
                    info="Key space used by dirty blocks.")
                graph.addField('clean', 'clean', draw='AREASTACK', type='GAUGE', 
                    info="Key space used by dirty blocks..")
                graph.addField('free', 'free', draw='AREASTACK', type='GAUGE', 
                    info="Free space in key buffer.")
                graph.addField('total', 'total', draw='LINE2', type='GAUGE', 
                               colour='000000',
                               info="Total size of key buffer.")
                self.appendGraph('mysql_myisam_key_buffer_util', graph)
            
            if self.graphEnabled('mysql_myisam_key_read_reqs'):
                graph = MuninGraph('MyISAM - Key Block Read Requests per second', 
                    self._category,
                    info='MySQL Server MyISAM Key block read requests satisfied '
                         ' from block cache (hits) vs. disk (misses).',
                    args='--base 1000 --lower-limit 0')
                graph.addField('disk', 'disk', draw='AREASTACK', 
                               type='DERIVE', min=0, 
                               info='Misses - Key block read requests requiring'
                                    ' read from disk.')
                graph.addField('buffer', 'buffer', draw='AREASTACK', 
                               type='DERIVE', min=0, 
                               info='Misses - Key block read requests satisfied'
                                    ' from block cache without requiring read'
                                    ' from disk.')
                self.appendGraph('mysql_myisam_key_read_reqs', graph)
            
        if self.engineIncluded('innodb'):
            
            if self.graphEnabled('mysql_innodb_buffer_pool_util'):
                graph = MuninGraph('InnoDB - Buffer Pool Utilization (bytes)', 
                    self._category,
                    info='MySQL Server InnoDB Buffer Pool Utilization in bytes.',
                    args='--base 1000 --lower-limit 0')
                graph.addField('dirty', 'dirty', draw='AREASTACK', type='GAUGE', 
                    info="Buffer pool space used by dirty pages.")
                graph.addField('clean', 'clean', draw='AREASTACK', type='GAUGE', 
                    info="Buffer pool space used by clean pages.")
                graph.addField('misc', 'misc', draw='AREASTACK', type='GAUGE', 
                    info="Buffer pool space used for administrative overhead.")
                graph.addField('free', 'free', draw='AREASTACK', type='GAUGE', 
                    info="Free space in buffer pool.")
                graph.addField('total', 'total', draw='LINE2', type='GAUGE', 
                               colour='000000',
                               info="Total size of buffer pool.")
                self.appendGraph('mysql_innodb_buffer_pool_util', graph)
                
            if self.graphEnabled('mysql_innodb_buffer_pool_activity'):
                graph = MuninGraph('InnoDB - Buffer Pool Activity (Pages per second)', 
                    self._category,
                    info='MySQL Server Pages read into, written from and created'
                         ' in InnoDB buffer pool.',
                    args='--base 1000 --lower-limit 0')
                for (field, desc) in (('created',
                                       'Pages created in the buffer pool without'
                                       ' reading corresponding disk pages.'),
                                      ('read', 
                                       'Pages read into the buffer pool from disk.'),
                                      ('written', 
                                       'Pages written to disk from the buffer pool.')):
                    graph.addField(field, field, draw='LINE2', 
                                   type='DERIVE', min=0, info=desc)
                self.appendGraph('mysql_innodb_buffer_pool_activity', graph)
                
            if self.graphEnabled('mysql_innodb_buffer_pool_read_reqs'):
                graph = MuninGraph('InnoDB - Buffer Pool Read Requests per second', 
                    self._category,
                    info='MySQL Server read requests satisfied from InnoDB buffer'
                         ' pool (hits) vs. disk (misses).',
                    args='--base 1000 --lower-limit 0')
                graph.addField('disk', 'disk', draw='AREASTACK', 
                               type='DERIVE', min=0, 
                               info='Misses - Logical read requests requiring'
                                    ' read from disk.')
                graph.addField('buffer', 'buffer', draw='AREASTACK', 
                               type='DERIVE', min=0, 
                               info='Misses - Logical read requests satisfied'
                                    ' from buffer pool without requiring read'
                                    ' from disk.')
                self.appendGraph('mysql_innodb_buffer_pool_read_reqs', graph)
                    
            if self.graphEnabled('mysql_innodb_row_ops'):
                graph = MuninGraph('InnoDB - Row Operations per Second', 
                    self._category,
                    info='MySQL Server InnoDB Inserted, updated, deleted, read'
                         ' rows per second.',
                    args='--base 1000 --lower-limit 0')
                for field in ('inserted', 'updated', 'deleted', 'read'):
                    graph.addField(field, field, draw='AREASTACK', 
                                   type='DERIVE', min=0,
                                   info="Rows %s per second." % field)
                self.appendGraph('mysql_innodb_row_ops', graph)
                    
    def retrieveVals(self):
        """Retrieve values for graphs."""
        if self._genStats is None:
            self._genStats = self._dbconn.getStats()
        if self._genVars is None:
            self._genVars = self._dbconn.getParams()
        if self.hasGraph('mysql_connections'):
            self.setGraphVal('mysql_connections', 'conn',
                             self._genStats.get('Connections'))
            self.setGraphVal('mysql_connections', 'abort_conn',
                             self._genStats.get('Aborted_connects'))
            self.setGraphVal('mysql_connections', 'abort_client',
                             self._genStats.get('Aborted_clients'))
        if self.hasGraph('mysql_traffic'):
            self.setGraphVal('mysql_traffic', 'rx',
                             self._genStats.get('Bytes_received'))
            self.setGraphVal('mysql_traffic', 'tx',
                             self._genStats.get('Bytes_sent'))
        if self.graphEnabled('mysql_slowqueries'):
            self.setGraphVal('mysql_slowqueries', 'queries',
                             self._genStats.get('Slow_queries'))
        if self.hasGraph('mysql_rowmodifications'):
            self.setGraphVal('mysql_rowmodifications', 'insert',
                             self._genStats.get('Handler_write'))
            self.setGraphVal('mysql_rowmodifications', 'update',
                             self._genStats.get('Handler_update'))
            self.setGraphVal('mysql_rowmodifications', 'delete',
                             self._genStats.get('Handler_delete'))
        if self.hasGraph('mysql_rowreads'):
            for field in self.getGraphFieldList('mysql_rowreads'):
                self.setGraphVal('mysql_rowreads', field, 
                                 self._genStats.get('Handler_read_%s' % field))
        if self.hasGraph('mysql_tablelocks'):
            self.setGraphVal('mysql_tablelocks', 'waited',
                             self._genStats.get('Table_locks_waited'))
            self.setGraphVal('mysql_tablelocks', 'immediate',
                             self._genStats.get('Table_locks_immediate'))
        if self.hasGraph('mysql_threads'):
            self.setGraphVal('mysql_threads', 'running',
                             self._genStats.get('Threads_running'))
            self.setGraphVal('mysql_threads', 'idle',
                             self._genStats.get('Threads_connected')
                             - self._genStats.get('Threads_running'))
            self.setGraphVal('mysql_threads', 'cached',
                             self._genStats.get('Threads_cached'))
            self.setGraphVal('mysql_threads', 'total',
                             self._genStats.get('Threads_connected') 
                             + self._genStats.get('Threads_cached'))
        if self.hasGraph('mysql_commits_rollbacks'):
            self.setGraphVal('mysql_commits_rollbacks', 'commit',
                             self._genStats.get('Handler_commit'))
            self.setGraphVal('mysql_commits_rollbacks', 'rollback',
                             self._genStats.get('Handler_rollback'))
        if self.hasGraph('mysql_qcache_memory'):
            try:
                total = self._genVars['query_cache_size']
                free = self._genStats['Qcache_free_memory']
                used = total - free
            except KeyError:
                free = None
                used = None
            self.setGraphVal('mysql_qcache_memory', 'used', used)
            self.setGraphVal('mysql_qcache_memory', 'free', free)
        if self.hasGraph('mysql_qcache_hits'):
            try:
                hits = self._genStats['Qcache_hits']
                misses = self._genStats['Com_select'] - hits
            except KeyError:
                hits = None
                misses = None
            self.setGraphVal('mysql_qcache_hits', 'hits', hits)
            self.setGraphVal('mysql_qcache_hits', 'misses', misses)
            
        if self.hasGraph('mysql_qcache_prunes'):
            self.setGraphVal('mysql_qcache_prunes', 'insert', 
                             self._genStats.get('Qcache_inserts'))
            self.setGraphVal('mysql_qcache_prunes', 'prune',
                             self._genStats.get('Qcache_lowmem_prunes'))
        if self.hasGraph('mysql_proc_status'):
            self._procStatus = self._dbconn.getProcessStatus()
            if self._procStatus:
                stats = {}
                for field in self.getGraphFieldList('mysql_proc_status'):
                    stats[field] = 0
                for (k, v) in self._procStatus.items():
                    if stats.has_key(k):
                        stats[k] = v
                    else:
                        stats['unknown'] += v
                for (k,v) in stats.items():
                    self.setGraphVal('mysql_proc_status', k, v)
        if self.hasGraph('mysql_proc_db'):
            self._procDB = self._dbconn.getProcessDatabase()
            for db in self._dbList:
                self.setGraphVal('mysql_proc_db', db, self._procDB.get(db, 0))
           
        if self.engineIncluded('myisam'):
            
            if self.hasGraph('mysql_myisam_key_buffer_util'):
                try:
                    bsize = self._genVars['key_cache_block_size']
                    total = self._genVars['key_buffer_size']
                    free = self._genStats['Key_blocks_unused'] * bsize
                    dirty = self._genStats['Key_blocks_not_flushed'] * bsize
                    clean = total - free - dirty
                except KeyError:
                    total = None
                    free = None
                    dirty = None
                    clean = None
                for (field,val) in (('dirty', dirty), 
                                    ('clean', clean),
                                    ('free', free),
                                    ('total', total)):
                    self.setGraphVal('mysql_myisam_key_buffer_util', 
                                     field, val)
            if self.hasGraph('mysql_myisam_key_read_reqs'):
                try:
                    misses = self._genStats['Key_reads']
                    hits = (self._genStats['Key_read_requests']
                            - misses)
                except KeyError:
                    misses = None
                    hits = None
                self.setGraphVal('mysql_myisam_key_read_reqs', 'disk', misses)
                self.setGraphVal('mysql_myisam_key_read_reqs', 'buffer', hits)
            
        if self.engineIncluded('innodb'):
            
            if self.hasGraph('mysql_innodb_buffer_pool_util'):
                self._genStats['Innodb_buffer_pool_pages_clean'] = (
                    self._genStats.get('Innodb_buffer_pool_pages_data')
                    - self._genStats.get('Innodb_buffer_pool_pages_dirty'))
                page_size = int(self._genStats.get('Innodb_page_size'))
                for field in ('dirty', 'clean', 'misc', 'free', 'total'):
                    self.setGraphVal('mysql_innodb_buffer_pool_util', 
                                     field, 
                                     self._genStats.get('Innodb_buffer_pool_pages_%s'
                                                        % field)
                                     * page_size)
            if self.hasGraph('mysql_innodb_buffer_pool_activity'):
                for field in ('created', 'read', 'written'):
                    self.setGraphVal('mysql_innodb_buffer_pool_activity', field, 
                                     self._genStats.get('Innodb_pages_%s' % field))
            if self.hasGraph('mysql_innodb_buffer_pool_read_reqs'):
                try:
                    misses = self._genStats['Innodb_buffer_pool_reads']
                    hits = (self._genStats['Innodb_buffer_pool_read_requests']
                            - misses)
                except KeyError:
                    misses = None
                    hits = None
                self.setGraphVal('mysql_innodb_buffer_pool_read_reqs', 'disk', 
                                 misses)
                self.setGraphVal('mysql_innodb_buffer_pool_read_reqs', 'buffer', 
                                 hits)
            if self.hasGraph('mysql_innodb_row_ops'):
                for field in ('inserted', 'updated', 'deleted', 'read'):
                    self.setGraphVal('mysql_innodb_row_ops', field, 
                                     self._genStats.get('Innodb_rows_%s' % field))
            
    def engineIncluded(self, name):
        """Utility method to check if a storage engine is included in graphs.
        
        @param name: Name of storage engine.
        @return:     Returns True if included in graphs, False otherwise.
            
        """
        if self._engines is None:
            self._engines = self._dbconn.getStorageEngines()
        return self.envCheckFilter('engine', name) and name in self._engines
    
    def autoconf(self):
        """Implements Munin Plugin Auto-Configuration Option.
        
        @return: True if plugin can be  auto-configured, False otherwise.
                 
        """
        return (self._dbconn is not None 
                and len(self._dbconn.getDatabases()) > 0)
              

def main():
    sys.exit(muninMain(MuninMySQLplugin))


if __name__ == "__main__":
    main()
