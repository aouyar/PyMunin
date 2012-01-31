#!/usr/bin/env python
"""ntphostoffset_ - Munin Plugin to monitor time offset of remote host using NTP.

Requirements
  - Requires ntpd running on remote host and access to NTP on remote host.
  - Requires ntpdate utility on local host.

Wild Card Plugin
  Symlink indicates IP of remote host to be monitored:
  Ex: ntphostoffset_192.168.1.1 -> /usr/shar/munin/plugins/ntphostoffset_


Multigraph Plugin - Graph Structure
   - ntp_host_stratum_
   - ntp_host_stat_


Environment Variables

  include_graphs: Comma separated list of enabled graphs.
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.

  Example:
    [ntphostoffset_*]
       env.exclude_graphs ntp_host_stratum_

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


class MuninNTPhostOffsetPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring time offset of remote host using NTP.

    """
    plugin_name = 'ntphostoffset_'
    isMultigraph = True

    def __init__(self, argv=(), env={}, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)

        if self.arg0 is None:
            raise Exception("Remote host name cannot be determined.")
        else:
            self._remoteHost = self.arg0

        if self.graphEnabled('ntp_host_stratum'):
            graphName = 'ntp_host_stratum_%s' % self._remoteHost
            graph = MuninGraph('NTP Stratum of Host %s' % self._remoteHost, 
                'Time',
                info='NTP Stratum of Host %s.' % self._remoteHost,
                args='--base 1000 --lower-limit 0')
            graph.addField('stratum', 'stratum', type='GAUGE', draw='LINE2')
            self.appendGraph(graphName, graph)

        if self.graphEnabled('ntp_host_stat'):
            graphName = 'ntp_host_stat_%s' % self._remoteHost
            graph = MuninGraph('NTP Offset of Host %s' % self._remoteHost, 'Time',
                info=('NTP Offset of Host %s relative to current node.' 
                      % self._remoteHost),
                args='--base 1000 --lower-limit 0',
                vlabel='seconds'
                )
            graph.addField('offset', 'offset', type='GAUGE', draw='LINE2')
            graph.addField('delay', 'delay', type='GAUGE', draw='LINE2')
            self.appendGraph(graphName, graph)

    def retrieveVals(self):
        """Retrieve values for graphs."""
        ntpinfo = NTPinfo()
        stats = ntpinfo.getHostOffset(self._remoteHost)
        if stats:
            graph_name = 'ntp_host_stratum_%s' % self._remoteHost
            if self.hasGraph(graph_name):
                self.setGraphVal(graph_name, 'stratum', stats.get('stratum'))
            graph_name = 'ntp_host_stat_%s' % self._remoteHost
            if self.hasGraph(graph_name):
                self.setGraphVal(graph_name, 'offset', stats.get('offset'))
                self.setGraphVal(graph_name, 'delay', stats.get('delay'))


def main():
    sys.exit(muninMain(MuninNTPhostOffsetPlugin))


if __name__ == "__main__":
    main()
