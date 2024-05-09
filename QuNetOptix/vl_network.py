from qns.network import QuantumNetwork
from qns.network.topology import Topology
from qns.network.network import ClassicTopology
from qns.network.requests import Request
from vlaware_qnode import VLAwareQNode
from vl_routing import VLEnabledRouteAlgorithm
from metadata import SimData
from vl_net_graph import VLNetGraph, EntanglementLogEntry
from typing import Dict, List, Optional
import networkx as nx
import matplotlib.pyplot as plt
from dataclasses import dataclass
import queue
    
'''
Quantum network containing special request types called superlinks, that are considered for routing as entanglement links
'''
class VLNetwork(QuantumNetwork):
    def __init__(self, topo: Topology, metadata: SimData, continuous_distro: bool, schedule_n_vlinks: Optional[int], vlink_send_rate: float):
        # init metadata
        self.metadata: SimData = metadata
        self.metadata.distribution_requests = set()
        self.metadata.vlink_requests = set()
        self.metadata.distro_results = {}
        self.metadata.entanglement_log = [] # for plotting
        self.metadata.entanglement_log_timestamps = {} # for plotting

        # members
        self.name = 'vl network'
        self.vlink_send_rate = vlink_send_rate
        self.continuous_distro: bool = continuous_distro
        self.schedule_n_vlinks: Optional[int] = schedule_n_vlinks
        self.requests: List[Request] = []
        self.nodes, self.qchannels = topo.build()
        self.cchannels = topo.add_cchannels(classic_topo=ClassicTopology.All, nl=self.nodes, ll=self.qchannels)
        for n in self.nodes:
            n.add_network(self)

        # TODO SLS
        # TODO at this point the network graph is built, based on the graph requests for virtual links need to be produced
        # TODO one superlink per node, look at random_requests in QuantumNetwork
        self.vlinks: List[Request] = []
        self.add_vlink(src=self.get_node('n2'), dest=self.get_node(f'n{len(self.nodes)-1}'), attr={'send_rate': self.vlink_send_rate})

        self.physical_graph = VLNetGraph(self.nodes, self.qchannels)
        self.vlink_graph = VLNetGraph(self.nodes, self.qchannels, vlinks=self.vlinks, lvl=1)

        # set routing algorithm
        self.route = VLEnabledRouteAlgorithm(self.physical_graph, self.vlink_graph)


    def add_vlink(self, src: VLAwareQNode, dest: VLAwareQNode, attr: Dict = {}):
        vlink = Request(src=src, dest=dest, attr=attr)
        self.vlinks.append(vlink)
        src.add_vlink(vlink)
        dest.add_vlink(vlink)

