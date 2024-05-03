from dataclasses import dataclass
from typing import List, Set, Dict
from vlaware_qnode import Transmit
from qns.network.requests import Request
from qns.models.core import QuantumModel

@dataclass
class MetaData:
    '''
    This is per simulation run.
    '''
    # Routing
    distribution_requests: Set[Request] = None
    vlink_requests: Set[Request] = None
    result_eprs: Dict[Transmit, QuantumModel] = None

    @property
    def throughput(self) -> float:
        return 0.0

    @property
    def generation_latency(self) -> float:
        return 0.0

    @property
    def fidelity(self) -> float:
        return 0.0
