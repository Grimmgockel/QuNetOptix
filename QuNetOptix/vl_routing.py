from qns.network.route import RouteImpl, DijkstraRouteAlgorithm, NetworkRouteError
from qns.entity.cchannel import ClassicChannel
from qns.entity.qchannel import QuantumChannel

from vlaware_qnode import VLAwareQNode

from typing import Callable, Union, List, Tuple, Dict
import networkx as nx
import matplotlib.pyplot as plt
from dataclasses import dataclass

@dataclass
class RoutingResult:
    metric: float
    path: List[VLAwareQNode]
    next_hop: VLAwareQNode
    vlink: bool

@dataclass
class RoutingTableEntry:
    metric: int
    vl_path: List[Tuple[VLAwareQNode, str]]

class VLEnabledRouteAlgorithm(RouteImpl):
    def __init__(self, graph: nx.Graph, metric_func: Callable[[Union[QuantumChannel, ClassicChannel]], float] = None) -> None:
        super().__init__('vl_dijkstra')

        # members
        self.graph = graph
        self.route_table = {}
        self.metric_func = lambda _: 1 if metric_func is None else self.metric_func

    def build(self, nodes: List[VLAwareQNode], channels: List[Union[QuantumChannel, ClassicChannel]]):
        for source in nodes:
            self.route_table[source] = {}
            for target in nodes:
                shortest_path = nx.shortest_path(self.graph, source=source, target=target)
                shortest_path_length = nx.shortest_path_length(self.graph, source=source, target=target)
                path_edges = [(shortest_path[i], shortest_path[i+1]) for i in range(len(shortest_path)-1)]
                edge_types = [self.graph.get_edge_data(u, v)['type'] for u, v in path_edges]
                entry = RoutingTableEntry(
                    metric=shortest_path_length,
                    vl_path=list(zip(path_edges, edge_types))
                )
                self.route_table[source][target] = entry


    def query(self, src: VLAwareQNode, dest: VLAwareQNode) -> RoutingResult:
        src_route_table = self.route_table.get(src, None)
        if src_route_table is None: 
            return []
        entry: RoutingTableEntry = src_route_table.get(dest, None)
        if entry is None:
            return []
        try:
            metric = entry.metric
            path = [hop[0] for hop in entry.vl_path]
            next_hop = entry.vl_path[0][0][1]
            vlink=True if entry.vl_path[0][1] == 'entanglement' else False

            result = RoutingResult(
                metric=metric,
                path=path,
                next_hop=next_hop,
                vlink=vlink,
            )

            return result

        except Exception:
            return []
