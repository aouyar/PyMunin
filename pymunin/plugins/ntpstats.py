#!/usr/bin/python
"""ntpstats - Munin Plugin to monitor stats of active synchronization peer.

Requirements
  - Requires ntpd running on local host and ntpq utility.

Wild Card Plugin - No


Multigraph Plugin - Graph Structure
   - ntp_peer_stratum
   - ntp_peer_stats


Environment Variables

  include_graphs: Comma separated list of enabled graphs.
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.

  Example:
    [ntpstats]
        env.exclude_graphs ntp_peer_stratum

"""
# Munin  - Magic Markers
#%# family=manual
#%# capabilities=noautoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.ntp import NTPinfo


__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninNTPstatsPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring NTP Peer.

    """
    plugin_name = 'ntpstats'
    isMultigraph = True

    def __init__(self, argv=(), env={}, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """      
        MuninPlugin.__init__(self, argv, env, debug)

        if self.graphEnabled('ntp_peer_stratum'):
            graph = MuninGraph('NTP Stratum for System Peer', 'Time',
                info='Stratum of the NTP Server the system is in sync with.',
                args='--base 1000 --lower-limit 0')
            graph.addField('stratum', 'stratum', type='GAUGE', draw='LINE2')
            self.appendGraph('ntp_peer_stratum', graph)

        if self.graphEnabled('ntp_peer_stats'):
            graph = MuninGraph('NTP Timing Stats for System Peer', 'Time',
                info='Timing Stats for the NTP Server the system is in sync with.',
                args='--base 1000 --lower-limit 0',
                vlabel='seconds'
                )
            graph.addField('offset', 'offset', type='GAUGE', draw='LINE2')
            graph.addField('delay', 'delay', type='GAUGE', draw='LINE2')
            graph.addField('jitter', 'jitter', type='GAUGE', draw='LINE2')
            self.appendGraph('ntp_peer_stats', graph)

    def retrieveVals(self):
        """Retrieve values for graphs."""
        ntpinfo = NTPinfo()
        stats = ntpinfo.getPeerStats()
        if stats:
            if self.hasGraph('ntp_peer_stratum'):
                self.setGraphVal('ntp_peer_stratum', 'stratum', 
                                 stats.get('stratum'))
            if self.hasGraph('ntp_peer_stats'):
                self.setGraphVal('ntp_peer_stats', 'offset', 
                                 stats.get('offset'))
                self.setGraphVal('ntp_peer_stats', 'delay', 
                                 stats.get('delay'))
                self.setGraphVal('ntp_peer_stats', 'jitter', 
                                 stats.get('jitter'))


def main():
    sys.exit(muninMain(MuninNTPstatsPlugin))


if __name__ == "__main__":
    main()
