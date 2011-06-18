"""Implements TomcatInfo Class for gathering stats from Apache Tomcat Server.

The statistics are obtained by connecting to and querying local and/or 
remote Apache Tomcat Servers. 

"""

import sys
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


if sys.version_info[:2] < (2,5):
    from elementtree import ElementTree #@UnresolvedImport @UnusedImport
else:
    from xml.etree import ElementTree #@Reimport

defaultTomcatPort = 8080
defaultTomcatSSLport = 8443


class TomcatInfo:
    """Class to retrieve stats for Apache Tomcat Application Server."""

    def __init__(self, host=None, port=None, user=None, password=None,
                 ssl=False, autoInit=True):
        """Initialize Apache Tomcat Manager access.
        
        @param host:     Apache Tomcat Host. (Default: 127.0.0.1)
        @param port:     Apache Tomcat Port. (Default: 8080, SSL: 8443)
        @param user:     Apache Tomcat Manager User.
        @param password: Apache Tomcat Manager Password.
        @param ssl:      Use SSL if True. (Default: False)
        @param autoInit: If True connect to Apache Tomcat Server on instantiation.
            
        """
        if host is not None:
            self._host = host
        else:
            self._host = '127.0.0.1'
        if port is not None:
            self._port = port
        else:
            if ssl:
                self._port = defaultTomcatSSLport
            else:
                self._port = defaultTomcatPort
        self._user = user
        self._password = password
        if ssl:
            self._proto = 'https'
        else:
            self._proto = 'http'
        self._statusxml = None 
        if autoInit:
            self.initStats()

    def _retrieve(self):
        """Query Apache Tomcat Server Status Page in XML format and return 
        the result as an ElementTree object.
        
        @return: ElementTree object of Status Page XML.
        
        """
        if self._user is not None and self._password is not None:
            url = "%s://%s:%s@%s:%d/manager/status?XML=true" % (self._proto,
                urllib.quote(self._user), urllib.quote(self._password), 
                self._host, self._port)
        else:
            url = "%s://%s:%d/manager/status?XML=true" % (self._proto,
                 self._host, self._port)
        fp = urllib.urlopen(url)
        response = util.socket_read(fp)
        fp.close()
        tree = ElementTree.XML(response)
        return tree
    
    def initStats(self):
        """Query Apache Tomcat Server Status Page to initialize statistics."""
        self._statusxml = self._retrieve()
        
    def getMemoryStats(self):
        """Return JVM Memory Stats for Apache Tomcat Server.
        
        @return: Dictionary of memory utilization stats.
        
        """
        if self._statusxml is None:
            self.initStats()
        node = self._statusxml.find('jvm/memory')
        memstats = {}
        if node is not None:
            for (key,val) in node.items():
                memstats[key] = util.parse_value(val)
        return memstats
    
    def getConnectorStats(self):
        """Return dictionary of Connector Stats for Apache Tomcat Server.
        
        @return: Nested dictionary of Connector Stats.
        
        """
        if self._statusxml is None:
            self.initStats()
        connnodes = self._statusxml.findall('connector')
        connstats = {}
        if connnodes:
            for connnode in connnodes:
                namestr = connnode.get('name')
                if namestr is not None:
                    mobj = re.match('(\w+)-(\d+)', namestr)
                    if mobj:
                        proto = mobj.group(1)
                        port = int(mobj.group(2))
                        connstats[port] = {'proto': proto}
                        for tag in ('threadInfo', 'requestInfo'):
                            stats = {}
                            node = connnode.find(tag)
                            if node is not None:
                                for (key,val) in node.items():
                                    if re.search('Time$', key):
                                        stats[key] = float(val) / 1000.0
                                    else:
                                        stats[key] = util.parse_value(val)
                            if stats:
                                connstats[port][tag] = stats
        return connstats

