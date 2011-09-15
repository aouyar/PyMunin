"""Implements SystemInfo Class for gathering system stats.

"""

import re
import os
import platform

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


# Defaults
uptimeFile = '/proc/uptime'
loadavgFile = '/proc/loadavg'
cpustatFile = '/proc/stat'
meminfoFile = '/proc/meminfo'
swapsFile = '/proc/swaps'
vmstatFile = '/proc/vmstat'



class SystemInfo:
    """Class to retrieve stats for system resources."""
    
    def getPlatformInfo(self):
        """Get platform info.
        
        @return: Platform information in dictionary format.
        
        """
        info = platform.uname()
        return {
            'hostname': info[1],
            'arch': info[4],
            'os': info[0],
            'osversion': info[2]
            }

    def getUptime(self):
        """Return system uptime in seconds.
        
        @return: Float that represents uptime in seconds.
        
        """
        try:
            fp = open(uptimeFile, 'r')
            line = fp.readline()
            fp.close()
        except:
            raise IOError('Failed reading stats from file: %s' % uptimeFile)
        return float(line.split()[0])
    
    def getLoadAvg(self):
        """Return system Load Average.
        
        @return: List of 1 min, 5 min and 15 min Load Average figures.
        
        """
        try:
            fp = open(loadavgFile, 'r')
            line = fp.readline()
            fp.close()
        except:
            raise IOError('Failed reading stats from file: %s' % loadavgFile)
        arr = line.split()
        if len(arr) >= 3:
            return [float(col) for col in arr[:3]]
        else:
            return None
        
    def getCPUuse(self):
        """Return cpu time utilization in seconds.
        
        @return: Dictionary of stats.
        
        """
        hz = os.sysconf('SC_CLK_TCK')
        info_dict = {}
        try:
            fp = open(cpustatFile, 'r')
            line = fp.readline()
            fp.close()
        except:
            raise IOError('Failed reading stats from file: %s' % cpustatFile)
        headers = ['user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal', 'guest']
        arr = line.split()
        if len(arr) > 1 and arr[0] == 'cpu':
            return dict(zip(headers[0:len(arr)], [(float(t) / hz) for t in arr[1:]]))
        return info_dict
    
    def getProcessStats(self):
        """Return stats for running and blocked processes, forks, 
        context switches and interrupts.
        
        @return: Dictionary of stats.
        
        """
        info_dict = {}
        try:
            fp = open(cpustatFile, 'r')
            data = fp.read()
            fp.close()
        except:
            raise IOError('Failed reading stats from file: %s' % cpustatFile)
        for line in data.splitlines():
            arr = line.split()
            if len(arr) > 1 and arr[0] in ('ctxt', 'intr', 'softirq',
                                           'processes', 'procs_running', 
                                           'procs_blocked'):
                info_dict[arr[0]] = arr[1]
        return info_dict
        
    def getMemoryUse(self):
        """Return stats for memory utilization.
        
        @return: Dictionary of stats.
        
        """
        info_dict = {}
        try:
            fp = open(meminfoFile, 'r')
            data = fp.read()
            fp.close()
        except:
            raise IOError('Failed reading stats from file: %s' % meminfoFile)
        for line in data.splitlines():
            mobj = re.match('^(.+):\s*(\d+)\s*(\w+|)\s*$', line)
            if mobj:
                if mobj.group(3).lower() == 'kb':
                    mult = 1024
                else:
                    mult = 1
                info_dict[mobj.group(1)] = int(mobj.group(2)) * mult
        return info_dict
    
    def getSwapStats(self):
        """Return information on swap partition and / or files.
        
            @return: Dictionary of stats.
            
        """
        info_dict = {}
        try:
            fp = open(swapsFile, 'r')
            data = fp.read()
            fp.close()
        except:
            raise IOError('Failed reading stats from file: %s' % swapsFile)
        lines = data.splitlines()
        if len(lines) > 1:
            colnames = [name.lower() for name in lines[0].split()]
            for line in lines[1:]:
                cols = line.split()
                info_dict[cols[0]] = dict(zip(colnames[1:], cols[1:]))
        return info_dict
    
    def getVMstats(self):
        """Return stats for Virtual Memory Subsystem.
        
        @return: Dictionary of stats.
        
        """
        info_dict = {}
        try:
            fp = open(vmstatFile, 'r')
            data = fp.read()
            fp.close()
        except:
            raise IOError('Failed reading stats from file: %s' % vmstatFile)
        for line in data.splitlines():
            cols = line.split()
            if len(cols) == 2:
                info_dict[cols[0]] = cols[1]
        return info_dict
