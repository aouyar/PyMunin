#!/usr/bin/env python
"""activemqstats - Munin Plugin to monitor stats for Apache ActiveMQ.


Requirements

  - Access to Apache ActiveMQ REST API.


Wild Card Plugin - No


Multigraph Plugin - Graph Structure

   - activemq_enqdeqrate
   - activemq_prodconscount
   - activemq_queuetopiccount
   - activemq_usage
   - activemq_%s_%s_size
   - activemq_%s_%s_enqdeq
   - activemq_%s_%s_prodconsc
   - activemq_%s_%s_blkt

   
Environment Variables

  host:           ActiveMQ REST API Host. (Default: 127.0.0.1)
  port:           ActiveMQ REST API Port. (Default: 8161, SSL: 8162)
  user:           Username. (Not needed unless authentication is
                            required to access REST API.
  password:       Password. (Not needed unless authentication is
                            required to access REST API.
  statuspath:     Path of REST API. (Default: hawtio/jolokia)
  ssl:            Use SSL if yes. (Default: no)
  brokername:     The broker's name. $HOSTNAME is replaced with
                            hostname. (Default: localhost)
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
    [activemqstats]
        env.exclude_graphs activemq_enqdeqrate,activemq_prodconscount

"""
# Munin  - Magic Markers
#%# family=auto
#%# capabilities=autoconf nosuggest

import sys
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.activemq import ActiveMQInfo

__author__ = "Nagy, Attila"
__copyright__ = "Copyright 2013, Nagy, Attila"
__credits__ = []
__license__ = "GPL"
__version__ = "0.1.0"
__maintainer__ = "Nagy, Attila"
__email__ = "bra@fsn.hu"
__status__ = "Development"

class MuninActiveMQPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring ActiveMQ server.

    """
    plugin_name = 'activemqstats'
    isMultigraph = True
    isMultiInstance = True
    prodconscountlist = ['TemporaryTopicProducers', 'TopicSubscribers',
                        'TemporaryTopicSubscribers', 'TopicProducers',
                        'QueueProducers', 'QueueSubscribers',
                        'InactiveDurableTopicSubscribers',
                        'TemporaryQueueSubscribers', 'TemporaryQueueProducers',
                        'DynamicDestinationProducers', 'DurableTopicSubscribers',
                        ]
    usagelist = ['JobSchedulerStorePercentUsage','TempPercentUsage',
                 'StorePercentUsage','MemoryPercentUsage']
    queuetopiccountlist = ['Queues','TemporaryTopics','Topics','TemporaryQueues']

    def __init__(self, argv=(), env=None, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)
        
        self._host = self.envGet('host')
        self._port = self.envGet('port', None, int)
        self._user = self.envGet('user')
        self._password = self.envGet('password')
        self._statuspath = self.envGet('statuspath')
        self._brokername = self.envGet('brokername')
        self._ssl = self.envCheckFlag('ssl', False)
        self._category = 'ActiveMQ'
        
        # global stats for the broker
        if self.graphEnabled('activemq_enqdeqrate'):
            graph = MuninGraph('ActiveMQ Enqueue/Dequeue rate', 
                self._category,
                info='Enqueue/Dequeue rate for ActiveMQ broker.',
                vlabel='msg/s',
                args='--base 1000 --lower-limit 0')
            graph.addField('enqueue', 'enqueue', draw='LINE2', type='DERIVE',
                           min=0, max=200000, info="Enqueued messages rate")
            graph.addField('dequeue', 'dequeue', draw='LINE2', type='DERIVE',
                           min=0, max=200000, info="Dequeued messages rate")
            self.appendGraph('activemq_enqdeqrate', graph)

        if self.graphEnabled('activemq_prodconscount'):
            graph = MuninGraph('ActiveMQ number of producers and consumers', 
                self._category,
                info='Number of producers and consumers.',
                args='--base 1000 --lower-limit 0')
            for key in self.prodconscountlist:
                graph.addField(key, key, draw='LINE2', type='GAUGE',
                               min=0, info=key)
            self.appendGraph('activemq_prodconscount', graph)

        if self.graphEnabled('activemq_queuetopiccount'):
            graph = MuninGraph('ActiveMQ number of topics/queues', 
                self._category,
                info='Number of topics/queues.',
                args='--base 1000 --lower-limit 0')
            for key in self.queuetopiccountlist:
                graph.addField(key, key, draw='LINE2', type='GAUGE',
                               min=0, info=key)
            self.appendGraph('activemq_queuetopiccount', graph)
            
        if self.graphEnabled('activemq_usage'):
            graph = MuninGraph('ActiveMQ memory/store usage', 
                self._category,
                info='Percent used from available memory/store.',
                args='--base 1000 --lower-limit 0')
            for key in self.usagelist:
                graph.addField(key, key, draw='LINE2', type='GAUGE',
                               min=0, info=key)
            self.appendGraph('activemq_usage', graph)
        
        # we need to get the values here, in order to make queue/topic and
        # other dynamic graphs
        activemqInfo = ActiveMQInfo(self._host, self._port,
                                self._user, self._password, 
                                self._statuspath, self._ssl, self._brokername)
        self.stats = activemqInfo.getServerStats()
        for types in ['Queues','TemporaryQueues','TemporaryTopics','Topics']:
            # remove the trailing s
            type = types[:-1]
            for queue in self.stats[types]:
                name = queue['Name']
                # memory usages
                graph_name = 'activemq_%s_%s_usage_bytes' % (
                                                             type,
                                                             name.replace('.',
                                                                          '_')
                                                             )
                if self.graphEnabled(graph_name):
                    graph = MuninGraph('Memory usage of %s' % graph_name, 
                        self._category,
                        info='Memory usage in bytes',
                        vlabel='Bytes',
                        args='--base 1000 --lower-limit 0')
                    for key in ['MemoryUsageByteCount','CursorMemoryUsage']:
                        graph.addField(key, key, draw='LINE2', type='GAUGE',
                                       min=0, info=key)
                    self.appendGraph(graph_name, graph)
                # queue size
                graph_name = 'activemq_%s_%s_size' % (
                                                      type,
                                                      name.replace('.','_')
                                                      )
                if self.graphEnabled(graph_name):
                    graph = MuninGraph('Queue size of %s' % graph_name, 
                        self._category,
                        info='Queue size',
                        vlabel='msgs',
                        args='--base 1000 --lower-limit 0')
                    for key in ['QueueSize']:
                        graph.addField(key, key, draw='LINE2', type='GAUGE',
                                       min=0, info=key)
                    self.appendGraph(graph_name, graph)
                # enqueue/dequeue count
                graph_name = 'activemq_%s_%s_enqdeq' % (
                                                        type,
                                                        name.replace('.','_')
                                                        )
                if self.graphEnabled(graph_name):
                    graph = MuninGraph('Enqueue/Dequeue rate of %s' % graph_name, 
                        self._category,
                        info='Enqueue/Dequeue rate',
                        vlabel='msgs/s',
                        args='--base 1000 --lower-limit 0')
                    for key in ['EnqueueCount','DequeueCount']:
                        graph.addField(key, key, draw='LINE2', type='DERIVE',
                           min=0, max=200000, info=key)
                    self.appendGraph(graph_name, graph)
                # producer/consumer count
                graph_name = 'activemq_%s_%s_prodconsc' % (
                                                           type,
                                                           name.replace('.','_')
                                                           )
                if self.graphEnabled(graph_name):
                    graph = MuninGraph('Producer/consumer count of %s' % graph_name, 
                        self._category,
                        info='Producer/consumer count',
                        args='--base 1000 --lower-limit 0')
                    for key in ['ProducerCount','ConsumerCount']:
                        graph.addField(key, key, draw='LINE2', type='GAUGE',
                                       min=0, info=key)
                    self.appendGraph(graph_name, graph)
                # blocked time
                graph_name = 'activemq_%s_%s_blkt' % (
                                                      type,
                                                      name.replace('.','_')
                                                      )
                if self.graphEnabled(graph_name):
                    graph = MuninGraph('Blocked time of %s' % graph_name, 
                        self._category,
                        info='Blocked time in seconds since the last gather',
                        vlabel='s',
                        args='--base 1000 --lower-limit 0')
                    for key in ['TotalBlockedTime']:
                        graph.addField(key, key, draw='LINE2', type='DERIVE',
                           min=0, max=200000, info=key)
                    self.appendGraph(graph_name, graph)
             
    def retrieveVals(self):
        """Retrieve values for graphs."""
        if self.hasGraph('activemq_enqdeqrate'):
            self.setGraphVal('activemq_enqdeqrate', 'enqueue',
                             self.stats['TotalEnqueueCount'])
            self.setGraphVal('activemq_enqdeqrate', 'dequeue',
                             self.stats['TotalDequeueCount'])
            
        if self.hasGraph('activemq_prodconscount'):
            for key in self.prodconscountlist:
                self.setGraphVal('activemq_prodconscount', key, 
                                 len(self.stats[key]))

        if self.hasGraph('activemq_queuetopiccount'):
            for key in self.queuetopiccountlist:
                self.setGraphVal('activemq_queuetopiccount', key, 
                                 len(self.stats[key]))                
        
        if self.hasGraph('activemq_usage'):
            for key in self.usagelist:
                self.setGraphVal('activemq_usage', key, self.stats[key])

        for types in ['Queues','TemporaryQueues','TemporaryTopics','Topics']:
            # remove the trailing s
            type = types[:-1]
            for queue in self.stats[types]:
                name = queue['Name']
                graph_name = 'activemq_%s_%s_usage_bytes' % (
                                                             type,
                                                             name.replace('.',
                                                                          '_')
                                                             )
                for key in ['MemoryUsageByteCount','CursorMemoryUsage']:
                    try:
                        self.setGraphVal(graph_name, key, queue[key])
                    except KeyError:
                        pass
                graph_name = 'activemq_%s_%s_size' % (
                                                      type,
                                                      name.replace('.','_')
                                                      )
                for key in ['QueueSize']:
                    self.setGraphVal(graph_name, key, queue[key])
                graph_name = 'activemq_%s_%s_enqdeq' % (
                                                        type,
                                                        name.replace('.','_')
                                                        )
                for key in ['EnqueueCount','DequeueCount']:
                    self.setGraphVal(graph_name, key, queue[key])
                graph_name = 'activemq_%s_%s_prodconsc' % (
                                                           type,
                                                           name.replace('.','_')
                                                           )
                for key in ['ProducerCount','ConsumerCount']:
                    self.setGraphVal(graph_name, key, queue[key])
                graph_name = 'activemq_%s_%s_blkt' % (
                                                      type,
                                                      name.replace('.','_')
                                                      )
                for key in ['TotalBlockedTime']:
                    # time is in millis
                    self.setGraphVal(graph_name, key, queue[key]/1000.)

    def autoconf(self):
        """Implements Munin Plugin Auto-Configuration Option.
        
        @return: True if plugin can be  auto-configured, False otherwise.
                 
        """
        activemqInfo = ActiveMQInfo(self._host, self._port,
                                self._user, self._password, 
                                self._statuspath, self._ssl)
        return activemqInfo is not None


def main():
    sys.exit(muninMain(MuninActiveMQPlugin))


if __name__ == "__main__":
    main()
