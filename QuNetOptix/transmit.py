from vlaware_qnode import VLAwareQNode
from typing import Optional
from dataclasses import dataclass

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