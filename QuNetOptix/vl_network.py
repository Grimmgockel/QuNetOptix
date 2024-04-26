from qns.network import QuantumNetwork
from qns.network.topology import Topology
from qns.network.network import ClassicTopology
from qns.network.route import RouteImpl, DijkstraRouteAlgorithm
from qns.network.requests import Request
from vlaware_qnode import VLAwareQNode
from vl_routing import VLEnabledRouteAlgorithm
from typing import Dict, List
import networkx as nx



'''
Quantum network containing special request types called superlinks, that are considered for routing as entanglement links
'''
class VLNetwork(QuantumNetwork):
    def __init__(self, topo: Topology):
        # members
        self.name = 'vl network'
        self.requests: List[Request] = []
        self.nodes, self.qchannels = topo.build()
        self.cchannels = topo.add_cchannels(classic_topo=ClassicTopology.All, nl=self.nodes, ll=self.qchannels)
        for n in self.nodes:
            n.add_network(self)

        # build network graph
        self.graph = nx.Graph()
        self.graph.add_nodes_from(self.nodes)
        for qchannel in self.qchannels:
            self.graph.add_edge(qchannel.node_list[0], qchannel.node_list[1])

        # set routing algorithm
        # TODO
        self.route = VLEnabledRouteAlgorithm(self.graph)

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
