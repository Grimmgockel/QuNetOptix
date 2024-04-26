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

from vlaware_qnode import VLAwareQNode
from transmit import Transmit
from vl_app import VLApp

from typing import Optional, Type
import uuid

'''
Node application for maintaining selected virtual links 
'''
class VLMaintenanceApp(VLApp):
    def __init__(self):
        super().__init__()

        # members
        self.classic_msg_type: str = 'vlink'
        self.entanglement_type: Type[QuantumModel] = BellStateEntanglement # TODO custom entanglement model for no ambiguity
        self.app_name: str = 'vlink maintenance'
        self.has_vlink: bool = False
        self.vlink_src: Optional[VLAwareQNode] = None
        self.vlink_dst: Optional[VLAwareQNode] = None


    def install(self, node: QNode, simulator: Simulator):
        super().install(node, simulator)

        self.own: VLAwareQNode = self._node
        self.memory: QuantumMemory = self.own.memories[0]
        self.net: QuantumNetwork = self.own.network

        if self.own.vlinks:
            vlink_request: Request = self.own.vlinks[0] 
            self.vlink_src = vlink_request.src if self.own == vlink_request.dest else None
            self.vlink_dst = vlink_request.dest if self.own == vlink_request.src else None

        if self.vlink_dst is not None: # node is sender
            t = simulator.ts
            event = func_to_event(t, self.start_vlink_distribution, by=self)
            self._simulator.add_event(event)

    '''
    Initiate EP distribution distributed algorithm as a sender node
    '''
    def start_vlink_distribution(self):
        epr = self.generate_qubit(self.own, self.vlink_dst, None)

        # save transmission
        transmit = Transmit(
            id=epr.transmit_id,
            src=self.own,
            dst=self.vlink_dst,
            second_epr_name=epr.name,
            start_time_s=self._simulator.current_time.sec,
            vl=True
        )
        self.state[epr.transmit_id] = transmit

        store_success = self.memory.write(epr)
        if not store_success:
            self.memory.read(epr)
            self.state[epr.transmit_id] = None

        log.debug(f'{self}: start new vlink distribution: {transmit}')
        self.send_count += 1
        self.distribute_qubit_adjacent(epr.transmit_id)

    def distribute_qubit_adjacent(self, transmit_id: str):
        transmit = self.state.get(transmit_id)
        #if transmit is None:
            #return
        epr = self.memory.get(transmit.second_epr_name)
        #if epr is None: 
            #return
        dst = transmit.dst
        route_result = self.net.query_route(self.own, dst)
        try:
            next_hop: VLAwareQNode = route_result[0][1]
        except IndexError:
            raise Exception(f"{self}: Route error.")

        qchannel: QuantumChannel = self.own.get_qchannel(next_hop)
        if qchannel is None:
            raise Exception(f"{self}: No such quantum channel.")

        # send entanglement
        log.debug(f'{self}: sending qubit {epr} to {next_hop.name}')
        qchannel.send(epr, next_hop)

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
            second_epr_name=next_epr.name,
            vl=True
        )
        self.state[epr.transmit_id] = updated_transmit

        # storage
        storage_success_1 = self.memory.write(epr)
        storage_success_2 = self.memory.write(next_epr)
        if not storage_success_1 or not storage_success_2:
            # revoke distribution
            self.memory.read(epr)
            self.memory.read(next_epr)
            classic_packet = ClassicPacket(
                msg={"cmd": "revoke", "transmid_id": epr.transmit_id, 'type': 'vlink'},
                src=self.own,
                dest=src_node
            ),
            log.debug(f'{self}: storage failed; sending {classic_packet.msg} to {src_node.name}; destroyed {epr} and {next_epr}')
            cchannel.send(classic_packet, next_hop=src_node)
            return

        # storage successful
        classic_packet = ClassicPacket(
            msg={"cmd": 'swap', "transmit_id": epr.transmit_id, 'type': 'vlink'}, 
            src=self.own, 
            dest=src_node
        )
        log.debug(f'{self}: sending {classic_packet.msg} to {src_node.name}')
        cchannel.send(classic_packet, next_hop=src_node)


    def receive_classic(self, n: QNode, e: RecvClassicPacket):
        # get sender and channel
        src_cchannel: ClassicChannel = e.by
        src_node: VLAwareQNode = src_cchannel.node_list[0] if src_cchannel.node_list[1] == self.own else src_cchannel.node_list[1]
        if src_cchannel is None:
            raise Exception(f"{self}: No such classic channel")
        
        # receive message
        msg = e.packet.get()
        log.debug(f'{self}: received {msg} from {src_node.name}')
        transmit = self.state[msg["transmit_id"]]

        # handle classical message
        self.control.get(msg["cmd"])(src_node, src_cchannel, transmit)

    def _swap(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        # dont swap for first node
        if self.own != transmit.src:
            first: BellStateEntanglement = self.memory.read(transmit.first_epr_name)
            second: BellStateEntanglement = self.memory.read(transmit.second_epr_name)
            new_epr: BellStateEntanglement = first.swapping(second)
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
        classic_packet = ClassicPacket(
            msg={"cmd": "next", "transmit_id": transmit.id, 'type': 'vlink'}, 
            src=self.own, 
            dest=src_node,
        )
        log.debug(f'{self}: sending {classic_packet.msg} to {src_node.name}')
        src_cchannel.send(classic_packet, next_hop=src_node)

    def _next(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        if self.own == transmit.dst: # successful distribution
            # cleanup on receiver's side
            result_epr = self.memory.read(transmit.first_epr_name)
            self.memory.read(transmit.second_epr_name)
            self.state[transmit.id] = None

            # TODO this must be a test
            #src_app = transmit.src.get_apps(VLMaintenanceApp)[0]
            #src_epr = src_app.get_second_epr(transmit.id)
            #assert(result_epr == src_epr)

            # send 'success' control to source node
            classic_packet = ClassicPacket(
                msg={'cmd': 'success', 'transmit_id': transmit.id, 'type': 'vlink'},
                src=self.own,
                dest=transmit.src
            )
            cchannel: Optional[ClassicChannel] = self.own.get_cchannel(transmit.src) # TODO implemented for fully meshed classical network
            log.debug(f'{self}: sending {classic_packet.msg} to {transmit.src.name}')
            cchannel.send(classic_packet, next_hop=transmit.src)

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
        log.info(f'{self}: established vlink ({self.own.name}, {src_node.name})')

        # TODO just for testing seperate app communication
        classic_packet = ClassicPacket(
            msg={'cmd': 'fun', 'transmit_id': 0, 'type': 'standard'},
            src=self.own,
            dest=src_node
        )
        cchannel: Optional[ClassicChannel] = self.own.get_cchannel(src_node) 
        log.debug(f'{self}: sending {classic_packet.msg} to {src_node.name}')
        cchannel.send(classic_packet, next_hop=src_node)



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
        self.state[transmit.id] = None
        if self.own != None: # recurse back to source node
            classic_packet = ClassicPacket(
                msg={'cmd': 'revoke', "transmit_id": transmit.id, 'type': 'vlink'},
                src=self.own,
                dest=transmit.src
            )
            cchannel = self.own.get_cchannel(transmit.src)
            log.debug(f'{self}: sending {classic_packet.msg} to {transmit.src.name}')
            cchannel.send(classic_packet, next_hop=transmit.src)

    def _restore(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        self.memory.read(self.state[transmit.id].second_epr_name)
        self.state[transmit.id] = None

        self.start_vlink_distribution()