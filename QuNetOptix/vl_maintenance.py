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
        self.app_name: str = 'vlink maintenance'

    def send_qubit(self, epr, routing_result: RoutingResult, transmit: Transmit):
        next_hop: VLAwareQNode = routing_result.next_hop_physical
        log.debug(f'{self}: physical transmission of qubit {epr} to {next_hop}')
        qchannel: QuantumChannel = self.own.get_qchannel(next_hop)
        if qchannel is None:
            raise Exception(f"{self}: No such quantum channel.")
        qchannel.send(epr, next_hop=next_hop)

    def receive_qubit(self, event: RecvQubitPacket):
        # get sender channel and node 
        src_qchannel: QuantumChannel = event.qchannel
        src_node: VLAwareQNode = src_qchannel.node_list[0] if src_qchannel.node_list[1] == self.own else src_qchannel.node_list[1]
        cchannel: ClassicChannel = self.own.get_cchannel(src_node)
        if cchannel is None:
            raise Exception(f"{self}: No such classic channel")

        # receive epr
        epr: self.entanglement_type = event.qubit
        log.debug(f'{self}: received qubit {epr} from {src_node.name}\t transmit: {epr.account.transmit_id}')

        # generate second epr for swapping
        forward_epr = self.generate_qubit(src=epr.account.src, dst=epr.account.dst, transmit_id=epr.account.transmit_id)

        # storage
        storage_success_1 = self.memory.write(epr)
        storage_success_2 = self.memory.write(forward_epr)
        if not storage_success_1 or not storage_success_2:
            # revoke distribution
            self.memory.read(epr)
            self.memory.read(forward_epr)
            self.send_control(cchannel, src_node, epr.transmit_id, 'revoke', self.app_name)
            return

        # bookkeeping
        updated_transmit: Transmit = Transmit(
            id=epr.account.transmit_id,
            src=epr.account.src,
            dst=epr.account.dst,
            alice=epr.account,
            charlie=forward_epr.account,
        )
        updated_transmit.alice.locB = self.own
        self.own.trans_registry[epr.account.transmit_id] = updated_transmit

        # if storage successful
        self.send_control(cchannel, src_node, epr.account.transmit_id, 'swap', self.app_name)


    def receive_control(self, n: QNode, e: RecvClassicPacket):
        # get sender and channel
        src_cchannel: ClassicChannel = e.by
        src_node: VLAwareQNode = src_cchannel.node_list[0] if src_cchannel.node_list[1] == self.own else src_cchannel.node_list[1]
        if src_cchannel is None:
            raise Exception(f"{self}: No such classic channel")
        
        # receive message
        msg = e.packet.get()
        log.debug(f'{self}: received {msg} from {src_node.name}')
        transmit = self.own.trans_registry[msg["transmit_id"]]

        # handle classical message
        self.control.get(msg["cmd"])(src_node, src_cchannel, transmit)

    def _success(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        log.info(f'{self}: established vlink ({self.own.name}, {src_node.name}) id={transmit.id}')

        self.own.vlink_buf.put(transmit.id)
        src_node.vlink_buf.put(transmit.id)

        cchannel: Optional[ClassicChannel] = self.own.get_cchannel(src_node) 
        self.send_control(cchannel, self.own, transmit.id, "vlink", "vlink enabled routing")
        self.send_control(cchannel, transmit.dst, transmit.id, "vlink", "vlink enabled routing")

    def _vlink(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        # TODO clear vlink on this side
        print(transmit) # once trans_registry is global, this should be easy
        #s1 = self.memory.read(vlink_transmit.second_epr_name)
