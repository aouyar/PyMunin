PyMunin - Python Multigraph Munin Plugins
=========================================

Python Module for developing Munin Multigraph Monitoring Plugins.

Regular Munin Plugins employ one-plugin one-graph logic and require the execution of a script for data 
retrieval for each graph.
Multigraph plugins permit retrieval of data for multiple graphs in one execution run (one-plugin many-graphs), 
reducing the processing time and delay for the fetch cycle significantly.
More information on Multigraph Plugins can be found in the [Munin Wiki](http://munin-monitoring.org/wiki/):

* [Multigraph Plugins](http://munin-monitoring.org/wiki/MultigraphSampleOutput)
* [Multigraph Plugin Protocol](http://munin-monitoring.org/wiki/protocol-multigraph)

The plugins consist of the following components:

* The _pymunin_ module _(/pymunin/pymunin)_ implements the base classes for developing Munin plugins.
* The plugin logic is implemented in the plugin scripts in _/pymunin_.
* The actual data retrieval logic is separated from the plugins to facilitate code reuse.
  Individual modules in _/pymunin/pysysinfo/_ implement classes for getting the monitoring data and
  returning them in dictionary objects. The separation of the data retrieval logic should facilitate 
  the use of the same code in other monitoring solution.

Although the solution is focused on implementing _Multigraph Plugins_ the 

The initial design of the solution was inspired by [python-munin](https://github.com/samuel/python-munin) 
by [samuel](https://github.com/samuel) (Samuel Stauffer).


Plugin Development
------------------

The first step for implementing a new _Multigraph Munin Plugin_ is developing a new module in _pysysinfo_ for
retrieving the monitoring data.

The steps for developing the actual plugin script are as follows:

* The new plugin can be implemented by extending the the _MuninPlugin_ class in _pymunin_.
* The _plugin_name_ property of _MuninPlugin_ class must be set to the name of the plugin.
* Graph Objects are registered to the plugin in the constructor of the plugin class.
* Code for creating graph objects using the _MuninGraph_ class is placed in the constructor.
* Code for adding fields to the graph using the _addField_ method of _MuninGraph_ class 
  is placed in the constructor.
* The _retrieveVals_ method of the plugin class is overwritten to retrieve data points and to associate values
  with the graph fields.
* The _muninMain_ function in _pymunin_ is called with the plugin class as argument for initializing the main
  method of plugin. 


Munin Plugins
-------------

Multigraph Monitoring Plugins for the following applications are already
included:

* Apache Tomcat
* Apache Web Server
* Asterisk Telephony Server
* Disk Usage
* Memcached
* Network Interface Traffic and Errors
* NTP - Time Server
* PostgreSQL Database
* Sangoma Wanpipe Telephony Interfaces

Classes for retrieving stats are available, but no plugins have been developed
yet for the following:

* APC - PHP Cache
* Disk I/O
* MySQL Database
* Squid Web Proxy
* System - Processor Utilization
* System - Load Average
* System - Processes
* System - Memory Usage


Licensing
_________

PyMunin is copyrighted free software made available under the terms of the GPL License Version 3 or later.
See the file COPYING that acompanies the code for full licensing information.


The Future
----------

I would be happy to receive suggestions on improving the code for developing Munin Plugins.

I hope that by sharing the code, the existing plugins will get more testing and receive improvements, and
many more Multigraph plugins will be developed collaboratively.
