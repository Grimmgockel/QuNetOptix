from qns.network.route import RouteImpl
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

from typing import List, Tuple, Type, Optional


class VLEnabledRouteAlgorithm(RouteImpl):
    # TODO determine how vlinks should be treated 
    # - EITHER: every node knows its closest vlink (start at lvl2 graph and work down, internet adressing paper)
    # - OR: simple dijkstra on lvl1 graph
    def __init__(self, name: str = "route") -> None:
        pass

    def build(self, nodes: List[QNode], channels: List[QuantumChannel | ClassicChannel]):
        pass

    def query(self, src: QNode, dest: QNode) -> List[Tuple[float | QNode | List[QNode]]]:
        pass

'''
Node application for entanglement distribution over physical and virtual links
'''
class VLEnabledDistributionApp(VLApp):
    def __init__(self):
        super().__init__()

        # members
        self.classic_msg_type: str = 'standard'
        self.entanglement_type: Type[QuantumModel] = WernerStateEntanglement # TODO custom entanglement model for no ambiguity
        self.app_name: str = 'vlink enabled routing'

    def distribute_qubit_adjacent(self, transmit_id: str):
        transmit = self.trans_registry.get(transmit_id)
        if transmit is None:
            raise Exception('does this occur?')
            #return

        epr = self.memory.get(transmit.second_epr_name)
        if epr is None:
            raise Exception('does this occur?')
            # return

        try:
            [(_, next_hop, _)] = self.net.query_route(self.own, transmit.src)
        except IndexError:
            raise Exception(f'{self}: Route error.')

        # TODO send over virtual link or qchannel


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


















