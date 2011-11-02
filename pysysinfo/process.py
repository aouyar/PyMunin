"""Implements ProcessInfo Class for gathering process stats.

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
psCmd = '/bin/ps'


# Maps
procStatusNames = {'D': 'uninterruptable_sleep',
                   'R': 'running',
                   'S': 'sleep',
                   'T': 'stopped',
                   'W': 'paging',
                   'X': 'dead',
                   'Z': 'defunct'} 


class ProcessFilter:
    
    def __init__(self):
        self._filters = {}
    
    def registerFilter(self, column, patterns, is_regex=False, 
                       ignore_case=False):
        if isinstance(patterns, (str, unicode)):
            patterns = (patterns,)
        elif not isinstance(patterns, (tuple, list)):
            raise ValueError("The patterns parameter must either be as string "
                             "or a tuple / list of strings.")
        if is_regex:
            if ignore_case:
                flags = re.IGNORECASE
            else:
                flags = 0
            patterns = [re.compile(pattern, flags) for pattern in patterns]
        elif ignore_case:
            patterns = [pattern.lower() for pattern in patterns]
        self._filters[column] = (patterns, is_regex, ignore_case)
                
    def unregisterFilter(self, column):
        if self._filters.has_key(column):
            del self._filters[column]
            
    def checkFilter(self, headers, table):
        result = []
        column_idxs = {}
        for column in self._filters.keys():
            try:
                column_idxs[column] = headers.index(column)
            except ValueError:
                raise ValueError('Invalid column name %s in filter.' 
                                 % filter[0])
        for row in table:
            for (column, (patterns, 
                          is_regex, 
                          ignore_case)) in self._filters.items():
                col_idx = column_idxs[column]
                col_val = row[col_idx]
                if is_regex:
                    for pattern in patterns:
                        if pattern.search(col_val):
                            break
                    else:
                        break
                else:
                    if ignore_case:
                        col_val = col_val.lower()
                    if col_val in patterns:
                        pass
                    else:
                        break
            else:
                result.append(row)
        return result
             
    
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
    
    def getProcList(self, field_list=['uid', 'cmd',], threads=False):
        """Execute ps command with custom output format with columns from fields
        positional arguments and return result as a nested list.
        
        @param field_list: Fields included in the output.
                           Default: uid, cmd
        @param threads:    If True, include threads in output. 
        @return:           List of headers and list of rows and columns.
        
        """
        args = []
        if threads:
            args.append('-T')
        args.append('-o')
        args.append(','.join(field_list))
        args.append('-e')
        lines = self.execProcCmd(*args)    
        if len(lines) > 1:
            headers = []
            field_ranges = []
            header_line = lines[0]
            colfields = re.findall('(\S+)(\s*)', header_line)
            start = 0
            for (header, space) in colfields:
                headers.append(header.lower())
                if len(space) != 0:
                    end = start + len(header) + len(space)
                else:
                    end = None
                field_ranges.append((start, end))
                start = end
            stats = []
            for line in lines[1:]:
                cols = []
                for (start, end) in field_ranges:
                    cols.append(line[start:end].strip())
                stats.append(cols)
            return {'headers': headers, 'stats': stats}
        else:
            return None
    
    def getProcDict(self, field_list=['uid', 'cmd',], threads=False):
        """Execute ps command with custom output format with columns from fields
        positional arguments and return result as a nested dictionary with the 
        key PID or SPID.
        
        @param field_list: Fields included in the output.
                           Default: uid, cmd
                           (PID or SPID column is included by default.)
        @param threads:    If True, include threads in output.
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
        result = self.getProcList(field_list, threads)
        if result is not None:
            headers = result['headers'][:num_cols]
            lines = result['stats']
            if len(lines) > 1:
                for cols in lines:
                    stats[cols[key_idx]] = dict(zip(headers, cols[:num_cols]))
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
