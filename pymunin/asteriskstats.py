#!/usr/bin/python
#
# asteriskstats - Munin Plugin to monitor Asterisk through Manager Interface
#
# Requirements
#   - Access to Asterisk Manager Interface
#
# Wild Card Plugin - No
#
# Multigraph Plugin - Graph Structure
#    - asterisk_calls
#    - asterisk_channels
#    - asterisk_peers_sip
#    - asterisk_peers_iax2
#    - asterisk_voip_codecs
#    - asterisk_conferences
#    - asterisk_voicemail
#    - asterisk_trunks
#
#
# Environment Variables
#
#   include_graphs: Comma separated list of enabled graphs. (All graphs enabled by default.)
#   exclude_graphs: Comma separated list of disabled graphs.
#   amihost:        IP of Asterisk Server (Default: 127.0.0.1)
#   amiport:        Asterisk Manager Interface Port (Default: 5038)
#   amiuser:        Asterisk Manager Interface User
#   amipass:        Asterisk Manager Interface Password
#   trunks:         Comma separated search expressions of the following formats:
#                   - "Trunk Name"="Regular Expression"
#                   - "Trunk Name"="Regular Expression /w Named Group num"="MIN"-"MAX"
#
#   Example:
#       [asteriskstats]
#         env.amihost 192.168.1.10
#         env.amiport 5038
#         env.amiuser manager
#         env.amipass secret
#         env.trunks PSTN=    Zap\/(?P<num>\d+)=1-3,VoIP=SIP\/(net2phone|skype)
#
#
# Munin  - Magic Markers
#%# family=manual
#%# capabilities=noautoconf nosuggest

import sys
import re
from pymunin import MuninGraph, MuninPlugin, muninMain
from pysysinfo.asterisk import AsteriskInfo

