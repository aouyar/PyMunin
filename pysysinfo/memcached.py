"""Implements MemcachedInfo Class for gathering stats from Memcached.

The statistics are obtained by connecting to and querying the Memcached. 

"""

import re
import os
import util

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


defaultMemcachedPort = 11211


class MemcachedInfo:
    """Class that establishes connection to Memcached Instance
    to retrieve statistics on operation.

    """

    def __init__(self, host='127.0.0.1', port=defaultMemcachedPort, 
                 socket_file=None, timeout=None, autoInit=True):
        """Initialize connection to Memcached.
        
        @param host:        Memcached Host for TCP connections.
        @param port:        Memcached Port for TCP connections.
        @param socket_file: Memcached Socket File Path for UNIX Socket connections.
        @param timeout:     Memcached Socket Timeout in seconds.
        @param autoInit:    If True connect to Memcached on init.

        """
        self._conn = None
        if socket_file is not None:
            self._host = None
            self._port = None
            self._socketFile = socket_file
            self._instanceName = ("Memcached Instance on socket file %s" 
                                  % self._socketFile)
        else:
            self._host = host or '127.0.0.1'
            self._port = int(port or defaultMemcachedPort)
            self._socketFile = None
            self._instanceName = ("Memcached Instance on host %s and port %s"
                                  % (self._host, self._port))
        if timeout is not None:
            self._timeout = float(timeout)
        else:
            self._timeout = None
        if autoInit:
            self._connect()
    
    def __del__(self):
        """Cleanup."""
        if self._conn is not None:
            self._conn.close()

    def _connect(self):
        """Connect to Memcached."""
        if self._socketFile is not None:
            if not os.path.exists(self._socketFile):
                raise Exception("Socket file (%s) for Memcached Instance not found."
                                % self._socketFile)
        try:
            if self._timeout is not None:
                self._conn = util.Telnet(self._host, self._port, self._socketFile, 
                                         timeout)
            else:
                self._conn = util.Telnet(self._host, self._port, self._socketFile)
        except:     
            raise Exception("Connection to %s failed." % self._instanceName)
            
    def _sendStatCmd(self,  cmd):
        """Send stat command to Memcached Server and return response lines.
        
        @param cmd: Command string.
        @return:    Array of strings.
        
        """
        try:
            self._conn.write("%s\r\n" % cmd)
            regex = re.compile('^(END|ERROR)\r\n', re.MULTILINE)
            (idx, mobj, text) = self._conn.expect([regex,], self._timeout) #@UnusedVariable
        except:
            raise Exception("Communication with %s failed" % self._instanceName)
        if mobj is not None:
            if mobj.group(1) == 'END':
                return text.splitlines()[:-1]
            elif mobj.group(1) == 'ERROR':
                raise Exception("Protocol error in communication with %s."
                                % self._instanceName)
        else:
            raise Exception("Connection with %s timed out." % self._instanceName)
    def _parseStats(self, lines, parse_slabs = False):
        """Parse stats output from memcached and return dictionary of stats-
        
        @param lines:       Array of lines of input text.
        @param parse_slabs: Parse slab stats if True.
        @return:            Stats dictionary.
        
        """
        info_dict = {}
        info_dict['slabs'] = {}
        for line in lines:
            mobj = re.match('^STAT\s(\w+)\s(\S+)$',  line)
            if mobj:
                info_dict[mobj.group(1)] = util.parse_value(mobj.group(2), True)
                continue
            elif parse_slabs:
                mobj = re.match('STAT\s(\w+:)?(\d+):(\w+)\s(\S+)$',  line)
                if mobj:
                    (slab, key, val) = mobj.groups()[-3:]      
                    if not info_dict['slabs'].has_key(slab):
                        info_dict['slabs'][slab] = {}
                    info_dict['slabs'][slab][key] = util.parse_value(val, True)
        return info_dict
        
    def getStats(self):
        """Query Memcached and return operational stats.
        
        @return: Dictionary of stats.
        
        """
        lines = self._sendStatCmd('stats')
        return self._parseStats(lines, False)
    
    def getStatsItems(self):
        """Query Memcached and return stats on items broken down by slab.
        
        @return: Dictionary of stats.
        
        """
        lines = self._sendStatCmd('stats items')
        return self._parseStats(lines, True)
    
    def getStatsSlabs(self):
        """Query Memcached and return stats on slabs.
        
        @return: Dictionary of stats.
        
        """
        lines = self._sendStatCmd('stats slabs')
        return self._parseStats(lines, True)

    def getSettings(self):
        """Query Memcached and return settings.
        
        @return: Dictionary of settings.
        
        """
        lines = self._sendStatCmd('stats settings')
        return self._parseStats(lines, False)
    