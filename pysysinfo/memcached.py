#!/usr/bin/python
"""Implements MemcachedInfo Class for gathering stats from Memcached.

The statistics are obtained by connecting to and querying the Memcached. 

"""

import socket
import re

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MemcachedInfo:
    """Class that establishes connection to Memcached Instance
    to retrieve statistics on operation.

    """

    def __init__(self, host='127.0.0.1', port=11211, autoInit=True):
        """Initialize connection to Memcached.
        
        @param host:     Memcached Host
        @param port:     Memcached Port
        @param autoInit: If True connect to Memcached on init.

        """
        self._host = host or '127.0.0.1'
        self._port = port or 11211
        self._conn = None
        if autoInit:
            self._connect()
    
    def __del__(self):
        """Cleanup."""
        if self._conn is not None:
            self._conn.close()

    def _connect(self):
        """Connect to Memcached."""
        try:
            self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._conn.connect((self._host,  self._port))
        except:
            raise Exception(
                "Connection to Memcached Instance on host %s and port %d failed."
                % (self._host, self._port)
                )
    
    def _sendStatCmd(self,  cmd):
        """Send stat command to Memcached Server and return result dictionary.
        
        @param cmd: Command string.
        
        """
        try:
            self._conn.sendall("%s\n" % cmd)
            buf = ""
            while 'END\r\n' not in buf:
                buf += self._conn.recv(1024)
        except:
            raise Exception(
                "Communication with Memcached Instance on host %s and port %d failed."
                % (self._host, self._port)
                )
        info_dict = {}
        for line in buf.split("\r\n"):
            mobj = re.match('STAT\s(\w+)\s(\d+)$',  line)
            if mobj:
                info_dict[mobj.group(1)] = int(mobj.group(2))
                continue
            mobj = re.match('STAT\s(\w+)\s(\d+\.\d+)$',  line)
            if mobj:
                info_dict[mobj.group(1)] = float(mobj.group(2))
                continue
            mobj = re.match('STAT\s(\w+)\s+(\S.*\S)\s*$',  line)
            if mobj:
                info_dict[mobj.group(1)] = mobj.group(2)
                continue
        return info_dict
        
    def getStats(self):
        """Query Memcached and return operational stats.
        
        @return: Dictionary of stats.
        
        """
        return self._sendStatCmd('stats')
    
    def getStatsItems(self):
        """Query Memcached and return stats on items broken down by slab.
        
        @return: Dictionary of stats.
        
        """
        return self._sendStatCmd('stats items')
    
    def getStatsSlabs(self):
        """Query Memcached and return stats on slabs.
        
        @return: Dictionary of stats.
        
        """
        return self._sendStatCmd('stats items')
