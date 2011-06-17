"""Implements NTPinfo Class for gathering time synchronization stats from NTP.

The statistics are obtained by connecting to and querying local and/or 
remote NTP servers. 

"""

import re
import commands

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


# Defaults
ntpqCmd = "ntpq -n -c peers"
ntpdateCmd = "ntpdate -u -q"


class NTPinfo:
    """Class to retrieve stats for Time Synchronization from NTP Service"""

    def getPeerStats(self):
        """Get NTP Peer Stats for localhost by querying local NTP Server.
        
        @return: Dictionary of NTP stats converted to seconds.

        """
        info_dict = {}
        (retval, output) = commands.getstatusoutput(ntpqCmd)
        if retval == 0:
            for line in output.splitlines():
                mobj = re.match('\*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+', line)
                if mobj:
                    info_dict['ip'] = mobj.group(1)
                    cols = line.split()
                    info_dict['stratum'] = int(cols[2])
                    info_dict['delay'] = float(cols[7]) / 1000.0
                    info_dict['offset'] = float(cols[8]) / 1000.0
                    info_dict['jitter'] = float(cols[9]) / 1000.0
                    return info_dict
        else:
            raise Exception("Execution of command failed: %s" % ntpqCmd)
        return info_dict

    def getHostOffset(self, host):
        """Get NTP Stats and offset of remote host relative to localhost
        by querying NTP Server on remote host.
        
        @param host: Remote Host IP.
        @return:     Dictionary of NTP stats converted to seconds.

        """
        info_dict = {}
        (retval, output) = commands.getstatusoutput("%s %s" % (ntpdateCmd, host))
        if retval == 0:
            for line in output.splitlines():
                mobj = re.match('server.*,\s*stratum\s+(\d),.*'
                                'offset\s+([\d\.-]+),.*delay\s+([\d\.]+)\s*$', 
                                line)
                if mobj:
                    info_dict['stratum'] = int(mobj.group(1))
                    info_dict['delay'] = float(mobj.group(3))
                    info_dict['offset'] = float(mobj.group(2))
                    return info_dict
        return info_dict

    def getHostOffsets(self, hosts):
        """Get NTP Stats and offset of multiple remote hosts relative to localhost
        by querying NTP Servers on remote hosts.
        
        @param host: List of Remote Host IPs.
        @return:     Dictionary of NTP stats converted to seconds.

        """
        info_dict = {}
        (retval, output) = commands.getstatusoutput("%s %s" % (ntpdateCmd, 
                                                               " ".join(hosts)))
        if retval == 0:
            for line in output.splitlines():
                mobj = re.match('server\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}),'
                                '\s*stratum\s+(\d),.*offset\s+([\d\.-]+),'
                                '.*delay\s+([\d\.]+)\s*$', line)
                if mobj:
                    host_dict = {}
                    host = mobj.group(1)
                    host_dict['stratum'] = int(mobj.group(2))
                    host_dict['delay'] = float(mobj.group(4))
                    host_dict['offset'] = float(mobj.group(3))
                    info_dict[host] = host_dict
        return info_dict
