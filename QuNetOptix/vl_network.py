from qns.network import QuantumNetwork
from qns.network.topology import Topology
from qns.network.network import ClassicTopology
from qns.network.requests import Request
from vlaware_qnode import VLAwareQNode
from vl_routing import VLEnabledRouteAlgorithm
from metadata import MetaData
from vl_net_graph import VLNetGraph
from typing import Dict, List, Optional
import networkx as nx
import matplotlib.pyplot as plt
from dataclasses import dataclass
    
'''
Quantum network containing special request types called superlinks, that are considered for routing as entanglement links
'''
class VLNetwork(QuantumNetwork):
    def __init__(self, topo: Topology, metadata: MetaData):
        # init metadata
        self.metadata: MetaData = metadata
        self.metadata.distribution_requests = set()
        self.metadata.vlink_requests = set()
        self.metadata.distro_results = {}

        # members
        self.name = 'vl network'
        self.requests: List[Request] = []
        self.nodes, self.qchannels = topo.build()
        self.cchannels = topo.add_cchannels(classic_topo=ClassicTopology.All, nl=self.nodes, ll=self.qchannels)
        for n in self.nodes:
            n.add_network(self)

        # TODO SLS
        # TODO at this point the network graph is built, based on the graph requests for virtual links need to be produced
        # TODO one superlink per node, look at random_requests in QuantumNetwork
        self.vlinks: List[Request] = []
        self.add_vlink(src=self.get_node('n2'), dest=self.get_node('n9'), attr={'send_rate': 1})

        self.physical_graph = VLNetGraph(self.nodes, self.qchannels)
        self.vlink_graph = VLNetGraph(self.nodes, self.qchannels, vlinks=self.vlinks, lvl=1)

        # set routing algorithm
        self.route = VLEnabledRouteAlgorithm(self.physical_graph, self.vlink_graph)


    def add_vlink(self, src: VLAwareQNode, dest: VLAwareQNode, attr: Dict = {}):
        vlink = Request(src=src, dest=dest, attr=attr)
        self.vlinks.append(vlink)
        src.add_vlink(vlink)
        dest.add_vlink(vlink)

