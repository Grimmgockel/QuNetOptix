from qns.models.epr import BellStateEntanglement

class VLEntangledPair(BellStateEntanglement):
    def __init__(self, fidelity: float = 1, name: str | None = None, p_swap: float = 1):
        super().__init__(fidelity, name, p_swap)
        self.src = None
        self.dst = None
        self.transmit_id = None

class StandardEntangledPair(BellStateEntanglement):
    def __init__(self, fidelity: float = 1, name: str | None = None, p_swap: float = 1):
        super().__init__(fidelity, name, p_swap)
        self.src = None
        self.dst = None
        self.transmit_id = None