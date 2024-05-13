from qns.network.requests import Request
from itertools import groupby
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
    timestamp: int

    class ent_type(Enum):
        ENT = 0
        VLINK = 1
    ent_t: Optional[ent_type] = None

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
        color: str = 'purple' if self.ent_t == self.ent_type.VLINK else 'red'
        return color

    @property
    def width(self):
        width: float = 4 if self.status == self.status_type.END2END else 1
        return width

    @property
    def style(self):
        style: str = 'solid' if self.status == self.status_type.END2END else 'dashed'
        return style

    def __repr__(self) -> str:
        return f'{self.instruction.name} {self.status.name} {self.ent_t.name} for {self.nodeA.name} -> {self.nodeB.name} [ts={self.timestamp}]'

class GraphAnimation():
    def __init__(self, filename: str, fps: int, G: nx.Graph, entanglement_log: List[EntanglementLogEntry]) -> None:
        # backlog for animation
        self.entanglement_log: List[EntanglementLogEntry] = entanglement_log

        # build graph from other graph
        self.graph = nx.Graph()
        for node in G.nodes:
            node_number = int(re.search(r'\d+$', node.name).group())
            bipartite: int = 0 if node_number >= 6 else 1
            self.graph.add_node(node.name, bipartite=bipartite)
        for edge in G.edges:
            self.graph.add_edge(edge[0].name, edge[1].name)

        # viz
        plt.style.use('dark_background')
        self.start_frame = True
        self.entanglement_edges = []
        self.entanglement_edges_e2e = []
        self.vlink_edges = []
        self.vlink_edges_e2e = []
        self.timestamp: int = 0
        self.fig, self.ax = plt.subplots()
        self.pos = nx.circular_layout(self.graph)  
        self.edge_colors = {}  # Dictionary to store colors for edges

        # sort for timestamps
        self.entanglement_log.sort(key=lambda entry: entry.timestamp)
        self.groups = groupby(self.entanglement_log, key=lambda entry: entry.timestamp)
        self.batches = []
        self.frame_count = 0
        self.interval = 500
        for timestamp, group in self.groups:
            self.frame_count += 1
            self.batches.append(list(group))
        self.frame_count += 2

        self.anim = FuncAnimation(self.fig, self.update, interval=self.interval, frames=self.frame_count)
        self.anim.save(filename=filename, writer='ffmpeg', fps=fps)
        self.draw_physical()

    def update(self, frame):
        self.draw_physical()

        if self.start_frame: 
            self.start_frame = False
            return

        try:
            batch = self.batches[self.timestamp]
            #print(f'{self.timestamp}\t{batch}')
            self.timestamp += 1

            for item in batch: # per timestamp
                entry: EntanglementLogEntry = item
                if entry.ent_t == EntanglementLogEntry.ent_type.ENT:
                    if entry.instruction == EntanglementLogEntry.instruction_type.CREATE:
                        if entry.status == EntanglementLogEntry.status_type.INTERMEDIATE:
                            self.entanglement_edges.append((entry.nodeA.name, entry.nodeB.name))
                        elif entry.status == EntanglementLogEntry.status_type.END2END:
                            self.entanglement_edges_e2e.append((entry.nodeA.name, entry.nodeB.name))
                        else:
                            pass
                    elif entry.instruction == EntanglementLogEntry.instruction_type.DELETE:
                        try:
                            if entry.status == EntanglementLogEntry.status_type.INTERMEDIATE:
                                self.entanglement_edges.remove((entry.nodeA.name, entry.nodeB.name))
                            elif entry.status == EntanglementLogEntry.status_type.END2END:
                                self.entanglement_edges_e2e.remove((entry.nodeA.name, entry.nodeB.name))
                            else:
                                pass
                        except ValueError:
                            pass
                    else: # invalid instruction
                        pass
                if entry.ent_t == EntanglementLogEntry.ent_type.VLINK:
                    if entry.instruction == EntanglementLogEntry.instruction_type.CREATE:
                        if entry.status == EntanglementLogEntry.status_type.INTERMEDIATE:
                            self.vlink_edges.append((entry.nodeA.name, entry.nodeB.name))
                        elif entry.status == EntanglementLogEntry.status_type.END2END:
                            self.vlink_edges_e2e.append((entry.nodeA.name, entry.nodeB.name))
                        else:
                            pass
                    elif entry.instruction == EntanglementLogEntry.instruction_type.DELETE:
                        try:
                            if entry.status == EntanglementLogEntry.status_type.INTERMEDIATE:
                                self.vlink_edges.remove((entry.nodeA.name, entry.nodeB.name))
                            elif entry.status == EntanglementLogEntry.status_type.END2END:
                                self.vlink_edges_e2e.remove((entry.nodeA.name, entry.nodeB.name))
                            else:
                                pass
                        except ValueError:
                            pass
                    else: # invalid instruction
                        pass
        except IndexError:
            pass

        nx.draw_networkx_edges(self.graph, pos=self.pos, edgelist=self.vlink_edges, edge_color='blue', width=2)
        nx.draw_networkx_edges(self.graph, pos=self.pos, edgelist=self.vlink_edges_e2e, edge_color='blue', width=2)
        nx.draw_networkx_edges(self.graph, pos=self.pos, edgelist=self.entanglement_edges, edge_color='red', width=2)
        nx.draw_networkx_edges(self.graph, pos=self.pos, edgelist=self.entanglement_edges_e2e, edge_color='purple', width=4)

    def draw_physical(self):
        # Clear previous plot
        self.ax.clear()

        # Draw network graph
        nx.draw(self.graph, pos=self.pos, ax=self.ax, with_labels=True, node_color='black', node_size=500, font_size=10, edgecolors='white', font_color='white', edge_color='white', style='dotted')

