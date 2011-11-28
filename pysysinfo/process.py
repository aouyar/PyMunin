"""Implements ProcessInfo Class for gathering process stats.

"""

import subprocess
import re
from util import TableFilter

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

psFieldWidth = {'args': 128,
                'cmd': 128,
                'command': 128,
                's': 4,
                'stat': 8,
                'state': 4,}
psDefaultFieldWidth = 16

    
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
    
    def parseProcCmd(self, field_list=['pid', 'user', 'cmd',], threads=False):
        """Execute ps command with custom output format with columns from 
        field_list and return result as a nested list.
        
        The Standard Format Specifiers from ps man page must be used in the
        field_list.
        
        @param field_list: Fields included in the output.
                           Default: pid, user, cmd
        @param threads:    If True, include threads in output. 
        @return:           List of headers and list of rows and columns.
        
        """
        args = []
        headers = [f.lower() for f in field_list]
        args.append('--no-headers')
        args.append('-e')
        if threads:
            args.append('-T')
        field_ranges = []
        fmt_strs = []
        start = 0
        for header in headers:
            field_width = psFieldWidth.get(header, psDefaultFieldWidth)
            fmt_strs.append('%s:%d' % (header, field_width))
            end = start + field_width + 1
            field_ranges.append((start,end))
            start = end
        args.append('-o')
        args.append(','.join(fmt_strs))
        lines = self.execProcCmd(*args)
        if len(lines) > 0:
            stats = []
            for line in lines:
                cols = []
                for (start, end) in field_ranges:
                    cols.append(line[start:end].strip())
                stats.append(cols)
            return {'headers': headers, 'stats': stats}
        else:
            return None
        
    def getProcList(self, field_list=['pid', 'user', 'cmd',], threads=False,
                    **kwargs):
        """Execute ps command with custom output format with columns columns from 
        field_list, select lines using the filters defined by kwargs and return 
        result as a nested list.
        
        The Standard Format Specifiers from ps man page must be used in the
        field_list and filters.
        
        @param field_list: Fields included in the output.
                           Default: pid, user, cmd
        @param threads:    If True, include threads in output.
        @param **kwargs:   Keyword variables are used for filtering the results
                           depending on the values of the columns. Each keyword 
                           must correspond to a field name with an optional 
                           suffix:
                           field:          Field equal to value or in list of 
                                           values.
                           field_ic:       Field equal to value or in list of 
                                           values, using case insensitive 
                                           comparison.
                           field_regex:    Field matches regex value or matches
                                           with any regex in list of values.
                           field_ic_regex: Field matches regex value or matches
                                           with any regex in list of values 
                                           using case insensitive match.                                  
        @return:           List of headers and list of rows and columns.
        
        """
        for key in kwargs:
            col = re.sub('(_ic)?(_regex)?$', '', key)
            if not col in field_list:
                field_list.append(col)
        pinfo = self.parseProcCmd(field_list, threads)
        if pinfo:
            if len(kwargs) > 0:
                pfilter = TableFilter()
                pfilter.registerFilters(**kwargs)
                stats = pfilter.applyFilters(pinfo['headers'], pinfo['stats'])
                return {'headers': pinfo['headers'], 'stats': stats}
            else:
                return pinfo
        else:
            return None
        
    def getProcDict(self, field_list=['user', 'cmd',], threads=False, **kwargs):
        """Execute ps command with custom output format with columns format with 
        columns from field_list, and return result as a nested dictionary with 
        the key PID or SPID.
        
        The Standard Format Specifiers from ps man page must be used in the
        field_list.
        
        @param field_list: Fields included in the output.
                           Default: user, cmd
                           (PID or SPID column is included by default.)
        @param threads:    If True, include threads in output.
        @param **kwargs:   Keyword variables are used for filtering the results
                           depending on the values of the columns. Each keyword 
                           must correspond to a field name with an optional 
                           suffix:
                           field:          Field equal to value or in list of 
                                           values.
                           field_ic:       Field equal to value or in list of 
                                           values, using case insensitive 
                                           comparison.
                           field_regex:    Field matches regex value or matches
                                           with any regex in list of values.
                           field_ic_regex: Field matches regex value or matches
                                           with any regex in list of values 
                                           using case insensitive match. 
        @return:           Nested dictionary indexed by:
                             PID for process info.
                             SPID for thread info.
        
        """
        stats = {}
        num_cols = len(field_list)
        if threads:
            key = 'spid'
        else:
            key = 'pid'
        try:
            key_idx = field_list.index(key)
        except ValueError:
            field_list.append(key)
            key_idx = len(field_list) - 1
        result = self.getProcList(field_list, threads, **kwargs)
        if result is not None:
            headers = result['headers'][:num_cols]
            lines = result['stats']
            if len(lines) > 1:
                for cols in lines:
                    stats[cols[key_idx]] = dict(zip(headers, cols[:num_cols]))
            return stats
        else:
            return None
    
    def getProcStatStatus(self, threads=False, **kwargs):
        """Return process counts per status and priority.
        
        @param **kwargs: Keyword variables are used for filtering the results
                         depending on the values of the columns. Each keyword 
                         must correspond to a field name with an optional 
                         suffix:
                         field:          Field equal to value or in list of 
                                         values.
                         field_ic:       Field equal to value or in list of 
                                         values, using case insensitive 
                                         comparison.
                         field_regex:    Field matches regex value or matches
                                         with any regex in list of values.
                         field_ic_regex: Field matches regex value or matches
                                         with any regex in list of values 
                                         using case insensitive match.
        @return: Dictionary of process counters.
        
        """
        procs = self.getProcList(['stat',], threads=threads, **kwargs)
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
