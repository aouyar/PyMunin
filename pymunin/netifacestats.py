#!/usr/bin/python
#
# netifacestats - Munin Plugin to monitor Network Interfaces.
#
# Requirements
#
#
# Wild Card Plugin - No
#
#
# Multigraph Plugin - Graph Structure
#    - netiface_traffic
#    - netiface_errors
#
#
# Environment Variables
#
#   ifaces:         Comma separated list of Network Interfaces.
#                   (All Network Interfaces are monitored by default.)
#   include_graphs: Comma separated list of enabled graphs. (All graphs enabled by default.)
#   exclude_graphs: Comma separated list of disabled graphs.
#
#   Example:
#     [netifacestats]
#        env.ifaces eth0,eth1
#        env.exclude_graphs netiface_errors
#
#
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=noautoconf nosuggest

import sys
import re
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.netiface import NetIfaceInfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninNetIfacePlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring Network Interfaces.

    """
    plugin_name = 'netifacestats'
    isMultigraph = True
    
    def __init__(self, argv = (), env = {}):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv: List of command line arguments.
        @param env:  Dictionary of environment variables.
        
        """
        MuninPlugin.__init__(self, argv, env)

        self._ifaceInfo = NetIfaceInfo()
        self._ifaceStats = self._ifaceInfo.getIfStats()
        
        self._ifaceList = []
        if self._env.has_key('ifaces'):
            iface_str = re.sub('[^\w\d,:]', '', self._env.get('ifaces'))
            self._ifaceList = iface_str.split(',')
        else:
            for iface in list(self._ifaceStats):
                if iface not in ['lo',]:
                    if max(self._ifaceStats[iface].values()) > 0:
                        self._ifaceList.append(iface)
        self._ifaceList.sort()
        
        for iface in self._ifaceList:
            if self.graphEnabled('netiface_traffic'):
                graph = MuninGraph('Network Interface - Traffic - %s' % iface, 'Network',
                    info='Traffic Stats for Network Interface %s in bps.' % iface,
                    args='--base 1000 --lower-limit 0',
                    vlabel='bps in (-) / out (+) per second')
                graph.addField('rx', 'bps', draw='LINE2', type='DERIVE', min=0, graph=False)
                graph.addField('tx', 'bps', draw='LINE2', type='DERIVE', min=0,
                    negative='rx')
                self.appendGraph('netiface_traffic_%s' % iface, graph)

            if self.graphEnabled('netiface_errors'):
                graph = MuninGraph('Network Interface - Errors - %s' % iface, 'Network',
                    info='Error Stats for Network Interface %s in errors/sec.' % iface,
                    args='--base 1000 --lower-limit 0',
                    vlabel='errors in (-) / out (+) per second')
                graph.addField('rxerrs', 'errors', draw='LINE2', type='DERIVE', min=0, graph=False)
                graph.addField('txerrs', 'errors', draw='LINE2', type='DERIVE', min=0,
                    negative='rxerrs', info='Rx(-)/Tx(+) Errors per second.')
                graph.addField('rxframe', 'frm/crr', draw='LINE2', type='DERIVE', min=0, graph=False)
                graph.addField('txcarrier', 'frm/crr', draw='LINE2', type='DERIVE', min=0,
                    negative='rxframe', info='Frame(-)/Carrier(+) Errors per second.')
                graph.addField('rxdrop', 'drop', draw='LINE2', type='DERIVE', min=0, graph=False)
                graph.addField('txdrop', 'drop', draw='LINE2', type='DERIVE', min=0,
                    negative='rxdrop', info='Rx(-)/Tx(+) Dropped Packets per second.')
                graph.addField('rxfifo', 'fifo', draw='LINE2', type='DERIVE', min=0, graph=False)
                graph.addField('txfifo', 'fifo', draw='LINE2', type='DERIVE', min=0,
                    negative='rxfifo', info='Rx(-)/Tx(+) FIFO Errors per second.')
                self.appendGraph('netiface_errors_%s' % iface, graph)

        
    def retrieveVals(self):
        """Retrive values for graphs."""
        for iface in self._ifaceList:
            stats = self._ifaceStats.get(iface)
            if self.hasGraph('netiface_traffic'):
                self.setGraphVal('netiface_traffic_%s' % iface, 'rx', stats.get('rxbytes') * 8)
                self.setGraphVal('netiface_traffic_%s' % iface, 'tx', stats.get('txbytes') * 8)
            if self.hasGraph('netiface_errors'):
                for field in ('rxerrs', 'txerrs', 'rxframe', 'txcarrier',
                    'rxdrop', 'txdrop', 'rxfifo', 'txfifo'):
                    self.setGraphVal('netiface_errors_%s' % iface, field, stats.get(field))


if __name__ == "__main__":
    sys.exit(muninMain(MuninNetIfacePlugin))
