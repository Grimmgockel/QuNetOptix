from dataclasses import dataclass
from qns.entity.node.app import Application
from base_routing import BaseApp

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
    sessions: int 
    send_rate: float 
    app: Application

