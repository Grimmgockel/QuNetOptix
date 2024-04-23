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

    def __repr__(self):
        return f'-----------------\nSIMULATION PARAMS:\nts={self.ts}\nte={self.te}\nacc={self.acc}\nnode_count={self.node_count}\nline_count={self.line_count}\nqchannel_delay={self.qchannel_delay}\ncchannel_delay={self.cchannel_delay}\nmem_cap={self.mem_cap}\ninit_fidelity={self.init_fidelity}\nsessions={self.sessions}\nsend_rate={self.send_rate}\n'
