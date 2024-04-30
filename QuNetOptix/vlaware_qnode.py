from qns.entity.node.app import Application
from qns.entity.node import QNode
from qns.network.requests import Request

from typing import List, Dict, Optional

from typing import Optional
from dataclasses import dataclass


'''
QNode with knowledge over vlink requests
'''
class VLAwareQNode(QNode):
    def __init__(self, name: str = None, apps: List[Application] = None):
        super().__init__(name, apps)
        self.has_vlink = False
        self.vlinks: List[Request] = []
        self.trans_registry: Dict[str, Transmit] = {}

    def add_vlink(self, vlink: Request):
        self.vlinks.append(vlink)

'''
Bookkeeping
'''
@dataclass
class Transmit:
    id: str
    src: VLAwareQNode
    dst: VLAwareQNode
    first_epr_name: Optional[str] = None
    second_epr_name: Optional[str] = None
    start_time_s: Optional[float] = None