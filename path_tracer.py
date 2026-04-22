# -*- coding: utf-8 -*-
from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

mac_to_port = {}
packet_paths = {}

def _handle_PacketIn(event):
    packet = event.parsed

    if not packet.parsed:
        return

    dpid = event.dpid
    in_port = event.port

    src = packet.src
    dst = packet.dst

    if dpid not in mac_to_port:
        mac_to_port[dpid] = {}

    mac_to_port[dpid][src] = in_port

    flow_id = (str(src), str(dst))

    if flow_id not in packet_paths:
        packet_paths[flow_id] = []

    if dpid not in packet_paths[flow_id]:
        packet_paths[flow_id].append(dpid)

    if dst in mac_to_port[dpid]:
        out_port = mac_to_port[dpid][dst]

        msg = of.ofp_flow_mod()
        msg.match.dl_dst = dst
        msg.actions.append(of.ofp_action_output(port=out_port))
        event.connection.send(msg)

        msg2 = of.ofp_packet_out()
        msg2.data = event.ofp
        msg2.actions.append(of.ofp_action_output(port=out_port))
        event.connection.send(msg2)

        path = packet_paths[flow_id]

        if len(path) >= 3:
            path_str = " -> ".join(["s%s" % d for d in path])

            try:
                src_id = int(str(src).split(":")[-1], 16)
                dst_id = int(str(dst).split(":")[-1], 16)

                log.info("FINAL PATH h%s -> h%s: h%s -> %s -> h%s",
                         src_id, dst_id,
                         src_id, path_str, dst_id)
            except:
                log.info("FINAL PATH: %s -> %s",
                         str(src),
                         path_str + " -> " + str(dst))
    else:
        msg = of.ofp_packet_out()
        msg.data = event.ofp
        msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        event.connection.send(msg)

def launch():
    log.info("Path Tracer Running...")
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
