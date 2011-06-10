"""Implements APCinfo Class for gathering stats from Alternative PGP Accelerator.

The statistics are obtained through a request to custom apcinfo.php script
that must be placed in the Apache Web Server Document Root Directory.

"""

__author__="Ali Onur Uyar"
__date__ ="$Dic 29, 2010 2:55:43 PM$"

import urllib
import util


defaultApachePort = 80
defaultApacheSSLport = 443

buffSize = 4096


class APCinfo:
    """Class to retrieve stats from APC on Apache Web Server."""

    def __init__(self, host=None, port=None, user=None, password=None,
                 relurl=None, ssl=False, autoInit=True):
        """Initialize URL for APC stats access.
        
        @param host:     Apache Web Server Host. (Default: 127.0.0.1)
        @param port:     Apache Web Server Port. (Default: 8080, SSL: 8443)
        @param user:     Username. (Not needed unless authentication is required 
                         to access status page.
        @param password: Password. (Not needed unless authentication is required 
                         to access status page.
        @param relurl:   URL of APC status script relative to Document Root.
        @param ssl:      Use SSL if True. (Default: False)
        @param autoInit: If True connect to Apache Web Server on creation.
            
        """
        if host is not None:
            self._host = host
        else:
            self._host = '127.0.0.1'
        if port is not None:
            self._port = port
        else:
            if ssl:
                self._port = defaultApacheSSLport
            else:
                self._port = defaultApachePort
        self._user = user
        self._password = password
        if ssl:
            self._proto = 'https'
        else:
            self._proto = 'http'
        if relurl:
            self._relurl = relurl
        else:
            self._relurl = 'apcinfo.php'
        self._statusDict = None 
        if autoInit:
            self.initStats()

    def initStats(self):
        """Query and parse Apache Web Server Status Page.
        
        """
        if self._user is not None and self._password is not None:
            url = "%s://%s:%s@%s:%d/%s" % (self._proto,
                urllib.quote(self._user), urllib.quote(self._password), 
                self._host, self._port, self._relurl)
        else:
            url = "%s://%s:%d/%s" % (self._proto, self._host, self._port, self._relurl)
        fp = urllib.urlopen(url)
        response = ''
        oldlen = 0
        newlen = 0
        while True:
            response += fp.read(buffSize)
            newlen = len(response)
            if newlen - oldlen == 0:
                break
            else:
                oldlen = newlen
        fp.close()
        self._statusDict = {}
        for line in response.splitlines():
            cols = line.split(':')
            if not self._statusDict.has_key(cols[0]):
                self._statusDict[cols[0]] = {}
            self._statusDict[cols[0]][cols[1]] = util.parse_value(cols[2])

    
    def getMemoryStats(self):
        """Return Memory Utilization Stats for APC.
        
        @return: Dictionary of stats.
        
        """
        return self._statusDict.get('memory');
    
    def getSysCacheStats(self):
        """Return System Cache Stats for APC.
        
        @return: Dictionary of stats.
        
        """
        return self._statusDict.get('cache_sys');
    
    def getUserCacheStats(self):
        """Return User Cache Stats for APC.
        
        @return: Dictionary of stats.
        
        """
        return self._statusDict.get('cache_user');

    def getAllStats(self):
        """Return All Stats for APC.
        
        @return: Nested dictionary of stats.
        
        """
        return self._statusDict;    

        