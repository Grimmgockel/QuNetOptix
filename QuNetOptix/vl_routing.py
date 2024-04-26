from qns.network.route import RouteImpl, DijkstraRouteAlgorithm, NetworkRouteError
from qns.entity.cchannel import ClassicChannel
from qns.entity.qchannel import QuantumChannel

from vlaware_qnode import VLAwareQNode

from typing import Callable, Union, List, Tuple, Dict
import networkx as nx
import math
import matplotlib.pyplot as plt


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
                self.route_table[source][target] = {}
                shortest_path = nx.shortest_path(self.graph, source=source, target=target, weight='weight')
                l = nx.shortest_path_length(self.graph, source=source, target=target, weight='weight')

                self.route_table[source][target] = [l, shortest_path]

    def query(self, src: VLAwareQNode, dest: VLAwareQNode) -> List[Tuple[float, VLAwareQNode, List[VLAwareQNode]]]:
        src_route_table = self.route_table.get(src, None)
        if src_route_table is None: 
            return []

        entry = src_route_table.get(dest, None)
        if entry is None:
            return []

        try:
            metric = entry[0]
            path = entry[1]
            if len(path) <= 1 or metric == float('inf'):
                return []
                
            next_hop = path[1]
            return [(metric, next_hop, path)]

        except Exception:
            return []
