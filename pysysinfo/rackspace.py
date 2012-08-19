"""
Implements methods for gathering stats from Rackspace.
"""
import cloudfiles

__author__ = "Ben Welsh"
__copyright__ = "Copyright 2012, Ben Welsh"
__credits__ = []
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Ben Welsh"
__email__ = "ben.welsh@gmail.com"
__status__ = "Development"


class RackspaceContainerInfo:
    """
    Establishes connection to Rackspace to retrieve statistics on operation.
    """
    def __init__(self, container, username, api_key):
        """
        Initialize connection to Rackspace.
        
        @param container: Rackspace CDN container
        @param username: Rackspace username
        @param api_key: Rackspace api_key
        """
        self.container = container
        self.username = username
        self.api_key = api_key
    
    def getStats(self):
        """
        Query Rackspace and return stats.
        
        @return: Dictionary of stats.
        """
        conn = cloudfiles.get_connection(self.username, self.api_key)
        bucket = conn.get_container(self.container)
        return {
            'rackspace_containercount': bucket.object_count,
            'rackspace_containersize': bucket.size_used
        }

