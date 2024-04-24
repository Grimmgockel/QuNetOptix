from qns.network.protocol import EntanglementDistributionApp
from qns.entity.node import QNode
from qns.entity.qchannel import QuantumChannel
from qns.simulator.event import Event, func_to_event
from qns.network.route import DijkstraRouteAlgorithm, RouteImpl
from qns.network.topology import RandomTopology, WaxmanTopology
from qns.entity.node.app import Application
from qns.simulator.simulator import Simulator
import qns.utils.log as log


from vls import Transmit
from typing import Optional
from dataclasses import dataclass



'''
Node application for entanglement distribution over physical and virtual links
'''
class VLEnabledDistributionApp(EntanglementDistributionApp):
    def install(self, node: QNode, simulator: Simulator):
        super().install(node, simulator)

    def new_distribution(self):
        # generate new entanglement
        epr = self.generate_qubit(self.own, self.dst, None)

        self.state[epr.transmit_id] = Transmit(
            id=epr.transmit_id, 
            src=self.own, 
            dst=self.dst, 
            second_epr_name=epr.name, 
            start_time_s=self._simulator.current_time.sec
        )

        if not self.memory.write(epr):
            self.memory.read(epr)
            self.state[epr.transmit_id] = None

        self.send_count += 1
        self.request_distrbution(epr.transmit_id)

