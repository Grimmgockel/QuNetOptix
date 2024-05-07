from dataclasses import dataclass
from typing import List, Set, Dict, Tuple, Optional
from vlaware_qnode import Transmit
from qns.network.requests import Request
from vl_net_graph import EntanglementLogEntry
from qns.models.core import QuantumModel

@dataclass
class DistroResult:
    src_result: Optional[Tuple[Transmit, QuantumModel]] = None
    dst_result: Optional[Tuple[Transmit, QuantumModel]] = None

@dataclass
class MetaData:
    '''
    This is per simulation run.
    '''
    # data
    send_count: int = 0
    success_count: int = 0
    vlink_count: int = 0

    # plotting
    entanglement_log: List[EntanglementLogEntry] = None
    entanglement_log_timestamps: Dict[str, int] = None

    # Routing
    distribution_requests: Set[Request] = None
    vlink_requests: Set[Request] = None
    distro_results: Dict[str, DistroResult] = None
    remaining_memory_usage: int = 0

    @property
    def throughput(self) -> float:
        return 0.0

    @property
    def generation_latency(self) -> float:
        return 0.0

    @property
    def fidelity(self) -> float:
        return 0.0
