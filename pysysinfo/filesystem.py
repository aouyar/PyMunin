"""Implements DiskUsageInfo Class for gathering disk usage stats.

"""

import subprocess

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


# Defaults
dfCmd = '/bin/df'
mountsFile = '/proc/mounts'



class DiskUsageInfo:
    """Class to retrieve stats for disk utilization."""
    
    def __init__(self):
        """ Read /proc/mounts to get filesystem types.
        
        """
        self._fstypeDict = {}
        try:
            fp = open(mountsFile, 'r')
            data = fp.read()
            fp.close()
        except:
            raise Exception('Reading of file %s failed.' % mountsFile)
        for line in data.splitlines():
            cols = line.split()
            self._fstypeDict[cols[1]] = cols[2]
    
    def getFSlist(self):
        """Returns list of filesystems.
        
        @return: Lis of filesystems.
        
        """
        return self._fstypeDict.keys()

    def getSpaceUse(self):
        """Get disk space usage.
        
        @return: Dictionary of filesystem space utilization stats for filesystems.
        
        """
        stats = {}
        try:
            out = subprocess.Popen([dfCmd, "-Pk"], 
                                   stdout=subprocess.PIPE).communicate()[0]
        except:
            raise Exception('Execution of command %s failed.' % dfCmd)
        lines = out.splitlines()
        if len(lines) > 1:
            for line in lines[1:]:
                fsstats = {}
                cols = line.split()
                fsstats['device'] = cols[0]
                fsstats['type'] = self._fstypeDict[cols[5]]
                fsstats['total'] = 1024 * int(cols[1])
                fsstats['inuse'] = 1024 * int(cols[2])
                fsstats['avail'] = 1024 * int(cols[3])
                fsstats['inuse_pcent'] = int(cols[4][:-1])
                stats[cols[5]] = fsstats
        return stats
    
    def getInodeUse(self):
        """Get disk space usage.
        
        @return: Dictionary of filesysten inode utilization stats for filesystems.
        
        """
        stats = {}
        try:
            out = subprocess.Popen([dfCmd, "-i", "-Pk"], 
                                   stdout=subprocess.PIPE).communicate()[0]
        except:
            raise Exception('Execution of command %s failed.' % dfCmd)
        lines = out.splitlines()
        if len(lines) > 1:
            for line in lines[1:]:
                fsstats = {}
                cols = line.split()
                fsstats['device'] = cols[0]
                fsstats['type'] = self._fstypeDict[cols[5]]
                fsstats['total'] = int(cols[1])
                fsstats['inuse'] = int(cols[2])
                fsstats['avail'] = int(cols[3])
                fsstats['inuse_pcent'] = int(cols[4][:-1])
                stats[cols[5]] = fsstats
        return stats
