from qns.entity.cchannel import ClassicChannel, RecvClassicPacket
from qns.entity.qchannel import QuantumChannel, RecvQubitPacket
from qns.models.core import QuantumModel
from qns.models.epr import WernerStateEntanglement, BellStateEntanglement
import qns.utils.log as log

from vlaware_qnode import VLAwareQNode, Transmit
from vl_app import VLApp
from vl_routing import RoutingResult
from vl_entanglement import StandardEntangledPair

from typing import Type, Optional
import uuid
import queue

'''
Node application for entanglement distribution over physical and virtual links
'''
class VLEnabledDistributionApp(VLApp):
    def __init__(self):
        super().__init__()

        # members
        self.entanglement_type: Type[QuantumModel] = StandardEntangledPair # TODO custom entanglement model for no ambiguity
        self.app_name: str = 'vlink enabled routing'

    def send_qubit(self, epr, routing_result: RoutingResult, transmit_id: str):
        next_hop: VLAwareQNode = routing_result.next_hop_virtual

        if routing_result.vlink:
            # TODO put qubit into queue and wait for 'vlink' event, (keywords: multiplexing, asynchronous)
            log.debug(f'{self}: waiting for teleportation of transmit {transmit_id} to {next_hop.name}')
            self.own.teleport_buf.put(transmit_id)
            return

        log.debug(f'{self}: physical transmission of qubit {epr} to {next_hop}')
        qchannel: QuantumChannel = self.own.get_qchannel(next_hop)
        if qchannel is None:
            raise Exception(f"{self}: No such quantum channel.")
        qchannel.send(epr, next_hop=next_hop)

    def receive_qubit(self, node: VLAwareQNode, e: RecvQubitPacket):
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

    def receive_classic(self, node: VLAwareQNode, e: RecvClassicPacket):
        # get sender and channel
        src_cchannel: ClassicChannel = e.by
        src_node: VLAwareQNode = src_cchannel.node_list[0] if src_cchannel.node_list[1] == self.own else src_cchannel.node_list[1]
        if src_cchannel is None:
            raise Exception(f"{self}: No such classic channel")
        
        # receive message
        msg = e.packet.get()
        log.debug(f'{self}: received {msg} from {src_node.name}')

        transmit = self.own.trans_registry[msg["transmit_id"]] # TODO this fails because apps have different registries

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
            alice_app: VLEnabledDistributionApp = alice.get_apps(VLEnabledDistributionApp)[0]
            alice_app.set_second_epr(new_epr, transmit_id=transmit.id)

            # set new EP in Charlie (next in path)
            charlie = src_node
            charlie_app: VLEnabledDistributionApp = charlie.get_apps(VLEnabledDistributionApp)[0]
            charlie_app.set_first_epr(new_epr, transmit_id=transmit.id)

            log.debug(f'{self}: performed swap (({alice.name}, {self.own.name}) - ({self.own.name}, {charlie.name})) -> ({alice.name}, {charlie.name})')

        # send next
        self.send_control(src_cchannel, src_node, transmit.id, 'next', self.app_name)

    def _next(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        if self.own == transmit.dst: # successful distribution
            # cleanup on receiver's side
            result_epr = self.memory.read(transmit.first_epr_name)
            self.memory.read(transmit.second_epr_name)
            self.own.trans_registry[transmit.id] = None

            # TODO this could be a test case
            #src_app = transmit.src.get_apps(VLMaintenanceApp)[0]
            #src_epr = src_app.get_second_epr(transmit.id)
            #assert(result_epr == src_epr)

            # send 'success' control to source node
            cchannel: Optional[ClassicChannel] = self.own.get_cchannel(transmit.src) # TODO implemented for fully meshed classical network
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
        print("success")
        return

    def _revoke(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        print("revoke")
        return

    def _vlink(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        # TODO take next transmission in queue and teleport over vlink, raise recvqubitevent to trigger receive_qubit
        vlink_transmit: Transmit = transmit
        next_teleport: Transmit = self.own.trans_registry[self.own.teleport_buf.get()]

        log.debug(f'{self}: vlink transmit first {vlink_transmit.first_epr_name}')
        log.debug(f'{self}: vlink transmit second {vlink_transmit.second_epr_name}')
        log.debug(f'{self}: next transmit first {next_teleport.first_epr_name}')
        log.debug(f'{self}: next transmit second {next_teleport.second_epr_name}')

        
        first: self.entanglement_type = self.memory.read(next_teleport.first_epr_name)
        second: self.entanglement_type = self.memory.read(vlink_transmit.second_epr_name)
        new_epr: self.entanglement_type = first.swapping(second)
        new_epr.name=uuid.uuid4().hex

        # set new EP in Alice (request src)
        print(next_teleport.src)
        alice: VLAwareQNode = next_teleport.src
        #alice_app: VLEnabledDistributionApp = alice.get_apps(VLEnabledDistributionApp)[0]
        #alice_app.set_second_epr(new_epr, transmit_id=transmit.id)

        # set new EP in Charlie (next in path)
        #charlie = src_node
        #charlie_app: VLEnabledDistributionApp = charlie.get_apps(VLEnabledDistributionApp)[0]
        #charlie_app.set_first_epr(new_epr, transmit_id=transmit.id)

        # TODO next_teleport.second_epr is not up to date here ?
        # TODO swap next_teleport.first with vlink.second ?
        # TODO clear vlink transmit 

        #self.own.trans_registry[vlink_transmit.id] = None

    def _restore(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        print("restore")
        return