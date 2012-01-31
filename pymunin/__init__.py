"""Foundations for creating MultiGraph Munin Plugins.

    - Munin Plugins can be created by subclassing the MuninPlugin Class.
    - Each plugin contains one or more graphs implemented by MuninGraph instances.
    - The muninMain function implements the entry point for Munin Plugins.

"""

import os.path
import sys
import re
import cPickle as pickle

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = ["Samuel Stauffer"]
__license__ = "GPL"
__version__ = "0.9.3"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


maxLabelLenGraphSimple = 40
maxLabelLenGraphDual = 14


class MuninAttrFilter:
    """Class for implementing Attribute Filters for Munin Graphs.
    
    - Attributes are filtered using an Include List and an Exclude List.
    - If the include List is empty, all Attributes are enabled by default.
    - If the Include List is not empty, only the Attributes that are in the
      list are enabled.
    - Any Attribute that is in the Exclude List is disabled.
    
    """
    
    def __init__(self, list_include = [], list_exclude = [], 
                 attr_regex = None, default = True):
        """Initialize Munin Attribute Filter.
        
        @param list_include: Include List (List of attributes that are enabled.)
        @param list_exclude: Exclude List (List of attributes that are disabled.)
        @param attr_regex:   If the regex is defined, the Attributes in the 
                             Include List and Exclude List are ignored unless 
                             they comply with the format dictated by the match 
                             regex.
        @param default:      Filter default. Applies when the include list is 
                             not defined and the attribute is not in the exclude 
                             list.
        
        """
        self._attrs = {}
        self._default = default
        if attr_regex:
            self._regex = re.compile(attr_regex)
        else:
            self._regex = None
        if list_include:
            self._default = False
            for attr in list_include:
                if not self._regex or self._regex.search(attr):
                    self._attrs[attr] = True
        if list_exclude:
            for attr in list_exclude:
                if not self._regex or self._regex.search(attr):
                    self._attrs[attr] = False
    
    def check(self, attr):
        """Check if the attribute attr is in the include or exclude list.
        Returns True if the attribute is enabled, false otherwise.
        
        @param attr: Name of attribute.
        
        """
        return self._attrs.get(attr, self._default)


