from qns.network.network import QuantumNetwork
from qns.network.protocol import EntanglementDistributionApp
from qns.network.protocol.entanglement_distribution import Transmit
from qns.simulator.ts import Time
from qns.entity.node import QNode
from qns.network.topology import Topology 
from qns.models.epr.werner import WernerStateEntanglement
from qns.network.route import RouteImpl 
from qns.network.topology.topo import ClassicTopology 
from qns.entity.memory import QuantumMemory
from qns.simulator.simulator import Simulator
from qns.entity.entity import Entity
from qns.simulator.event import Event, func_to_event
from qns.network.requests import Request
from qns.entity.node.app import Application
from qns.models.core import QuantumModel
from qns.entity.qchannel.qchannel import QuantumChannel, RecvQubitPacket
from qns.entity.cchannel.cchannel import ClassicChannel, ClassicPacket, RecvClassicPacket
from qns.network.topology import Topology, TreeTopology
from typing import Optional, Dict, List, Tuple, Union, Callable
import qns.utils.log as log
from dataclasses import dataclass
import os
import uuid

@dataclass
class Transmit():
    id: str
    src: QNode
    dst: QNode
    first_epr_name: Optional[str] = None
    second_epr_name: Optional[str] = None
    start_time_s: Optional[float] = None
    vl: bool = False

class VLAwareQNode(QNode):
    def __init__(self, name: str = None, apps: List[Application] = None):
        super().__init__(name, apps)
        self.vlinks: List[Request] = []

    def add_vlink(self, vlink: Request):
        self.vlinks.append(vlink)

'''
Quantum network containing special request types called superlinks, that are considered for routing as entanglement links
'''
class VLNetwork(QuantumNetwork):
    def __init__(self, topo: Topology | None = None, route: RouteImpl | None = None, classic_topo: ClassicTopology | None = ClassicTopology.Empty, name: str | None = None):
        super().__init__(topo, route, classic_topo, name)
        self.vlinks: List[Request] = []
        self.vls()

    def vls(self):
        # TODO at this point the network graph is built, based on the graph requests for virtual links need to be produced
        # TODO one superlink per node, look at random_requests in QuantumNetwork
        self.add_vlink(src=self.get_node('n2'), dest=self.get_node('n9'))

    def add_vlink(self, src: VLAwareQNode, dest: VLAwareQNode, attr: Dict = {}):
        vlink = Request(src=src, dest=dest, attr=attr)
        self.vlinks.append(vlink)
        src.add_vlink(vlink)
        dest.add_vlink(vlink)

'''
Node application for maintaining selected virtual links 
'''
class VLMaintenanceApp(Application):
    def __init__(self):
        super().__init__()

        # members
        self.own: QNode = None 
        self.memory: QuantumMemory = None 
        self.net: QuantumNetwork = None 
        self.vlink_src: Optional[QNode] = None
        self.vlink_dst: Optional[QNode] = None
        self.state: Dict[str, Transmit] = {}

        # communication
        self.add_handler(lambda n, e: self.receive_qubit(n, e), [RecvQubitPacket])
        self.add_handler(lambda n, e: self.receive_classic(n, e), [RecvClassicPacket])

    def install(self, node: QNode, simulator: Simulator):
        super().install(node, simulator)

        self.own: QNode = self._node
        self.memory: QuantumMemory = self.own.memories[0]
        self.net: QuantumNetwork = self.own.network

        print(f'reqs:{self.own.requests}\tvlinks:{self.own.vlinks}')







    def receive_qubit(self, n: QNode, e: Event):
        pass

    def receive_classic(self, n: QNode, e: Event):
        pass

