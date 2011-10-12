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


# Maps
procStatusNames = {'D': 'uninterruptable_sleep',
                   'R': 'running',
                   'S': 'sleep',
                   'T': 'stopped',
                   'W': 'paging',
                   'X': 'dead',
                   'Z': 'defunct'} 


class ProcessInfo:
    """Class to retrieve stats for processes."""
    
    def __init__(self):
        """Initialize Process Stats."""
        pass
    
    def _execProcCmd(self, *args):
        """Execute ps command with positional params args and return result as 
        list of lines.
        
        @param *args: Positional params for ps command.
        @return:      List of output lines
        
        """
        try:
            out = subprocess.Popen([psCmd,] + list(args), 
                                   stdout=subprocess.PIPE).communicate()[0]
        except:
            raise Exception('Execution of command %s failed.' % psCmd)
        return out.splitlines()
    
    def getProcDict(self, threads=False, *fields):
        """Execute ps command with custom output format with columns from fields
        positional arguments and return result as a nested dictionary.
        
        @param threads: If True, include threads in output.
        @param *fields: Fields included in the output.
        @return:        Nested dictionary indexed by:
                          PID for process info.
                          SPID for thread info.
        
        """
        if threads:
            opts = '-eT'
            key = 'spid'
        else:
            opts = '-e'
            key = 'pid'
        stats = {}
        lines = self._execProcCmd(opts, '-o', ','.join([key,] + list(fields)))
        if len(lines) > 1:
            headers = lines[0].split()[1:]
            for line in lines[1:]:
                cols = line.split()
                stats[cols[0]] = dict(zip(headers, cols[1:]))
        return stats
    
    def getProcList(self, threads=False, *fields):
        """Execute ps command with custom output format with columns from fields
        positional arguments and return result as a nested list.
        
        @param threads: If True, include threads in output. 
        @param *fields: Fields included in the output.
        @return:        List of headers and list of rows and columns.
        
        """
        if threads:
            opts = '-eT'
        else:
            opts = '-e'
        lines = self._execProcCmd(opts, '-o', ','.join(fields))
        if len(lines) > 1:
            headers = lines[0].split()
            stats = [line.split() for line in lines] 
        return {'headers': headers, 'stats': stats}
    
    def getProcStatStatus(self, threads=False):
        """Return process counts per status and priority.
        
        @return: Dictionary of process counters.
        
        """
        procs = self.getProcList(threads, 'stat')
        status = dict(zip(procStatusNames.values(), 
                          [0,] * len(procStatusNames)))
        prio = {'high': 0, 'low': 0, 'norm': 0, 'locked_in_mem': 0}
        total = 0
        locked_in_mem = 0
        for cols in procs['stats']:
            col_stat = cols[0]
            status[procStatusNames[col_stat[0]]] += 1
            if '<' in col_stat[1:]:
                prio['high'] += 1
            elif 'N' in col_stat[1:]:
                prio['low'] += 1
            else:
                prio['norm'] += 1
            if 'L' in col_stat[1:]:
                locked_in_mem += 1
            total += 1
        return {'status': status, 
                'prio': prio, 
                'locked_in_mem': locked_in_mem, 
                'total': total}
    
    
    
    
