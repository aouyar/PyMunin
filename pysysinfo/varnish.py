"""Implements VarnishInfo Class for gathering stats from Varnish Cache.

The statistics are obtained by running the command varnishstats.

"""

import re
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
varnishstatCmd = "varnishstat"



class VarnishInfo:
    """Class to retrieve stats from Varnish Cache."""
    
    _descDict = {}
    
    def __init__(self, instance=None):
        """Initialization for monitoring Varnish Cache instance.
        
        @param instance: Name  of the Varnish Cache instance.
                        (Defaults to hostname.)
        """
        self._instance = instance
        

    def getStats(self):
        """Runs varnishstats command to get stats from Varnish Cache.
        
        @return: Dictionary of stats.

        """
        info_dict = {}
        args = [varnishstatCmd, '-1']
        if self._instance is not None:
            args.extend(['-n', self._instance])
        output = util.exec_command(args)
        if self._descDict is None:
            self._descDict = {}
        for line in output.splitlines():
            mobj = re.match('(\S+)\s+(\d+)\s+(\d+\.\d+|\.)\s+(\S.*\S)\s*$', 
                            line)
            if mobj:
                info_dict[mobj.group(1)] = util.parse_value(mobj.group(2))
                self._descDict[mobj.group(1)] = mobj.group(4)
        return info_dict
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