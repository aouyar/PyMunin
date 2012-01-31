#!/usr/bin/env python
"""pgstats - Munin Plugin to monitor stats for PostgreSQL Database Server.

Requirements
  - Access permissions for PostgreSQL Database.


Wild Card Plugin - No


Multigraph Plugin - Graph Structure
   - pg_connections
   - pg_diskspace
   - pg_blockreads
   - pg_xact
   - pg_checkpoints
   - pg_bgwriter
   - pg_tup_read
   - pg_tup_write
   - pg_blockreads_detail
   - pg_xact_commit_detail
   - pg_xact_rollback_detail
   - pg_tup_return_detail
   - pg_tup_fetch_detail
   - pg_tup_delete_detail
   - pg_tup_update_detail
   - pg_tup_insert_detail
   

Environment Variables

  host:           PostgreSQL Server IP. 
                  (Defaults to UNIX socket if not provided.)
  port:           PostgreSQL Server Port
                  (Defaults to 5432 for network connections.)
  database:       PostgreSQL Database for monitoring connection.
                  (The default is the login the for connecting user.)
  user:           Database User Name
                  (The default is the login of OS user for UNIX sockets.
                  Must be specified for network connections.)
  password:       Database User Password
                  (Attempt login without password by default.)
  include_db:     Comma separated list of databases to include in detail graphs.
                  (All enabled by default.)
  exclude_db:     Comma separated list of databases to exclude from detail graphs.
  detail_graphs:  Enable (on) / disable (off) detail graphs. 
                  (Disabled by default.)
  include_graphs: Comma separated list of enabled graphs. 
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.

  Example:
    [pgstats]
        user postgres
        env.exclude_graphs pg_tup_read,pg_tup_write
        env.db_include postgres,webapp

"""
# Munin  - Magic Markers
#%# family=manual
#%# capabilities=noautoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.postgresql import PgInfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninPgPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring PostgreSQL Database Server.

    """
    plugin_name = 'pgstats'
    isMultigraph = True

    def __init__(self, argv=(), env={}, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)
        
        self.envRegisterFilter('db', '^\w+$')
        self._host = self.envGet('host')
        self._port = self.envGet('port')
        self._database = self.envGet('database')
        self._user = self.envGet('user')
        self._password = self.envGet('password')
        self._detailGraphs = self.envCheckFlag('detail_graphs', False)
        
        self._dbconn = PgInfo(self._host, self._port, self._database, 
                              self._user, self._password)
        dblist = [db for db in self._dbconn.getDatabases()
                  if self.dbIncluded(db)]
        dblist.sort()
        
        if self.graphEnabled('pg_connections'):
            graph = MuninGraph('PostgreSQL - Active Connections', 
                'PostgreSQL Sys',
                info='Active connections for PostgreSQL Database Server.',
                args='--base 1000 --lower-limit 0',
                autoFixNames = True)
            for db in dblist:
                graph.addField(db, db, draw='AREASTACK', type='GAUGE',
                    info="Active connections to database %s." % db)
            graph.addField('total', 'total', draw='LINE2', type='GAUGE', 
                           colour='000000',
                info="Total number of active connections.")
            graph.addField('max_conn', 'max_conn', draw='LINE2', type='GAUGE', 
                           colour='FF0000',
                info="Global server level concurrent connections limit.")
            self.appendGraph('pg_connections', graph)
        
        if self.graphEnabled('pg_diskspace'):
            graph = MuninGraph('PostgreSQL - Database Disk Usage', 
                'PostgreSQL Sys',
                info='Disk usage of databases on PostgreSQL Server in bytes.',
                args='--base 1024 --lower-limit 0',
                autoFixNames = True)
            for db in dblist:
                graph.addField(db, db, draw='AREASTACK', type='GAUGE',
                    info="Disk usage of database %s." % db)
            graph.addField('total', 'total', draw='LINE2', type='GAUGE', 
                colour='000000', info="Total disk usage of all databases.")
            self.appendGraph('pg_diskspace', graph)
        
        if self.graphEnabled('pg_blockreads'):
            graph = MuninGraph('PostgreSQL - Block Read Stats', 'PostgreSQL Sys',
                info='Block read stats for PostgreSQL Server.',
                args='--base 1000 --lower-limit 0')
            graph.addField('blk_hit', 'cache hits', draw='AREASTACK', 
                type='DERIVE', min=0, 
                info="Blocks read from PostgreSQL Cache per second.")
            graph.addField('blk_read', 'disk reads', draw='AREASTACK', 
                type='DERIVE', min=0,
                info="Blocks read directly from disk or operating system "
                     "disk cache per second.")
            self.appendGraph('pg_blockreads', graph)
        
        if self.graphEnabled('pg_xact'):
            graph = MuninGraph('PostgreSQL - Transactions', 'PostgreSQL Sys',
                info='Transaction commit / rollback Stats for PostgreSQL Server.',
                args='--base 1000 --lower-limit 0')
            graph.addField('commits', 'commits', draw='LINE2', type='DERIVE', 
                           min=0, info="Transactions per second.")
            graph.addField('rollbacks', 'rollbacks', draw='LINE2', type='DERIVE', 
                           min=0, info="Rollbacks per second.")
            self.appendGraph('pg_xact', graph)
        
        if self._dbconn.checkVersion('8.3'):
            if self.graphEnabled('pg_checkpoints'):
                graph = MuninGraph('PostgreSQL - Checkpoints per minute', 
                    'PostgreSQL Sys',
                    info='Number of Checkpoints per Minute for PostgreSQL Server.',
                    args='--base 1000 --lower-limit 0', period='minute')
                graph.addField('req', 'req', draw='LINE2', type='DERIVE', 
                               min=0, info="Requested checkpoints..")
                graph.addField('timed', 'timed', draw='LINE2', type='DERIVE', 
                               min=0, info="Check points started by timeout.")
                self.appendGraph('pg_checkpoints', graph)
            if self.graphEnabled('pg_bgwriter'):
                graph = MuninGraph('PostgreSQL - BgWriter Stats (blocks / second)', 
                    'PostgreSQL Sys',
                    info='PostgreSQL Server - Bgwriter - Blocks written per second.',
                    args='--base 1000 --lower-limit 0', period='minute')
                graph.addField('backend', 'backend', draw='LINE2', 
                               type='DERIVE', min=0, 
                               info="Buffers written by backend and not bgwriter.")
                graph.addField('clean', 'clean', draw='LINE2', 
                               type='DERIVE', min=0, 
                               info="Buffers cleaned by bgwriter runs.")
                graph.addField('chkpoint', 'chkpoint', draw='LINE2', type='DERIVE', 
                               min=0, info="Buffers written performing checkpoints.")
                self.appendGraph('pg_bgwriter', graph)
        
        if self.graphEnabled('pg_tup_read'):
            graph = MuninGraph('PostgreSQL - Tuple Reads', 'PostgreSQL Sys',
                info='Tuple return and fetch Stats for PostgreSQL Server.',
                args='--base 1000 --lower-limit 0')
            graph.addField('fetch', 'fetch', draw='AREASTACK', 
                type='DERIVE', min=0, 
                info="Tuples returned per second by table or index scans.")
            graph.addField('return', 'return', draw='AREASTACK', 
                type='DERIVE', min=0,
                info="Tuples fetched per second from tables using indices "
                     "or bitmap scans.")
            self.appendGraph('pg_tup_read', graph)
            
        if self.graphEnabled('pg_tup_write'):
            graph = MuninGraph('PostgreSQL - Tuple Writes', 'PostgreSQL Sys',
                info='Tuple insert, update and delete Stats for PostgreSQL Server.',
                args='--base 1000 --lower-limit 0')
            graph.addField('delete', 'delete', draw='AREASTACK', type='DERIVE', 
                           min=0, info="Tuples deleted per second.")
            graph.addField('update', 'update', draw='AREASTACK', type='DERIVE', 
                           min=0, info="Tuples updated per second.")
            graph.addField('insert', 'insert', draw='AREASTACK', type='DERIVE', 
                           min=0, info="Tuples inserted per second.")
            self.appendGraph('pg_tup_write', graph)
        
        if self._detailGraphs:        
            if self.graphEnabled('pg_blockread_detail'):
                graph = MuninGraph('PostgreSQL - Block Read Stats Detail', 
                    'PostgreSQL DB',
                    info='Block read stats for each database in PostgreSQL Server.',
                    args='--base 1000 --lower-limit 0',
                    autoFixNames = True)
                for db in dblist:
                    graph.addField(db, db, draw='AREASTACK', 
                        type='DERIVE', min=0,
                        info="Blocks read per second for database %s." % db)
                self.appendGraph('pg_blockread_detail', graph)
            if self.graphEnabled('pg_xact_commit_detail'):
                graph = MuninGraph('PostgreSQL - Transaction Commits Detail', 
                    'PostgreSQL DB',
                    info='Transaction commits for each database in PostgreSQL Server.',
                    args='--base 1000 --lower-limit 0',
                    autoFixNames = True)
                for db in dblist:
                    graph.addField(db, db, draw='AREASTACK', 
                        type='DERIVE', min=0,
                        info="Transaction commits per second for database %s." % db)
                self.appendGraph('pg_xact_commit_detail', graph)
            if self.graphEnabled('pg_xact_rollback_detail'):
                graph = MuninGraph('PostgreSQL - Transaction Rollbacks Detail', 
                    'PostgreSQL DB',
                    info='Transaction rollbacks for each database in PostgreSQL Server.',
                    args='--base 1000 --lower-limit 0',
                    autoFixNames = True)
                for db in dblist:
                    graph.addField(db, db, draw='AREASTACK', 
                        type='DERIVE', min=0,
                        info="Transaction rollbacks per second for database %s." % db)
                self.appendGraph('pg_xact_rollback_detail', graph)
            if self.graphEnabled('pg_tup_return_detail'):
                graph = MuninGraph('PostgreSQL - Tuple Scan Detail', 
                    'PostgreSQL DB',
                    info='Tuple scans for each database in PostgreSQL Server.',
                    args='--base 1000 --lower-limit 0',
                    autoFixNames = True)
                for db in dblist:
                    graph.addField(db, db, draw='AREASTACK', 
                        type='DERIVE', min=0,
                        info="Tuples scanned per second from database %s." % db)
                self.appendGraph('pg_tup_return_detail', graph)
            if self.graphEnabled('pg_tup_fetch_detail'):
                graph = MuninGraph('PostgreSQL - Tuple Fetch Detail', 
                    'PostgreSQL DB',
                    info='Tuple fetches for each database in PostgreSQL Server.',
                    args='--base 1000 --lower-limit 0',
                    autoFixNames = True)
                for db in dblist:
                    graph.addField(db, db, draw='AREASTACK', 
                        type='DERIVE', min=0,
                        info="Tuples fetched per second from database %s." % db)
                self.appendGraph('pg_tup_fetch_detail', graph)
            if self.graphEnabled('pg_tup_delete_detail'):
                graph = MuninGraph('PostgreSQL - Tuple Delete Detail', 
                    'PostgreSQL DB',
                    info='Tuple deletes for each database in PostgreSQL Server.',
                    args='--base 1000 --lower-limit 0',
                    autoFixNames = True)
                for db in dblist:
                    graph.addField(db, db, draw='AREASTACK',
                        type='DERIVE', min=0,
                        info="Tuples deleted per second from database %s." % db)
                self.appendGraph('pg_tup_delete_detail', graph)
            if self.graphEnabled('pg_tup_update_detail'):
                graph = MuninGraph('PostgreSQL - Tuple Updates Detail', 
                    'PostgreSQL DB',
                    info='Tuple updates for each database in PostgreSQL Server.',
                    args='--base 1000 --lower-limit 0',
                    autoFixNames = True)
                for db in dblist:
                    graph.addField(db, db, draw='AREASTACK', 
                        type='DERIVE', min=0,
                        info="Tuples updated per second in database %s." % db)
                self.appendGraph('pg_tup_update_detail', graph)
            if self.graphEnabled('pg_tup_insert_detail'):
                graph = MuninGraph('PostgreSQL - Tuple Inserts Detail', 
                    'PostgreSQL DB',
                    info='Tuple insertes for each database in PostgreSQL Server.',
                    args='--base 1000 --lower-limit 0',
                    autoFixNames = True)
                for db in dblist:
                    graph.addField(db, db, draw='AREASTACK', 
                        type='DERIVE', min=0,
                        info="Tuples inserted per second into database %s." % db)
                self.appendGraph('pg_tup_insert_detail', graph)
            
    def retrieveVals(self):
        """Retrieve values for graphs."""                
        stats = self._dbconn.getDatabaseStats()
        databases = stats.get('databases')
        totals = stats.get('totals')
        if databases and len(databases) > 0:
            if self.hasGraph('pg_connections'):
                limit = self._dbconn.getParam('max_connections')
                self.setGraphVal('pg_connections', 'max_conn', limit)
                for (db, dbstats) in databases.iteritems():
                    if self.dbIncluded(db):
                        self.setGraphVal('pg_connections', db, 
                                         dbstats['numbackends'])
                self.setGraphVal('pg_connections', 'total', totals['numbackends'])
            if self.hasGraph('pg_diskspace'):
                for (db, dbstats) in databases.iteritems():
                    if self.dbIncluded(db):
                        self.setGraphVal('pg_diskspace', db, dbstats['disk_size'])
                self.setGraphVal('pg_diskspace', 'total', totals['disk_size'])
        if self.hasGraph('pg_blockreads'):
            self.setGraphVal('pg_blockreads', 'blk_hit', totals['blks_hit'])
            self.setGraphVal('pg_blockreads', 'blk_read', totals['blks_read'])
        if self.hasGraph('pg_xact'):
            self.setGraphVal('pg_xact', 'commits', totals['xact_commit'])
            self.setGraphVal('pg_xact', 'rollbacks', totals['xact_rollback'])
        if self.hasGraph('pg_tup_read'):
            self.setGraphVal('pg_tup_read', 'fetch', totals['tup_fetched'])
            self.setGraphVal('pg_tup_read', 'return', totals['tup_returned'])
        if self.hasGraph('pg_tup_write'):
            self.setGraphVal('pg_tup_write', 'delete', totals['tup_deleted'])
            self.setGraphVal('pg_tup_write', 'update', totals['tup_updated'])
            self.setGraphVal('pg_tup_write', 'insert', totals['tup_inserted'])
            
        if self._detailGraphs:
            for (db, dbstats) in databases.iteritems():
                if self.dbIncluded(db):
                    if self.hasGraph('pg_blockread_detail'):
                        self.setGraphVal('pg_blockread_detail', db, 
                            dbstats['blks_hit'] + dbstats['blks_read'])
                    for (graph_name, attr_name) in (
                            ('pg_xact_commit_detail', 'xact_commit'),
                            ('pg_xact_rollback_detail', 'xact_rollback'),
                            ('pg_tup_return_detail', 'tup_returned'),
                            ('pg_tup_fetch_detail', 'tup_fetched'),
                            ('pg_tup_delete_detail', 'tup_deleted'),
                            ('pg_tup_update_detail', 'tup_updated'),
                            ('pg_tup_insert_detail', 'tup_inserted'),
                        ):
                        if self.hasGraph(graph_name):
                            self.setGraphVal(graph_name, db, dbstats[attr_name])
        
        stats = None               
        if self.hasGraph('pg_checkpoints'):
            if stats is None:
                stats = self._dbconn.getBgWriterStats()
            self.setGraphVal('pg_checkpoints', 'req', 
                             stats.get('checkpoints_req'))
            self.setGraphVal('pg_checkpoints', 'timed', 
                             stats.get('checkpoints_timed'))
        if self.hasGraph('pg_bgwriter'):
            if stats is None:
                stats = self._dbconn.getBgWriterStats()
            self.setGraphVal('pg_bgwriter', 'backend', 
                             stats.get('buffers_backend'))
            self.setGraphVal('pg_bgwriter', 'clean', 
                             stats.get('buffers_clean'))
            self.setGraphVal('pg_bgwriter', 'chkpoint', 
                             stats.get('buffers_checkpoint'))
            
    
    def dbIncluded(self, name):
        """Utility method to check if database is included in graphs.
        
        @param name: Name of database.
        @return:     Returns True if included in graphs, False otherwise.
            
        """
        return self.envCheckFilter('db', name)
              

def main():
    sys.exit(muninMain(MuninPgPlugin))


if __name__ == "__main__":
    main()
