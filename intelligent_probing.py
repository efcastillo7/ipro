from operator import attrgetter
from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER, CONFIG_DISPATCHER, HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.controller.ofp_event import EventOFPErrorMsg
from ryu.lib import hub

from ryu.lib.packet import packet
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import dpid as dpid_lib

import json
import sys
sys.path.insert(0, '/home/efcastillo/ryu/ryu/app/ipro/mp')
import ConnectionBD_v2


class IntelligentProbing(simple_switch_13.SimpleSwitch13):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(IntelligentProbing, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(5)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        #Individual flow statistics request message
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        #Port statistics request message
        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

        #Aggregate flow statistics request message
        cookie = cookie_mask = 0
        match = parser.OFPMatch(in_port=1)
        req = parser.OFPAggregateStatsRequest(datapath, 0,
                                              ofproto.OFPTT_ALL,
                                              ofproto.OFPP_ANY,
                                              ofproto.OFPG_ANY,
                                              cookie, cookie_mask,
                                              match)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body
        flow_statistics = {}
        """
        self.logger.info('datapath         '
                         'in-port  eth-dst           '
                         'out-port packets  bytes')
        self.logger.info('---------------- '
                         '-------- ----------------- '
                         '-------- -------- --------')
        """                 
        for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match['in_port'],
                                             flow.match['eth_dst'])):
            """
            self.logger.info('%016x %8x %17s %8x %8d %8d',
                             ev.msg.datapath.id,
                             stat.match['in_port'], stat.match['eth_dst'],
                             stat.instructions[0].actions[0].port,
                             stat.packet_count, stat.byte_count)
            """
            flow_statistics['id_datapath'] = ev.msg.datapath.id
            flow_statistics['in_port']     = stat.match['in_port']
            flow_statistics['eth_dst']     = stat.match['eth_dst']
            flow_statistics['out_port']    = stat.instructions[0].actions[0].port
            flow_statistics['packets']     = stat.packet_count
            flow_statistics['bytes']       = stat.byte_count
            #ConnectionBD_v2.insertStatFlow(flow_statistics)
            #self.logger.info('%s', json.dumps(ev.msg.to_jsondict(), ensure_ascii=True,
             #                     indent=3, sort_keys=True))

        flows = []
        for stat in ev.msg.body:
            flows.append('cookie=%d packet_count=%d byte_count=%d '
                         'match=%s instructions=%s' %
                         (stat.cookie, stat.packet_count, stat.byte_count,
                          stat.match, stat.instructions))
        #self.logger.info('FlowStats: %s', flows)     

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        port_statistics = {}
        """
        self.logger.info('datapath         port     '
                         'rx-pkts  rx-bytes rx-error '
                         'tx-pkts  tx-bytes tx-error')
        self.logger.info('---------------- -------- '
                         '-------- -------- -------- '
                         '-------- -------- --------')
        """                 
        for stat in sorted(body, key=attrgetter('port_no')):
            """
            self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
                             ev.msg.datapath.id, stat.port_no,
                             stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                             stat.tx_packets, stat.tx_bytes, stat.tx_errors)
            """
            port_statistics['id_datapath'] = ev.msg.datapath.id
            port_statistics['port_number'] = stat.port_no
            port_statistics['rx_packets']  = stat.rx_packets
            port_statistics['rx_bytes']    = stat.rx_bytes
            port_statistics['rx_errors']   = stat.rx_errors
            port_statistics['tx_packets']  = stat.tx_packets
            port_statistics['tx_bytes']    = stat.tx_bytes
            port_statistics['tx_errors']   = stat.tx_errors

            #ConnectionBD_v2.insertStatPort(port_statistics)

    @set_ev_cls(ofp_event.EventOFPAggregateStatsReply, MAIN_DISPATCHER)
    def aggregate_stats_reply_handler(self, ev):

        body = ev.msg.body

        self.logger.debug('AggregateStats: packet_count=%d byte_count=%d' 
            'flow_count=%d',
            body.packet_count, body.byte_count,
            body.flow_count)        

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        #self.logger.info("[Ehsan] Received EventOFPPacketIn")
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("\tPACKET IN.... %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)


    @set_ev_cls(EventOFPErrorMsg,
                [HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def error_msg_handler(self, ev):
        msg = ev.msg
        self.logger.info('OFPErrorMsg received: type=0x%02x code=0x%02x '
                         'message=%s',
                        msg.type, msg.code, hex_array(msg.data))        
