"""Implements NginxInfo Class for gathering stats from Nginx Web Server.

The statistics are obtained by connecting to and querying the server-status
page of local and/or remote Nginx Web Servers. 

"""

import re
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


defaultHTTPport = 80
defaultHTTPSport = 443


class NginxInfo:
    """Class to retrieve stats for Nginx Web Server."""

    def __init__(self, host=None, port=None, user=None, password=None,
                 statuspath = None, ssl=False, autoInit=True):
        """Initialize Nginx server-status URL access.
        
        @param host:     Nginx Web Server Host. (Default: 127.0.0.1)
        @param port:     Nginx Web Server Port. (Default: 80, SSL: 443)
        @param user:     Username. (Not needed unless authentication is required 
                         to access server-status page.
        @param password: Password. (Not needed unless authentication is required 
                         to access server-status page.
        @statuspath:     Path of status page. (Default: nginx_status)                
        @param ssl:      Use SSL if True. (Default: False)
        @param autoInit: If True connect to Nginx Web Server on instantiation.
            
        """
        if host is not None:
            self._host = host
        else:
            self._host = '127.0.0.1'
        if port is not None:
            self._port = port
        else:
            if ssl:
                self._port = defaultHTTPSport
            else:
                self._port = defaultHTTPport
        self._user = user
        self._password = password
        if statuspath is not None:
            self._statuspath = statuspath
        else:
            self._statuspath = 'nginx_status'
        if ssl:
            self._proto = 'https'
        else:
            self._proto = 'http'
        self._statusDict = None 
        if autoInit:
            self.initStats()

    def initStats(self):
        """Query and parse Nginx Web Server Status Page."""
        if self._user is not None and self._password is not None:
            url = "%s://%s:%s@%s:%d/%s" % (self._proto,
                urllib.quote(self._user), urllib.quote(self._password), 
                self._host, self._port, self._statuspath)
        else:
            url = "%s://%s:%d/%s" % (self._proto, self._host, self._port, 
                                     self._statuspath)
        fp = urllib.urlopen(url)
        response = util.socket_read(fp)
        fp.close()
        self._statusDict = {}
        for line in response.splitlines():
            mobj = re.match('\s*(\d+)\s+(\d+)\s+(\d+)\s*$', line)
            if mobj:
                idx = 0
                for key in ('accepts','handled','requests'):
                    idx += 1
                    self._statusDict[key] = util.parse_value(mobj.group(idx))
            else:
                for (key,val) in re.findall('(\w+):\s*(\d+)', line):
                    self._statusDict[key.lower()] = util.parse_value(val)
    
    def getServerStats(self):
        """Return Stats for Nginx Web Server.
        
        @return: Dictionary of server stats.
        
        """
        return self._statusDict;
    
        