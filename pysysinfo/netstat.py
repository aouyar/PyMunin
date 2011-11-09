"""Implements NetstatInfo Class for gathering network stats.

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
netstatCmd = '/bin/netstat'

             
    
class NetstatInfo:
    """Class to retrieve network stats."""
    
    def __init__(self):
        """Initialize Process Stats."""
        pass
    
    def execNetstatCmd(self, *args):
        """Execute ps command with positional params args and return result as 
        list of lines.
        
        @param *args: Positional params for ps command.
        @return:      List of output lines
        
        """
        try:
            out = subprocess.Popen([netstatCmd,] + list(args), 
                                   stdout=subprocess.PIPE).communicate()[0]
        except:
            raise Exception('Execution of command %s failed.' % netstatCmd)
        return out.splitlines()
    
    def getStatList(self, tcp=True, udp=True, ipv4=True, ipv6=True,
                    include_listen=True, only_listen=False,
                    show_users=False, show_procs=False,
                    resolve_hosts=False, resolve_ports=False, resolve_users=True):
        """Execute netstat command and return result as a nested list.
         
        @return:           List of headers and list of rows and columns.
        
        """
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
        if show_users:
            args.append('-e')
        if show_procs:
            args.append('-p')
        if not resolve_hosts:
            args.append('--numeric-hosts')
        if not resolve_ports:
            args.append('--numeric-ports')
        if not resolve_users:
            args.append('--numeric-users')
        lines = self.execNetstatCmd(*args)
        return lines

