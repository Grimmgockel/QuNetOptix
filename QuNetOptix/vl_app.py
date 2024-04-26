from qns.network.network import QuantumNetwork
from qns.network.protocol.entanglement_distribution import Transmit
from qns.entity.memory import QuantumMemory
from qns.network.requests import Request
from qns.entity.node.app import Application
from qns.models.core import QuantumModel
from qns.entity.qchannel.qchannel import RecvQubitPacket
from qns.entity.cchannel.cchannel import ClassicChannel, RecvClassicPacket
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
        self.classic_msg_type: str = None
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
        if not msg['type'] == self.classic_msg_type:
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

    @abstractmethod
    def distribute_qubit_adjacent(self, transmit_id: str):
        pass

    @abstractmethod
    def receive_qubit(node: VLAwareQNode, event: RecvQubitPacket):
        pass

    @abstractmethod
    def receive_classic(node: VLAwareQNode, event: RecvClassicPacket):
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

    def __repr__(self) -> str:
        return f'[{self.own.name}]\t<{self.app_name}>\t'

