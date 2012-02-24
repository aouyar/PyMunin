#!/usr/bin/env python
"""fsstats - Munin Plugin to monitor FreeSWITCH through the Event Socket 
Interface.

Requirements
  - Access to FreeSWITCH Event Socket Interface

Wild Card Plugin - No

Multigraph Plugin - Graph Structure
   - fs_calls
   - fs_channels
   

Environment Variables

  fshost:        FreeSWITCH Server (Default: 127.0.0.1)
  fsport:        FreeSWITCH Event Socket Port (Default: 8021)
  fspass:        FreeSWITCH Event Socket Password
  include_graphs: Comma separated list of enabled graphs.
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.
  

  Example:
      [fsstats]
        env.fshost 192.168.1.10
        env.fsport 5038
        env.fspass secret

"""
# Munin  - Magic Markers
#%# family=manual
#%# capabilities=noautoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.freeswitch import FSinfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.8"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninFreeswitchPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring FreeSWITCH.

    """
    plugin_name = 'fsstats'
    isMultigraph = True

    def __init__(self, argv=(), env={}, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)

        self._fshost = self.envGet('fshost')
        self._fsport = self.envGet('fsport', None, int)
        self._fspass = self.envGet('fspass')

        if self.graphEnabled('fs_calls'):
            graph = MuninGraph('FreeSWITCH - Active Calls', 'FreeSwitch',
                info = 'FreeSWITCH - Number of Active Calls.',
                args = '--base 1000 --lower-limit 0')
            graph.addField('calls', 'calls', type='GAUGE',
                draw='LINE2',info='Active Calls')
            self.appendGraph('fs_calls', graph)

        if self.graphEnabled('fs_channels'):
            graph = MuninGraph('FreeSWITCH - Active Channels', 'FreeSWITCH',
                info = 'FreeSWITCH - Number of Active Channels.',
                args = '--base 1000 --lower-limit 0')
            graph.addField('channels', 'channels', type='GAUGE',
                           draw='LINE2')
            self.appendGraph('fs_channels', graph)

    def retrieveVals(self):
        """Retrieve values for graphs."""
        fs = FSinfo(self._fshost, self._fsport, self._fspass)
        if self.hasGraph('fs_calls'):
            count = fs.getCallCount()
            self.setGraphVal('fs_calls', 'calls', count)
        if self.hasGraph('fs_channels'):
            count = fs.getChannelCount()
            self.setGraphVal('fs_channels', 'channels', count)


def main():
    sys.exit(muninMain(MuninFreeswitchPlugin))


if __name__ == "__main__":
    main()
