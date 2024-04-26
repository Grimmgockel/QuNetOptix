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
from qns.simulator.event import func_to_event
import qns.utils.log as log

from transmit import Transmit
from vlaware_qnode import VLAwareQNode

from typing import Optional, Dict, Callable, Type, Any
from abc import ABC, abstractmethod
import uuid

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
            "restore": self._restore
        }
        self.entanglement_type: Type[QuantumModel] = None
        self.app_name: str = None
        self.own: VLAwareQNode = None 
        self.memory: QuantumMemory = None 
        self.net: QuantumNetwork = None 
        self.trans_registry: Dict[str, Transmit] = {}

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

    def install(self, node: QNode, simulator: Simulator):
        super().install(node, simulator)

        self.own: VLAwareQNode = self._node
        self.memory: QuantumMemory = self.own.memories[0]
        self.net: QuantumNetwork = self.own.network

        try:
            request: Request = self.own.vlinks[0] if self.app_name == 'vlink maintenance' else self.own.requests[0]
            self.src = request.src if self.own == request.dest else None
            self.dst = request.dest if self.own == request.src else None
        except IndexError:
            pass

        if self.dst is not None: # sender
            t = simulator.ts
            event = func_to_event(t, self.start_ep_distribution, by=self)
            self._simulator.add_event(event)

    def RecvQubitHandler(self, node: VLAwareQNode, event: RecvQubitPacket):
        if not isinstance(event.qubit, self.entanglement_type): 
            return
        self.receive_qubit(node, event)

    def RecvClassicPacketHandler(self, node: VLAwareQNode, event: RecvClassicPacket):
        msg = event.packet.get()
        if msg['app_name'] != self.app_name:
            return
        self.receive_classic(node, event)


    '''
    Initiate EP distribution distributed algorithm as a sender node
    '''
    def start_ep_distribution(self):
        epr = self.generate_qubit(self.own, self.dst, None)

        # save transmission
        transmit = Transmit(
            id=epr.transmit_id,
            src=self.own,
            dst=self.dst,
            second_epr_name=epr.name,
            start_time_s=self._simulator.current_time.sec
        )
        self.trans_registry[epr.transmit_id] = transmit

        store_success = self.memory.write(epr)
        if not store_success:
            self.memory.read(epr)
            self.trans_registry[epr.transmit_id] = None

        log.debug(f'{self}: start new ep distribution: {transmit}')
        self.send_count += 1
        self.distribute_qubit_adjacent(epr.transmit_id)

    def distribute_qubit_adjacent(self, transmit_id: str):
        transmit = self.trans_registry.get(transmit_id)
        if transmit is None:
            raise Exception("does this occur?")
            #return
        epr = self.memory.get(transmit.second_epr_name)
        if epr is None: 
            raise Exception("does this occur?")
            #return

        try:
            [(_, next_hop, _)] = self.net.query_route(self.own, transmit.dst)
        except IndexError:
            raise Exception(f"{self}: Route error.")

        qchannel: QuantumChannel = self.own.get_qchannel(next_hop)
        if qchannel is None:
            raise Exception(f"{self}: No such quantum channel.")

        # send entanglement
        self.send_qubit(qchannel, epr, next_hop)

    '''
    Send classical control message
    '''
    def send_control(self, cchannel: ClassicChannel, dst: VLAwareQNode, transmit_id: str, control: str):
        classic_packet = ClassicPacket(
            msg={"cmd": control, "transmit_id": transmit_id, 'app_name': self.app_name}, 
            src=self.own, 
            dest=dst
        )
        log.debug(f'{self}: sending {classic_packet.msg} to {dst.name}')
        cchannel.send(classic_packet, next_hop=dst)

    '''
    Generate qubit according to applications quantum model
    '''
    def generate_qubit(self, src: VLAwareQNode, dst: VLAwareQNode,
                       transmit_id: Optional[str] = None) -> QuantumModel:
        epr = self.entanglement_type(name=uuid.uuid4().hex)
        epr.src = src
        epr.dst = dst
        epr.transmit_id = transmit_id if transmit_id is not None else uuid.uuid4().hex
        return epr

    '''
    Remote access
    '''
    def query_transmit(self, id: int):
        return self.trans_registry[id]

    '''
    Remote access
    '''
    def set_first_epr(self, epr: QuantumModel, transmit_id: str):
        transmit = self.trans_registry.get(transmit_id, None)
        if transmit is None or transmit.first_epr_name is None:
            return
        self.memory.read(transmit.first_epr_name)
        self.memory.write(epr)
        transmit.first_epr_name = epr.name

    '''
    Remote access
    '''
    def set_second_epr(self, epr: QuantumModel, transmit_id: str):
        transmit = self.trans_registry.get(transmit_id, None)
        if transmit is None or transmit.second_epr_name is None:
            return
        self.memory.read(transmit.second_epr_name)
        self.memory.write(epr)
        transmit.second_epr_name = epr.name

    @abstractmethod
    def send_qubit(self, qchannel: QuantumChannel, epr, next_hop):
        pass

    @abstractmethod
    def receive_qubit(self, node: VLAwareQNode, event: RecvQubitPacket):
        pass

    @abstractmethod
    def receive_classic(self, node: VLAwareQNode, event: RecvClassicPacket):
        pass

    @abstractmethod
    def _swap(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        pass

    @abstractmethod
    def _next(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        pass

    @abstractmethod
    def _success(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        pass

    @abstractmethod
    def _revoke(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        pass

    @abstractmethod
    def _restore(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        pass

    def __repr__(self) -> str:
        return f'[{self.own.name}]\t<{self.app_name}>\t'

