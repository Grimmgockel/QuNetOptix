from qns.models.epr import BellStateEntanglement, WernerStateEntanglement, MixedStateEntanglement, BaseEntanglement
from vlaware_qnode import EprAccount
from typing import Optional
import numpy as np

class VLEntangledPair(WernerStateEntanglement):
    '''
    Custom entanglement for distro app
    '''
    def __init__(self, fidelity: float = 1, name: str | None = None, p_swap: float = 1):
        super().__init__(1, name)
        self.src = None
        self.dst = None
        self.account: EprAccount = None

    def store_error_model(self, t: float, decoherence_rate: Optional[float] = 0, **kwargs):
        self.w = self.w 

    def transfer_error_model(self, length: float, decoherence_rate: Optional[float] = 0, **kwargs):
        self.w = self.w 

class StandardEntangledPair(WernerStateEntanglement):
    '''
    Custom entanglement for maintenance app
    '''
    def __init__(self, fidelity: float = 1, name: str | None = None, p_swap: float = 1):
        super().__init__(0.99, name)
        self.src = None
        self.dst = None
        self.account: EprAccount = None
