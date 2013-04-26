"""Implements ZOPinfo Class for gathering stats from Zend Optimizor +.

The statistics are obtained through a request to custom zopinfo.php script
that must be placed in the Web Server Document Root Directory.

"""

import util
import json

__author__ = "Preston M."
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9.24"
__maintainer__ = "Preston M."
__email__ = "pentie at gmail.com"
__status__ = "Development"


defaultHTTPport = 80
defaultHTTPSport = 443


class ZOPinfo:
    """Class to retrieve stats from APC from Web Server."""

    def __init__(self, host=None, port=None, user=None, password=None,
                 monpath=None, ssl=False, extras=False, autoInit=True):
        """Initialize URL for APC stats access.
        
        @param host:     Web Server Host. (Default: 127.0.0.1)
        @param port:     Web Server Port. (Default: 80, SSL: 443)
        @param user:     Username. (Not needed unless authentication is required 
                         to access status page.
        @param password: Password. (Not needed unless authentication is required 
                         to access status page.
        @param monpath:  APC status script path relative to Document Root.
                         (Default: apcinfo.php)
        @param ssl:      Use SSL if True. (Default: False)
        @param extras:   Include extra metrics, which can be computationally more 
                         expensive.
        @param autoInit: If True connect to Web Server on instantiation.
            
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
        if ssl:
            self._proto = 'https'
        else:
            self._proto = 'http'
        if monpath:
            self._monpath = monpath
        else:
            self._monpath = 'zopinfo.php'
        self._extras = extras
        self._statusDict = None
        if autoInit:
            self.initStats()

    def initStats(self, extras=None):
        """Query and parse Web Server Status Page.
        
        @param extras: Include extra metrics, which can be computationally more 
                       expensive.
        
        """
        url = "%s://%s:%d/%s" % (self._proto, self._host, self._port, self._monpath)
        response = util.get_url(url, self._user, self._password)
        #with open('/tmp/zopinfo.json') as f:
        #    response = f.read()
        self._statusDict = json.loads(response)
    
    def getAllStats(self):
        """Return All Stats for APC.
        
        @return: Nested dictionary of stats.
        
        """
        return self._statusDict;
