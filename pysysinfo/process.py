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
    
    def execProcCmd(self, *args):
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
    
    def getProcList(self, field_list=['uid', 'cmd',],
                    user_list=None, cmd_list=None, 
                    threads=False):
        """Execute ps command with custom output format with columns from fields
        positional arguments and return result as a nested list.
        
        @param field_list: Fields included in the output.
                           Default: uid, cmd
        @param user_list:  Filter processes by user name or id.
        @param cmd_list:   Filter processes by command name.
        @param threads:    If True, include threads in output. 
        @return:           List of headers and list of rows and columns.
        
        """
        args = []
        stats = {}
        if threads:
            args.append('-T')
        args.append('-o')
        args.append(','.join(field_list))
        filter = False
        if user_list is not None:
            args.append('-u')
            args.append(','.join(user_list))
            filter = True
        if cmd_list is not None:
            args.append('-C')
            args.append(','.join(cmd_list))
            filter = True
        if not filter:
            args.append('-e')
        lines = self.execProcCmd(*args)    
        if len(lines) > 1:
            headers = lines[0].split()
            stats = [line.split() for line in lines[1:]] 
            return {'headers': headers, 'stats': stats}
        else:
            return None
    
    def getProcDict(self, field_list=['uid', 'cmd',],
                    user_list=None, cmd_list=None,
                    threads=False):
        """Execute ps command with custom output format with columns from fields
        positional arguments and return result as a nested dictionary.
        
        @param field_list: Fields included in the output.
                           Default: uid, cmd
                           (PID or SPID column is included by default.)
        @param user_list:  Filter processes by user name or id.
        @param cmd_list:   Filter processes by command name.
        @param threads:    If True, include threads in output.
        @return:           Nested dictionary indexed by:
                             PID for process info.
                             SPID for thread info.
        
        """
        stats = {}
        if threads:
            key = 'spid'
        else:
            key = 'pid'
        field_list.append(key)
        result = self.getProcList(field_list, user_list, cmd_list, threads)
        if result is not None:
            headers = result['headers'][:-1]
            lines = result['stats']
            if len(lines) > 1:
                for cols in lines:
                    stats[cols[-1]] = dict(zip(headers, cols[:-1]))
            return stats
        else:
            return None
    
    def getProcStatStatus(self, threads=False):
        """Return process counts per status and priority.
        
        @return: Dictionary of process counters.
        
        """
        procs = self.getProcList(['stat',], threads=threads)
        status = dict(zip(procStatusNames.values(), 
                          [0,] * len(procStatusNames)))
        prio = {'high': 0, 'low': 0, 'norm': 0, 'locked_in_mem': 0}
        total = 0
        locked_in_mem = 0
        if procs is not None:
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
    
    
    
    
