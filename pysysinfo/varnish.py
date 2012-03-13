"""Implements VarnishInfo Class for gathering stats from Varnish Proxy Server.

The statistics are obtained by running the command varnishstats.

"""

import re
import commands
import util

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.8"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


# Defaults
varnishstatCmd = "varnishstat -1"



class VarnishInfo:
    """Class to retrieve stats from Varnish Proxy Server."""
    
    _descDict = {}

    def getStats(self):
        """Runs varnishstats command to get stats from Varnish Proxy Server.
        
        @return: Dictionary of stats.

        """
        info_dict = {}
        (retval, output) = commands.getstatusoutput(varnishstatCmd)
        if retval == 0:
            if self._descDict is None:
                self._descDict = {}
            for line in output.splitlines():
                mobj = re.match('(\S+)\s+(\d+)\s+(\d+\.\d+|\.)\s+(\S.*\S)\s*$', 
                                line)
                if mobj:
                    info_dict[mobj.group(1)] = util.parse_value(mobj.group(2))
                    self._descDict[mobj.group(1)] = mobj.group(4)
            return info_dict
        else:
            raise Exception("Execution of command failed: %s" % varnishstatCmd)
        return info_dict
    
    def getDescDict(self):
        """Returns dictionary mapping stats entries to decriptions.
        
        @return: Dictionary.
        
        """
        if len(self._descDict) == 0:
            self.getStats()
        return self._descDict
    
    def getDesc(self, entry):
        """Returns description for stat entry.
        
        @param entry: Entry name.
        @return:      Description for entry.
        
        """
        if len(self._descDict) == 0:
            self.getStats()
        return self._descDict.get(entry)