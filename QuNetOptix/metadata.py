from dataclasses import dataclass
from typing import List, Set, Dict, Tuple, Optional
from vlaware_qnode import Transmit
import pandas as pd
from qns.network.requests import Request
from qns.models.core import QuantumModel


@dataclass
class DistroResult:
    src_result: Optional[Tuple[Transmit, QuantumModel]] = None
    dst_result: Optional[Tuple[Transmit, QuantumModel]] = None

@dataclass
class SimData:
    '''
    This is per simulation run.
    '''
    # plotting
    entanglement_log = None
    entanglement_log_timestamps: Dict[str, int] = None

    # Routing
    distribution_requests: Set[Request] = None
    vlink_requests: Set[Request] = None
    distro_results: Dict[str, DistroResult] = None

    # sim performance data
    df = pd.DataFrame()

    @property
    def send_count(self) -> int:
        return self.df['send_count'][0]

    @property
    def success_count(self) -> int:
        return self.df['success_count'][0]

    @property
    def remaining_mem_usage(self) -> int:
        return self.df['remaining_mem_usage'][0]


    @property
    def success_rate(self) -> float:
        # TODO success count / send count
        return 0.0

    @property
    def throughput(self) -> float:
        throughput_EPps = self.df['success_count'] / self.df['sim_time_s']
        return throughput_EPps

    @property
    def generation_latency(self) -> float:
        return 0.0

    @property
    def fidelity(self) -> float:
        return 0.0
