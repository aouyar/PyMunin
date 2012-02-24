"""Implements FSinfo Class for gathering stats from the FreeSWITCH ESL Interface.

"""

import re
import ESL

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.5"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


#
# DEFAULTS
#

conn_timeout = 5


    
class FSinfo:
    """Class that establishes connection to Asterisk Manager Interface
    to retrieve statistics on operation.

    """

    def __init__(self, host='127.0.0.1', port=8021, secret="ClueCon", 
                 autoInit=True):
        """Initialize connection to FreeSWITCH ESL Interface.
        
        @param host:     FreeSWITCH Host
        @param port:     FreeSWITCH ESL Port
        @param secret: FreeSWITCH ESL Secret
        @param autoInit: If True connect to FreeSWITCH ESL Interface on 
                         instantiation.

        """
        # Set Connection Parameters
        self._eslhost = host or '127.0.0.1'
        self._eslport = int(port) or 8021
        self._eslpass = secret or "ClueCon"
        self._eslconn = None
        
        ESL.eslSetLogLevel(0)
        if autoInit:
            self._connect()

    def __del__(self):
        """Cleanup."""
        if self._eslconn is not None:
            del self._eslconn

    def _connect(self):
        """Connect to FreeSWITCH ESL Interface."""
        try:
            self._eslconn = ESL.ESLconnection(self._eslhost, 
                                              str(self._eslport), 
                                              self._eslpass)
        except:
            pass
        if not self._eslconn.connected():
            raise Exception(
                "Connection to FreeSWITCH ESL Interface on host %s and port %d failed."
                % (self._eslhost, self._eslport)
                )
    
    def _execCmd(self, cmd, args):
        """Execute command and return result body as list of lines.
        
            @param cmd:  Command string.
            @param args: Comand arguments string. 
            @return:     Result dictionary.
            
        """
        output = self._eslconn.api(cmd, args)
        if output:
            body = output.getBody()
            if body:
                return body.splitlines()
        return None
    
    def _execShowCmd(self, showcmd):
        """Execute 'show' command and return result dictionary.
        
            @param cmd: Command string.
            @return: Result dictionary.
            
        """
        result = None
        lines = self._execCmd("show", showcmd)
        if lines and len(lines) >= 2 and lines[0] != '' and lines[0][0] != '-':
            result = {}
            result['keys'] = lines[0].split(',')
            items = []
            for line in lines[1:]:
                if line == '':
                    break
                items.append(line.split(','))
            result['items'] = items
        return result
    
    def _execShowCountCmd(self, showcmd):
        """Execute 'show' command and return result dictionary.
        
            @param cmd: Command string.
            @return: Result dictionary.
            
        """
        result = None
        lines = self._execCmd("show", showcmd + " count")
        for line in lines:
            mobj = re.match('\s*(\d+)\s+total', line)
            if mobj:
                return int(mobj.group(1))
        return result
    
    def getChannelCount(self):
        """Get number of active channels from FreeSWITCH.
        
        @return: Integer or None.
        
        """
        return self._execShowCountCmd("channels")
    
    def getCallCount(self):
        """Get number of active calls from FreeSWITCH.
        
        @return: Integer or None.
        
        """
        return self._execShowCountCmd("calls")
