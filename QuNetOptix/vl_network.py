from qns.network import QuantumNetwork
from qns.network.topology import Topology
from qns.network.network import ClassicTopology
from qns.network.route import RouteImpl
from qns.network.requests import Request
from vlaware_qnode import VLAwareQNode
from vl_routing import VLEnabledRouteAlgorithm
from typing import Dict, List


'''
Quantum network containing special request types called superlinks, that are considered for routing as entanglement links
'''
class VLNetwork(QuantumNetwork):
    def __init__(self, topo: Topology | None = None):
        super().__init__(topo, VLEnabledRouteAlgorithm(), ClassicTopology.All, 'vl network')

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
