#!/usr/bin/python
"""phpfpmstats - Munin Plugin for monitoring PHP FPM (Fast Process Manager).

Requirements
  - The PHP FPM status page must be configured and it must have access 
    permissions from localhost.


Wild Card Plugin - No


Multigraph Plugin - Graph Structure
   - php_fpm_connections
   - php_fpm_processes
   
Environment Variables
  host:           Web Server Host. (Default: 127.0.0.1)
  port:           Web Server Port. (Default: 80, SSL: 443)
  user:           User in case authentication is required for access to 
                  APC Status page.
  password:       User in case authentication is required for access to 
                  APC Status page.
  monpath:        APC status script path relative to Document Root.
  ssl:            Use SSL if yes. (Default: no)
  include_graphs: Comma separated list of enabled graphs. 
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.

  Example:
    [phpfpmstats]
        env.exclude_graphs php_fpm_processes

"""
# Munin  - Magic Markers
#%# family=manual
#%# capabilities=noautoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.phpfpm import PHPfpmInfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.8"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninPHPfpmPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring PHP Fast Process Manager (FPM).

    """
    plugin_name = 'phpfpmstats'
    isMultigraph = True

    def __init__(self, argv = (), env = {}):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv: List of command line arguments.
        @param env:  Dictionary of environment variables.
        
        """
        MuninPlugin.__init__(self, argv, env)
        
        self._host = self._env.get('host')
        self._port = self._env.get('port')
        self._user = self._env.get('user')
        self._monpath = self._env.get('monpath')
        self._password = self._env.get('password')
        self._ssl = self.registerFlag('ssl', False) 
        
        if self.graphEnabled('php_fpm_connections'):
            graph = MuninGraph('PHP FPM - Connections per second', 'PHP',
                info='PHP Fast Process Manager (FPM) - Connections per second.',
                args='--base 1000 --lower-limit 0')
            graph.addField('conn', 'conn', draw='LINE2', type='DERIVE', min=0)
            self.appendGraph('php_fpm_connections', graph)
        
        if self.graphEnabled('php_fpm_processes'):
            graph = MuninGraph('PHP FPM - Processes', 'PHP',
                info='PHP Fast Process Manager (FPM) - Active / Idle Processes.',
                args='--base 1000 --lower-limit 0')
            graph.addField('active', 'active', draw='AREASTACK', type='GAUGE')
            graph.addField('idle', 'idle', draw='AREASTACK', type='GAUGE')
            graph.addField('total', 'total', draw='LINE2', type='GAUGE',
                           colour='000000')
            self.appendGraph('php_fpm_processes', graph)
        
        
    def retrieveVals(self):
        """Retrive values for graphs."""
        fpminfo = PHPfpmInfo(self._host, self._port, self._user, self._password, 
                             self._monpath, self._ssl)
        stats = fpminfo.getStats()
        if self.hasGraph('php_fpm_connections') and stats: 
            self.setGraphVal('php_fpm_connections', 'conn', 
                             stats['accepted conn'])
        if self.hasGraph('php_fpm_processes') and stats: 
            self.setGraphVal('php_fpm_processes', 'active', 
                             stats['active processes'])
            self.setGraphVal('php_fpm_processes', 'idle', 
                             stats['idle processes'])
            self.setGraphVal('php_fpm_processes', 'total', 
                             stats['total processes'])
            
       
if __name__ == "__main__":
    sys.exit(muninMain(MuninPHPfpmPlugin))

