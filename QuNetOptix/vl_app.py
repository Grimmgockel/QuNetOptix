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
from metadata import MetaData, DistroResult

from typing import Optional, Dict, Callable, Type, Any, Tuple
from abc import ABC, abstractmethod
import queue
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
        self.vlink_cnt: int = 0

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

        requests = self.own.requests if self.app_name == 'distro' else self.own.vlinks
        for request in requests:
            if self.own == request.src: # i am a sender
                # save into session registry
                session_id = uuid.uuid4().hex 
                self.own.session_registry[session_id] = {'src': request.src, 'dst': request.dest}
                request.dest.session_registry[session_id] = {'src': request.src, 'dst': request.dest} 

                # start first ep distro
                self.send_rate = request.attr['send_rate'] 
                event = func_to_event(simulator.ts, self.start_ep_distribution, by=self, session_id=session_id)
                self._simulator.add_event(event)

    def schedule_next_ep_distribution(self, session_id: str):
        t = self._simulator.tc + Time(sec=1 / self.send_rate)
        event = func_to_event(t, self.start_ep_distribution, by=self, session_id=session_id)
        self._simulator.add_event(event)

    def start_ep_distribution(self, session_id: str = None):
        if session_id is None:
            raise ValueError('Session id required for new distribution')

        if self.app_name == 'maint':
            if self.net.n_vlinks is not None: # only distribute n_vlinks virtual links (for testing purposes)
                if self.vlink_cnt >= self.net.n_vlinks:
                    return
                self.vlink_cnt += 1
            self.schedule_next_ep_distribution(session_id)

        elif self.app_name == 'distro':
            if self.net.continuous_distro: # one distribution per session
                if self.waiting_for_vlink:
                    return # don't send new when there is an active distribution on that session
                self.schedule_next_ep_distribution(session_id)
        else:
            raise Exception("Unknown app name")

        # generate base epr
        session_src: VLAwareQNode = self.own.session_registry[session_id]['src']
        session_dst: VLAwareQNode = self.own.session_registry[session_id]['dst']
        epr: self.entanglement_type = self.generate_qubit(session_src, session_dst, session_id, transmit_id=None)

        # save transmission
        transmit: Transmit = Transmit(
            id=epr.account.transmit_id,
            session=session_id,
            src=session_src,
            dst=session_dst,
            #alice=ep,
            charlie=epr.account,
            start_time_s=self._simulator.current_time.sec
        )
        self.own.trans_registry[epr.account.transmit_id] = transmit
        self.log_trans(f'start new ep distribution: {transmit.src} -> {transmit.dst} \t[{epr}]', transmit=transmit)

        store_success = self.memory.write(epr)
        if not store_success:
            self.memory.read(epr)
            self.own.trans_registry[epr.account.transmit_id] = None
            self.log_trans(f'failed starting new distribution {transmit.src} -> {transmit.dst} \t[{epr}]', transmit=transmit)
            return
        self.log_trans(f"stored qubit {epr}", transmit=transmit)

        if self.app_name == 'distro':
            self.net.metadata.send_count += 1
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
            self.own.waiting_for_vlink_buf.put_nowait(transmit)
            if self.own.vlink_buf.empty() and next_hop.vlink_buf.empty():
                self.log_trans(f'waiting for vlink on {self.own.name} to {next_hop.name}\t[{epr}]', transmit=transmit)
                self.waiting_for_vlink = True
                return
            self._vlink(next_hop, None, None)
            return

        self.log_trans(f'physical transmission of qubit to {next_hop}\t[{epr}]', transmit=transmit)
        qchannel: QuantumChannel = self.own.get_qchannel(next_hop)
        if qchannel is None:
            raise Exception(f"{self}: No such quantum channel.")
        qchannel.send(epr, next_hop=next_hop)

    def store_received_qubit(self, src_node: VLAwareQNode, epr: QuantumModel):
        # get sender channel 
        cchannel: ClassicChannel = self.own.get_cchannel(src_node)
        if cchannel is None:
            raise Exception(f"{self}: No such classic channel")

        if self.own == epr.account.dst:
            # bookkeeping
            updated_transmit: Transmit = Transmit(
                id=epr.account.transmit_id,
                session=epr.account.session_id,
                src=epr.account.src,
                dst=epr.account.dst,
                alice=epr.account,
                #charlie=forward_epr.account,
            )
            updated_transmit.alice.locB = self.own
            self.own.trans_registry[epr.account.transmit_id] = updated_transmit
            self.log_trans(f"received qubit from {src_node.name}\t[{epr}]", transmit=updated_transmit)

            storage_success_1 = self.memory.write(epr)
            if not storage_success_1:
                # revoke distribution
                self.memory.read(epr)
                self.send_control(cchannel, src_node, updated_transmit, 'revoke', self.app_name)
                self.own.trans_registry[updated_transmit.id] = None # clear
                return

            self.log_trans(f"stored qubit {epr.name}", transmit=updated_transmit)

            # if storage successful
            self.send_control(cchannel, src_node, updated_transmit, 'swap', self.app_name)
            return


        # generate second epr for swapping
        forward_epr = self.generate_qubit(src=epr.account.src, dst=epr.account.dst, session_id=epr.account.session_id, transmit_id=epr.account.transmit_id) # TODO this may be the culprit for memory issues

        # bookkeeping
        updated_transmit: Transmit = Transmit(
            id=epr.account.transmit_id,
            session=epr.account.session_id,
            src=epr.account.src,
            dst=epr.account.dst,
            alice=epr.account,
            charlie=forward_epr.account,
        )
        updated_transmit.alice.locB = self.own
        self.own.trans_registry[epr.account.transmit_id] = updated_transmit
        self.log_trans(f"received qubit from {src_node.name}\t[{epr}]", transmit=updated_transmit)

        # storage 
        storage_success_1 = self.memory.write(epr)
        storage_success_2 = self.memory.write(forward_epr)
        if not storage_success_1 or not storage_success_2:
            # revoke distribution
            self.memory.read(epr)
            self.memory.read(forward_epr)
            self.send_control(cchannel, src_node, updated_transmit, 'revoke', self.app_name)
            self.own.trans_registry[updated_transmit.id] = None # clear
            return

        self.log_trans(f"stored qubit {epr.name} and {forward_epr.name}", transmit=updated_transmit)

        # if storage successful
        self.send_control(cchannel, src_node, updated_transmit, 'swap', self.app_name)

    def send_control(self, cchannel: ClassicChannel, dst: VLAwareQNode, transmit: Transmit, control: str, app_name: str):
        classic_packet = ClassicPacket(
            msg={"cmd": control, "transmit_id": transmit.id, 'app_name': app_name}, 
            src=self.own, 
            dest=dst
        )
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

            # set new EP in Charlie (next in path)
            forward_node: VLAwareQNode = new_epr.account.locB
            forward_node_app: self.entanglement_type = forward_node.get_apps(type(self))[0]

            # set alicea and charlie after swap
            backward_node_app.set_charlie(new_epr, first, second)
            forward_node_app.set_alice(new_epr, first, second)

            # clear for repeater node
            self.own.trans_registry[transmit.id] = None

            self.log_trans(f'performed swap (({backward_node.name}, {self.own.name}) - ({self.own.name}, {forward_node.name})) -> ({backward_node.name}, {forward_node.name})', transmit=transmit)
            self.log_trans(f'consumed: {first} and {second} | new: {new_epr}', transmit=transmit)

        # send next
        self.send_control(src_cchannel, src_node, transmit, 'next', self.app_name)

    def _next(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        if self.own == transmit.dst: # successful distribution
            cchannel: Optional[ClassicChannel] = self.own.get_cchannel(transmit.src) 

            # meta data
            if self.app_name == 'distro':
                result_epr: QuantumModel = self.memory.read(transmit.alice.name)
                self.net.metadata.distro_results[transmit.id] = DistroResult(dst_result=(transmit, result_epr))

            self.send_control(cchannel, transmit.src, transmit, 'success', self.app_name)
            return

        self.distribute_qubit_adjacent(transmit.id)

    def _revoke(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        # revoke transmission fully
        if transmit.alice is not None:
            epr = self.memory.read(transmit.alice.name)
            if epr is not None:
                self.log_trans(f'revoked qubit {epr}', transmit=transmit)
        if transmit.charlie is not None:
            epr = self.memory.read(transmit.charlie.name)
            if epr is not None:
                self.log_trans(f'revoked qubit {epr}', transmit=transmit)
        self.own.trans_registry[transmit.id] = None
        if self.own != transmit.src: # recurse back to source node
            cchannel = self.own.get_cchannel(transmit.src)
            self.send_control(cchannel, transmit.src, transmit, 'revoke', self.app_name)


    @abstractmethod
    def _success(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        pass

    @abstractmethod
    def _vlink(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        pass

    def generate_qubit(self, src: VLAwareQNode, dst: VLAwareQNode, session_id: str,
                       transmit_id: Optional[str] = None) -> QuantumModel:
        epr = self.entanglement_type(name=uuid.uuid4().hex)
        epr.account = EprAccount(
            transmit_id=transmit_id if transmit_id is not None else uuid.uuid4().hex,
            session_id=session_id,
            name=epr.name,
            src = src,
            dst = dst,
            locA=self.own,
            locB=self.own,
        )
        return epr

    def set_charlie(self, epr: QuantumModel, first_old: QuantumModel, second_old: QuantumModel, used_vlink: Transmit = None):
        transmit = self.own.trans_registry.get(epr.account.transmit_id)
        if transmit is None:
            return

        transmit.charlie = epr.account

        # cleanup
        self.memory.read(first_old.name) # read out old alice
        self.memory.read(second_old.name) # read out old alice
        self.memory.read(epr.account.name) # read out new epr name before writing

        # safe new epr
        self.memory.write(epr)

    def set_alice(self, epr: QuantumModel, first_old: QuantumModel, second_old: QuantumModel, used_vlink: Transmit = None):
        transmit = self.own.trans_registry.get(epr.account.transmit_id)
        if transmit is None:
            return

        transmit.alice = epr.account

        # cleanup
        self.memory.read(first_old.name) # read out old alice
        self.memory.read(second_old.name) # read out old alice
        self.memory.read(epr.account.name) # read out new epr name before writing

        # safe new epr
        self.memory.write(epr)

    def log_trans(self, str: str, transmit: Transmit = None):
        if transmit is None:
            log.debug(f'\t[{self.own.name}]\t{self.memory._usage}/{self.memory.capacity}\t{self.app_name}\tNone:\t{str}')
        else:
            log.debug(f'\t[{self.own.name}]\t{self.memory._usage}/{self.memory.capacity}\t{self.app_name}\t{transmit}:\t{str}')

