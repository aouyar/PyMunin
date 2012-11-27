"""Implements RedisInfo Class for gathering stats from Redis.

"""

import time
import redis
import util

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"




class RedisInfo:
    """Class that establishes connection to Memcached Instance
    to retrieve statistics on operation.

    """

    def __init__(self, host=None, port=None, db=None, password=None, 
                 socket_timeout=None, unix_socket_path=None):
        """Initialize connection to Redis.
        
        @param host:             Redis Host.  (Default: localhost)
        @param port:             Redis Port.  (Default: Default Redis Port)
        @param db:               Redis DB ID. (Default: 0)
        @param password:         Redis Password (Optional)
        @param socket_timeout:   Redis Socket Timeout (Default: OS Default.)
        @param unix_socket_path: Socket File Path for UNIX Socket connections.
                                 (Not required unless connection to Redis is 
                                 through named socket.)
        
        """
        params = locals()
        self._conn = None
        self._connParams = dict((k, params[k]) 
                                for k in ('host', 'port', 'db', 'password', 
                                          'socket_timeout', 'unix_socket_path')
                                if params[k] is not None)
        self._conn = redis.Redis(**self._connParams)
        
    def ping(self):
        """Ping Redis Server and return Round-Trip-Time in seconds.
        
        @return: Round-trip-time in seconds as float.
        
        """
        start = time.time()
        self._conn.ping()
        return (time.time() - start)
        
    def getStats(self):
        """Query Redis and return stats.
        
        @return: Dictionary of stats.
        
        """
        try:
            return self._conn.info('all')
        except TypeError:
            return self._conn.info()
        