class MuninPlugin:
    """Base class for Munin Plugins

    Munin Plugins are implemented as child classes which contain
    single or multiple MuninGraph objects.

    """

    plugin_name = None
    """The name of the plugin executable.
    Must be overriden in child classes to indicate plugin name.
    If it ends with an underscore the name will be parsed to separate plugin
    argument embedded in the name."""

    isMultigraph = False
    """True for Multi-Graph Plugins, and False for Simple Plugins.
    Must be overriden in child classes to indicate plugin type."""

    def __init__(self, argv=(), env={}, debug=False):
        """Constructor for MuninPlugin Class.
        
        @param argv: List of command line arguments.
        @param env:  Dict of environment variables.
            
        """
        self._graphDict = {}
        self._graphNames = []
        self._subGraphDict = {}
        self._filters = {}
        self._flags = {}
        self._argv = argv
        self._env = env
        self.arg0 = None
        self._debug = debug
        self._dirtyConfig = False
        if (self.plugin_name is not None and argv is not None and len(argv) > 0 
            and re.search('_$', self.plugin_name)):
            mobj = re.match("%s(\S+)$" % self.plugin_name, 
                            os.path.basename(argv[0]))
            if mobj:
                self.arg0 = mobj.group(1)
        self._parseEnv()
        self.envRegisterFilter('graphs', '^[\w\-]+$')
        self._nestedGraphs = self.envCheckFlag('nested_graphs', True)
                
    def _parseEnv(self,  env=None):
        """Utility method that parses through environment variables.
        
        Parses for environment variables common to all Munin Plugins:
            - MUNIN_STATEFILE
            - MUNIN_CAP_DIRTY_CONFIG
            - nested_graphs
        
        @param env: Dictionary of environment variables.
                    (Only used for testing. initialized automatically by constructor.
        
        """
        if not env:
            env = self._env
        if env.has_key('MUNIN_STATEFILE'):
            self._stateFile = env.get('MUNIN_STATEFILE')
        else:
            self._stateFile = '/tmp/munin-state-%s' % self.plugin_name
        if env.has_key('MUNIN_CAP_DIRTY_CONFIG'):
            self._dirtyConfig = True
       
    def envHasKey(self, name):
        """Return True if environment variable with name exists.  
        
        @param name: Name of environtment variable.
        
        """
        return self._env.has_key(name)
    
    def envGet(self, name, default=None):
        """Return value for environment variable or None.  
        
        @param name:    Name of environment variable.
        @param default: Default value if variable is undefined.
        
        """
        return self._env.get(name, default)
    
    def envGetList(self, name, attr_regex = '^\w+$'):
        """Parse the plugin environment variables to return list from variable
        with name list_<name>. The value of the variable must be a comma 
        separated list of items.
        
        @param name:       Name of list.
                           (Also determines suffix for environment variable name.)
        @param attr_regex: If the regex is defined, the items in the list are 
                           ignored unless they comply with the format dictated 
                           by the match regex.
        @return:           List of items.
        
        """
        key = "list_%s" % name
        item_list = []
        if self._env.has_key(key):
            if attr_regex:
                recomp = re.compile(attr_regex)
                for attr in self._env[key].split(','):
                    attr = attr.strip()
                    if recomp.search(attr):
                        item_list.append(attr) 
            else:
                item_list = [attr.strip() for attr in self._env[key].split(',')]
        return item_list
    
    def envRegisterFilter(self, name, attr_regex = '^\w+$', default = True):
        """Register filter for including, excluding attributes in graphs through 
        the use of include_<name> and exclude_<name> environment variables.
        The value of the variables must be a comma separated list of items. 
        
        @param name:       Name of filter.
                           (Also determines suffix for environment variable name.)
        @param attr_regex: Regular expression string for checking valid items.
        @param default:    Filter default. Applies when the include list is not 
                           defined and the attribute is not in the exclude list.
        
        """
        attrs = {}
        for prefix in ('include', 'exclude'):
            key = "%s_%s" % (prefix, name)
            val = self._env.get(key)
            if val:
                attrs[prefix] = [attr.strip() for attr in val.split(',')]
            else:
                attrs[prefix] = []
        self._filters[name] = MuninAttrFilter(attrs['include'], attrs['exclude'], 
                                              attr_regex, default)
        
    def envCheckFilter(self, name, attr):
        """Check if a specific graph attribute is enabled or disabled through 
        the use of a filter based on include_<name> and exclude_<name> 
        environment variables.
        
        @param name: Name of the Filter.
        @param attr: Name of the Attribute.
        @return:     Return True if the attribute is enabled.
        
        """
        filter = self._filters.get(name)
        if filter:
            return filter.check(attr) 
        else:
            raise AttributeError("Undefined filter: %s" % name)
        
    def envCheckFlag(self, name, default = False):
        """Check graph flag for enabling / disabling attributes through
        the use of <name> environment variable.
        
        @param name:    Name of flag.
                        (Also determines the environment variable name.)
        @param default: Boolean (True or False). Default value for flag.
        @return:        Return True if the flag is enabled.
        
        """
        if self._flags.has_key(name):
            return self._flags[name]
        else:
            val = self._env.get(name)
            if val is None:
                return default
            elif val.lower() in ['yes', 'on']:
                self._flags[name] = True
                return True
            elif val.lower() in ['no', 'off']:
                self._flags[name] = False
                return False
            else:
                raise AttributeError("Value for flag %s, must be yes, no, on or off" 
                                     % name)
                
    def debugEnabled(self):
        """Return True if plugin debugging is enabled.
        
            @return: Boolean
            
        """
        return self._debug
    
    def graphEnabled(self, name):
        """Utility method to check if graph with the given name is enabled.
        
        @param name: Name of Root Graph Instance.
        @return:     Returns True if Root Graph is enabled, False otherwise.
            
        """
        return self.envCheckFilter('graphs', name)
        
    def saveState(self,  stateObj):
        """Utility methos to save plugin state stored in stateObj to persistent 
        storage to permit access to previous state in subsequent plugin runs.
        
        Any object that can be pickled and unpickled can be used to store the 
        plugin state.
        
        @param stateObj: Object that stores plugin state.
        
        """
        try:
            fp = open(self._stateFile,  'w')
            pickle.dump(stateObj, fp)
        except:
            raise IOError("Failure in storing plugin state in file: %s" 
                          % self._stateFile)
        return True
    
    def restoreState(self):
        """Utility method to restore plugin state from persistent storage to 
        permit access to previous plugin state.
        
        @return: Object that stores plugin state.
        
        """
        if os.path.exists(self._stateFile):
            try:
                fp = open(self._stateFile,  'r')
                stateObj = pickle.load(fp)
            except:
                raise IOError("Failure in reading plugin state from file: %s" 
                              % self._stateFile)
            return stateObj
        return None
        
    def appendGraph(self, name, graph):
        """Utility method to associate Graph Object to Plugin.
        
        This utility method is for use in constructor of child classes for
        associating a MuninGraph instances to the plugin.
        
        @param name:  Graph Name
        @param graph: MuninGraph Instance

        """
        self._graphDict[name] = graph
        self._graphNames.append(name)
        if not self.isMultigraph  and len(self._graphNames) > 1:
            raise AttributeError("Simple Munin Plugins cannot have more than one graph.")
        
    def appendSubgraph(self, parent_name,  graph_name, graph):
        """Utility method to associate Subgraph Instance to Root Graph Instance.

        This utility method is for use in constructor of child classes for 
        associating a MuninGraph Subgraph instance with a Root Graph instance.
        
        @param parent_name: Root Graph Name
        @param graph_name:  Subgraph Name
        @param graph:       MuninGraph Instance

        """
        if not self.isMultigraph:
            raise AttributeError("Simple Munin Plugins cannot have more than one graph.")
        if self._graphDict.has_key(parent_name):
            if not self._subGraphDict.has_key(parent_name):
                self._subGraphDict['parent_name'] = {}
            self._subGraphDict['parent_name']['graph_name'] = graph
        else:
            raise AttributeError("Invalid parent graph name %s used for subgraph %s."
                % (parent_name,  graph_name))
            
    def setGraphVal(self, graph_name, field_name, val):
        """Utility method to set Value for Field in Graph.
        
        The private method is for use in retrieveVals() method of child classes.
        
        @param name:    Graph Name
        @param valDict: Dictionary of monitored values

        """
        graph = self._graphDict.get(graph_name)
        if graph is not None:
            if graph.hasField(field_name):
                graph.setVal(field_name, val)
            else:
                raise AttributeError("Invalid field name %s used for setting "
                                     "value for graph %s." 
                                     % (field_name, graph_name))
        else:
            raise AttributeError("Invalid graph name %s used for setting value." 
                                 % graph_name)
    
    def setSubgraphVal(self,  parent_name,  graph_name,  val):
        """Set Value for Field in Subgraph.

        The private method is for use in retrieveVals() method of child
        classes.
        
        @param parent_name: Root Graph Name
        @param name:        Subgraph Name
        @param valDict:     Dictionary of monitored values

        """        
        graph = self._graphDict.get(parent_name)
        if graph is not None:
            graph.setVal("%s.%s" % (parent_name, graph_name),  val)
        else:
            raise AttributeError("Invalid parent graph name %s used "
                                 "for setting value for subgraph %s."
                                 % (parent_name, graph_name))
    
    def hasGraph(self, name):
        """Return true if graph with name is registered to plugin.
        
        @return: Boolean
        
        """
        return self._graphDict.has_key(name)
            
    def getGraphList(self):
        """Returns list of names of graphs registered to plugin.
        
        @return - List of graph names.
        
        """
        return self._graphNames

    def graphHasField(self, graph_name, field_name):
        """Return true if graph with name graph_name has field with 
        name field_name.
        
        @return: Boolean
        
        """
        return self._graphDict[graph_name].hasField(field_name)
            
    def getGraphFieldList(self, graph_name):
        """Returns list of names of fields for graph with name graph_name.
        
        @return - List of field names for graph.
        
        """
        return self._graphDict[graph_name].getFieldList()
        
    def retrieveVals(self):
        """Initialize measured values for Graphs.

        This method must be overwritten in child classes for initializing the
        values to be graphed by the Munin Plugin.

        """
        pass

    def autoconf(self):
        """Implements Munin Plugin Auto-Configuration Option.

        Auto-configuration is disabled by default. To implement 
        auto-configuration for the Munin Plugin, this method must be overwritten 
        in child class.

        """
        return False

    def config(self):
        """Implements Munin Plugin Graph Configuration.
        
        Prints out configuration for graphs.

        Use as is. Not required to be overwritten in child classes. The plugin
        will work correctly as long as the Munin Graph objects have been 
        populated.

        """
        for name in self._graphNames:
            graph = self._graphDict[name]
            if self.isMultigraph:
                print "multigraph %s" % name
            print graph.getConfig()
            print
        if self._nestedGraphs and self._subGraphDict:
            for (parent_name, subgraphs) in self._subGraphDict.iteritems():
                for (graph_name,  graph) in subgraphs:
                    print "multigraph %s.%s" % (parent_name,  graph_name)
                    print graph.getConfig()
                    print
        return True

    def suggest(self):
        """Implements Munin Plugin Suggest Option.

        Suggest option is disabled by default. To implement the Suggest option
        for the Munin, Plugin this method must be overwritten in child class.

        """
        return True

    def fetch(self):
        """Implements Munin Plugin Fetch Option.

        Prints out measured values.

        """
        self.retrieveVals()
        for name in self._graphNames:
            graph = self._graphDict[name]
            if self.isMultigraph:
                print "multigraph %s" % name
            print graph.getVals()
            print
        if self._nestedGraphs and self._subGraphDict:
            for (parent_name, subgraphs) in self._subGraphDict.iteritems():
                for (graph_name,  graph) in subgraphs:
                    print "multigraph %s.%s" % (parent_name,  graph_name)
                    print graph.getVals()
                    print
        return True

    def run(self):
        """Implements main entry point for plugin execution."""
        if len(self._argv) > 1 and len(self._argv[1]) > 0:
            oper = self._argv[1]
        else:
            oper = 'fetch'
        if oper == 'fetch':
            ret = self.fetch()
        elif oper == 'config':
            ret = self.config()
            if ret and self._dirtyConfig:
                ret = self.fetch()
        elif oper == 'autoconf':
            ret = self.autoconf()
            if ret:
                print "yes"
            else:
                print "no"
            ret = True
        elif oper == 'suggest':
            ret = self.suggest()
        else:
            raise AttributeError("Invalid command argument: %s" % oper)
        return ret


