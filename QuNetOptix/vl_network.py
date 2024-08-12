from qns.network import QuantumNetwork
from qns.network.topology import Topology
from qns.network.network import ClassicTopology
from qns.network.requests import Request
from vlaware_qnode import VLAwareQNode
from vl_routing import VLEnabledRouteAlgorithm
from metadata import SimData
from vl_animation import EntanglementLogEntry
from typing import Dict, List, Optional, Tuple
import networkx as nx
import matplotlib.pyplot as plt
from dataclasses import dataclass
import queue

class VLNetGraph():
    '''
    For routing and animation
    '''
    def __init__(self, nodes: List[VLAwareQNode], qchannels: List[VLAwareQNode], lvl: int = 0, vlinks: List[Request] = None):
        self.nodes = nodes
        self.qchannels = qchannels
        self.vlinks = vlinks
        self.lvl = lvl
        self.graph = nx.Graph()

        self.graph.add_nodes_from(self.nodes) # add nodes
        for qchannel in self.qchannels: # add edges 
            self.graph.add_edge(qchannel.node_list[0], qchannel.node_list[1], type='physical')
        if self.lvl == 1:
            for vlink in self.vlinks: # additional virtual edges in lvl1 graph
                self.graph.add_edge(vlink.src, vlink.dest, type='entanglement')


    def shortest_path(self, source, target) -> List[Tuple[Tuple[VLAwareQNode, VLAwareQNode], str]]:
        shortest_path = nx.shortest_path(self.graph, source=source, target=target)
        path_edges = [(shortest_path[i], shortest_path[i+1]) for i in range(len(shortest_path)-1)] # get additional information over edge type
        edge_types = [self.graph.get_edge_data(u, v)['type'] for u, v in path_edges]
        shortest_path = list(zip(path_edges, edge_types))
        return shortest_path


    def shortest_path_length(self, source, target) -> int:
        shortest_path_length = nx.shortest_path_length(self.graph, source=source, target=target)
        return shortest_path_length
    
class VLNetwork(QuantumNetwork):
    '''
    Quantum network containing special request types called superlinks, that are considered for routing as entanglement links
    '''
    def __init__(self, topo: Topology, metadata: SimData, continuous_distro: bool, schedule_n_vlinks: Optional[int], custom_vlinks: List[Tuple[str]], vlink_send_rate: float):
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

        self.vlinks: List[Request] = []

        for vlink in custom_vlinks or []:
            node_index_src = int(vlink[0][1:])
            node_index_dst = int(vlink[1][1:])
            if abs(node_index_src - node_index_dst) > 1: # exclude vlinks that have no intermediary node
                self.add_vlink(src=self.get_node(vlink[0]), dest=self.get_node(vlink[1]), attr={'send_rate': self.vlink_send_rate})

        if not self.vlinks:
            # TODO SLS
            # TODO at this point the network graph is built, based on the graph requests for virtual links need to be produced
            # TODO one superlink per node, look at random_requests in QuantumNetwork
            pass

        # set routing algorithm
        self.physical_graph = VLNetGraph(self.nodes, self.qchannels)
        self.vlink_graph = VLNetGraph(self.nodes, self.qchannels, vlinks=self.vlinks, lvl=1)
        self.route = VLEnabledRouteAlgorithm(self.physical_graph, self.vlink_graph)

    def add_vlink(self, src: VLAwareQNode, dest: VLAwareQNode, attr: Dict = {}):
        vlink = Request(src=src, dest=dest, attr=attr)
        self.vlinks.append(vlink)
        src.add_vlink(vlink)
        dest.add_vlink(vlink)

