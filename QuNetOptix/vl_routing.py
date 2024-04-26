from qns.network.route import RouteImpl, DijkstraRouteAlgorithm
from qns.entity.node import QNode
from qns.entity.cchannel import ClassicChannel, RecvClassicPacket
from qns.entity.qchannel import QuantumChannel
from qns.simulator.simulator import Simulator
from qns.models.core import QuantumModel
from qns.models.epr import WernerStateEntanglement
from qns.network.requests import Request
from qns.simulator.event import func_to_event
import qns.utils.log as log

from vlaware_qnode import VLAwareQNode
from transmit import Transmit
from vl_app import VLApp

from typing import Callable, List, Tuple, Type, Optional


class VLEnabledRouteAlgorithm(DijkstraRouteAlgorithm):
    # TODO determine how vlinks should be treated 
    # - EITHER: every node knows its closest vlink (start at lvl2 graph and work down, internet adressing paper)
    # - OR: simple dijkstra on lvl1 graph
    def __init__(self, name: str = "dijkstra", metric_func: Callable[[QuantumChannel | ClassicChannel], float] = None) -> None:
        super().__init__(name, metric_func)

'''
Node application for entanglement distribution over physical and virtual links
'''
class VLEnabledDistributionApp(VLApp):
    def __init__(self):
        super().__init__()

        # members
        self.entanglement_type: Type[QuantumModel] = WernerStateEntanglement # TODO custom entanglement model for no ambiguity
        self.app_name: str = 'vlink enabled routing'

    def send_qubit(self, qchannel: QuantumChannel, epr, next_hop):
        # TODO send over vlink 
        pass

    def receive_qubit(self, node: VLAwareQNode, event: RecvClassicPacket):
        pass

    def receive_classic(self, node: VLAwareQNode, event: RecvClassicPacket):
        pass

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


















