from qns.network.protocol import EntanglementDistributionApp
from qns.entity.node import QNode
from qns.entity.qchannel import QuantumChannel
from qns.simulator.event import Event, func_to_event
from qns.network.route import DijkstraRouteAlgorithm, RouteImpl
from qns.network.topology import RandomTopology, WaxmanTopology
import qns.utils.log as log

from typing import Optional
from dataclasses import dataclass

@dataclass
class Transmit():
    id: str
    src: QNode
    dst: QNode
    first_epr_name: Optional[str] = None
    second_epr_name: Optional[str] = None
    start_time_s: Optional[float] = None

class VLAwareNode(QNode):
    pass

class VLAwareChannel(QuantumChannel):
    pass

class CustomWax(WaxmanTopology):
    pass

class VLRouting(RouteImpl):
    pass

'''
Node application for entanglement distribution over physical and virtual links
'''
class VLEnabledDistributionApp(EntanglementDistributionApp):
    def new_distribution(self):
        log.debug(f"{self.own}: start single request")

        # generate new entanglement
        epr = self.generate_qubit(self.own, self.dst, None)
        log.debug(f"{self.own}: generate epr {epr.name}")

        self.state[epr.transmit_id] = Transmit(
            id=epr.transmit_id,
            src=self.own,
            dst=self.dst,
            second_epr_name=epr.name)

        log.debug(f"{self.own}: generate transmit {self.state[epr.transmit_id]}")
        if not self.memory.write(epr):
            self.memory.read(epr)
            self.state[epr.transmit_id] = None
        self.send_count += 1
        self.request_distrbution(epr.transmit_id)

