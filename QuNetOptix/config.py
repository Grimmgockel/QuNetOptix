from dataclasses import dataclass

@dataclass
class Config:
    ts: int
    te: int
    acc: int
    node_count: int
    line_count: int
    qchannel_delay: float
    cchannel_delay: float
    mem_cap: int
    init_fidelity: float
    sessions: int
    send_rate: float

    def __repr__(self):
        return f'-----------------\nSIMULATION PARAMS:\nts={self.ts}\nte={self.te}\nacc={self.acc}\nnode_count={self.node_count}\nline_count={self.line_count}\nqchannel_delay={self.qchannel_delay}\ncchannel_delay={self.cchannel_delay}\nmem_cap={self.mem_cap}\ninit_fidelity={self.init_fidelity}\nsessions={self.sessions}\nsend_rate={self.send_rate}\n'
