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

psFieldWidth = {'args': 128,
                'cmd': 128,
                'command': 128,
                's': 4,
                'stat': 8,
                'state': 4,}
psDefaultFieldWidth = 16


class ProcessFilter:
    """Class for filtering results of ps command based on filters on values of
    columns."""
    
    def __init__(self):
        """Constructor."""
        self._filters = {}
    
    def registerFilter(self, column, patterns, is_regex=False, 
                       ignore_case=False):
        """Register filter on column of ps output.
        
        @param column:      The column header. The Standard Format Specifiers 
                            from ps man page must used as column names.
        @param patterns:    A single pattern or a list of patterns used for 
                            matching column values.
        @param is_regex:    The patterns will be treated as regex if True, the 
                            column values will be tested for equality with the
                            patterns otherwise.
        @param ignore_case: Case insensitive matching will be used if True.
        
        """
        if isinstance(patterns, basestring):
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
        """Un register filter on column of ps output.
        
        @param column: The column header. The Standard Format Specifiers 
                       from ps man page must used as column names.
        
        """
        if self._filters.has_key(column):
            del self._filters[column]
            
    def applyFilter(self, headers, table):
        """Apply filter on ps command result.
        
        @param headers: List of column headers.
        @param table:   Nested list of rows and columns of ps command output.
        @return:        Nested list of rows and columns of ps command output
                        filtered using registered filters.
                        
        """
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
        """Execute ps command with custom output format with columns from 
        field_list and return result as a nested list.
        
        The Standard Format Specifiers from ps man page must be used in the
        field_list.
        
        @param field_list: Fields included in the output.
                           Default: uid, cmd
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
        
    def getFilteredProcList(self, field_list=['uid', 'cmd',], threads=False,
                            **kwargs):
        """Execute ps command with custom output format with columns columns from 
        field_list, select lines using the filters defined by kwargs and return 
        result as a nested list.
        
        The Standard Format Specifiers from ps man page must be used in the
        field_list and filters.
        
        @param field_list: Fields included in the output.
                           Default: uid, cmd
        @param threads:    If True, include threads in output.
        @param **kwargs:   Filters are keyword variables. Each keyword must 
                           correspond to a field name and an optional suffix:
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
        pfilter = ProcessFilter()
        for (key, patterns) in kwargs.items():
            if key.endswith('_regex'):
                col = key[:-len('_regex')]
                is_regex = True
            else:
                col = key
                is_regex = False
            if col.endswith('_ic'):
                col = col[:-len('_ic')]
                ignore_case = True
            else:
                ignore_case = False
            pfilter.registerFilter(col, patterns, is_regex, ignore_case)
            if not col in field_list:
                field_list.append(col)
        pinfo = self.getProcList(field_list, threads)
        if pinfo:
            stats = pfilter.applyFilter(pinfo['headers'], pinfo['stats'])
            return {'headers': pinfo['headers'], 'stats': stats}
        else:
            return None
    
    def getProcDict(self, field_list=['uid', 'cmd',], threads=False):
        """Execute ps command with custom output format with columns format with 
        columns from field_list, select lines using the filters defined by kwargs 
        and return result as a nested dictionary with the key PID or SPID.
        
        The Standard Format Specifiers from ps man page must be used in the
        field_list.
        
        @param field_list: Fields included in the output.
                           Default: uid, cmd
                           (PID or SPID column is included by default.)
        @param threads:    If True, include threads in output.
        @return:           Nested dictionary indexed by:
                             PID for process info.
                             SPID for thread info.
        
        """
        return self.getFilteredProcDict(field_list, threads)
        
    def getFilteredProcDict(self, field_list=['uid', 'cmd',], threads=False,
                            **kwargs):
        """Execute ps command with custom output format with columns format with 
        columns from field_list, and return result as a nested dictionary with 
        the key PID or SPID.
        
        The Standard Format Specifiers from ps man page must be used in the
        field_list.
        
        @param field_list: Fields included in the output.
                           Default: uid, cmd
                           (PID or SPID column is included by default.)
        @param threads:    If True, include threads in output.
        @param **kwargs:   Filters are keyword variables. Each keyword must 
                           correspond to a field name and an optional suffix:
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
        if len(kwargs) > 0:
            result = self.getFilteredProcList(field_list, threads, **kwargs)
        else:
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
