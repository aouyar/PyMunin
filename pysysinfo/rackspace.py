"""Implements methods for gathering stats from Rackspace Cloud Service.

"""

import cloudfiles

__author__ = "Ben Welsh"
__copyright__ = "Copyright 2012, Ben Welsh"
__credits__ = []
__license__ = "GPL"
__version__ = "0.2"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class CloudFilesInfo:
    """
    Establishes connection to Rackspace Cloud to retrieve stats on Cloud Files.
    """
    def __init__(self, username, api_key, 
                region=None, servicenet=False, timeout=4):
        """Initialize connection to Rackspace Cloud Files.
        
        @param username: Rackspace Cloud username
        @param api_key:  Rackspace Cloud api_key
        @param region:   Try passing "us" for US Auth Service, and "uk" UK Auth 
                         Service; omit parameter to use library default.
        @servicenet:     If True, Rackspace ServiceNet network will be used to 
                         access Cloud Files.
        @timeout:        Connection timeout in seconds. (Default: 4)
        
        """
        self._connParams = {}
        self._connParams['username'] = username
        self._connParams['api_key'] = api_key
        if region is not None:
            try:
                authurl = getattr(cloudfiles, '%s_authurl' % str(region))
                self._connParams['authurl'] = authurl
            except:
                raise Exception("Invalid region code: %s" % str(region))
        if servicenet:
            self._connParams['servicenet'] = True
        self._connParams['timeout'] = timeout
        self._conn = cloudfiles.get_connection(**self._connParams)
        
    def getContainerList(self, limit=None, marker=None):
        """Returns list of Rackspace Cloud Files containers names.
        
        @param limit:  Number of containers to return.
        @param marker: Return only results whose name is greater than marker.
        @return:       List of container names.
        
        """
        return self._conn.list_containers(limit, marker)
    
    def getContainerStats(self, limit=None, marker=None):
        """Returns Rackspace Cloud Files usage stats for containers.
        
        @param limit:  Number of containers to return.
        @param marker: Return only results whose name is greater than marker.
        @return:       Dictionary of container stats indexed by container name.
        
        """
        stats = {}
        for row in self._conn.list_containers_info(limit, marker):
            stats[row['name']] = {'count': row['count'], 'size': row['bytes']}
        return stats
