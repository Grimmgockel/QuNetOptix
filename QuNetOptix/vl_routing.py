from qns.network.route import RouteImpl, DijkstraRouteAlgorithm
from qns.entity.cchannel import ClassicChannel
from qns.entity.qchannel import QuantumChannel

from typing import Callable


class VLEnabledRouteAlgorithm(DijkstraRouteAlgorithm):
    # TODO determine how vlinks should be treated 
    # - EITHER: every node knows its closest vlink (start at lvl2 graph and work down, internet adressing paper)
    # - OR: simple dijkstra on lvl1 graph
    def __init__(self, name: str = "dijkstra", metric_func: Callable[[QuantumChannel | ClassicChannel], float] = None) -> None:
        super().__init__(name, metric_func)



















