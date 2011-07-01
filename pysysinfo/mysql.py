"""Implements MySQLinfo Class for gathering stats from MySQL Database Server.

The statistics are obtained by connecting to and querying local and/or 
remote MySQL Servers. 

"""

import MySQLdb
import util

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


defaultMySQLport = 3306


class MySQLinfo:
    """Class to retrieve stats for MySQL Database"""

    def __init__(self, host=None, port=None,
                 database=None, user=None, password=None, autoInit=True):
        """Initialize connection to MySQL Database.
        
        @param host:     MySQL Host
        @param port:     MySQL Port
        @param database: MySQL Database
        @param user:     MySQL User
        @param password: MySQL Password
        @param autoInit: If True connect to MySQL Database on instantiation.
            
        """
        self._connParams = {}
        if host is not None:
            self._connParams['host'] = host
            if port is not None:
                self._connParams['port'] = port
            else:
                self._connParams['port'] = defaultMySQLport
        elif port is not None:
            self._connParams['host'] = '127.0.0.1'
            self._connParams['port'] = port
        if database is not None:
            self._connParams['db'] = database
        if user is not None:
            self._connParams['user'] = user
            if password is not None:
                self._connParams['passwd'] = password
        if autoInit:
            self._connect()
        
    def __del__(self):
        """Cleanup."""
        if self._conn is not None:
            self._conn.close()
            
    def _connect(self):
        """Establish connection to PostgreSQL Database."""
        if self._connParams:
            self._conn = MySQLdb.connect(**self._connParams)
        else:
            self._conn = MySQLdb.connect('')

    def getStorageEngines(self):
        """Returns list of supported storage engines.
        
        @return: List of storage engine names.
        
        """
        cur = self._conn.cursor()
        cur.execute("""SHOW STORAGE ENGINES;""")
        rows = cur.fetchall()
        if rows:
            return [row[0].lower() for row in rows if row[1] in ['YES', 'DEFAULT']]
        else:
            return []     
    
    def getParam(self, key):
        """Returns value of Run-time Database Parameter 'key'.
        
        @param key: Run-time parameter name.
        @return:    Run-time parameter value.
        
        """
        cur = self._conn.cursor()
        cur.execute("SHOW GLOBAL VARIABLES LIKE %s", key)
        row = cur.fetchone()
        return int(row[1])
    
    def getParams(self):
        """Returns dictionary of all run-time parameters.
        
        @return: Dictionary of all Run-time parameters.
        
        """
        cur = self._conn.cursor()
        cur.execute("SHOW GLOBAL VARIABLES")
        rows = cur.fetchall()
        info_dict = {}
        for row in rows:
            key = row[0]
            val = util.parse_value(row[1])
            info_dict[key] = val
        return info_dict
        
    def getStats(self):
        """Returns global stats for database.
        
        @return: Dictionary of database statistics.
        
        """
        cur = self._conn.cursor()
        cur.execute("SHOW GLOBAL STATUS")
        rows = cur.fetchall()
        info_dict = {}
        for row in rows:
            key = row[0]
            val = util.parse_value(row[1])
            info_dict[key] = val
        return info_dict
     
    def getDatabases(self):
        """Returns list of databases.
        
        @return: List of database schemas.
        
        """
        cur = self._conn.cursor()
        cur.execute("""SHOW DATABASES;""")
        rows = cur.fetchall()
        if rows:
            return [row[0] for row in rows]
        else:
            return []
