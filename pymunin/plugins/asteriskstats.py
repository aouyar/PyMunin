#!/usr/bin/env python
"""asteriskstats - Munin Plugin to monitor Asterisk through Manager Interface.

Requirements
  - Access to Asterisk Manager Interface

Wild Card Plugin - No

Multigraph Plugin - Graph Structure
   - asterisk_calls
   - asterisk_channels
   - asterisk_peers_sip
   - asterisk_peers_iax2
   - asterisk_voip_codecs
   - asterisk_conferences
   - asterisk_voicemail
   - asterisk_trunks
   - asterisk_queue_len
   - asterisk_queue_avg_hold
   - asterisk_queue_avg_talk
   - asterisk_queue_calls
   - asterisk_queue_abandon_pcent
   - asterisk_fax_attempts


Environment Variables

  amihost:        IP of Asterisk Server. (Default: 127.0.0.1)
  amiport:        Asterisk Manager Interface Port. (Default: 5038)
  amiuser:        Asterisk Manager Interface User.
  amipass:        Asterisk Manager Interface Password.
  list_channels:  List of channels that will be shown in channel stats.
                  (Default: dahdi,zap,sip',iax2,local)
  list_codecs:    List of codecs that will be shown in VoIP channel stats.
                  Any codec that is not in the list will be counted as 'other'.
                  (Default: alaw,ulaw,gsm,g729)
  list_trunks:    Comma separated search expressions of the following formats:
                  - "Trunk Name"="Regular Expr"
                  - "Trunk Name"="Regular Expr with Named Group 'num'"="MIN"-"MAX"
                  Check Python Regular Expressions docs for help on writing 
                  regular expressions:http://docs.python.org/library/re.html
  include_queues: Comma separated list of queues to include in  graphs.
                  (All queues included by default.)
  exclude_queues: Comma separated list of queues to exclude from graphs.
  include_graphs: Comma separated list of enabled graphs.
                  (All graphs enabled by default.)
  exclude_graphs: Comma separated list of disabled graphs.

  Note: Channel, codec and trunk expressions are case insensitive.

  Example:
      [asteriskstats]
        env.amihost 192.168.1.10
        env.amiport 5038
        env.amiuser manager
        env.amipass secret
        env.list_codecs alaw,ulaw,gsm,ilbc,g729
        env.list_trunks PSTN=Zap\/(?P<num>\d+)=1-3,VoIP=SIP\/(net2phone|skype)

"""
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
__version__ = "0.9.1"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


