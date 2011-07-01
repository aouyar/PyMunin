#!/usr/bin/python
"""mysqlstats - Munin Plugin to monitor stats for MySQL Database Server.

Requirements
  - Access permissions for MySQL Database.


Wild Card Plugin - No


Multigraph Plugin - Graph Structure
   - mysql_threads
   

Environment Variables
  host:           MySQL Server IP. 
                  (Defaults to UNIX socket if not provided.)
  port:           MySQL Server Port (3306 by default.)
  database:       MySQL Database
  user:           Database User Name
  password:       Database User Password
  include_graphs: Comma separated list of enabled graphs. 
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.
  include_engine: Comma separated list of storage engines to include graphs.
                  (All enabled by default.)
  exclude_engine: Comma separated list of storage engines to exclude from graphs.
  

  Example:
    [mysqlstats]
        user root
        env.exclude_graphs mysql_threads
        env.include_engine innodb

"""
# Munin  - Magic Markers
#%# family=manual
#%# capabilities=noautoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.mysql import MySQLinfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.7"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninMySQLplugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring MySQL Database Server.

    """
    plugin_name = 'pgstats'
    isMultigraph = True

    def __init__(self, argv = (), env = {}):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv: List of command line arguments.
        @param env:  Dictionary of environment variables.
        
        """
        MuninPlugin.__init__(self, argv, env)
        
        self.registerFilter('engine', '\w+$')
        
        self._host = self._env.get('host')
        self._port = self._env.get('port')
        self._database = self._env.get('database')
        self._user = self._env.get('user')
        self._password = self._env.get('password')
        
        self._dbconn = MySQLinfo(self._host, self._port, self._database, 
                              self._user, self._password)
        
        if self.graphEnabled('mysql_threads'):
            graph = MuninGraph('MySQL - Threads', 
                'MySQL',
                info='MySQL Database Server threads status.',
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
                    
    def retrieveVals(self):
        """Retrive values for graphs."""
        self._genStats = None
        if self.hasGraph('mysql_threads'):
            if self._genStats is None:
                self._genStats = self._dbconn.getStats()
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
            
    def engineIncluded(self, name):
        """Utility method to check if a storage engine is included in graphs.
        
        @param name: Name of storage engine.
        @return:     Returns True if included in graphs, False otherwise.
            
        """
        return self.checkFilter('engine', name)
              


if __name__ == "__main__":
    sys.exit(muninMain(MuninMySQLplugin))

