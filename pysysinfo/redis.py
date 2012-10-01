"""Implements RedisInfo Class for gathering stats from Redis.

"""

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


defaultRedisPort = 11211


class RedisInfo:
    """Class that establishes connection to Memcached Instance
    to retrieve statistics on operation.

    """

    def __init__(self, host='127.0.0.1', port=defaultRedisPort, db=0):
        """Initialize connection to Redis.
        
        @param host: Redis Host
        @param port: Redis Port
        @param db:   Redis DB ID

        """
        self._conn = None
        self._host = host or '127.0.0.1'
        self._port = int(port or defaultRedisPort)
        self._dbID = db
        
    def getStats(self):
        """Query Redis and return stats.
        
        @return: Dictionary of stats.
        
        """
        pass
