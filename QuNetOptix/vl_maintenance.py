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

from vlaware_qnode import VLAwareQNode, Transmit
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

    def send_qubit(self, epr, routing_result: RoutingResult, transmit_id: str):
        next_hop: VLAwareQNode = routing_result.next_hop_physical
        log.debug(f'{self}: physical transmission of qubit {epr} to {next_hop}')
        qchannel: QuantumChannel = self.own.get_qchannel(next_hop)
        if qchannel is None:
            raise Exception(f"{self}: No such quantum channel.")
        qchannel.send(epr, next_hop=next_hop)

    def receive_qubit(self, n: VLAwareQNode, e: RecvQubitPacket):
        # get sender channel and node 
        src_qchannel: QuantumChannel = e.qchannel
        src_node: VLAwareQNode = src_qchannel.node_list[0] if src_qchannel.node_list[1] == self.own else src_qchannel.node_list[1]
        cchannel: ClassicChannel = self.own.get_cchannel(src_node)
        if cchannel is None:
            raise Exception(f"{self}: No such classic channel")

        # receive epr
        epr = e.qubit
        log.debug(f'{self}: received qubit {epr} from {src_node.name}')

        # generate second epr for swapping
        next_epr = self.generate_qubit(src=epr.src, dst=epr.dst, transmit_id=epr.transmit_id)
        updated_transmit = Transmit(
            id=epr.transmit_id,
            src=epr.src,
            dst=epr.dst,
            first_epr_name=epr.name,
            second_epr_name=next_epr.name
        )
        self.own.trans_registry[epr.transmit_id] = updated_transmit

        # storage
        storage_success_1 = self.memory.write(epr)
        storage_success_2 = self.memory.write(next_epr)
        if not storage_success_1 or not storage_success_2:
            # revoke distribution
            self.memory.read(epr)
            self.memory.read(next_epr)
            self.send_control(cchannel, src_node, epr.transmit_id, 'revoke', self.app_name)
            return

        # if storage successful
        self.send_control(cchannel, src_node, epr.transmit_id, 'swap', self.app_name)


    def receive_classic(self, n: QNode, e: RecvClassicPacket):
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

    def _swap(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        # dont swap for first node
        if self.own != transmit.src:
            first: self.entanglement_type = self.memory.read(transmit.first_epr_name)
            second: self.entanglement_type = self.memory.read(transmit.second_epr_name)
            new_epr: self.entanglement_type = first.swapping(second)
            new_epr.name=uuid.uuid4().hex

            # set new EP in Alice (request src)
            alice: VLAwareQNode = transmit.src
            alice_app: VLMaintenanceApp = alice.get_apps(VLMaintenanceApp)[0]
            alice_app.set_second_epr(new_epr, transmit_id=transmit.id)

            # set new EP in Charlie (next in path)
            charlie = src_node
            charlie_app: VLMaintenanceApp = charlie.get_apps(VLMaintenanceApp)[0]
            charlie_app.set_first_epr(new_epr, transmit_id=transmit.id)

            log.debug(f'{self}: performed swap (({alice.name}, {self.own.name}) - ({self.own.name}, {charlie.name})) -> ({alice.name}, {charlie.name})')

        # send next
        self.send_control(src_cchannel, src_node, transmit.id, 'next', self.app_name)

    def _next(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        if self.own == transmit.dst: # successful distribution
            # cleanup on receiver's side
            #result_epr = self.memory.read(transmit.first_epr_name)
            #self.memory.read(transmit.second_epr_name)
            #self.own.trans_registry[transmit.id] = None

            # TODO this could be a test case
            #src_app = transmit.src.get_apps(VLMaintenanceApp)[0]
            #src_epr = src_app.get_second_epr(transmit.id)
            #assert(result_epr == src_epr)

            # send 'success' control to source node
            cchannel: Optional[ClassicChannel] = self.own.get_cchannel(transmit.src) 
            self.send_control(cchannel, transmit.src, transmit.id, 'success', self.app_name)

            # TODO just testing restore  
            #self.state[transmit.id] = None
            #classic_packet = ClassicPacket(
                #msg={'cmd': 'restore', 'transmit_id': transmit.id},
                #src=self.own,
                #dest=transmit.src
            #)
            #log.debug(f'{self}: sending {classic_packet.msg} to {transmit.src.name}')
            #cchannel.send(classic_packet, next_hop=transmit.src)
            return

        self.distribute_qubit_adjacent(transmit.id)

    def _success(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        log.info(f'{self}: established vlink ({self.own.name}, {src_node.name}) {transmit}')

        self.own.vlink_buf.put(transmit.id)
        src_node.vlink_buf.put(transmit.id)

        cchannel: Optional[ClassicChannel] = self.own.get_cchannel(src_node) 
        self.send_control(cchannel, self.own, transmit.id, "vlink", "vlink enabled routing")
        self.send_control(cchannel, transmit.dst, transmit.id, "vlink", "vlink enabled routing")

        # TODO just for testing seperate app communication
        #classic_packet = ClassicPacket(
            #msg={'cmd': 'fun', 'transmit_id': 0, 'type': 'standard'},
            #src=self.own,
            #dest=src_node
        #)
        ##cchannel: Optional[ClassicChannel] = self.own.get_cchannel(src_node) 
        #log.debug(f'{self}: sending {classic_packet.msg} to {src_node.name}')
        #cchannel.send(classic_packet, next_hop=src_node)



        #result_epr = self.memory.read(transmit.second_epr_name)

        # update meta data
        #self.success_eprs.append(result_epr)
        #self.success_count += 1

        # cleanup on sender's side
        #self.state[transmit.id] = None


    def _revoke(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        # revoke transmission fully
        log.debug(f'{self}: cleaning memory')
        self.memory.read(transmit.first_epr_name)
        self.memory.read(transmit.second_epr_name)
        self.own.trans_registry[transmit.id] = None
        if self.own != transmit.src: # recurse back to source node
            cchannel = self.own.get_cchannel(transmit.src)
            self.send_control(cchannel, transmit.src, transmit.id, 'revoke', 'vlink maintenance')

    def _vlink(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        raise NotImplementedError()