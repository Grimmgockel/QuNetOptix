from qns.network.network import QuantumNetwork
from qns.network.protocol.entanglement_distribution import Transmit
from qns.entity.memory import QuantumMemory
from qns.entity.node.app import Application
from qns.models.core import QuantumModel
from qns.entity.qchannel.qchannel import RecvQubitPacket
from qns.entity.cchannel.cchannel import ClassicChannel, RecvClassicPacket

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
        self.state: Dict[str, Transmit] = {}

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
        self.receive_qubit(node, event)

    def RecvClassicPacketHandler(self, node: VLAwareQNode, event: RecvClassicPacket):
        msg = event.packet.get()
        if not msg['type'] == self.classic_msg_type:
            return
        self.receive_classic(node, event)

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
        return self.state[id]

    '''
    Remote access
    '''
    def set_first_epr(self, epr: QuantumModel, transmit_id: str):
        transmit = self.state.get(transmit_id, None)
        if transmit is None or transmit.first_epr_name is None:
            return
        self.memory.read(transmit.first_epr_name)
        self.memory.write(epr)
        transmit.first_epr_name = epr.name

    '''
    Remote access
    '''
    def set_second_epr(self, epr: QuantumModel, transmit_id: str):
        transmit = self.state.get(transmit_id, None)
        if transmit is None or transmit.second_epr_name is None:
            return
        self.memory.read(transmit.second_epr_name)
        self.memory.write(epr)
        transmit.second_epr_name = epr.name

    def __repr__(self) -> str:
        return f'[{self.own.name}]\t<{self.app_name}>\t'

