PyMunin - Python Multigraph Munin Plugins
=========================================

Python Module for developing Munin Multigraph Monitoring Plugins.

Regular Munin Plugins employ one-plugin one-graph logic and require the 
execution of a script for data retrieval for each graph.
Multigraph plugins permit retrieval of data for multiple graphs in one execution 
run (one-plugin many-graphs), reducing the processing time and delay for the 
fetch cycle significantly.
More information on Multigraph Plugins can be found in the 
[Munin Wiki](http://munin-monitoring.org/wiki/):

* [Multigraph Plugins](http://munin-monitoring.org/wiki/MultigraphSampleOutput)
* [Multigraph Plugin Protocol](http://munin-monitoring.org/wiki/protocol-multigraph)

The plugins consist of the following components:

* The _pymunin_ module _(./plugins/pymunin)_ implements the base classes for
  developing Munin plugins.
* The plugin logic is implemented in the plugin scripts in _/pymunin_.
* The actual data retrieval logic is separated from the plugins to facilitate
  code reuse. Individual modules in the directory _./pysysinfo_ implement classes 
  for getting the monitoring data and returning them in dictionary objects. 
  The separation of the data retrieval logic should facilitate the use of the 
  same code in other monitoring solution.

Although the solution is focused on implementing _Multigraph Plugins_ the module
also supports simple single graph plugins.

The initial design of the solution was inspired by 
[python-munin](https://github.com/samuel/python-munin) 
by [samuel](https://github.com/samuel) (Samuel Stauffer).


Munin Plugins
-------------

Multigraph Monitoring Plugins for the following applications are already
included:

* Apache Tomcat
* Apache Web Server
* Asterisk Telephony Server
* Disk Usage
* Disk I/O
* FreeSWITCH Soft Switch
* Memcached
* MySQL Database
* Network Interface Traffic and Errors
* Nginx Web Server
* NTP - Time Server
* PHP APC - PHP Cache
* PHP FPM (FastCGI Process Manager)
* PostgreSQL Database
* System Resources 
  (Load, CPU, Memory, Processes, Interrupts, Paging, Swapping, etc.)
* Sangoma Wanpipe Telephony Interfaces

Classes for retrieving stats are available, but no plugins have been developed
yet for the following:

* Squid Web Proxy


Documentation
-------------

The documentation for the project and sample graphs for plugins will be 
published in the [PyMunin Project Web Page](http://aouyar.github.com/PyMunin/)


Installation
------------

### Installation of the Libraries ###

* The _pysysinfo_ directory should be placed in _PYTHON_ search path or in the 
  _Munin Plugins_ directory (ex. _/usr/share/munin/plugins_).
* The _plugins/pymunin_ directory should be placed in _PYTHON_ search path or in 
  the _Munin Plugins_ directory (ex. _/usr/share/munin/plugins_).
  
### Installation of the Plugins ###

* Copy the plugin scripts in the directory _plugins_ to the _Munin Plugins_ 
  directory (ex. _/usr/share/munin/plugins_) and remove the file extension
  '_py_'.
* Enable the plugins just like the standard plugins by creating a symbolic links 
  in the _Munin Plugins Configuration Directory_ (_/etc/munin/plugins_).
* Configuration files for plugins can be created in the _Munin Plugins
  Configuration Directory_ (_/etc/munin/plugin-conf.d_). The environment 
  variables used by the plugin scripts are documented in the header part of the
  script code.


Plugin Development
------------------

The first step for implementing a new _Multigraph Munin Plugin_ is developing a 
new module in _pysysinfo_ for retrieving the monitoring data.

The steps for developing the actual plugin script are as follows:

* The new plugin can be implemented by extending the the _MuninPlugin_ class in 
  _./plugins/pymunin_.
* The _plugin_name_ property of _MuninPlugin_ class must be set to the name of 
  the plugin.
* Graph Objects are registered to the plugin in the constructor of the plugin
  class.
* Code for creating graph objects of _MuninGraph_ class are placed in the 
  constructor of the plugin class.
* Code for adding fields to the graph using the _addField_ method of _MuninGraph_ 
  class is placed in the constructor of the plugin class.
* The _retrieveVals_ method of the plugin class is overwritten to retrieve 
  data points and to associate values with the graph fields.
* The _muninMain_ function in _pymunin_ is called with the plugin class as 
  argument for initializing the main method of plugin. 


Collaboration
-------------

I would be happy to receive suggestions on improving the code for developing 
Munin Plugins. Alternatively you can use the _Issues_ functionality of _GitHub_ 
to document problems and to propose improvements. You can use the internal 
messaging system of _GitHub_ or my e-mail address in case you prefer to 
contact me directly.

I hope that by sharing the code, the existing plugins will get more testing and 
receive improvements, and many more Multigraph plugins will be developed 
collaboratively.

I would be glad to receive some sample graphs from anyone using the plugins.


Licensing
---------

_PyMunin_ is copyrighted free software made available under the terms of the 
_GPL License Version 3_ or later.

See the _COPYING_ file that acompanies the code for full licensing information.
