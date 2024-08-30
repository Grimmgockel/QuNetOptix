from qns.entity.node.app import Application
from qns.entity.node import QNode
from qns.network.requests import Request

from typing import List, Dict, Optional, Tuple

from typing import Optional
from dataclasses import dataclass
from collections import deque
import re
#import queue


'''
QNode with knowledge over vlink requests
'''
class VLAwareQNode(QNode):
    def __init__(self, name: str = None, apps: List[Application] = None):
        super().__init__(name, apps)
        self.trans_registry: Dict[str, Transmit] = {}
        self.session_registry: Dict[str, Dict[str, VLAwareQNode]] = {} # one node can manage multiple src-dst sessions, save with transmit_id
        self.has_vlink = False
        self.vlinks: List[Request] = []
        #self.vlink_buf = queue.Queue() # shared resource
        #self.waiting_for_vlink_buf = queue.Queue() # shared resource
        self.vlink_buf = deque()
        self.waiting_for_vlink_buf = deque()

        self.storage_log: Dict[str, Dict[str, Optional[bool]]] = {} # key: transmit id, value: epr list to store, storage progress (e.g. 1/2)

    def add_vlink(self, vlink: Request):
        self.vlinks.append(vlink)

    @property
    def index(self) -> int:
        match = re.search(r'n(\d+)', self.name)
        if match:
            return int(match.group(1))
        else:
            raise ValueError(f'Label \'{self.name}\' does not match expected format')

@dataclass
class EprAccount:
    transmit_id: str = None
    session_id: str = None
    name: str = None
    src: VLAwareQNode = None # for retrieving transmit data when physically transmitting qubits
    dst: VLAwareQNode = None
    locA: Optional[VLAwareQNode] = None 
    locB: Optional[VLAwareQNode] = None

@dataclass
class Transmit:
    id: str
    session: str
    src: VLAwareQNode
    dst: VLAwareQNode
    alice: Optional[EprAccount] = None # points backward 
    charlie: Optional[EprAccount] = None # points forwards
    start_time_s: Optional[float] = None
    wait_time_s: Optional[float] = None # sim time where transmit started waiting for vlink
    revoked: bool = False

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self) -> str:
        alice_locA = 'xx' if self.alice is None or self.alice.locA is None else self.alice.locA.name
        alice_locB = 'xx' if self.alice is None or self.alice.locB is None else self.alice.locB.name
        charlie_locA = 'xx' if self.charlie is None or self.charlie.locA is None else self.charlie.locA.name
        charlie_locB = 'xx' if self.charlie is None or self.charlie.locB is None else self.charlie.locB.name

        return f"TRANSMIT[id={self.id};src={self.src.name};dst={self.dst.name};alice=({alice_locA},{alice_locB});charlie({charlie_locA},{charlie_locB})]"

