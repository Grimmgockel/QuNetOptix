from qns.network.network import QuantumNetwork
from qns.models.epr import BellStateEntanglement
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
from typing import Optional, Dict, List, Tuple, Union, Callable, Type, Any
from abc import ABC, abstractmethod
import qns.utils.log as log
from dataclasses import dataclass
import os
import uuid

@dataclass
class Transmit:
    id: str
    src: QNode
    dst: QNode
    first_epr_name: Optional[str] = None
    second_epr_name: Optional[str] = None
    start_time_s: Optional[float] = None
    vl: bool = False

'''
QNode with knowledge over vlink requests
'''
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

        # TODO SLS
        # TODO at this point the network graph is built, based on the graph requests for virtual links need to be produced
        # TODO one superlink per node, look at random_requests in QuantumNetwork
        self.vlinks: List[Request] = []
        self.add_vlink(src=self.get_node('n2'), dest=self.get_node('n9'))

    def add_vlink(self, src: VLAwareQNode, dest: VLAwareQNode, attr: Dict = {}):
        vlink = Request(src=src, dest=dest, attr=attr)
        self.vlinks.append(vlink)
        src.add_vlink(vlink)
        dest.add_vlink(vlink)

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
        self.vlink_src: Optional[QNode] = None
        self.vlink_dst: Optional[QNode] = None


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

    def receive_qubit(self, n: VLAwareQNode, e: Event):
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


    def receive_classic(self, n: QNode, e: Event):
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


class VLEnabledRouteAlgorithm(RouteImpl):
    # TODO determine how vlinks should be treated 
    # - EITHER: every node knows its closest vlink (start at lvl2 graph and work down, internet adressing paper)
    # - OR: simple dijkstra on lvl1 graph
    pass

'''
Node application for entanglement distribution over physical and virtual links
'''
class VLEnabledDistributionApp(VLApp):
    def install(self, node: QNode, simulator: Simulator):
        super().install(node, simulator)

        # members
        self.classic_msg_type: str = 'standard'
        self.entanglement_type: Type[QuantumModel] = WernerStateEntanglement # TODO custom entanglement model for no ambiguity
        self.app_name: str = "vlink enabled routing"

        self.own = self._node

    def receive_qubit(self, node: VLAwareQNode, event: RecvClassicPacket):
        pass

    def receive_classic(self, node: VLAwareQNode, event: RecvClassicPacket):
        log.debug(f'{self}: received something !!!')

    def _swap(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        return

    def _next(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        return

    def _success(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        return

    def _revoke(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        return

    def _restore(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        return



















