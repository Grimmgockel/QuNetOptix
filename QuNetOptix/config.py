from dataclasses import dataclass
from qns.entity.node.app import Application
from qns.network.topology import Topology
from qns.network.requests import Request

from typing import List, Optional, Tuple

class Job:
    def __init__(self, session_count: int, sessions: List[Request]) -> None:
        self.session_count: Optional[int] = session_count
        self.sessions: Optional[List[Tuple[str]]] = sessions

    @classmethod
    def random(cls, session_count: int):
        return cls(session_count, None)

    @classmethod
    def custom(cls, sessions: List[Tuple[str]]):
        session_count = len(sessions)
        return cls(session_count, sessions)

    def __repr__(self) -> str:
        return f'Job(cnt={self.session_count},sessions={self.sessions})'

@dataclass
class Config:
    ts: int 
    te: int 
    acc: int 
    topo: Topology
    job: Job 
    vlink_send_rate: float = 1
    vls: bool = True
    send_rate: float = 1
    continuous_distro: bool = True
    vlinks: List[Tuple[str]] = None
    schedule_n_vlinks: Optional[int] = None

    def __repr__(self):
        return f'Config(ts={self.ts}, te={self.te}, acc={self.acc}, send_rate={self.send_rate}, node_count={self.topo.nodes_number}, sessions={self.job.session_count}, job={self.job})'
    