class MuninGraph:
    """Base class for Munin Graphs

    """

    def __init__(self, title, category = None, vlabel=None, info=None, 
                 args =None, period=None, scale=None,  total=None, order=None, 
                 printf=None, witdh=None, height=None,
                 autoFixNames = False):
        """Initialize Munin Graph.
        
        @param title:        Graph Title
        @param category:     Graph Category
        @param vlabel:       Label on Vertical Axis
        @param info:         Graph Information
        @param args:         Args passed to RRDtool
        @param period:       Time Unit - 'second' / 'minute' (Default: 'second')
        @param scale:        Graph Scaling - True / False (Default: True)
        @param total:        Add a total field with sum of all datasources if 
                             defined. The value of the parameter is used as the 
                             label for the total field.
        @param order:        The order in which the fields are drawn on graph.
                             The attribute must contain a comma separated list 
                             of field names.
                             When the parameter is not used, the datasources are 
                             drawn in the order they are defined by default.
        @param printf:       Format for printing numbers on graph. The defaults 
                             are usually OK and this parameter is rarely needed.
        @param width:        Graph width in pixels.
        @param height:       Graph height in pixels.
        @param autoFixNames: Automatically fix invalid characters in field names
                             by replacing them with '_'.
        
        """
        self._graphAttrDict = locals()
        self._fieldNameList = []
        self._fieldAttrDict = {}
        self._fieldValDict = {}
        self._autoFixNames = autoFixNames

    def addField(self, name, label, type=None,  draw=None, info=None, 
                 extinfo=None, colour=None, negative=None, graph=None, 
                 min=None, max=None, cdef=None, line=None, 
                 warning=None, critical=None):
        """Add field to Munin Graph
        
            @param name:     Field Name
            @param label:    Field Label
            @param type:     Stat Type:
                             'COUNTER' / 'ABSOLUTE' / 'DERIVE' / 'GAUGE'
            @param draw:     Graph Type:
                             'AREA' / 'LINE{1,2,3}' / 
                             'STACK' / 'LINESTACK{1,2,3}' / 'AREASTACK'
            @param info:     Detailed Field Info
            @param extinfo:  Extended Field Info
            @param colour:   Field Colour
            @param negative: Mirror Value
            @param graph:    Draw on Graph - True / False (Default: True)
            @param min:      Minimum Valid Value
            @param max:      Maximum Valid Value
            @param cdef:     CDEF
            @param line:     Adds horizontal line at value defined for field. 
            @param warning:  Warning Value
            @param critical: Critical Value
            
        """
        if self._autoFixNames:
            name = self._fixName(name)
            if negative is not None:
                negative = self._fixName(negative)
        self._fieldAttrDict[name] = locals()
        self._fieldNameList.append(name)

    def hasField(self, name):
        """Returns true if field with field_name exists.
        
        @param name: Field Name
        @return:     Boolean
        
        """
        if self._autoFixNames:
            name = self._fixName(name)
        return self._fieldAttrDict.has_key(name)
    
    def getFieldList(self):
        """Returns list of field names registered to Munin Graph.
        
        @return: List of field names registered to Munin Graph.
        
        """
        return self._fieldNameList
    
    def getConfig(self):
        """Returns config entries for Munin Graph.
        
        @return: Multi-line text output with Munin Graph configuration. 
        
        """
        conf = []
        
        # Process Graph Attributes
        for key in ('title', 'category', 'vlabel', 'info', 'args', 'period', 
                    'scale', 'total', 'order', 'printf', 'width', 'height'):
            val = self._graphAttrDict.get(key)
            if val is not None:
                if isinstance(val, bool):
                    if val:
                        val = "yes"
                    else:
                        val = "no"
                conf.append("graph_%s %s" % (key,val))

        # Process Field Attributes
        for field_name in self._fieldNameList:
            field_attrs = self._fieldAttrDict.get(field_name)
            for key in ('label', 'type', 'draw', 'info', 'extinfo', 'colour',
                        'negative', 'graph', 'min', 'max', 'cdef', 
                        'line', 'warning', 'critical'):
                val = field_attrs.get(key)
                if val is not None:
                    if isinstance(val, bool):
                        if val:
                            val = "yes"
                        else:
                            val = "no"
                    conf.append("%s.%s %s" % (field_name, key, val))
        return "\n".join(conf)

    def setVal(self, name, val):
        """Set value for field in graph.
        
        @param name   : Graph Name
        @param value  : Value for field. 
        
        """
        if self._autoFixNames:
            name = self._fixName(name)
        if val is not None:
            self._fieldValDict[name] = val
        else:
            self._fieldValDict[name] = 'U'

    def getVals(self):
        """Returns value entries for Munin Graph
        
        @return: Multi-line text output with Munin Graph values.
        
        """
        vals = []
        for name in self._fieldNameList:
            val = self._fieldValDict.get(name)
            if val is not None:
                if isinstance(val, float):
                    vals.append("%s.value %f" % (name, val))
                else:
                    vals.append("%s.value %s" % (name, val))
        return "\n".join(vals)
    
    def _fixName(self, name):
        """Replace invalid characters in field names with underscore.
            @param name: Original name.
            @return:     Fixed name.
            
        """        
        return re.sub('[^A-Za-z0-9_]', '_',
                      re.sub('^[^A-Za-z_]', '_', name))


