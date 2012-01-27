#!/usr/bin/python
"""wanpipestats - Munin Plugin to monitor Wanpipe Interfaces.

Requirements
  - Wanpipe utility wanpipemon.
  - Plugin must be executed with root user privileges.

Wild Card Plugin - No


Multigraph Plugin - Graph Structure
   - wanpipe_traffic
   - wanpipe_errors
   - wanpipe_pri_errors_
   - wanpipe_pri_rxlevel

Environment Variables

  include_ifaces: Comma separated list of wanpipe interfaces to include in 
                  graphs. (All Wanpipe Interfaces are monitored by default.)
  exclude_ifaces: Comma separated list of wanpipe interfaces to exclude from 
                  graphs.
  include_graphs: Comma separated list of enabled graphs.
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.

  Example:
    [wanpipestats]
       user root
       env.include_ifaces w1g1,w2g2
       env.exclude_graphs wanpipe_errors

"""
# Munin  - Magic Markers
#%# family=manual
#%# capabilities=noautoconf nosuggest

import sys
import re
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.wanpipe import WanpipeInfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninWanpipePlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring Wanpipe Interfaces.

    """
    plugin_name = 'wanpipestats'
    isMultigraph = True
    
    def __init__(self, argv=(), env={}, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)
        
        self.envRegisterFilter('ifaces', '^[\w\d]+$')

        self._wanpipeInfo = WanpipeInfo()
        self._ifaceStats = self._wanpipeInfo.getIfaceStats()
        self._ifaceList = []
        for iface in list(self._ifaceStats):
            if self.ifaceIncluded(iface):
                self._ifaceList.append(iface)
        self._ifaceList.sort()
        
        for iface in self._ifaceList:
            if self._reqIfaceList is None or iface in self._reqIfaceList:
                if self.graphEnabled('wanpipe_traffic'):
                    graph = MuninGraph('Wanpipe - Traffic - %s' % iface, 
                        'Asterisk',
                        info='Traffic Stats for Wanpipe Interface %s '
                             'in packets/sec.' % iface,
                        args='--base 1000 --lower-limit 0',
                        vlabel='packets in (-) / out (+) per second')
                    graph.addField('rxpackets', 'packets', draw='LINE2', 
                                   type='DERIVE', min=0, graph=False)
                    graph.addField('txpackets', 'packets', draw='LINE2', 
                                   type='DERIVE', min=0,
                        negative='rxpackets')
                    self.appendGraph('wanpipe_traffic_%s' % iface, graph)

                if self.graphEnabled('wanpipe_errors'):
                    graph = MuninGraph('Wanpipe - Errors - %s' % iface, 'Asterisk',
                        info='Error Stats for Wanpipe Interface %s'
                             ' in errors/sec.' % iface,
                        args='--base 1000 --lower-limit 0',
                        vlabel='errors in (-) / out (+) per second')
                    graph.addField('rxerrs', 'errors', draw='LINE2', 
                                   type='DERIVE', min=0, graph=False)
                    graph.addField('txerrs', 'errors', draw='LINE2', 
                                   type='DERIVE', min=0, negative='txerrs', 
                                   info='Rx(-)/Tx(+) Errors per second.')
                    graph.addField('rxframe', 'frm/crr', draw='LINE2', 
                                   type='DERIVE', min=0, graph=False)
                    graph.addField('txcarrier', 'frm/crr', draw='LINE2', 
                                   type='DERIVE', min=0, negative='rxframe', 
                                   info='Frame(-)/Carrier(+) Errors per second.')
                    graph.addField('rxdrop', 'drop', draw='LINE2', 
                                   type='DERIVE', min=0, graph=False)
                    graph.addField('txdrop', 'drop', draw='LINE2', 
                                   type='DERIVE', min=0, negative='rxdrop', 
                                   info='Rx(-)/Tx(+) Dropped Packets per second.')
                    graph.addField('rxfifo', 'fifo', draw='LINE2', 
                                   type='DERIVE', min=0, graph=False)
                    graph.addField('txfifo', 'fifo', draw='LINE2', 
                                   type='DERIVE', min=0, negative='rxfifo', 
                                   info='Rx(-)/Tx(+) FIFO Errors per second.')
                    self.appendGraph('wanpipe_errors_%s' % iface, graph)

                if self.graphEnabled('wanpipe_pri_errors'):
                    graph = MuninGraph('Wanpipe - ISDN PRI Stats - %s' % iface, 
                        'Asterisk',
                        info='ISDN PRI Error Stats for Wanpipe Interface %s'
                             ' in errors/sec.' % iface,
                        args='--base 1000 --lower-limit 0',
                        vlabel='errors in (-) / out (+) per second')
                    graph.addField('linecodeviolation', 'Line Code Violation', 
                        draw='LINE2', type='DERIVE', min=0, 
                        info='Line Code Violation errors per second.')
                    graph.addField('farendblockerrors', 'Far End Block Errors', 
                        draw='LINE2', type='DERIVE', min=0, 
                        info='Far End Block errors per second.')
                    graph.addField('crc4errors', 'CRC4 Errors', draw='LINE2',
                        type='DERIVE', min=0, info='CRC4 errors per second.')
                    graph.addField('faserrors', 'FAS Errors', draw='LINE2',
                        type='DERIVE', min=0, info='FAS errors per second.')
                    self.appendGraph('wanpipe_pri_errors_%s' % iface, graph)

        if self.graphEnabled('wanpipe_pri_rxlevel'):
            graph = MuninGraph('Wanpipe - ISDN PRI Signal Level', 'Asterisk',
                        info='ISDN PRI received signal level in DB.',
                        args='--base 1000 --lower-limit 0',
                        vlabel='db')
            for iface in self._ifaceList:
                if self._reqIfaceList is None or iface in self._reqIfaceList:
                    graph.addField(iface, iface, draw='LINE2')
            self.appendGraph('wanpipe_pri_rxlevel', graph)
        
    def retrieveVals(self):
        """Retrieve values for graphs."""
        for iface in self._ifaceList:
            if self._reqIfaceList is None or iface in self._reqIfaceList:
                if (self.graphEnabled('wanpipe_traffic') 
                    or self.graphEnabled('wanpipe_errors')):
                    stats = self._ifaceStats.get(iface)
                    if stats:
                        graph_name = 'wanpipe_traffic_%s' % iface
                        if self.hasGraph(graph_name):
                            for field in ('rxpackets', 'txpackets'):
                                self.setGraphVal(graph_name, field, 
                                                 stats.get(field))
                        graph_name = 'wanpipe_errors_%s' % iface
                        if self.hasGraph(graph_name):
                            for field in ('rxerrs', 'txerrs', 'rxframe', 'txcarrier',
                                'rxdrop', 'txdrop', 'rxfifo', 'txfifo'):
                                self.setGraphVal(graph_name, field, 
                                                 stats.get(field))
                if (self.graphEnabled('wanpipe_pri_errors') 
                    or self.graphEnabled('wanpipe_rxlevel')):
                    try:
                        stats = self._wanpipeInfo.getPRIstats(iface)
                    except:
                        stats = None
                    if stats:
                        graph_name = 'wanpipe_pri_errors_%s' % iface
                        if self.hasGraph(graph_name):
                            for field in ('linecodeviolation', 
                                          'farendblockerrors',
                                          'crc4errors', 'faserrors'):
                                self.setGraphVal(graph_name, field, 
                                                 stats.get(field))
                        if self.hasGraph('wanpipe_rxlevel'):
                            self.setGraphVal('wanpipe_pri_rxlevel', 
                                             iface, stats.get('rxlevel'))
                            
    def ifaceIncluded(self, iface):
        """Utility method to check if interface is included in monitoring.
        
        @param iface: Interface name.
        @return:      Returns True if included in graphs, False otherwise.
            
        """
        return self.envCheckFilter('ifaces', iface)


def main():
    sys.exit(muninMain(MuninWanpipePlugin))


if __name__ == "__main__":
    main()
