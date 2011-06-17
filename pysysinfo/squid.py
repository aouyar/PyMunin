"""Implements SquidInfo Class for gathering stats from Squid Proxy Server.

The statistics are obtained by connecting to and querying local and/or 
remote Squid Proxy Servers. 

"""

import sys
import re
import httplib
import urllib
import util

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


defaultSquidPort = 3128
defaultTimeout = 8
buffSize = 4096

memMultiplier = {'G': 1024 * 1024 * 1024, 'M':1024 * 1024, 'K':1024}


def parse_value(val):
    """Parse input string and return int, float or str depending on format.
    
    @param val: Input string.
    @return:    Value of type int, float or str.
        
    """
    
    mobj = re.match('(-{0,1}\d+)\s*(\sseconds|/\s*\w+)$',  val)
    if mobj:
        return int(mobj.group(1))
    mobj = re.match('(-{0,1}\d*\.\d+)\s*(\sseconds|/\s*\w+)$',  val)
    if mobj:
        return float(mobj.group(1))
    re.match('(-{0,1}\d+)\s*([GMK])B$',  val)
    if mobj:
        return int(mobj.group(1)) * memMultiplier[mobj.group(2)]
    mobj = re.match('(-{0,1}\d+(\.\d+){0,1})\s*\%$',  val)
    if mobj:
        return float(mobj.group(1)) / 100 
    return val

    
class SquidInfo:
    """Class to retrieve stats from Squid Proxy Server."""

    def __init__(self, host=None, port=None, user=None, password=None, 
                 autoInit=True):
        """Initialize Squid Proxy Manager access.
        
        @param host:     Squid Proxy Host. (Default: 127.0.0.1)
        @param port:     Squid Proxy Port. (Default: 3128)
        @param user:     Squid Proxy Manager User.
        @param password: Squid Proxy Manager Password.
        @param autoInit: If True connect to Apache Tomcat Server on instantiation.
            
        """
        if host is not None:
            self._host = host
        else:
            self._host = '127.0.0.1'
        if port is not None:
            self._port = port
        else:
            self._port = defaultSquidPort
        self._httpHeaders = {'Accept': '*/*',}
        if user is not None and password is not None:
            authstr = "%s:%s" % (urllib.quote(user), urllib.quote(password))
            self._httpHeaders['Authorization'] = "Basic %s" % authstr
            self._httpHeaders['Proxy-Authorization'] = "Basic %s" % authstr
        self._conn = None
        if autoInit:
            self._connect()
    
    def __del__(self):
        """Cleanup."""
        if self._conn is not None:
            self._conn.close()
        
    def _connect(self):
        """Connect to Squid Proxy Manager interface."""
        if sys.version_info[:2] < (2,6):
            self._conn = httplib.HTTPConnection(self._host, self._port)
        else:
            self._conn = httplib.HTTPConnection(self._host, self._port, 
                                                False, defaultTimeout)
        
    def _retrieve(self, map):
        """Query Squid Proxy Server Manager Interface for stats.
        
        @param map: Statistics map name.
        @return:    Dictionary of query results.
        
        """
        self._conn.request('GET', "cache_object://%s/%s" % (self._host, map), 
                           None, self._httpHeaders)
        rp = self._conn.getresponse()
        if rp.status == 200:
            data = rp.read()
            return data
        else:
            raise Exception("Retrieval of stats from Squid Proxy Server"
                            "on host %s and port %s failed.\n"
                            "HTTP - Status: %s    Reason: %s" 
                            % (self._host, self._port, rp.status, rp.reason))
    
    def _parseCounters(self, data):
        """Parse simple stats list of key, value pairs.
        
        @param data: Multiline data with one key-value pair in each line.
        @return:     Dictionary of stats.
            
        """
        info_dict = util.NestedDict()
        for line in data.splitlines():
            mobj = re.match('^\s*([\w\.]+)\s*=\s*(\S.*)$', line)
            if mobj:
                (key, value) = mobj.groups()
                klist = key.split('.')
                info_dict.set_nested(klist, parse_value(value))
        return info_dict
    
    def _parseSections(self, data):
        """Parse data and separate sections. Returns dictionary that maps 
        section name to section data.
        
        @param data: Multiline data.
        @return:     Dictionary that maps section names to section data.
        
        """
        section_dict = {}
        lines = data.splitlines()
        idx = 0
        numlines = len(lines)
        section = None
        while idx < numlines:
            line = lines[idx]
            idx += 1
            mobj = re.match('^(\w[\w\s\(\)]+[\w\)])\s*:$', line)
            if mobj:
                section = mobj.group(1)
                section_dict[section] = []
            else:
                mobj = re.match('(\t|\s)\s*(\w.*)$', line)
                if mobj:
                    section_dict[section].append(mobj.group(2))
                else:
                    mobj = re.match('^(\w[\w\s\(\)]+[\w\)])\s*:\s*(\S.*)$', line)
                    if mobj:
                        section = None
                        if not section_dict.has_key(section):
                            section_dict[section] = []
                        section_dict[section].append(line)
                    else:
                        if not section_dict.has_key('PARSEERROR'):
                            section_dict['PARSEERROR'] = []
                        section_dict['PARSEERROR'].append(line)   
        return section_dict

    def getMenu(self):
        """Get manager interface section list from Squid Proxy Server
        
        @return: List of tuples (section, description, type)
            
        """
        data = self._retrieve('')
        info_list = []
        for line in data.splitlines():
            mobj = re.match('^\s*(\S.*\S)\s*\t\s*(\S.*\S)\s*\t\s*(\S.*\S)$', line)
            if mobj:
                info_list.append(mobj.groups())
        return info_list
    
    def getCounters(self):
        """Get Traffic and Resource Counters from Squid Proxy Server.
        
        @return: Dictionary of stats.
            
        """
        data = self._retrieve('counters')
        return self._parseCounters(data)
    
    def getInfo(self):
        """Get General Run-time Information from Squid Proxy Server.
        
        @return: Dictionary of stats.
            
        """
        data = self._retrieve('info')
        return data
