#!/usr/bin/python
"""tomcatstats - Munin Plugin to monitor Apache Tomcat Application Server.

Requirements
  - Manager user credentials for accesing the Status Page of Apache Tomcat Server.
    Configuration example from tomcat-users.xml:
    <user username="munin" password="<set this>" roles="standard,manager"/>



Wild Card Plugin - No


Multigraph Plugin - Graph Structure
   - tomcat_memory
   - tomcat_threads
   - tomcat_access
   - tomcat_error
   - tomcat_traffic

   
Environment Variables
  host:          Apache Tomcat Host. (Default: 127.0.0.1)
  port:          Apache Tomcat Port. (Default: 8080, SSL: 8443)
  user:          Apache Tomcat Manager User.
  password:      Apache Tomcat Manager Password.
  ssl:           Use SSL if True. (Default: False)
  include_graphs: Comma separated list of enabled graphs.
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.
  include_ports:  Comma separated list of connector ports to include in graphs.
                  (All included by default.)
  exclude_ports:  Comma separated list of connector ports to include in graphs

  Example:
    [tomcatstats]
        env.user munin
        env.password xxxxxxxx
        env.graphs_off tomcat_traffic,tomcat_access
        env.include_ports 8080,8084

"""
# Munin  - Magic Markers
#%# family=manual
#%# capabilities=noautoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.tomcat import TomcatInfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninTomcatPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring Apache Tomcat Application Server.

    """
    plugin_name = 'tomcatstats'
    isMultigraph = True

    def __init__(self, argv=(), env={}, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)
        
        self.envRegisterFilter('ports', '^\d+$')
        
        self._host = self.envGet('host')
        self._port = self.envGet('port')
        self._user = self.envGet('user')
        self._password = self.envGet('password')
        self._ssl = self.envCheckFlag('ssl', False)
        
        self._tomcatInfo = TomcatInfo(self._host, self._port,
                                      self._user, self._password, self._ssl)
        
        if self.graphEnabled('tomcat_memory'):
            graph = MuninGraph('Apache Tomcat - Memory Usage', 'Tomcat',
                info='Memory Usage Stats for Apache Tomcat Server (bytes).',
                args='--base 1024 --lower-limit 0')
            graph.addField('used', 'used', draw='AREASTACK', type='GAUGE',
                           info="Memory in use (bytes) by Apache Tomcat Server.")
            graph.addField('free', 'free', draw='AREASTACK', type='GAUGE',
                           info="Free memory (bytes) availabe for use by "
                           "Apache Tomcat Server.")
            graph.addField('max', 'max', draw='LINE2', type='GAUGE',
                           info="Maximum memory (bytes) availabe for use by "
                           "Apache Tomcat Server.", colour='FF0000')
            self.appendGraph('tomcat_memory', graph)
            
        for (port, stats) in self._tomcatInfo.getConnectorStats().iteritems():
            proto = stats['proto']
            if self.portIncluded(port):
                if self.graphEnabled('tomcat_threads'):
                    name = "tomcat_threads_%d" % port
                    title = "Apache Tomcat - %s-%s - Threads" % (proto, port)
                    info = ("Thread stats for Apache Tomcat Connector %s-%s." 
                            % (proto, port))
                    graph = MuninGraph(title, 'Tomcat', info=info, 
                                       args='--base 1000 --lower-limit 0')
                    graph.addField('busy', 'busy', draw='AREASTACK', type='GAUGE',
                                   info="Number of busy threads.")
                    graph.addField('idle', 'idle', draw='AREASTACK', type='GAUGE',
                                   info="Number of idle threads.")
                    graph.addField('max', 'max', draw='LINE2', type='GAUGE',
                                   info="Maximum number of threads permitted.",
                                   colour='FF0000')
                    self.appendGraph(name, graph)
                if self.graphEnabled('tomcat_access'):
                    name = "tomcat_access_%d" % port
                    title = ("Apache Tomcat - %s-%s - Requests / sec" 
                             % (proto, port))
                    info = ("Requests per second for Apache Tomcat Connector %s-%s." 
                            % (proto, port))
                    graph = MuninGraph(title, 'Tomcat', info=info,
                                       args='--base 1000 --lower-limit 0')
                    graph.addField('reqs', 'reqs', draw='LINE2', type='DERIVE', 
                                   min=0, info="Requests per second.")
                    self.appendGraph(name, graph)
                if self.graphEnabled('tomcat_error'):
                    name = "tomcat_error_%d" % port
                    title = ("Apache Tomcat - %s-%s - Errors / sec" 
                             % (proto, port))
                    info = ("Errors per second for Apache Tomcat Connector %s-%s." 
                            % (proto, port))
                    graph = MuninGraph(title, 'Tomcat', info=info,
                                       args='--base 1000 --lower-limit 0')
                    graph.addField('errors', 'errors', draw='LINE2', 
                                   type='DERIVE', min=0, 
                                   info="Errors per second.")
                    self.appendGraph(name, graph)
                if self.graphEnabled('tomcat_traffic'):
                    name = "tomcat_traffic_%d" % port
                    title = ("Apache Tomcat - %s-%s - Traffic (bytes/sec)" 
                             % (proto, port))
                    info = ("Traffic in bytes per second for "
                            "Apache Tomcat Connector %s-%s." 
                            % (proto, port))
                    graph = MuninGraph(title, 'Tomcat', info=info,
                                       args='--base 1024 --lower-limit 0',
                                       vlabel='bytes in (-) / out (+) per second')
                    graph.addField('rx', 'bytes', draw='LINE2', type='DERIVE', 
                                   min=0, graph=False)
                    graph.addField('tx', 'bytes', draw='LINE2', type='DERIVE', 
                                   min=0, negative='rx',
                        info="Bytes In (-) / Out (+) per second.")
                    self.appendGraph(name, graph)
#                if self.graphEnabled('tomcat_cputime'):
#                    name = "tomcat_cputime_%d" % port
#                    title = ("Apache Tomcat - %s-%s - Processing Time (%%)" 
#                             % (proto, port))
#                    info = ("Processing time for Apache Tomcat Connector %s-%s." 
#                            % (proto, port))
#                    graph = MuninGraph(title, 'Tomcat', info=info,
#                                       args='--base 1000 --lower-limit 0')
#                    graph.addField('cpu', 'cpu', draw='LINE2', type='DERIVE', 
#                                   min=0, cdef='cpu,10,/')
#                    self.appendGraph(name, graph)
        
    def retrieveVals(self):
        """Retrieve values for graphs."""
        if self.hasGraph('tomcat_memory'):
            stats = self._tomcatInfo.getMemoryStats()
            self.setGraphVal('tomcat_memory', 'used', 
                             stats['total'] - stats['free'])
            self.setGraphVal('tomcat_memory', 'free', stats['free'])
            self.setGraphVal('tomcat_memory', 'max', stats['max'])
        for (port, stats) in self._tomcatInfo.getConnectorStats().iteritems():
            thrstats = stats['threadInfo']
            reqstats = stats['requestInfo']
            if self.portIncluded(port):
                name = "tomcat_threads_%d" % port
                if self.hasGraph(name):
                    self.setGraphVal(name, 'busy', 
                                     thrstats['currentThreadsBusy'])
                    self.setGraphVal(name, 'idle', 
                                     thrstats['currentThreadCount'] 
                                     - thrstats['currentThreadsBusy'])
                    self.setGraphVal(name, 'max', thrstats['maxThreads'])
                name = "tomcat_access_%d" % port
                if self.hasGraph(name):
                    self.setGraphVal(name, 'reqs', reqstats['requestCount'])
                name = "tomcat_error_%d" % port
                if self.hasGraph(name):
                    self.setGraphVal(name, 'errors', reqstats['errorCount'])
                name = "tomcat_traffic_%d" % port
                if self.hasGraph(name):
                    self.setGraphVal(name, 'rx', reqstats['bytesReceived'])
                    self.setGraphVal(name, 'tx', reqstats['bytesSent'])
#                name = "tomcat_cputime_%d" % port
#                if self.hasGraph(name):
#                    self.setGraphVal(name, 'cpu', 
#                                     int(reqstats['processingTime'] * 1000))
    
    def portIncluded(self, port):
        """Utility method to check if connector port is included in monitoring.
        
        @param port: Port number.
        @return:     Returns True if included in graphs, False otherwise.
            
        """
        return self.envCheckFilter('ports', str(port))


def main():
    sys.exit(muninMain(MuninTomcatPlugin))


if __name__ == "__main__":
    main()
