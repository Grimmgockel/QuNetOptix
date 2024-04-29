from qns.network.requests import Request
from vlaware_qnode import VLAwareQNode
from typing import List, Tuple
import networkx as nx
import matplotlib.pyplot as plt

class VLNetGraph():
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


    def plot(self):
        # TODO different colored edges for different levels
        # TODO lvl2 graph
        nx.draw(self.graph, with_labels=True, node_color='skyblue', node_size=800, font_size=12, font_weight='bold', width=2)
        plt.title(f'lvl {self.lvl} graph')
        plt.show()
