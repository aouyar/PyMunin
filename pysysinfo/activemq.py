"""Implements ActiveMQInfo Class for gathering stats from ActiveMQ.

The statistics are obtained by connecting to and querying the REST API. 

"""

import re
import util
import socket
import json

__author__ = "Nagy, Attila"
__copyright__ = "Copyright 2013, Nagy, Attila"
__credits__ = []
__license__ = "GPL"
__version__ = "0.1.0"
__maintainer__ = "Nagy, Attila"
__email__ = "bra@fsn.hu"
__status__ = "Development"


defaultHTTPport = 8161
defaultHTTPSport = 8162


class ActiveMQInfo:
    """Class to retrieve stats for Apache ActiveMQ."""

    def __init__(self, host=None, port=None, user=None, password=None,
                 statuspath = None, ssl=False, brokername=None, autoInit=True):
        """Initialize ActiveMQ REST API access.
        
        @param host:        ActiveMQ REST API Host. (Default: 127.0.0.1)
        @param port:        ActiveMQ REST API Port. (Default: 8161, SSL: 8162)
        @param user:        Username. (Not needed unless authentication is
                            required to access REST API.
        @param password:    Password. (Not needed unless authentication is
                            required to access REST API.
        @statuspath:        Path of REST API. (Default: hawtio/jolokia)                
        @param ssl:         Use SSL if True. (Default: False)
        @param brokername:  The broker's name. $HOSTNAME is replaced with
                            hostname. (Default: localhost)
        @param autoInit:    If True connect to ActiveMQ on instantiation.
            
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
            self._statuspath = 'hawtio/jolokia'
        if ssl:
            self._proto = 'https'
        else:
            self._proto = 'http'
        if brokername == '$HOSTNAME':
            self._brokername = socket.gethostname()
        elif brokername is not None:
            self._brokername = brokername
        else:
            self._brokername = 'localhost'
        self._statusDict = None 
        if autoInit:
            self.initStats()

    def parseToDict(self,string):
        d={}
        # remove org.apache.activemq:
        string=string.split(':',1)[1]
        for kv in string.split(','):
            (key, value) = kv.split('=',1)
            d[key]=value
        return d    
    
    def initStats(self):
        """Query ActiveMQ REST management API and parse its response."""
        # fetch the stats for the specified brokerName
        url = "%s://%s:%d/%s/read/org.apache.activemq:type=Broker," \
              "brokerName=%s"  % (self._proto, self._host, self._port, 
                                       self._statuspath, self._brokername)
        response = util.get_url(url, self._user, self._password)
        self._statusDict = {}
        p_response = json.loads(response)
        self._statusDict = p_response['value']
        
        # query all objectNames which can be found in lists
        for key in self._statusDict.keys():
            if isinstance(self._statusDict[key],list):                
                for i in xrange(len(self._statusDict[key])):
                    try:
                        objectName=self._statusDict[key][i]['objectName']
                    except KeyError:
                        continue
                    url = "%s://%s:%d/%s/read/%s" % (self._proto,
                                                     self._host,
                                                     self._port,
                                                     self._statuspath,
                                                     objectName)
                    response = util.get_url(url, self._user, self._password)
                    p_response = json.loads(response)
                    self._statusDict[key][i] = p_response['value']
            
    def getServerStats(self):
        """Return Stats for Apache ActiveMQ.
        
        @return: Dictionary of server stats.
        
        """
        return self._statusDict;
    
        
