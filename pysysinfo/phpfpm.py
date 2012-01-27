"""Implements PHPfpmInfo Class for gathering stats from PHP FastCGI Process 
Manager using the status page.

The status interface of PHP FastCGI Process Manager must be enabled. 

"""

import re
import urllib
import util

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.8"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


defaultHTTPport = 80
defaultHTTPSport = 443


class PHPfpmInfo:
    """Class to retrieve stats from APC from Web Server."""

    def __init__(self, host=None, port=None, user=None, password=None,
                 monpath=None, ssl=False):
        """Initialize URL for PHP FastCGI Process Manager status page.
        
        @param host:     Web Server Host. (Default: 127.0.0.1)
        @param port:     Web Server Port. (Default: 80, SSL: 443)
        @param user:     Username. (Not needed unless authentication is required 
                         to access status page.
        @param password: Password. (Not needed unless authentication is required 
                         to access status page.
        @param monpath:  PHP FPM  path relative to Document Root.
                         (Default: fpm_status.php)
        @param ssl:      Use SSL if True. (Default: False)
            
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
        if ssl:
            self._proto = 'https'
        else:
            self._proto = 'http'
        if monpath:
            self._monpath = monpath
        else:
            self._monpath = 'fpm_status.php'

    def getStats(self):
        """Query and parse Web Server Status Page.
        
        """
        if self._user is not None and self._password is not None:
            url = "%s://%s:%s@%s:%d/%s" % (self._proto,
                urllib.quote(self._user), urllib.quote(self._password), 
                self._host, self._port, self._monpath)
        else:
            url = "%s://%s:%d/%s" % (self._proto, self._host, self._port, 
                                     self._monpath)
        fp = urllib.urlopen(url)
        response = util.socket_read(fp)
        fp.close()
        stats = {}
        for line in response.splitlines():
            mobj = re.match('([\w\s]+):\s+(\w+)$', line)
            if mobj:
                stats[mobj.group(1)] = util.parse_value(mobj.group(2))
        return stats
    
                
            