def muninMain(pluginClass, argv=None, env=None, debug=False):
    """Main Block for Munin Plugins.
    
    @param pluginClass: Child class of MuninPlugin that implements plugin.
    @param argv:        List of command line arguments to Munin Plugin.
    @param env:         Dictionary of environment variables passed to Munin Plugin.
    @param debug:       Print debugging messages if True. (Default: False)
    
    """
    if argv is None:
        argv = sys.argv
    if env is None:
        env = os.environ
    debug = debug or env.has_key('MUNIN_DEBUG')
    try:
        plugin = pluginClass(argv, env, debug)
        ret = plugin.run()
        if ret:
            return 0
        else:
            return 1
    except Exception, msg:
        if debug:
            raise
        else:
            print >> sys.stderr, "EXCEPTION: %s" % msg
        return 1


def fixLabel(label, maxlen, delim=None, repl='', truncend=True):
    """Truncate long graph and field labels.
    
        @param label:    Label text.
        @param maxlen:   Maximum field label length in characters.
                         No maximum field label length is enforced by default.
        @param delim:    Delimiter for field labels field labels longer than 
                         maxlen will preferably be truncated at delimiter.
        @param repl:     Replacement string for truncated part.
        @param truncend: Truncate the end of label name if True. (Default)
                         The beginning part of label will be truncated if False.
                         
    """
    if len(label) <= maxlen:
        return label
    else:
        maxlen -= len(repl)
        if delim is not None:  
            if truncend:
                end = label.rfind(delim, 0, maxlen)
                if end > 0:
                    return label[:end+1] + repl
            else:
                start = label.find(delim, len(label) - maxlen)
                if start > 0:
                    return repl + label[start:]
        if truncend:
            return label[:maxlen] + repl
        else:
            return repl + label[-maxlen:]
            
            
    