from qns.models.epr import BellStateEntanglement, WernerStateEntanglement, MixedStateEntanglement, BaseEntanglement
from vlaware_qnode import EprAccount


class VLEntangledPair(WernerStateEntanglement):
    '''
    Custom entanglement for distro app
    '''
    def __init__(self, fidelity: float = 1, name: str | None = None, p_swap: float = 1):
        super().__init__(0.99, name)
        self.src = None
        self.dst = None
        self.account: EprAccount = None

class StandardEntangledPair(WernerStateEntanglement):
    '''
    Custom entanglement for maintenance app
    '''
    def __init__(self, fidelity: float = 1, name: str | None = None, p_swap: float = 1):
        super().__init__(0.99, name)
        self.src = None
        self.dst = None
        self.account: EprAccount = None