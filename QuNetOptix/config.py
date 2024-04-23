from dataclasses import dataclass
from qns.entity.node.app import Application
from base_routing import BaseApp

@dataclass
class Config:
    ts: int = 0
    te: int = 50
    acc: int = 1000000
    node_count: int = 100
    line_count: int = 150
    qchannel_delay: float = 0.05
    cchannel_delay: float = 0.05
    mem_cap: int = 10
    init_fidelity: float = 0.99
    sessions: int = 50
    send_rate: float = 0.05

