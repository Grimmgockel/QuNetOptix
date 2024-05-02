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

from typing import Optional, Type
import uuid



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
        self.log_trans(f'established vlink ({self.own.name}, {src_node.name})', transmit=transmit)

        self.own.vlink_buf.put(transmit)
        src_node.vlink_buf.put(transmit)

        cchannel: Optional[ClassicChannel] = self.own.get_cchannel(src_node) 
        self.send_control(cchannel, self.own, transmit.id, "vlink", "distro")
        self.send_control(cchannel, transmit.dst, transmit.id, "vlink", "distro")

    def _vlink(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        # TODO clear vlink on this side
        print(transmit) # once trans_registry is global, this should be easy
        #s1 = self.memory.read(vlink_transmit.second_epr_name)
