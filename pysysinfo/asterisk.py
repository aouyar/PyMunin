"""Implements AsteriskInfo Class for gathering stats from the Asterisk Manager 
Interface (AMI). The AsteriskInfo Class relies on two alternative mechanisms
for  obtaining the connection parameters for AMI:
    - Connection parameters be passed to AsteriskInfo on instance instantiation.
    - AsteriskInfo implements autoconfiguration for the following setups:
        - FreePBX:        The configuration file /etc/amportal.conf is parsed.
        - Plain Asterisk: The configuration file /etc/asterisk/manager.conf 
                          is parsed.

"""

import sys
import os.path
import re
import telnetlib
import util

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9.1"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


#
# DEFAULTS
#

confFileFreePBX = '/etc/amportal.conf'
confFileAMI = '/etc/asterisk/manager.conf'
connTimeout = 5



class AsteriskInfo:
    """Class that establishes connection to Asterisk Manager Interface
    to retrieve statistics on operation.

    """

    def __init__(self, host='127.0.0.1', port=5038, user=None, password=None, 
                 autoInit=True):
        """Initialize connection to Asterisk Manager Interface.
        
        @param host:     Asterisk Host
        @param port:     Asterisk Manager Port
        @param user:     Asterisk Manager User
        @param password: Asterisk Manager Password
        @param autoInit: If True connect to Asterisk Manager Interface on 
                         instantiation.

        """
        # Set Connection Parameters
        self._amihost = host or '127.0.0.1'
        self._amiport = port or 5038
        self._amiuser = user
        self._amipass = password
        self._conn = None
        self._ami_version = None
        self._asterisk_version = None
        self._modules = None
        self._applications = None
        self._chantypes = None

        if autoInit:
            if self._amiuser is None or self._amipass is None:
                if not(self._parseFreePBXconf() or self._parseAsteriskConf()):
                    raise Exception("Asterisk Manager User and Password not defined.")

            #Initialize Connection
            self._connect()
            self._getGreeting()
            self._login()
            self._initAsteriskVersion()

    def __del__(self):
        """Cleanup."""
        if self._conn is not None:
            self._conn.close()

    def _parseFreePBXconf(self):
        """Parses FreePBX configuration file /etc/amportal for user and password
        for Asterisk Manager Interface.
        
        @return: True if configuration file is found and parsed successfully.
        
        """
        amiuser = None
        amipass = None
        if os.path.isfile(confFileFreePBX):
            try:
                fp = open(confFileFreePBX, 'r')
                data = fp.read()
                fp.close()
            except:
                raise IOError('Failed reading FreePBX configuration file: %s'
                    % confFileFreePBX)
            for (key, val) in re.findall('^(AMPMGR\w+)\s*=\s*(\S+)\s*$',
                data, re.MULTILINE):
                if key == 'AMPMGRUSER':
                    amiuser = val
                elif key == 'AMPMGRPASS':
                    amipass = val
            if amiuser and amipass:
                self._amiuser = amiuser
                self._amipass = amipass
                return True
        return False

    def _parseAsteriskConf(self):
        """Parses Asterisk configuration file /etc/asterisk/manager.conf for
        user and password for Manager Interface. Returns True on success.
        
        @return: True if configuration file is found and parsed successfully.
        
        """
        if os.path.isfile(confFileAMI):
            try:
                fp = open(confFileAMI, 'r')
                data = fp.read()
                fp.close()
            except:
                raise IOError('Failed reading Asterisk configuration file: %s'
                    % confFileAMI)
            mobj = re.search('^\[(\w+)\]\s*\r{0,1}\nsecret\s*=\s*(\S+)\s*$', 
                             data, re.MULTILINE)
            if mobj:
                self._amiuser = mobj.group(1)
                self._amipass = mobj.group(2)
                return True
        return False

    def _connect(self):
        """Connect to Asterisk Manager Interface."""
        try:
            if sys.version_info[:2] >= (2,6):
                self._conn = telnetlib.Telnet(self._amihost, self._amiport, 
                                              connTimeout)
            else:
                self._conn = telnetlib.Telnet(self._amihost, self._amiport)
        except:
            raise Exception(
                "Connection to Asterisk Manager Interface on "
                "host %s and port %s failed."
                % (self._amihost, self._amiport)
                )

    def _sendAction(self, action, keys=None, vars=None):
        """Send action to Asterisk Manager Interface.
        
        @param action: Action name
        @param keys:   Tuple of key-value pairs for action attributes.
        @param vars:   Tuple of key-value pairs for channel variables.

        """
        self._conn.write("Action: %s\r\n" % action)
        if keys:
            for (key,val) in keys:
                self._conn.write("%s: %s\r\n" % (key, val))
        if vars:
            for (key,val) in vars:
                self._conn.write("Variable: %s=%s\r\n" % (key, val))
        self._conn.write("\r\n")

    def _getResponse(self):
        """Read and parse response from Asterisk Manager Interface.
        
        @return: Dictionary with response key-value pairs.

        """
        resp_dict= dict()
        resp_str = self._conn.read_until("\r\n\r\n", connTimeout)
        for line in resp_str.split("\r\n"):
            mobj = re.match('(\w+):\s*(\S.*)$', line);
            if mobj:
                resp_dict[mobj.group(1)] = mobj.group(2)
            else:
                mobj = re.match('(.*)--END COMMAND--\s*$', line, flags=re.DOTALL)
                if mobj:
                    resp_dict['command_response'] = mobj.group(1)
        return resp_dict
        
    def _printResponse(self):
        """Read and print response from Asterisk Manager Interface."""
        resp_str = self._conn.read_until("\r\n\r\n", connTimeout)
        print resp_str

    def _getGreeting(self):
        """Read and parse Asterisk Manager Interface Greeting to determine and
        set Manager Interface version.

        """
        greeting = self._conn.read_until("\r\n", connTimeout)
        mobj = re.match('Asterisk Call Manager\/([\d\.]+)\s*$', greeting)
        if mobj:
            self._ami_version = util.SoftwareVersion(mobj.group(1))
        else:
            raise Exception("Asterisk Manager Interface version cannot be determined.")

    def _initAsteriskVersion(self):
        """Query Asterisk Manager Interface for Asterisk Version to configure
        system for compatibility with multiple versions
        .
        CLI Command - core show version

        """
        if self._ami_version > util.SoftwareVersion('1.0'):
            cmd = "core show version"
        else:
            cmd = "show version"
        cmdresp = self.executeCommand(cmd)
        mobj = re.match('Asterisk\s*(SVN-branch-|\s)(\d+(\.\d+)*)', cmdresp)
        if mobj:
            self._asterisk_version = util.SoftwareVersion(mobj.group(2))
        else:
            raise Exception('Asterisk version cannot be determined.')
        
    def _login(self):
        """Login to Asterisk Manager Interface."""
        self._sendAction("login", (
            ("Username", self._amiuser),
            ("Secret", self._amipass),
            ("Events", "off"),
        ))
        resp = self._getResponse()
        if resp.get("Response") == "Success":
            return True
        else:
            raise Exception("Authentication to Asterisk Manager Interface Failed.")

    def executeCommand(self, command):
        """Send Action to Asterisk Manager Interface to execute CLI Command.
        
        @param command: CLI command to execute.
        @return:        Command response string.

        """
        self._sendAction("Command", (
            ("Command", command),
        ))
        resp = self._getResponse()
        result = resp.get("Response")
        if result == "Follows":
            return resp.get("command_response")
        elif result == "Error":
            raise Exception("Execution of Asterisk Manager Interface Command "
                            "(%s) failed with error message: %s" % 
                            (command, str(resp.get("Message"))))
        else:
            raise Exception("Execution of Asterisk Manager Interface Command "
                            "failed: %s" % command)

    def _initModuleList(self):
        """Query Asterisk Manager Interface to initialize internal list of 
        loaded modules.
        
        CLI Command - core show modules
        
        """
        if self.checkVersion('1.4'):
            cmd = "module show"
        else:
            cmd = "show modules"
        cmdresp = self.executeCommand(cmd)
        self._modules = set()
        for line in cmdresp.splitlines()[1:-1]:
            mobj = re.match('\s*(\S+)\s', line)
            if mobj:
                self._modules.add(mobj.group(1).lower())

    def _initApplicationList(self):
        """Query Asterisk Manager Interface to initialize internal list of 
        available applications.
        
        CLI Command - core show applications
        
        """
        if self.checkVersion('1.4'):
            cmd = "core show applications"
        else:
            cmd = "show applications"
        cmdresp = self.executeCommand(cmd)
        self._applications = set()
        for line in cmdresp.splitlines()[1:-1]:
            mobj = re.match('\s*(\S+):', line)
            if mobj:
                self._applications.add(mobj.group(1).lower())
                
    def _initChannelTypesList(self):
        """Query Asterisk Manager Interface to initialize internal list of 
        supported channel types.
        
        CLI Command - core show applications
        
        """
        if self.checkVersion('1.4'):
            cmd = "core show channeltypes"
        else:
            cmd = "show channeltypes"
        cmdresp = self.executeCommand(cmd)
        self._chantypes = set()
        for line in cmdresp.splitlines()[2:]:
            mobj = re.match('\s*(\S+)\s+.*\s+(yes|no)\s+', line)
            if mobj:
                self._chantypes.add(mobj.group(1).lower())
                
    def getAsteriskVersion(self):
        """Returns Asterisk version string.
        
        @return: Asterisk version string.

        """
        return str(self._asterisk_version)
    
    def checkVersion(self, verstr):
        """Checks if Asterisk version is higher than or equal to version 
        identified by verstr.
        
        @param version: Version string.
        
        """
        return self._asterisk_version >= util.SoftwareVersion(verstr)
                                    
    def hasModule(self, mod):
        """Returns True if mod is among the loaded modules.
        
        @param mod: Module name.
        @return:    Boolean 
        
        """
        if self._modules is None:
            self._initModuleList()
        return mod in self._modules
    
    def hasApplication(self, app):
        """Returns True if app is among the loaded modules.
        
        @param app: Module name.
        @return:    Boolean 
        
        """
        if self._applications is None:
            self._initApplicationList()
        return app in self._applications
    
    def hasChannelType(self, chan):
        """Returns True if chan is among the supported channel types.
        
        @param app: Module name.
        @return:    Boolean 
        
        """
        if self._chantypes is None:
            self._initChannelTypesList()
        return chan in self._chantypes
    
    def getModuleList(self):
        """Returns list of loaded modules.
        
        @return: List 
        
        """
        if self._modules is None:
            self._initModuleList()
        return list(self._modules)
    
    def getApplicationList(self):
        """Returns list of available applications.
        
        @return: List
         
        """
        if self._applications is None:
            self._initApplicationList()
        return list(self._applications)

    def getChannelTypesList(self):
        """Returns list of supported channel types.
        
        @return: List
        
        """
        if self._chantypes is None:
            self._initChannelTypesList()
        return list(self._chantypes)
        
    
    def getCodecList(self):
        """Query Asterisk Manager Interface for defined codecs.
        
        CLI Command - core show codecs
        
        @return: Dictionary - Short Name -> (Type, Long Name)
        
        """
        if self.checkVersion('1.4'):
            cmd = "core show codecs"
        else:
            cmd = "show codecs"
        cmdresp = self.executeCommand(cmd)
        info_dict = {}
        for line in cmdresp.splitlines():
            mobj = re.match('\s*(\d+)\s+\((.+)\)\s+\((.+)\)\s+(\w+)\s+(\w+)\s+\((.+)\)$',
                            line)
            if mobj:
                info_dict[mobj.group(5)] = (mobj.group(4), mobj.group(6))
        return info_dict

    def getChannelStats(self, chantypes=('dahdi', 'zap', 'sip', 'iax2', 'local')):
        """Query Asterisk Manager Interface for Channel Stats.
        
        CLI Command - core show channels

        @return: Dictionary of statistics counters for channels.
            Number of active channels for each channel type.

        """
        if self.checkVersion('1.4'):
            cmd = "core show channels"
        else:
            cmd = "show channels"
        cmdresp = self.executeCommand(cmd)
        info_dict ={}
        for chanstr in chantypes:
            chan = chanstr.lower()
            if chan in ('zap', 'dahdi'):
                info_dict['dahdi'] = 0
                info_dict['mix'] = 0
            else:
                info_dict[chan] = 0
        for k in ('active_calls', 'active_channels', 'calls_processed'):
            info_dict[k] = 0
        regexstr = ('(%s)\/(\w+)' % '|'.join(chantypes))    
        for line in cmdresp.splitlines():
            mobj = re.match(regexstr, 
                            line, re.IGNORECASE)
            if mobj:
                chan_type = mobj.group(1).lower()
                chan_id = mobj.group(2).lower()
                if chan_type == 'dahdi' or chan_type == 'zap':
                    if chan_id == 'pseudo':
                        info_dict['mix'] += 1
                    else:
                        info_dict['dahdi'] += 1
                else:
                    info_dict[chan_type] += 1
                continue

            mobj = re.match('(\d+)\s+(active channel|active call|calls processed)', 
                            line, re.IGNORECASE)
            if mobj:
                if mobj.group(2) == 'active channel':
                    info_dict['active_channels'] = int(mobj.group(1))
                elif mobj.group(2) == 'active call':
                    info_dict['active_calls'] = int(mobj.group(1))
                elif mobj.group(2) == 'calls processed':
                    info_dict['calls_processed'] = int(mobj.group(1))
                continue

        return info_dict

    def getPeerStats(self, chantype):
        """Query Asterisk Manager Interface for SIP / IAX2 Peer Stats.
        
        CLI Command - sip show peers
                      iax2 show peers
        
        @param chantype: Must be 'sip' or 'iax2'.
        @return:         Dictionary of statistics counters for VoIP Peers.

        """
        chan = chantype.lower()
        if not self.hasChannelType(chan):
            return None
        if chan == 'iax2':
            cmd = "iax2 show peers"
        elif chan == 'sip':
            cmd = "sip show peers"
        else:
            raise AttributeError("Invalid channel type in query for Peer Stats.")
        cmdresp = self.executeCommand(cmd)
        
        info_dict = dict(
            online = 0, unreachable = 0, lagged = 0, 
            unknown = 0, unmonitored = 0)
        for line in cmdresp.splitlines():
            if re.search('ok\s+\(\d+\s+ms\)\s*$', line, re.IGNORECASE):
                info_dict['online'] += 1
            else:
                mobj = re.search('(unreachable|lagged|unknown|unmonitored)\s*$', 
                                 line, re.IGNORECASE)
                if mobj:
                    info_dict[mobj.group(1).lower()] += 1
                
        return info_dict

    def getVoIPchanStats(self, chantype, 
                         codec_list=('ulaw', 'alaw', 'gsm', 'g729')):
        """Query Asterisk Manager Interface for SIP / IAX2 Channel / Codec Stats.
        
        CLI Commands - sip show channels
                       iax2 show channnels
        
        @param chantype:   Must be 'sip' or 'iax2'.
        @param codec_list: List of codec names to parse.
                           (Codecs not in the list are summed up to the other 
                           count.)
        @return:           Dictionary of statistics counters for Active VoIP 
                           Channels.

        """
        chan = chantype.lower()
        if not self.hasChannelType(chan):
            return None
        if chan == 'iax2':
            cmd = "iax2 show channels"
        elif chan == 'sip':
            cmd = "sip show channels"
        else:
            raise AttributeError("Invalid channel type in query for Channel Stats.")
        cmdresp = self.executeCommand(cmd)
        lines = cmdresp.splitlines()
        headers = re.split('\s\s+', lines[0])
        try:
            idx = headers.index('Format')
        except ValueError:
            try:
                idx = headers.index('Form')
            except:
                raise Exception("Error in parsing header line of %s channel stats." 
                                % chan)
        codec_list = tuple(codec_list) + ('other', 'none')
        info_dict = dict([(k,0) for k in codec_list])
        for line in lines[1:-1]:
            codec = None
            cols = re.split('\s\s+', line)
            colcodec = cols[idx]
            mobj = re.match('0x\w+\s\((\w+)\)$', colcodec)
            if mobj:
                codec = mobj.group(1).lower()
            elif re.match('\w+$', colcodec):
                codec = colcodec.lower()
            if codec:
                if codec in info_dict:
                    info_dict[codec] += 1
                elif codec == 'nothing' or codec[0:4] == 'unkn':
                    info_dict['none'] += 1
                else:
                    info_dict['other'] += 1
        return info_dict
    
    def hasConference(self):
        """Returns True if system has support for Meetme Conferences.
        
        @return: Boolean
        
        """
        return self.hasModule('app_meetme.so')

    def getConferenceStats(self):
        """Query Asterisk Manager Interface for Conference Room Stats.
        
        CLI Command - meetme list

        @return: Dictionary of statistics counters for Conference Rooms.

        """
        if not self.hasConference():
            return None
        if self.checkVersion('1.6'):
            cmd = "meetme list"
        else:
            cmd = "meetme"
        cmdresp = self.executeCommand(cmd)

        info_dict = dict(active_conferences = 0, conference_users = 0)
        for line in cmdresp.splitlines():
            mobj = re.match('\w+\s+0(\d+)\s', line)
            if mobj:
                info_dict['active_conferences'] += 1
                info_dict['conference_users'] += int(mobj.group(1))

        return info_dict

    def hasVoicemail(self):
        """Returns True if system has support for Voicemail.
        
        @return: Boolean
        
        """
        return self.hasModule('app_voicemail.so')

    def getVoicemailStats(self):
        """Query Asterisk Manager Interface for Voicemail Stats.
        
        CLI Command - voicemail show users

        @return: Dictionary of statistics counters for Voicemail Accounts.

        """
        if not self.hasVoicemail():
            return None
        if self.checkVersion('1.4'):
            cmd = "voicemail show users"
        else:
            cmd = "show voicemail users"
        cmdresp = self.executeCommand(cmd)

        info_dict = dict(accounts = 0, avg_messages = 0, max_messages = 0, 
                         total_messages = 0)
        for line in cmdresp.splitlines():
            mobj = re.match('\w+\s+\w+\s+.*\s+(\d+)\s*$', line)
            if mobj:
                msgs = int(mobj.group(1))
                info_dict['accounts'] += 1
                info_dict['total_messages'] += msgs
                if msgs > info_dict['max_messages']:
                    info_dict['max_messages'] = msgs
        if info_dict['accounts'] > 0:
            info_dict['avg_messages'] = (float(info_dict['total_messages']) 
                                         / info_dict['accounts'])
            
        return info_dict

    def getTrunkStats(self, trunkList):
        """Query Asterisk Manager Interface for Trunk Stats.
        
        CLI Command - core show channels

        @param trunkList: List of tuples of one of the two following types:
                            (Trunk Name, Regular Expression)
                            (Trunk Name, Regular Expression, MIN, MAX)
        @return: Dictionary of trunk utilization statistics.

        """
        re_list = []
        info_dict = {}
        for filter in trunkList:
            info_dict[filter[0]] = 0
            re_list.append(re.compile(filter[1], re.IGNORECASE))
                  
        if self.checkVersion('1.4'):
            cmd = "core show channels"
        else:
            cmd = "show channels"
        cmdresp = self.executeCommand(cmd)

        for line in cmdresp.splitlines():
            for idx in range(len(re_list)):
                recomp = re_list[idx]
                trunkid = trunkList[idx][0]
                mobj = recomp.match(line)
                if mobj:
                    if len(trunkList[idx]) == 2:
                        info_dict[trunkid] += 1
                        continue
                    elif len(trunkList[idx]) == 4:
                        num = mobj.groupdict().get('num')
                        if num is not None:
                            (vmin,vmax) = trunkList[idx][2:4]
                            if int(num) >= int(vmin) and int(num) <= int(vmax):
                                info_dict[trunkid] += 1
                                continue
        return info_dict
    
    def hasQueue(self):
        """Returns True if system has support for Queues.
        
        @return: Boolean
        
        """
        return self.hasModule('app_queue.so')
    
    def getQueueStats(self):
        """Query Asterisk Manager Interface for Queue Stats.
        
        CLI Command: queue show
        
        @return: Dictionary of queue stats.
        
        """
        if not self.hasQueue():
            return None
        info_dict = {}
        if self.checkVersion('1.4'):
            cmd = "queue show"
        else:
            cmd = "show queues"
        cmdresp = self.executeCommand(cmd)
        
        queue = None
        ctxt = None
        member_states = ("unknown", "not in use", "in use", "busy", "invalid", 
                         "unavailable", "ringing", "ring+inuse", "on hold", 
                         "total")
        member_state_dict = dict([(k.lower().replace(' ', '_'),0) 
                                  for k in member_states]) 
        for line in cmdresp.splitlines():
            mobj = re.match(r"([\w\-]+)\s+has\s+(\d+)\s+calls\s+"
                            r"\(max (\d+|unlimited)\)\s+in\s+'(\w+)'\s+strategy\s+"
                            r"\((.+)\),\s+W:(\d+),\s+C:(\d+),\s+A:(\d+),\s+"
                            r"SL:([\d\.]+)%\s+within\s+(\d+)s", line)
            if mobj:
                ctxt = None
                queue = mobj.group(1)
                info_dict[queue] = {}
                info_dict[queue]['queue_len'] = int(mobj.group(2))
                try:
                    info_dict[queue]['queue_maxlen'] = int(mobj.group(3))
                except ValueError:
                    info_dict[queue]['queue_maxlen'] = None
                info_dict[queue]['strategy'] = mobj.group(4)
                for tkn in mobj.group(5).split(','):
                    mobjx = re.match(r"\s*(\d+)s\s+(\w+)\s*", tkn)
                    if mobjx:
                        info_dict[queue]['avg_' + mobjx.group(2)] = int(mobjx.group(1))
                info_dict[queue]['queue_weight'] = int(mobj.group(6))
                info_dict[queue]['calls_completed'] = int(mobj.group(7))
                info_dict[queue]['calls_abandoned'] = int(mobj.group(8))
                info_dict[queue]['sla_pcent'] = float(mobj.group(9))
                info_dict[queue]['sla_cutoff'] = int(mobj.group(10))
                info_dict[queue]['members'] = member_state_dict.copy() 
                continue
            mobj = re.match('\s+(Members|Callers):\s*$', line)
            if mobj:
                ctxt = mobj.group(1).lower()
                continue
            if ctxt == 'members':
                mobj = re.match(r"\s+\S.*\s\((.*)\)\s+has\s+taken.*calls", line)
                if mobj:
                    info_dict[queue]['members']['total'] += 1
                    state = mobj.group(1).lower().replace(' ', '_')
                    if info_dict[queue]['members'].has_key(state):
                        info_dict[queue]['members'][state] += 1
                    else:
                        raise AttributeError("Undefined queue member state %s"
                                             % state)
                    continue
        return info_dict
    
    def hasFax(self):
        """Returns True if system has support for faxing.
        
        @return: Boolean
        
        """
        return self.hasModule('res_fax.so')
    
    def getFaxStatsCounters(self):
        """Query Asterisk Manager Interface for Fax Stats.
        
        CLI Command - fax show stats
        
        @return: Dictionary of fax stats.
        
        """
        if not self.hasFax():
            return None
        info_dict = {}
        cmdresp = self.executeCommand('fax show stats')
        ctxt = 'general'
        for section in cmdresp.strip().split('\n\n')[1:]:
            i = 0
            for line in section.splitlines():
                mobj = re.match('(\S.*\S)\s*:\s*(\d+)\s*$', line)
                if mobj:
                    if not info_dict.has_key(ctxt):
                        info_dict[ctxt] = {}
                    info_dict[ctxt][mobj.group(1).lower()] = int(mobj.group(2).lower())
                elif i == 0:
                    ctxt = line.strip().lower()
                i += 1    
        return info_dict

    def getFaxStatsSessions(self):
        """Query Asterisk Manager Interface for Fax Stats.
        
        CLI Command - fax show sessions
        
        @return: Dictionary of fax stats.
        
        """
        if not self.hasFax():
            return None
        info_dict = {}
        info_dict['total'] = 0
        fax_types = ('g.711', 't.38')
        fax_operations = ('send', 'recv')
        fax_states = ('uninitialized', 'initialized', 'open', 
                      'active', 'inactive', 'complete', 'unknown',)
        info_dict['type'] = dict([(k,0) for k in fax_types])
        info_dict['operation'] = dict([(k,0) for k in fax_operations])
        info_dict['state'] = dict([(k,0) for k in fax_states])
        cmdresp = self.executeCommand('fax show sessions')
        sections = cmdresp.strip().split('\n\n')
        if len(sections) >= 3:
            for line in sections[1][1:]:
                cols = re.split('\s\s+', line)
                if len(cols) == 7:
                    info_dict['total'] += 1
                    if cols[3].lower() in fax_types:
                        info_dict['type'][cols[3].lower()] += 1
                    if cols[4] == 'receive':
                        info_dict['operation']['recv'] += 1
                    elif cols[4] == 'send':
                        info_dict['operation']['send'] += 1
                    if cols[5].lower() in fax_states:
                        info_dict['state'][cols[5].lower()] += 1
        return info_dict