class MuninAsteriskPlugin(MuninPlugin):
    """Multigraph Munin Plugin for monitoring Asterisk.

    """
    plugin_name = 'asteriskstats'
    isMultigraph = True

    def __init__(self, argv=(), env={}, debug=False):
        """Populate Munin Plugin with MuninGraph instances.
        
        @param argv:  List of command line arguments.
        @param env:   Dictionary of environment variables.
        @param debug: Print debugging messages if True. (Default: False)
        
        """
        MuninPlugin.__init__(self, argv, env, debug)

        self.envRegisterFilter('queues', '^[\w\-]+$')
        self._amihost = self.envGet('amihost')
        self._amiport = self.envGet('amiport', None, int)
        self._amiuser = self.envGet('amiuser')
        self._amipass = self.envGet('amipass')
        
        self._ami = AsteriskInfo(self._amihost, self._amiport, 
                                 self._amiuser, self._amipass)
        
        self._codecList = (self.envGetList('codecs') 
                           or ['alaw', 'ulaw', 'gsm', 'g729'])
        
        self._chanList = []
        for chanstr in (self.envGetList('channels') 
                        or ['dahdi', 'zap', 'sip', 'iax2', 'local']):
            chan = chanstr.lower()
            if self._ami.hasChannelType(chan):
                if chan in ('zap', 'dahdi'):
                    if 'dahdi' not in self._chanList:
                        self._chanList.append('dahdi')
                else:
                    self._chanList.append(chan)
                
        self._trunkList = []
        for trunk_entry in self.envGetList('trunks', None):
            mobj = (re.match('(.*)=(.*)=(\d+)-(\d+)$',  trunk_entry, re.IGNORECASE) 
                    or re.match('(.*)=(.*)$',  trunk_entry,  re.IGNORECASE))
            if mobj:
                self._trunkList.append(mobj.groups())
                 
        if self.graphEnabled('asterisk_calls'):
            graph = MuninGraph('Asterisk - Call Stats', 'Asterisk',
                info='Asterisk - Information on Calls.', period='minute',
                args='--base 1000 --lower-limit 0')
            graph.addField('active_calls', 'active_calls', type='GAUGE',
                draw='LINE2',info='Active Calls')
            graph.addField('calls_per_min','calls_per_min', type='DERIVE', min=0,
                draw='LINE2', info='Calls per minute')
            self.appendGraph('asterisk_calls', graph)

        if self.graphEnabled('asterisk_channels'):
            graph = MuninGraph('Asterisk - Active Channels', 'Asterisk',
                info='Asterisk - Information on Active Channels.',
                args='--base 1000 --lower-limit 0')
            for field in self._chanList:
                graph.addField(field, field, type='GAUGE', draw='AREASTACK')
            if 'dahdi' in self._chanList:
                graph.addField('mix', 'mix', type='GAUGE', draw='LINE2')
            self.appendGraph('asterisk_channels', graph)

        if (self.graphEnabled('asterisk_peers_sip') 
            and self._ami.hasChannelType('sip')):
            graph = MuninGraph('Asterisk - VoIP Peers - SIP', 'Asterisk',
                info='Asterisk - Information on SIP VoIP Peers.',
                args='--base 1000 --lower-limit 0')
            for field in ('online', 'unmonitored', 'unreachable', 
                          'lagged', 'unknown'):
                graph.addField(field, field, type='GAUGE', draw='AREASTACK')
            self.appendGraph('asterisk_peers_sip', graph)

        if (self.graphEnabled('asterisk_peers_iax2') 
            and self._ami.hasChannelType('iax2')):
            graph = MuninGraph('Asterisk - VoIP Peers - IAX2', 'Asterisk',
                info='Asterisk - Information on IAX2 VoIP Peers.',
                args='--base 1000 --lower-limit 0')
            for field in ('online', 'unmonitored', 'unreachable', 
                          'lagged', 'unknown'):
                graph.addField(field, field, type='GAUGE', draw='AREASTACK')
            self.appendGraph('asterisk_peers_iax2', graph)

        if (self.graphEnabled('asterisk_voip_codecs') 
            and (self._ami.hasChannelType('sip') 
                 or self._ami.hasChannelType('iax2'))):
            graph = MuninGraph('Asterisk - VoIP Codecs for Active Channels', 
                'Asterisk',
                info='Asterisk - Codecs for Active VoIP Channels (SIP/IAX2)',
                args='--base 1000 --lower-limit 0')
            for field in self._codecList:
                graph.addField(field, field, type='GAUGE', draw='AREASTACK')
            graph.addField('other', 'other', type='GAUGE', draw='AREASTACK')
            self.appendGraph('asterisk_voip_codecs', graph)

        if (self.graphEnabled('asterisk_conferences') 
            and self._ami.hasConference()):
            graph = MuninGraph('Asterisk - Conferences', 'Asterisk',
                info='Asterisk - Information on Meetme Conferences',
                args='--base 1000 --lower-limit 0')
            graph.addField('rooms', 'rooms', type='GAUGE', draw='LINE2', 
                info='Active conference rooms.')
            graph.addField('users', 'users', type='GAUGE', draw='LINE2', 
                info='Total number of users in conferences.')
            self.appendGraph('asterisk_conferences', graph)

        if (self.graphEnabled('asterisk_voicemail')
            and self._ami.hasVoicemail()):
            graph = MuninGraph('Asterisk - Voicemail', 'Asterisk',
                info='Asterisk - Information on Voicemail Accounts',
                args='--base 1000 --lower-limit 0')
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
                info='Asterisk - Active calls on trunks.',
                args='--base 1000 --lower-limit 0',
                autoFixNames = True)
            for trunk in self._trunkList:
                graph.addField(trunk[0], trunk[0], type='GAUGE', draw='AREASTACK')
            self.appendGraph('asterisk_trunks', graph)
        
        self._queues = None
        self._queue_list = None
        if ((self.graphEnabled('asterisk_queue_len')
             or self.graphEnabled('asterisk_queue_avg_hold')
             or self.graphEnabled('asterisk_queue_avg_talk')
             or self.graphEnabled('asterisk_queue_calls')
             or self.graphEnabled('asterisk_queue_abandon_pcent'))
            and self._ami.hasQueue()):
            self._queues = self._ami.getQueueStats()
            self._queue_list = [queue for queue in self._queues.keys()
                                if self.envCheckFilter('queues', queue)]
            self._queue_list.sort()
            if self.graphEnabled('asterisk_queue_abandon_pcent'):
                self._queues_prev = self.restoreState()
                if self._queues_prev is None:
                    self._queues_prev = self._queues
                self.saveState(self._queues)
        
        if self._queues is not None and len(self._queue_list) > 0:
            if self.graphEnabled('asterisk_queue_len'):
                graph = MuninGraph('Asterisk - Queues - Calls in Queue', 'Asterisk',
                    info='Asterisk - Queues - Number of calls in queues.',
                    args='--base 1000 --lower-limit 0')
                for queue in self._queue_list:
                    graph.addField(queue, queue, type='GAUGE', draw='AREASTACK',
                                   info='Number of calls in queue %s.' % queue)
                self.appendGraph('asterisk_queue_len', graph)
            if self.graphEnabled('asterisk_queue_avg_hold'):
                graph = MuninGraph('Asterisk - Queues - Average Hold Time (sec)', 
                    'Asterisk',
                    info='Asterisk - Queues - Average Hold Time.',
                    args='--base 1000 --lower-limit 0')
                for queue in self._queue_list:
                    graph.addField(queue, queue, type='GAUGE', draw='LINE2',
                                   info='Average hold time for queue %s.' % queue)
                self.appendGraph('asterisk_queue_avg_hold', graph)
            if self.graphEnabled('asterisk_queue_avg_talk'):
                graph = MuninGraph('Asterisk - Queues - Average Talk Time (sec)', 
                    'Asterisk',
                    info='Asterisk - Queues - Average Talk Time.).',
                    args='--base 1000 --lower-limit 0')
                for queue in self._queue_list:
                    graph.addField(queue, queue, type='GAUGE', draw='LINE2',
                                   info='Average talk time for queue %s.' % queue)
                self.appendGraph('asterisk_queue_avg_talk', graph)
            if self.graphEnabled('asterisk_queue_calls'):
                graph = MuninGraph('Asterisk - Queues - Calls per Minute', 
                    'Asterisk', period='minute',
                    info='Asterisk - Queues - Abandoned/Completed Calls per minute.',
                    args='--base 1000 --lower-limit 0')
                graph.addField('abandon', 'abandon', type='DERIVE', draw='AREASTACK',
                               info='Abandoned calls per minute.')
                graph.addField('answer', 'answer', type='DERIVE', draw='AREASTACK',
                               info='Answered calls per minute.')
                self.appendGraph('asterisk_queue_calls', graph)
            if self.graphEnabled('asterisk_queue_abandon_pcent'):
                graph = MuninGraph('Asterisk - Queues - Abandoned Calls (%)', 
                    'Asterisk',
                    info='Asterisk - Queues - Abandoned calls vs, total calls.',
                    args='--base 1000 --lower-limit 0')
                for queue in self._queue_list:
                    graph.addField(queue, queue, type='GAUGE', draw='LINE2',
                                   info='Abandoned vs. total calls for queue %s.' 
                                        % queue)
                self.appendGraph('asterisk_queue_abandon_pcent', graph)
        
        if self._ami.hasFax():
            if self.graphEnabled('asterisk_fax_attempts'):
                graph = MuninGraph('Asterisk - Fax Stats', 
                    'Asterisk', period='minute',
                    info='Asterisk - Fax - Fax Recv / Send Attempts per minute.',
                    args='--base 1000 --lower-limit 0')
                graph.addField('send', 'send', type='DERIVE', draw='AREASTACK',
                               info='Fax send attempts per minute.')
                graph.addField('recv', 'recv', type='DERIVE', draw='AREASTACK',
                               info='Fax receive attempts per minute.')
                graph.addField('fail', 'fail', type='DERIVE', draw='LINE2',
                               info='Failed fax attempts per minute.')
                self.appendGraph('asterisk_fax_attempts', graph)

    def retrieveVals(self):
        """Retrieve values for graphs."""
        if self.hasGraph('asterisk_calls') or self.hasGraph('asterisk_channels'):
            stats = self._ami.getChannelStats(self._chanList)
            if  self.hasGraph('asterisk_calls')  and stats:
                self.setGraphVal('asterisk_calls', 'active_calls', 
                                 stats.get('active_calls'))
                self.setGraphVal('asterisk_calls', 'calls_per_min', 
                                 stats.get('calls_processed'))
            if  self.hasGraph('asterisk_channels')  and stats:
                for field in self._chanList:
                    self.setGraphVal('asterisk_channels', 
                                     field, stats.get(field))
                if 'dahdi' in self._chanList:
                    self.setGraphVal('asterisk_channels', 
                                     'mix', stats.get('mix'))

        if self.hasGraph('asterisk_peers_sip'):
            stats = self._ami.getPeerStats('sip')
            if stats:
                for field in ('online', 'unmonitored', 'unreachable', 
                              'lagged', 'unknown'):
                    self.setGraphVal('asterisk_peers_sip', 
                                     field, stats.get(field))
        
        if self.hasGraph('asterisk_peers_iax2'):
            stats = self._ami.getPeerStats('iax2')
            if stats:
                for field in ('online', 'unmonitored', 'unreachable', 
                              'lagged', 'unknown'):
                    self.setGraphVal('asterisk_peers_iax2', 
                                     field, stats.get(field))
        
        if self.hasGraph('asterisk_voip_codecs'):
            sipstats = self._ami.getVoIPchanStats('sip', self._codecList) or {}
            iax2stats = self._ami.getVoIPchanStats('iax2', self._codecList) or {}
            if stats:
                for field in self._codecList:
                    self.setGraphVal('asterisk_voip_codecs', field,
                                     sipstats.get(field,0) 
                                     + iax2stats.get(field, 0))
                self.setGraphVal('asterisk_voip_codecs', 'other',
                                 sipstats.get('other', 0) 
                                 + iax2stats.get('other', 0))
        
        if self.hasGraph('asterisk_conferences'):
            stats = self._ami.getConferenceStats()
            if stats:
                self.setGraphVal('asterisk_conferences', 'rooms', 
                                 stats.get('active_conferences'))
                self.setGraphVal('asterisk_conferences', 'users', 
                                 stats.get('conference_users'))

        if self.hasGraph('asterisk_voicemail'):
            stats = self._ami.getVoicemailStats()
            if stats:
                self.setGraphVal('asterisk_voicemail', 'accounts', 
                                 stats.get('accounts'))
                self.setGraphVal('asterisk_voicemail', 'msg_avg', 
                                 stats.get('avg_messages'))
                self.setGraphVal('asterisk_voicemail', 'msg_max', 
                                 stats.get('max_messages'))
                self.setGraphVal('asterisk_voicemail', 'msg_total', 
                                 stats.get('total_messages'))

        if self.hasGraph('asterisk_trunks') and len(self._trunkList) > 0:
            stats = self._ami.getTrunkStats(self._trunkList)
            for trunk in self._trunkList:
                self.setGraphVal('asterisk_trunks', trunk[0], 
                                 stats.get(trunk[0]))
                
        if self._queues is not None:
            total_answer = 0
            total_abandon = 0
            for queue in self._queue_list:
                stats = self._queues[queue]
                if self.hasGraph('asterisk_queue_len'):
                    self.setGraphVal('asterisk_queue_len', queue,
                                     stats.get('queue_len'))
                if self.hasGraph('asterisk_queue_avg_hold'):
                    self.setGraphVal('asterisk_queue_avg_hold', queue,
                                     stats.get('avg_holdtime'))
                if self.hasGraph('asterisk_queue_avg_talk'):
                    self.setGraphVal('asterisk_queue_avg_talk', queue,
                                     stats.get('avg_talktime'))
                if self.hasGraph('asterisk_queue_calls'):
                    total_abandon += stats.get('calls_abandoned')
                    total_answer += stats.get('calls_completed')
                if self.hasGraph('asterisk_queue_abandon_pcent'):
                    prev_stats = self._queues_prev.get(queue)
                    val = 0
                    if prev_stats is not None:
                        abandon = (stats.get('calls_abandoned', 0) -
                                   prev_stats.get('calls_abandoned', 0))
                        answer = (stats.get('calls_completed', 0) -
                                  prev_stats.get('calls_completed', 0))
                        if answer >= 0 and abandon >= 0:
                            total = abandon + answer
                            if total > 0:
                                val = 100.0 * float(abandon) / float(total)
                    self.setGraphVal('asterisk_queue_abandon_pcent', 
                                     queue, val)
            if self.hasGraph('asterisk_queue_calls'):
                    self.setGraphVal('asterisk_queue_calls', 'abandon', 
                                     total_abandon)
                    self.setGraphVal('asterisk_queue_calls', 'answer', 
                                     total_answer)
                    
            if self.hasGraph('asterisk_fax_attempts'):
                fax_stats = self._ami.getFaxStatsCounters()
                stats = fax_stats.get('general')
                if stats is not None:
                    self.setGraphVal('asterisk_fax_attempts', 'send', 
                                     stats.get('transmit attempts'))
                    self.setGraphVal('asterisk_fax_attempts', 'recv', 
                                     stats.get('receive attempts'))
                    self.setGraphVal('asterisk_fax_attempts', 'fail', 
                                     stats.get('failed faxes'))


def main():
    sys.exit(muninMain(MuninAsteriskPlugin))


if __name__ == "__main__":
    main()
