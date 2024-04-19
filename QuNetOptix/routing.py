from qns.network.protocol import EntanglementDistributionApp
from qns.entity.node import QNode
from qns.entity.qchannel import QuantumChannel
from qns.simulator.event import Event, func_to_event
from qns.network.route import DijkstraRouteAlgorithm, RouteImpl
from qns.network.topology import RandomTopology, WaxmanTopology

'''
Node application for entanglement distribution over physical and virtual links
'''
class VLEnabledDistributionApp(EntanglementDistributionApp):
    # TODO test this in pytest suite
    pass


class VLAwareNode(QNode):
    pass

class VLAwareChannel(QuantumChannel):
    pass

class CustomWax(WaxmanTopology):
    pass

class VLRouting(RouteImpl):
    pass