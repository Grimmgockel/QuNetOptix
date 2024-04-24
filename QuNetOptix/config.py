from dataclasses import dataclass
from qns.entity.node.app import Application
from base_routing import BaseApp
from qns.network.topology import Topology

@dataclass
class Config:
    ts: int 
    te: int 
    acc: int 
    sessions: int 
    send_rate: float 
    topo: Topology

