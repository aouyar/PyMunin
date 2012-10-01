#! /usr/bin/env python
"""ntphostoffsets - Munin Plugin to monitor time offset of multiple remote hosts
                 using NTP.

Requirements
  - Requires ntpd running on remote hosts and access to NTP on remote host.
  - Requires ntpdate utility on local host.

Wild Card Plugin - No


Multigraph Plugin - Graph Structure
   - ntp_host_stratums
   - ntp_host_offsets
   - ntp_host_delays


Environment Variables

  ntphosts:       Comma separated list of IP addresses of hosts to be monitored.
  include_graphs: Comma separated list of enabled graphs.
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.

Environment Variables for Multiple Instances of Plugin (Omitted by default.)
  instance_name:         Name of instance.
  instance_label:        Graph title label for instance.
                         (Default is the same as instance name.)
  instance_label_format: One of the following values:
                         - suffix (Default)
                         - prefix
                         - none 

  Example:
    [ntphostoffsets]
        env.ntphosts 192.168.1.1,192.168.1.2
        env.exclude_graphs ntp_host_stratums
    
"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=autoconf nosuggest

import sys
import re
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.ntp import NTPinfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9.20"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninNTPhostOffsetsPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring time offsets of multiple remote
    hosts using NTP.

    """
    plugin_name = 'ntphostoffsets'
    isMultigraph = True
    isMultiInstance = True

    def __init__(self, argv=(), env=None, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)
        self._category = 'Time'

        if self.envHasKey('ntphosts'):
            hosts_str = re.sub('[^\d\.,]', '', self.envGet('ntphosts'))
            self._remoteHosts = hosts_str.split(',')
        else:
            raise AttributeError("Remote host list must be passed in the "
                                 "'ntphosts' environment variable.")

        if self.graphEnabled('ntp_host_stratums'):
            graph = MuninGraph('NTP Stratums of Multiple Hosts', self._category,
                info='NTP Stratum of Multiple Remote Hosts.',
                args='--base 1000 --lower-limit 0')
            for host in self._remoteHosts:
                hostkey = re.sub('\.', '_', host)
                graph.addField(hostkey, host, type='GAUGE', draw='LINE2')
            self.appendGraph('ntp_host_stratums', graph)

        if self.graphEnabled('ntp_host_offsets'):
            graph = MuninGraph('NTP Offsets of Multiple Hosts', self._category,
                info='NTP Delays of Multiple Hosts relative to current node.',
                args ='--base 1000 --lower-limit 0',
                vlabel='seconds'
                )
            for host in self._remoteHosts:
                hostkey = re.sub('\.', '_', host)
                graph.addField(hostkey, host, type='GAUGE', draw='LINE2')
            self.appendGraph('ntp_host_offsets', graph)
    
        if self.graphEnabled('ntp_host_delays'):
            graph = MuninGraph('NTP Delays of Multiple Hosts', self._category,
                info='NTP Delays of Multiple Hosts relative to current node.',
                args='--base 1000 --lower-limit 0',
                vlabel='seconds'
                )
            for host in self._remoteHosts:
                hostkey = re.sub('\.', '_', host)
                graph.addField(hostkey, host, type='GAUGE', draw='LINE2')
            self.appendGraph('ntp_host_delays', graph)

    def retrieveVals(self):
        """Retrieve values for graphs."""
        ntpinfo = NTPinfo()
        ntpstats = ntpinfo.getHostOffsets(self._remoteHosts)
        if ntpstats:
            for host in self._remoteHosts:
                hostkey = re.sub('\.', '_', host)
                hoststats = ntpstats.get(host)
                if hoststats:
                    if self.hasGraph('ntp_host_stratums'):
                        self.setGraphVal('ntp_host_stratums', hostkey, 
                                         hoststats.get('stratum'))
                    if self.hasGraph('ntp_host_offsets'):
                        self.setGraphVal('ntp_host_offsets', hostkey, 
                                         hoststats.get('offset'))
                    if self.hasGraph('ntp_host_delays'):
                        self.setGraphVal('ntp_host_delays', hostkey, 
                                         hoststats.get('delay'))
                        
    def autoconf(self):
        """Implements Munin Plugin Auto-Configuration Option.
        
        @return: True if plugin can be  auto-configured, False otherwise.
                 
        """
        ntpinfo = NTPinfo()
        ntpstats = ntpinfo.getHostOffsets(self._remoteHosts)
        return len(ntpstats) > 0


def main():
    sys.exit(muninMain(MuninNTPhostOffsetsPlugin))


if __name__ == "__main__":
    main()
