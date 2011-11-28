"""Implements NetstatInfo Class for gathering network stats.

"""

import re
import subprocess
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
netstatCmd = '/bin/netstat'

             
    
class NetstatInfo:
    """Class to retrieve network stats."""
    
    def __init__(self):
        """Initialize Process Stats."""
        pass
    
    def execNetstatCmd(self, *args):
        """Execute ps command with positional params args and return result as 
        list of lines.
        
        @param *args: Positional params for netstat command.
        @return:      List of output lines
        
        """
        try:
            out = subprocess.Popen([netstatCmd,] + list(args), 
                                   stdout=subprocess.PIPE).communicate()[0]
        except:
            raise Exception('Execution of command %s failed.' % netstatCmd)
        return out.splitlines()
    
    def parseNetstatCmd(self, tcp=True, udp=True, ipv4=True, ipv6=True, 
                        include_listen=True, only_listen=False,
                        show_users=False, show_procs=False,
                        resolve_hosts=False, resolve_ports=False, 
                        resolve_users=True):
        """Execute netstat command and return result as a nested dictionary.
        
        @param tcp:            Include TCP ports in ouput if True.
        @param udp:            Include UDP ports in ouput if True.
        @param ipv4:           Include IPv4 ports in output if True.
        @param ipv6:           Include IPv6 ports in output if True.
        @param include_listen: Include listening ports in output if True.
        @param only_listen:    Include only listening ports in output if True.
        @param show_users:     Show info on owning users for ports if True.
        @param show_procs:     Show info on PID and Program Name attached to
                               ports if True.
        @param resolve_hosts:  Resolve IP addresses into names if True.
        @param resolve_ports:  Resolve numeric ports to names if True.
        @param resolve_users:  Resolve numeric user IDs to user names if True.
        @return:               List of headers and list of rows and columns.
        
        """
        headers = ['proto', 'ipversion', 'recvq', 'sendq', 
                   'localaddr', 'localport','foreignaddr', 'foreignport', 
                   'state']
        args = []
        args.append('--protocol=inet')
        if tcp:
            args.append('-t')
        if udp:
            args.append('-u')
        if only_listen:
            args.append('-l')
        elif include_listen:
            args.append('-a')
        if ipv4:
            args.append('-4')
        if ipv6:
            args.append('-6')
        regexp_str = ('(tcp|udp)(\d*)\s+(\d+)\s+(\d+)\s+'
                      '(\S+):(\w+)\s+(\S+):(\w+|\*)\s+(\w*)')
        if show_users:
            args.append('-e')
            regexp_str += '\s+(\w+)\s+(\d+)'
            headers.extend(['user', 'inode'])
        if show_procs:
            args.append('-p')
            regexp_str += '\s+(\S+)'
            headers.extend(['pid', 'prog'])
        if not resolve_hosts:
            args.append('--numeric-hosts')
        if not resolve_ports:
            args.append('--numeric-ports')
        if not resolve_users:
            args.append('--numeric-users')
        lines = self.execNetstatCmd(*args)
        stats = []
        regexp = re.compile(regexp_str)
        for line in lines[2:]:
            mobj = regexp.match(line)
            if mobj is not None:
                stat = list(mobj.groups())
                if stat[1] == '0':
                    stat[1] = '4'
                if stat[8] == '':
                    stat[8] = None
                if show_procs:
                    proc = stat.pop().split('/')
                    if len(proc) == 2:
                        stat.extend(proc)
                    else:
                        stat.extend([None, None])
                stats.append(stat)
        return {'headers': headers, 'stats': stats}
    
    def getStats(self, tcp=True, udp=True, ipv4=True, ipv6=True, 
                 include_listen=True, only_listen=False,
                 show_users=False, show_procs=False, 
                 resolve_hosts=False, resolve_ports=False, resolve_users=True, 
                 **kwargs):
        """Execute netstat command and return result as a nested dictionary.
        
        @param tcp:            Include TCP ports in ouput if True.
        @param udp:            Include UDP ports in ouput if True.
        @param ipv4:           Include IPv4 ports in output if True.
        @param ipv6:           Include IPv6 ports in output if True.
        @param include_listen: Include listening ports in output if True.
        @param only_listen:    Include only listening ports in output if True.
        @param show_users:     Show info on owning users for ports if True.
        @param show_procs:     Show info on PID and Program Name attached to
                               ports if True.
        @param resolve_hosts:  Resolve IP addresses into names if True.
        @param resolve_ports:  Resolve numeric ports to names if True.
        @param resolve_users:  Resolve numeric user IDs to user names if True.
        @param **kwargs:       Keyword variables are used for filtering the 
                               results depending on the values of the columns. 
                               Each keyword must correspond to a field name with 
                               an optional suffix:
                               field:          Field equal to value or in list 
                                               of values.
                               field_ic:       Field equal to value or in list of 
                                               values, using case insensitive 
                                               comparison.
                               field_regex:    Field matches regex value or 
                                               matches with any regex in list of 
                                               values.
                               field_ic_regex: Field matches regex value or 
                                               matches with any regex in list of 
                                               values using case insensitive 
                                               match.
        @return:               List of headers and list of rows and columns.
        
        """
        pinfo = self.parseNetstatCmd(tcp, udp, ipv4, ipv6, 
                                     include_listen, only_listen,
                                     show_users, show_procs, 
                                     resolve_hosts, resolve_ports, resolve_users)
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
    
    def getTCPportConnStatus(self, ipv4=True, ipv6=True, include_listen=False,
                             **kwargs):
        """Returns the number of TCP endpoints discriminated by status.
        
        @param ipv4:           Include IPv4 ports in output if True.
        @param ipv6:           Include IPv6 ports in output if True.
        @param include_listen: Include listening ports in output if True.
        @param **kwargs:       Keyword variables are used for filtering the 
                               results depending on the values of the columns. 
                               Each keyword must correspond to a field name with 
                               an optional suffix:
                               field:          Field equal to value or in list 
                                               of values.
                               field_ic:       Field equal to value or in list of 
                                               values, using case insensitive 
                                               comparison.
                               field_regex:    Field matches regex value or 
                                               matches with any regex in list of 
                                               values.
                               field_ic_regex: Field matches regex value or 
                                               matches with any regex in list of 
                                               values using case insensitive 
                                               match.
        @return:               Dictionary mapping connection status to the
                               number of endpoints.
        
        """
        status_dict = {}
        result = self.getStats(tcp=True, udp=False, 
                               include_listen=include_listen, 
                               ipv4=ipv4, ipv6=ipv6, 
                               **kwargs)
        stats = result['stats']
        for stat in stats:
            if stat is not None:
                status = stat[8].lower()
            status_dict[status] = status_dict.get(status, 0) + 1
        return status_dict

    def getTCPportConnCount(self, ipv4=True, ipv6=True, resolve_ports=False,
                            **kwargs):
        """Returns TCP connection counts for each local port.
        
        @param ipv4:          Include IPv4 ports in output if True.
        @param ipv6:          Include IPv6 ports in output if True.
        @param resolve_ports: Resolve numeric ports to names if True.
        @param **kwargs:      Keyword variables are used for filtering the 
                              results depending on the values of the columns. 
                              Each keyword must correspond to a field name with 
                              an optional suffix:
                              field:          Field equal to value or in list 
                                              of values.
                              field_ic:       Field equal to value or in list of 
                                              values, using case insensitive 
                                              comparison.
                              field_regex:    Field matches regex value or 
                                              matches with any regex in list of 
                                              values.
                              field_ic_regex: Field matches regex value or 
                                              matches with any regex in list of 
                                              values using case insensitive 
                                              match.
        @return:              Dictionary mapping port number or name to the
                              number of established connections.
        
        """
        port_dict = {}
        result = self.getStats(tcp=True, udp=False, 
                               include_listen=False, ipv4=ipv4, 
                               ipv6=ipv6, resolve_ports=resolve_ports,
                               **kwargs)
        stats = result['stats']
        for stat in stats:
            if stat[8] == 'ESTABLISHED':
                port_dict[stat[5]] = port_dict.get(5, 0) + 1
        return port_dict
    