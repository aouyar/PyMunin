"""Implements ApacheInfo Class for gathering stats from Apache Web Server.

The statistics are obtained by connecting to and querying the server-status
page of local and/or remote Apache Web Servers. 

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


class ApacheInfo:
    """Class to retrieve stats for Apache Web Server."""

    def __init__(self, host=None, port=None, user=None, password=None,
                 statuspath = None, ssl=False, autoInit=True):
        """Initialize Apache server-status URL access.
        
        @param host:     Apache Web Server Host. (Default: 127.0.0.1)
        @param port:     Apache Web Server Port. (Default: 80, SSL: 443)
        @param user:     Username. (Not needed unless authentication is required 
                         to access server-status page.
        @param password: Password. (Not needed unless authentication is required 
                         to access server-status page.
        @statuspath:     Path of status page. (Default: server-status)                
        @param ssl:      Use SSL if True. (Default: False)
        @param autoInit: If True connect to Apache Web Server on instantiation.
            
        """
        if host is not None:
            self._host = host
        else:
            self._host = '127.0.0.1'
        if port is not None:
            self._port = int(port)
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
            self._statuspath = 'server-status'
        if ssl:
            self._proto = 'https'
        else:
            self._proto = 'http'
        self._statusDict = None 
        if autoInit:
            self.initStats()

    def initStats(self):
        """Query and parse Apache Web Server Status Page."""
        if self._user is not None and self._password is not None:
            url = "%s://%s:%s@%s:%d/%s?auto" % (self._proto, 
                      urllib.quote(self._user), urllib.quote(self._password), 
                      self._host, self._port, self._statuspath)
        else:
            url = "%s://%s:%d/%s?auto"  % (self._proto, self._host, self._port, 
                                           self._statuspath)
        fp = urllib.urlopen(url)
        response = util.socket_read(fp)
        fp.close()
        self._statusDict = {}
        for line in response.splitlines():
            mobj = re.match('(\S.*\S)\s*:\s*(\S+)\s*$', line)
            if mobj:
                self._statusDict[mobj.group(1)] = util.parse_value(mobj.group(2))
        if self._statusDict.has_key('Scoreboard'):
            self._statusDict['MaxWorkers'] = len(self._statusDict['Scoreboard'])
    
    def getServerStats(self):
        """Return Stats for Apache Web Server.
        
        @return: Dictionary of server stats.
        
        """
        return self._statusDict;
    
        