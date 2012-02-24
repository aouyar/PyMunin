"""Implements MemcachedInfo Class for gathering stats from Memcached.

The statistics are obtained by connecting to and querying the Memcached. 

"""

import re
import sys
import telnetlib
import util

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


connTimeout = 5


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
        self._port = int(port) or 11211
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
            if sys.version_info[:2] >= (2,6):
                self._conn = telnetlib.Telnet(self._host, self._port, 
                                              connTimeout)
            else:
                self._conn = telnetlib.Telnet(self._host, self._port)
        except:
            raise Exception(
                "Connection to Memcached Instance on host %s and port %d failed."
                % (self._host, self._port)
                )
    
    def _sendStatCmd(self,  cmd):
        """Send stat command to Memcached Server and return response lines.
        
        @param cmd: Command string.
        @return:    Array of strings.
        
        """
        try:
            self._conn.write("%s\r\n" % cmd)
            regex = re.compile('^(END|ERROR)\r\n', re.MULTILINE)
            (idx, mobj, text) = self._conn.expect([regex,], connTimeout) #@UnusedVariable
        except:
            raise Exception("Communication with Memcached Instance on "
                            "host %s and port %d failed." % 
                            (self._host, self._port))
        if mobj is not None:
            if mobj.group(1) == 'END':
                return text.splitlines()[:-1]
            elif mobj.group(1) == 'ERROR':
                raise Exception("Protocol error in communication with "
                            "Memcached Instance on host %s and port %d."
                            % (self._host, self._port))
        else:
            raise Exception("Connection with Memcached Instance on "
                            "host %s and port %d timed out."
                            % (self._host, self._port))
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
    