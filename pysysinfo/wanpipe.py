"""Implements WanpipeInfo Class for gathering stats from Wanpipe
Telephony Interfaces.

"""

import re
import commands
import netiface

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


# Defaults
wanpipemonCmd = '/usr/sbin/wanpipemon -i %s -c Ta'


class WanpipeInfo:
    """Class to retrieve stats for Wanpipe Interfaces."""

    def getIfaceStats(self):
        """Return dictionary of Traffic Stats for each Wanpipe Interface.
        
        @return: Nested dictionary of statistics for each interface.
        
        """
        ifInfo = netiface.NetIfaceInfo()
        ifStats = ifInfo.getIfStats()
        info_dict = {}
        for ifname in ifStats:
            if re.match('^w\d+g\d+$', ifname):
                info_dict[ifname] = ifStats[ifname]        
        return info_dict
    
    def getPRIstats(self, iface):
        """Return RDSI Operational Stats for interface.
        
        @param iface: Interface name. (Ex. w1g1)
        @return:      Nested dictionary of statistics for interface.

        """
        info_dict = {}
        (retval, output) = commands.getstatusoutput(wanpipemonCmd % iface)
        if retval == 0:
            for line in output.splitlines():
                mobj = re.match('^\s*(Line Code Violation|Far End Block Errors|'
                                'CRC4 Errors|FAS Errors)\s*:\s*(\d+)\s*$', 
                                line, re.IGNORECASE)
                if mobj:
                    info_dict[mobj.group(1).lower().replace(' ', '')] = int(mobj.group(2))
                    continue
                mobj = re.match('^\s*(Rx Level)\s*:\s*>{0,1}\s*([-\d\.]+)db\s*', 
                                line, re.IGNORECASE)
                if mobj:
                    info_dict[mobj.group(1).lower().replace(' ', '')] = float(mobj.group(2))
                    continue
        else:
            raise Exception("Execution of command failed: %s" % wanpipemonCmd)
        return info_dict
