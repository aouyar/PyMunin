"""Implements IfaceInfo Class for gathering stats from Network Interfaces.

"""

import re
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
ifaceStatsFile = '/proc/net/dev'
ipCmd = '/sbin/ip'
routeCmd = '/sbin/route'


class NetIfaceInfo:
    """Class to retrieve stats for Network Interfaces."""

    def getIfStats(self):
        """Return dictionary of Traffic Stats for Network Interfaces.
        
        @return: Nested dictionary of statistics for each interface.
        
        """
        info_dict = {}
        try:
            fp = open(ifaceStatsFile, 'r')
            data = fp.read()
            fp.close()
        except:
            raise IOError('Failed reading interface stats from file: %s'
                          % ifaceStatsFile)
        for line in data.splitlines():
            mobj = re.match('^\s*([\w\d:]+):\s*(.*\S)\s*$', line)
            if mobj:
                iface = mobj.group(1)
                statline = mobj.group(2)
                info_dict[iface] = dict(zip(
                    ('rxbytes', 'rxpackets', 'rxerrs', 'rxdrop', 'rxfifo',
                     'rxframe', 'rxcompressed', 'rxmulticast',
                     'txbytes', 'txpackets', 'txerrs', 'txdrop', 'txfifo',
                     'txcolls', 'txcarrier', 'txcompressed'),
                    [int(x) for x in statline.split()]))
                    
        return info_dict
    
    def getIfConfig(self):
        """Return dictionary of Interface Configuration (ifconfig).
        
        @return: Dictionary of if configurations keyed by if name.
        
        """
        conf = {}
        try:
            out = subprocess.Popen([ipCmd, "addr", "show"], 
                                   stdout=subprocess.PIPE).communicate()[0]
        except:
            raise Exception('Execution of command %s failed.' % ipCmd)
        for line in out.splitlines():
            mobj = re.match('^\d+: (\S+):\s+<(\S*)>\s+(\S.*\S)\s*$', line)
            if mobj:
                iface = mobj.group(1)
                conf[iface] = {}
                continue
            mobj = re.match('^\s{4}link\/(.*\S)\s*$', line)
            if mobj:
                arr = mobj.group(1).split()
                if len(arr) > 0:
                    conf[iface]['type'] = arr[0]
                if len(arr) > 1:
                    conf[iface]['hwaddr'] = arr[1]
                continue
            mobj = re.match('^\s+(inet|inet6)\s+([\d\.\:A-Za-z]+)\/(\d+)($|\s+.*\S)\s*$', line)
            if mobj:
                proto = mobj.group(1)
                if not conf[iface].has_key(proto):
                    conf[iface][proto] = []
                addrinfo = {}
                addrinfo['addr'] = mobj.group(2).lower()
                addrinfo['mask'] = int(mobj.group(3))
                arr = mobj.group(4).split()
                if len(arr) > 0 and arr[0] == 'brd':
                    addrinfo['brd'] = arr[1]
                conf[iface][proto].append(addrinfo)
                continue
        return conf
    
    def getRoutes(self):
        """Get routing table.
        
        @return: List of routes.
        
        """
        routes = []
        try:
            out = subprocess.Popen([routeCmd, "-n"], 
                                   stdout=subprocess.PIPE).communicate()[0]
        except:
            raise Exception('Execution of command %s failed.' % ipCmd)
        lines = out.splitlines()
        if len(lines) > 1:
            headers = [col.lower() for col in lines[1].split()]
            for line in lines[2:]:
                routes.append(dict(zip(headers, line.split())))
        return routes
