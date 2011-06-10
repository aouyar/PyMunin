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
* The actual data retrieval logic is separated from the plugins to facilitate code reuse. Individual modules
in _/pymunin/pysysinfo/_ implement classes for getting the monitoring data and returning them in dictionary
objects. The separation of the data retrieval logic should facilitate the use of the same code in other 
monitoring solutions.

The initial design was inspired by [python-munin](https://github.com/samuel/python-munin) 
of [samuel](https://github.com/samuel) (Samuel Stauffer).


Munin Plugins
-------------

Multigraph Monitoring Plugins for the following applications are already
included:

* Apache Tomcat
* Apache Web Server
* Asterisk Telephony Server
* Asterisk Wanpipe Telephony Interface
* Disk Usage
* Memcached
* Network Interface Traffic and Errors
* NTP - Time Server
* PostgreSQL Database

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


The Future
----------

I would happy to receive suggestions on improving the code for developing Munin Plugins.

I hope that by sharing the code, the existing plugins will get more testing and receive improvements, and
many more Multigraph plugins will be developed collaboratively.

