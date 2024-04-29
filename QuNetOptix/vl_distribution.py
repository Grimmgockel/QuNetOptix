from qns.entity.cchannel import ClassicChannel, RecvClassicPacket
from qns.entity.qchannel import QuantumChannel
from qns.models.core import QuantumModel
from qns.models.epr import WernerStateEntanglement
import qns.utils.log as log

from vlaware_qnode import VLAwareQNode
from transmit import Transmit
from vl_app import VLApp
from vl_routing import RoutingResult

from typing import Type

'''
Node application for entanglement distribution over physical and virtual links
'''
class VLEnabledDistributionApp(VLApp):
    def __init__(self):
        super().__init__()

        # members
        self.entanglement_type: Type[QuantumModel] = WernerStateEntanglement # TODO custom entanglement model for no ambiguity
        self.app_name: str = 'vlink enabled routing'

    def send_qubit(self, epr, routing_result: RoutingResult):
        # TODO send over vlink 
        next_hop = routing_result.next_hop_virtual
        log.debug(f'{self}: send qubit {epr} to {next_hop.name}')

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