from qns.network.route import RouteImpl, DijkstraRouteAlgorithm, NetworkRouteError
from qns.entity.cchannel import ClassicChannel
from qns.entity.qchannel import QuantumChannel

from vlaware_qnode import VLAwareQNode

from typing import Callable, Union, List, Tuple, Dict
from dataclasses import dataclass

@dataclass
class RoutingResult:
    metric_physical: int
    metric_virtual: int
    path_physical: List[VLAwareQNode]
    path_virtual: List[VLAwareQNode]
    next_hop_physical: VLAwareQNode
    next_hop_virtual: VLAwareQNode
    vlink: bool

@dataclass
class RoutingTableEntry:
    metric_virtual: int
    path_virtual: List[Tuple[VLAwareQNode, str]]
    metric_physical: int
    path_physical: List[VLAwareQNode]

class VLEnabledRouteAlgorithm(RouteImpl):
    '''
    Dijkstra over virtual links
    '''
    def __init__(self, physical_graph, vlink_graph, metric_func: Callable[[Union[QuantumChannel, ClassicChannel]], float] = None) -> None:
        super().__init__('vl_dijkstra')

        # members
        self.physical_graph = physical_graph
        self.vlink_graph = vlink_graph
        self.route_table = {}
        self.metric_func = lambda _: 1 if metric_func is None else self.metric_func

    def build(self, nodes: List[VLAwareQNode], channels: List[Union[QuantumChannel, ClassicChannel]]):
        for source in nodes:
            self.route_table[source] = {}
            for target in nodes:

                # build lvl0 path - physical
                shortest_path_physical = self.physical_graph.shortest_path(source, target)
                shortest_path_physical_length = self.physical_graph.shortest_path_length(source, target)

                # build lvl1 path - entanglement enabled
                shortest_path_vlink = self.vlink_graph.shortest_path(source, target)
                shortest_path_vlink_length = self.vlink_graph.shortest_path_length(source, target)

                entry = RoutingTableEntry(
                    metric_virtual=shortest_path_vlink_length,
                    path_virtual=shortest_path_vlink,
                    metric_physical=shortest_path_physical_length,
                    path_physical=shortest_path_physical
                )
                self.route_table[source][target] = entry

    def query(self, src: VLAwareQNode, dest: VLAwareQNode) -> RoutingTableEntry:
        src_route_table = self.route_table.get(src, None)
        if src_route_table is None: 
            return []
        entry: RoutingTableEntry = src_route_table.get(dest, None)
        if entry is None:
            return []

        try:
            metric_physical: int = entry.metric_physical
            metric_virtual: int = entry.metric_virtual
            path_physical: List[VLAwareQNode] = [hop[0][1] for hop in entry.path_physical]
            path_virtual: List[VLAwareQNode] = [hop[0][1] for hop in entry.path_virtual]
            next_hop_physical: VLAwareQNode = path_physical[0]
            next_hop_virtual: VLAwareQNode = path_virtual[0]
            vlink = next_hop_virtual != next_hop_physical

            result = RoutingResult(
                metric_physical=metric_physical,
                metric_virtual=metric_virtual,
                path_physical=path_physical,
                path_virtual=path_virtual,
                next_hop_physical=next_hop_physical,
                next_hop_virtual=next_hop_virtual,
                vlink=vlink
            )

            return result

        except Exception:
            return []
