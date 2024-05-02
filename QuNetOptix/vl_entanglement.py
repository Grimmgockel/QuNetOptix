from qns.models.epr import BellStateEntanglement
from vlaware_qnode import EprAccount


class VLEntangledPair(BellStateEntanglement):
    '''
    Custom entanglement for distro app
    '''
    def __init__(self, fidelity: float = 1, name: str | None = None, p_swap: float = 1):
        super().__init__(fidelity, name, p_swap)
        self.src = None
        self.dst = None
        self.account: EprAccount = None

class StandardEntangledPair(BellStateEntanglement):
    '''
    Custom entanglement for maintenance app
    '''
    def __init__(self, fidelity: float = 1, name: str | None = None, p_swap: float = 1):
        super().__init__(fidelity, name, p_swap)
        self.src = None
        self.dst = None
        self.account: EprAccount = None