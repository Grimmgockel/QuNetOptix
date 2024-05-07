from qns.network.requests import Request
import re
from vlaware_qnode import VLAwareQNode
from typing import List, Tuple
import networkx as nx
import matplotlib.pyplot as plt
import queue
from dataclasses import dataclass
from matplotlib.animation import FuncAnimation
from enum import Enum
from typing import Optional

@dataclass
class EntanglementLogEntry:
    class ent_type(Enum):
        ENT = 0
        VLINK = 1
    type: Optional[ent_type] = None

    class instruction_type(Enum):
        CREATE = 0
        DELETE = 1
    instruction: Optional[instruction_type] = None

    class status_type(Enum):
        INTERMEDIATE = 0
        END2END = 1
    status: Optional[status_type] = None

    nodeA: Optional[VLAwareQNode] = None
    nodeB: Optional[VLAwareQNode] = None

    @property
    def color(self):
        color: str = 'purple' if self.type == self.ent_type.VLINK else 'red'
        return color

    @property
    def width(self):
        width: float = 4 if self.status == self.status_type.END2END else 1
        return width

    @property
    def style(self):
        style: str = 'solid' if self.status == self.status_type.END2END else 'dashed'
        return style


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

    def save_entanglement(self, nodeA: VLAwareQNode, nodeB: VLAwareQNode, type: str):
        pass

    def plot(self):
        # TODO different colored edges for different levels
        # TODO lvl2 graph
        nx.draw(self.graph, with_labels=True, node_color='skyblue', node_size=800, font_size=12, font_weight='bold', width=4)
        plt.title(f'lvl {self.lvl} graph')
        plt.show()



class GraphAnimation():
    def __init__(self, G: nx.Graph, entanglement_log: queue.Queue) -> None:
        # backlog for animation
        self.entanglement_log: queue.Queue = entanglement_log

        # build graph from other graph
        self.graph = nx.Graph()
        for node in G.nodes:
            node_number = int(re.search(r'\d+$', node.name).group())
            bipartite: int = 0 if node_number >= 6 else 1
            self.graph.add_node(node.name, bipartite=bipartite)
        for edge in G.edges:
            self.graph.add_edge(edge[0].name, edge[1].name)

        # viz
        self.fig, self.ax = plt.subplots()
        self.pos = nx.kamada_kawai_layout(self.graph)  
        self.edge_colors = {}  # Dictionary to store colors for edges
        self.anim = FuncAnimation(self.fig, self.update, interval=500)

    def update(self, frame):
        try:
            ent: EntanglementLogEntry = self.entanglement_log.get_nowait()
        except queue.Empty:
            ent = None

        # Update graph with item from buffer
        if ent:
            source: VLAwareQNode = ent.nodeA.name 
            target: VLAwareQNode = ent.nodeB.name
            color: VLAwareQNode = ent.color
            #self.graph.add_edge(source, target)
            self.edge_colors[(source, target)] = color


        # Clear previous plot
        self.ax.clear()

        # Draw network graph
        nx.draw(self.graph, pos=self.pos, ax=self.ax, with_labels=True, node_color='white', node_size=500, font_size=10, edgecolors='black', style='dotted')

        # Draw colored edges
        #for edge, color in self.edge_colors.items():
            #nx.draw_networkx_edges(self.graph, pos=self.pos, edgelist=[edge], edge_color=color, width=5)

