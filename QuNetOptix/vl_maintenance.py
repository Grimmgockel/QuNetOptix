from qns.models.core import QuantumModel
from qns.models.epr import BellStateEntanglement
from qns.entity.node import QNode
from qns.simulator.simulator import Simulator
from qns.entity.memory import QuantumMemory
from qns.network.network import QuantumNetwork
from qns.network.requests import Request
from qns.entity.cchannel import ClassicChannel, RecvClassicPacket, ClassicPacket
from qns.entity.qchannel import QuantumChannel, RecvQubitPacket
from qns.simulator.event import func_to_event
import qns.utils.log as log

from vlaware_qnode import VLAwareQNode, Transmit, EprAccount
from vl_app import VLApp
from vl_routing import RoutingResult
from vl_entanglement import VLEntangledPair
from vl_net_graph import EntanglementLogEntry

from typing import Optional, Type
import uuid

import simple_colors
import random

'''
Node application for maintaining selected virtual links 
'''
class VLMaintenanceApp(VLApp):
    def __init__(self):
        super().__init__()

        # members
        self.entanglement_type: Type[QuantumModel] = VLEntangledPair # TODO custom entanglement model for no ambiguity
        self.app_name: str = 'maint'

    def _success(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        self.log_trans(simple_colors.magenta(f'established vlink ({self.own.name}, {src_node.name})'), transmit=transmit)
        self.net.metadata.vlink_count += 1
        # for plotting
        self.net.entanglement_log.put(EntanglementLogEntry(
            type=EntanglementLogEntry.ent_type.VLINK,
            status=EntanglementLogEntry.status_type.END2END,
            instruction=EntanglementLogEntry.instruction_type.CREATE,
            nodeA=self.own,
            nodeB=src_node,
        ))

        self.own.vlink_buf.put_nowait(transmit)
        src_node.vlink_buf.put_nowait(transmit)

        cchannel: Optional[ClassicChannel] = self.own.get_cchannel(src_node) 

        src_waiting = not self.own.waiting_for_vlink_buf.empty()
        dst_waiting = not transmit.dst.waiting_for_vlink_buf.empty()

        # decide where to notify about new vlink
        tgt: Optional[VLAwareQNode] = None
        if src_waiting and not dst_waiting:
            tgt = self.own
        elif not src_waiting and dst_waiting:
            tgt = transmit.dst
        elif src_waiting and dst_waiting:
            # flip a coin
            coinflip_result =  random.choice([True, False])
            tgt = self.own if coinflip_result else transmit.dst

        if tgt is not None:
            self.send_control(cchannel, tgt, transmit, "vlink", "distro") 

    def _vlink(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        # TODO clear vlink on this side
        print(transmit) # once trans_registry is global, this should be easy
        #s1 = self.memory.read(vlink_transmit.second_epr_name)
