from qns.models.epr import BellStateEntanglement, WernerStateEntanglement, MixedStateEntanglement, BaseEntanglement
from vlaware_qnode import EprAccount
from typing import Optional
import numpy as np

from qns.utils.rnd import get_rand

class VLEntangledPair(MixedStateEntanglement):
    '''
    Custom entanglement for maintenance app
    '''
    def __init__(self, fidelity: float = 0.99, b: float | None = None, c: float | None = None, d: float | None = None, name: str | None = None):
        super().__init__(fidelity, b, c, d, name)
        self.src = None
        self.dst = None
        self.account: EprAccount = None

    def store_error_model(self, t: float, decoherence_rate: Optional[float] = 0, **kwargs):
        self.a = 0.999
        self.normalized()

    def transfer_error_model(self, length: float, decoherence_rate: Optional[float] = 0, **kwargs):
        self.a = 0.999
        self.normalized()



class StandardEntangledPair(MixedStateEntanglement):
    '''
    Custom entanglement for distro app
    '''
    def __init__(self, fidelity: float = 0.99, b: float | None = None, c: float | None = None, d: float | None = None, name: str | None = None):
        super().__init__(fidelity, b, c, d, name)
        self.src = None
        self.dst = None
        self.account: EprAccount = None


