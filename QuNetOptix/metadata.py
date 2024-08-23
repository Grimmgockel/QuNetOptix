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

    # max values
    gl_max: float = 0.0
    gl_min: float = 0.0


    # sim performance data
    df = pd.DataFrame()

    @property
    def q_message_count(self) -> int:
        return self.df['q_message_count'][0]

    @property
    def c_message_count(self) -> int:
        return self.df['c_message_count'][0]

    @property
    def agg_swap_count(self) -> int:
        return self.df['swap_count'][0]

    @property
    def send_count(self) -> int:
        return self.df['send_count'][0]

    @property
    def success_count(self) -> int:
        return self.df['success_count'][0]

    @property
    def avg_swap_count(self) -> int:
        return self.agg_swap_count / self.success_count

    @property
    def remaining_mem_usage(self) -> int:
        return self.df['remaining_mem_usage'][0]

    @property
    def success_rate_p(self) -> float:
        return self.df['success_count'][0] / self.df['send_count'][0] * 100


    @property
    def generation_latency_avg(self) -> Optional[float]:
        try:
            return self.df['generation_latency_agg'][0] / self.df['success_count'][0]
        except ZeroDivisionError:
            return None

    @property
    def generation_latency_max(self) -> float:
        return self.gl_max

    @property
    def generation_latency_agg(self) -> float:
        return self.df['generation_latency_agg'][0]

    @property
    def fidelity_avg(self) -> Optional[float]:
        fidelity_agg = self.df['fidelity_agg'][0]
        try:
            fidelity_avg = fidelity_agg / self.success_count
            return fidelity_avg
        except ZeroDivisionError:
            return None

    @property
    def fidelity_loss_avg(self) -> float:
        return 1-self.fidelity_avg

    @property
    def throughput(self) -> float:
        throughput_EPps = 1/self.generation_latency_avg
        return throughput_EPps

    @property
    def mem_utilization_p(self) -> float:
        # TODO
        return 0.0

    @property
    def generation_latency_max(self) -> float:
        # TODO
        return 0.0