__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninAsteriskPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring Asterisk.

    """
    plugin_name = 'asteriskstats'
    isMultigraph = True

    def __init__(self, argv = (), env = {}):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv: List of command line arguments.
        @param env:  Dictionary of environment variables.
        
        """
        MuninPlugin.__init__(self, argv, env)

        self._amihost = self._env.get('amihost')
        self._amiport = self._env.get('amiport')
        self._amiuser = self._env.get('amiuser')
        self._amipass = self._env.get('amipass')

        self._trunkList = []
        if self._env.has_key('trunks'):
            strtrunks = re.sub('[\s]',  '',  self._env.get('trunks'))
            for trunk_entry in strtrunks.split(','):
                mobj = (re.match('(.*)=(.*)=(\d+)-(\d+)',  trunk_entry,  re.IGNORECASE) 
                        or re.match('(.*)=(.*)',  trunk_entry,  re.IGNORECASE))
                if mobj:
                    self._trunkList.append(mobj.groups())

        if self.graphEnabled('asterisk_calls'):
            graph = MuninGraph('Asterisk - Call Stats', 'Asterisk',
                info = 'Asterisk - Information on Calls.', period='minute',
                args = '--base 1000 --lower-limit 0')
            graph.addField('active_calls', 'active_calls', type='GAUGE',
                draw='LINE2',info='Active Calls')
            graph.addField('calls_per_min','calls_per_min', type='DERIVE', min=0,
                draw='LINE2', info='Calls per minute')
            self.appendGraph('asterisk_calls', graph)

        if self.graphEnabled('asterisk_channels'):
            graph = MuninGraph('Asterisk - Active Channels', 'Asterisk',
                info = 'Asterisk - Information on Active Channels.',
                args = '--base 1000 --lower-limit 0')
            for field in ('sip', 'iax2', 'dahdi', 'misdn', 'local', 'mix'):
                graph.addField(field, field, type='GAUGE', draw='AREASTACK')
            graph.addField('mix', 'mix', draw='LINE2')
            self.appendGraph('asterisk_channels', graph)

        if self.graphEnabled('asterisk_peers_sip'):
            graph = MuninGraph('Asterisk - VoIP Peers - SIP', 'Asterisk',
                info = 'Asterisk - Information on SIP VoIP Peers.',
                args = '--base 1000 --lower-limit 0')
            for field in ('online', 'unmonitored', 'unreachable', 'lagged', 'unknown'):
                graph.addField(field, field, type='GAUGE', draw='AREASTACK')
            self.appendGraph('asterisk_peers_sip', graph)

        if self.graphEnabled('asterisk_peers_iax2'):
            graph = MuninGraph('Asterisk - VoIP Peers - IAX2', 'Asterisk',
                info = 'Asterisk - Information on IAX2 VoIP Peers.',
                args = '--base 1000 --lower-limit 0')
            for field in ('online', 'unmonitored', 'unreachable', 'lagged', 'unknown'):
                graph.addField(field, field, type='GAUGE', draw='AREASTACK')
            self.appendGraph('asterisk_peers_iax2', graph)

        if self.graphEnabled('asterisk_voip_codecs'):
            graph = MuninGraph('Asterisk - VoIP Codecs for Active Channels', 'Asterisk',
                info = 'Asterisk - Codecs for Active VoIP Channels (SIP/IAX2)',
                args = '--base 1000 --lower-limit 0')
            for field in ('alaw', 'ulaw', 'gsm', 'g729', 'other'):
                graph.addField(field, field, type='GAUGE', draw='AREASTACK')
            self.appendGraph('asterisk_voip_codecs', graph)

        if self.graphEnabled('asterisk_conferences'):
            graph = MuninGraph('Asterisk - Conferences', 'Asterisk',
                info = 'Asterisk - Information on Meetme Conferences',
                args = '--base 1000 --lower-limit 0')
            graph.addField('rooms', 'rooms', type='GAUGE', draw='LINE2', 
                info='Active conference rooms.')
            graph.addField('users', 'users', type='GAUGE', draw='LINE2', 
                info='Total number of users in conferences.')
            self.appendGraph('asterisk_conferences', graph)

        if self.graphEnabled('asterisk_voicemail'):
            graph = MuninGraph('Asterisk - Voicemail', 'Asterisk',
                info = 'Asterisk - Information on Voicemail Accounts',
                args = '--base 1000 --lower-limit 0')
            graph.addField('accounts', 'accounts', type='GAUGE', draw='LINE2',
                info='Number of voicemail accounts.')
            graph.addField('msg_avg', 'msg_avg', type='GAUGE', draw='LINE2',
                info='Average number of messages per voicemail account.')
            graph.addField('msg_max', 'msg_max', type='GAUGE', draw='LINE2',
                info='Maximum number of messages in one voicemail account.')
            graph.addField('msg_total', 'msg_total', type='GAUGE', draw='LINE2',
                info='Total number of messages in all voicemail accounts.')
            self.appendGraph('asterisk_voicemail', graph)

        if self.graphEnabled('asterisk_trunks') and len(self._trunkList) > 0:
            graph = MuninGraph('Asterisk - Trunks', 'Asterisk',
                info = 'Asterisk - Active calls on trunks.',
                args = '--base 1000 --lower-limit 0')
            for trunk in self._trunkList:
                graph.addField(trunk[0], trunk[0], type='GAUGE', draw='AREASTACK')
            self.appendGraph('asterisk_trunks', graph)


    def retrieveVals(self):
        """Retrive values for graphs."""
        ami = AsteriskInfo(self._amihost, self._amiport, self._amiuser, self._amipass)

        if self.graphEnabled('asterisk_calls') or self.graphEnabled('asterisk_channels'):
            stats = ami.getChannelStats()
            if  self.graphEnabled('asterisk_calls')  and stats:
                self.setGraphVal('asterisk_calls', 'active_calls', stats.get('active_calls'))
                self.setGraphVal('asterisk_calls', 'calls_per_min', stats.get('calls_processed'))
            if  self.graphEnabled('asterisk_channels')  and stats:
                for field in ('sip', 'iax2', 'dahdi', 'misdn', 'local', 'mix'):
                    self.setGraphVal('asterisk_channels', field, stats.get(field))

        if self.graphEnabled('asterisk_peers_sip'):
            stats = ami.getPeerStats('sip')
            if stats:
                for field in ('online', 'unmonitored', 'unreachable', 'lagged', 'unknown'):
                    self.setGraphVal('asterisk_peers_sip', field, stats.get(field))
        
        if self.graphEnabled('asterisk_peers_iax2'):
            stats = ami.getPeerStats('iax2')
            if stats:
                for field in ('online', 'unmonitored', 'unreachable', 'lagged', 'unknown'):
                    self.setGraphVal('asterisk_peers_iax2', field, stats.get(field))
        
        if self.graphEnabled('asterisk_voip_codecs'):
            sipstats = ami.getVoIPchanStats('sip')
            iax2stats = ami.getVoIPchanStats('iax2')
            if stats:
                for field in ('alaw', 'ulaw', 'gsm', 'g729', 'other'):
                    self.setGraphVal('asterisk_voip_codecs', field,
                        sipstats.get(field) + iax2stats.get(field))
        
        if self.graphEnabled('asterisk_conferences'):
            stats = ami.getConferenceStats()
            if stats:
                self.setGraphVal('asterisk_conferences', 'rooms', stats.get('active_conferences'))
                self.setGraphVal('asterisk_conferences', 'users', stats.get('conference_users'))

        if self.graphEnabled('asterisk_voicemail'):
            stats = ami.getVoicemailStats()
            if stats:
                self.setGraphVal('asterisk_voicemail', 'accounts', stats.get('accounts'))
                self.setGraphVal('asterisk_voicemail', 'msg_avg', stats.get('avg_messages'))
                self.setGraphVal('asterisk_voicemail', 'msg_max', stats.get('max_messages'))
                self.setGraphVal('asterisk_voicemail', 'msg_total', stats.get('total_messages'))

        if self.graphEnabled('asterisk_trunks') and len(self._trunkList) > 0:
            stats = ami.getTrunkStats(self._trunkList)
            for trunk in self._trunkList:
                self.setGraphVal('asterisk_trunks', trunk[0], stats.get(trunk[0]))


if __name__ == "__main__":
    sys.exit(muninMain(MuninAsteriskPlugin))
