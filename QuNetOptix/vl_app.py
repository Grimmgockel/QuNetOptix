from qns.network.network import QuantumNetwork
from qns.entity.qchannel import QuantumChannel
from qns.network.protocol.entanglement_distribution import Transmit
from qns.entity.memory import QuantumMemory
from qns.network.requests import Request
from qns.entity.node.app import Application
from qns.models.core import QuantumModel
from qns.entity.qchannel.qchannel import RecvQubitPacket
from qns.entity.cchannel.cchannel import ClassicChannel, RecvClassicPacket, ClassicPacket
from qns.entity.node import QNode
from qns.simulator.simulator import Simulator
from qns.simulator.event import func_to_event, Event
from qns.simulator.ts import Time
import qns.utils.log as log

from vlaware_qnode import VLAwareQNode, Transmit, EprAccount
from vl_routing import RoutingResult
from vl_entanglement import StandardEntangledPair

from typing import Optional, Dict, Callable, Type, Any, Tuple
from abc import ABC, abstractmethod
import uuid
from simple_colors import *

'''
Abstract class for node protocol in virtual link network
'''
class VLApp(ABC, Application):
    def __init__(self):
        super().__init__()

        # members
        self.control: Dict[str, Callable[..., Any]] = {
            "swap": self._swap,
            "next": self._next,
            "success": self._success,
            "revoke": self._revoke,
            "vlink": self._vlink,
        }
        self.entanglement_type: Type[QuantumModel] = None
        self.app_name: str = None
        self.own: VLAwareQNode = None 
        self.memory: QuantumMemory = None 
        self.net: QuantumNetwork = None 
        self.waiting_for_vlink: bool = False # always false for maintenance app

        # ep info can be vlink or standard ep
        self.src: Optional[VLAwareQNode] = None
        self.dst: Optional[VLAwareQNode] = None

        # communication
        self.add_handler(self.RecvQubitHandler, [RecvQubitPacket])
        self.add_handler(self.RecvClassicPacketHandler, [RecvClassicPacket])

        # meta data
        self.success_eprs = []
        self.success_count = 0
        self.send_count = 0

    def RecvQubitHandler(self, node: VLAwareQNode, event: RecvQubitPacket):
        if not isinstance(event.qubit, self.entanglement_type): 
            return
        qchannel: QuantumChannel = event.qchannel 
        src_node: VLAwareQNode = qchannel.node_list[0] if qchannel.node_list[1] == self.own else qchannel.node_list[1]
        # receive epr
        epr = event.qubit
        self.store_received_qubit(src_node, epr)

    def RecvClassicPacketHandler(self, node: VLAwareQNode, event: RecvClassicPacket):
        msg = event.packet.get()
        if msg['app_name'] != self.app_name:
            return

        self.receive_control(node, event)

    def install(self, node: QNode, simulator: Simulator):
        super().install(node, simulator)

        self.own: VLAwareQNode = self._node
        self.memory: QuantumMemory = self.own.memories[0]
        self.net: QuantumNetwork = self.own.network

        try:
            if self.app_name == 'maint':
                request: Request = self.own.vlinks[0] 
                self.net.metadata.distribution_requests.add(request)
            elif self.app_name == 'distro':
                request: Request = self.own.requests[0]
                self.net.metadata.vlink_requests.add(request)
            self.src = request.src if self.own == request.dest else None
            self.dst = request.dest if self.own == request.src else None
        except IndexError:
            pass

        if self.dst is not None: # sender
            t = simulator.ts
            self.send_rate = request.attr['send_rate'] 
            event = func_to_event(t, self.start_ep_distribution, by=self)
            self._simulator.add_event(event)

    def start_ep_distribution(self):
        # insert the next send event
        t = self._simulator.tc + Time(sec=1 / self.send_rate)
        event = func_to_event(t, self.start_ep_distribution, by=self)
        self._simulator.add_event(event)
        if self.memory._usage >= (self.memory.capacity / 2) or self.waiting_for_vlink:
            return

        # generate base epr
        epr: self.entanglement_type = self.generate_qubit(self.own, self.dst, None)

        # save transmission
        transmit: Transmit = Transmit(
            id=epr.account.transmit_id,
            src=self.own,
            dst=self.dst,
            #alice=ep,
            charlie=epr.account,
            start_time_s=self._simulator.current_time.sec
        )
        self.own.trans_registry[epr.account.transmit_id] = transmit

        store_success = self.memory.write(epr)
        if not store_success:
            self.memory.read(epr)
            self.own.trans_registry[epr.transmit_id] = None

        self.log_trans(f'start new ep distribution: {transmit.src} -> {transmit.dst} \t[usage={self.memory.count}/{self.memory.capacity}]', transmit=transmit)
        self.send_count += 1
        self.distribute_qubit_adjacent(epr.account.transmit_id)

    def distribute_qubit_adjacent(self, transmit_id: str):
        transmit = self.own.trans_registry.get(transmit_id)
        if transmit is None:
            return
        epr = self.memory.get(transmit.charlie.name)
        if epr is None: 
            return

        routing_result: RoutingResult = self.net.query_route(self.own, transmit.dst)
        if not routing_result:
            raise Exception(f"{self}: Route error.")


        next_hop: VLAwareQNode = routing_result.next_hop_physical

        # put into queue and exit if its vlink distro
        if routing_result.vlink and self.app_name == 'distro':
            next_hop: VLAwareQNode = routing_result.next_hop_virtual
            self.own.waiting_for_vlink_buf.put(transmit)
            if self.own.vlink_buf.empty() and next_hop.vlink_buf.empty():
                self.log_trans(f'waiting for vlink on {self.own.name} to {next_hop.name}', transmit=transmit)
                self.waiting_for_vlink = True
                return
            self._vlink(next_hop, None, None)
            return

        self.log_trans(f'physical transmission of qubit to {next_hop}', transmit=transmit)
        qchannel: QuantumChannel = self.own.get_qchannel(next_hop)
        if qchannel is None:
            raise Exception(f"{self}: No such quantum channel.")
        qchannel.send(epr, next_hop=next_hop)

    def store_received_qubit(self, src_node: VLAwareQNode, epr: QuantumModel):
        # get sender channel 
        cchannel: ClassicChannel = self.own.get_cchannel(src_node)
        if cchannel is None:
            raise Exception(f"{self}: No such classic channel")

        # generate second epr for swapping
        forward_epr = self.generate_qubit(src=epr.account.src, dst=epr.account.dst, transmit_id=epr.account.transmit_id) # TODO this may be the culprit for memory issues

        # storage
        storage_success_1 = self.memory.write(epr)
        storage_success_2 = self.memory.write(forward_epr)
        if not storage_success_1 or not storage_success_2:
            # revoke distribution
            self.memory.read(epr)
            self.memory.read(forward_epr)
            self.send_control(cchannel, src_node, epr.account.transmit_id, 'revoke', self.app_name)
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
        self.log_trans(f"received and stored qubit from {src_node.name}", transmit=updated_transmit)

        # if storage successful
        self.send_control(cchannel, src_node, epr.account.transmit_id, 'swap', self.app_name)

    def send_control(self, cchannel: ClassicChannel, dst: VLAwareQNode, transmit_id: str, control: str, app_name: str):
        classic_packet = ClassicPacket(
            msg={"cmd": control, "transmit_id": transmit_id, 'app_name': app_name}, 
            src=self.own, 
            dest=dst
        )
        transmit: Transmit = self.own.trans_registry.get(transmit_id)
        self.log_trans(f'sending \'{control}\' to {dst.name}', transmit=transmit)
        cchannel.send(classic_packet, next_hop=dst)


    def receive_control(self, node: VLAwareQNode, e: RecvClassicPacket):
        # get sender and channel
        src_cchannel: ClassicChannel = e.by
        src_node: VLAwareQNode = src_cchannel.node_list[0] if src_cchannel.node_list[1] == self.own else src_cchannel.node_list[1]
        if src_cchannel is None:
            raise Exception(f"{self}: No such classic channel")
        
        # receive message
        msg = e.packet.get()
        cmd = msg['cmd']
        transmit = self.own.trans_registry[msg["transmit_id"]] 
        self.log_trans(f'received \'{cmd}\' from {src_node.name}', transmit=transmit)

        # handle classical message
        self.control.get(cmd)(src_node, src_cchannel, transmit)

    def _swap(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        if self.own != transmit.src: # dont swap for first node


            # swap and manage new epr
            first: self.entanglement_type = self.memory.read(transmit.alice.name)
            second: self.entanglement_type = self.memory.read(transmit.charlie.name)
            new_epr: self.entanglement_type = self.entanglement_type(first.swapping(second))
            new_epr.name = uuid.uuid4().hex
            new_epr.account = EprAccount(
                transmit_id=transmit.id,
                name=new_epr.name,
                src=transmit.src,
                dst=transmit.dst,
                locA=first.account.locA,
                locB=second.account.locB,
            )

            # set new EP in Alice (request src)
            backward_node: VLAwareQNode = new_epr.account.locA
            backward_node_app: self.entanglement_type = backward_node.get_apps(type(self))[0]
            backward_node_app.set_epr(new_epr, 'charlie')

            # set new EP in Charlie (next in path)
            forward_node: VLAwareQNode = new_epr.account.locB
            forward_node_app: self.entanglement_type = forward_node.get_apps(type(self))[0]
            forward_node_app.set_epr(new_epr, 'alice')

            # clear for repeater node
            #self.own.trans_registry[transmit.id] = None

            self.log_trans(f'performed swap (({backward_node.name}, {self.own.name}) - ({self.own.name}, {forward_node.name})) -> ({backward_node.name}, {forward_node.name})', transmit=transmit)

        # send next
        self.send_control(src_cchannel, src_node, transmit.id, 'next', self.app_name)

    def _next(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        if self.own == transmit.dst: # successful distribution
            cchannel: Optional[ClassicChannel] = self.own.get_cchannel(transmit.src) 
            self.send_control(cchannel, transmit.src, transmit.id, 'success', self.app_name)
            return

        self.distribute_qubit_adjacent(transmit.id)

    def _revoke(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        # revoke transmission fully
        self.log_trans(f'cleaning memory', transmit=transmit)
        if transmit.alice is not None:
            self.memory.read(transmit.alice.name) 
        if transmit.charlie is not None:
            self.memory.read(transmit.charlie.name) 
        self.own.trans_registry[transmit.id] = None
        if self.own != transmit.src: # recurse back to source node
            cchannel = self.own.get_cchannel(transmit.src)
            self.send_control(cchannel, transmit.src, transmit.id, 'revoke', self.app_name)


    @abstractmethod
    def _success(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        pass

    @abstractmethod
    def _vlink(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        pass

    def generate_qubit(self, src: VLAwareQNode, dst: VLAwareQNode,
                       transmit_id: Optional[str] = None) -> Tuple[QuantumModel, EprAccount]:
        epr = self.entanglement_type(name=uuid.uuid4().hex)
        epr.account = EprAccount(
            transmit_id=transmit_id if transmit_id is not None else uuid.uuid4().hex,
            name=epr.name,
            src = src,
            dst = dst,
            locA=self.own,
            locB=self.own,
        )
        return epr

    def set_charlie(self, epr: QuantumModel, charlie: VLAwareQNode):
        transmit = self.own.trans_registry.get(epr.account.transmit_id)
        if transmit is None:
            return

        transmit.charlie = epr.account
        self.memory.read(transmit.charlie.name) # read out old alice
        self.memory.read(epr.account.name) # read out new epr name before writing
        self.memory.write(epr)

    def set_alice(self, epr: QuantumModel, alice: VLAwareQNode):
        transmit = self.own.trans_registry.get(epr.account.transmit_id)
        if transmit is None:
            return

        transmit.alice = epr.account
        self.memory.read(transmit.alice.name) # read out old alice
        self.memory.read(epr.account.name) # read out new epr name before writing
        self.memory.write(epr)

    def log_trans(self, str: str, transmit: Transmit = None):
        if transmit is None:
            log.debug(f'\t[{self.own.name}]\t{self.app_name}\tNone:\t{str}')
        else:
            log.debug(f'\t[{self.own.name}]\t{self.app_name}\t{transmit}:\t{str}')

