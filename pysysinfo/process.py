"""Implements ProcessInfo Class for gathering process stats.

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
psCmd = '/bin/ps'



class ProcessInfo:
    """Class to retrieve stats for processes."""
    
    def __init__(self):
        """Initialize Process Stats."""
        pass
    
    def _getStats(self, field_list):
        stats = {}
        format_opt = ",".join(['pid',] + field_list)
        try:
            out = subprocess.Popen([psCmd, "-e", "-o", format_opt], 
                                   stdout=subprocess.PIPE).communicate()[0]
        except:
            raise Exception('Execution of command %s failed.' % psCmd)
        lines = out.splitlines()
        if len(lines) > 1:
            headers = lines[0].split()[1:]
            for line in lines[1:]:
                print line
                cols = line.split()
                stats[cols[0]] = dict(zip(headers, cols[1:]))
        return stats
