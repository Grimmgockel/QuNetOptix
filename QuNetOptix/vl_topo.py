from qns.entity.qchannel.qchannel import QuantumChannel
from qns.network.topology import Topology
from vlaware_qnode import VLAwareQNode
from vl_maintenance import VLMaintenanceApp
from dummy_app import DummyApp
from vl_distribution import VLEnabledDistributionApp

from typing import List, Tuple

'''
Custom double star topology for testing virtual link routing: minimum topology for virtual link exploitation
'''
class CustomDoubleStarTopology(Topology):
    def __init__(self):
        super().__init__(12, memory_args=[{"capacity": 50}], nodes_apps=[VLEnabledDistributionApp(),VLMaintenanceApp()])
        #super().__init__(12, memory_args=[{"capacity": 50}], nodes_apps=[DummyApp(),VLMaintenanceApp()])

    def build(self) -> Tuple[List[VLAwareQNode], List[QuantumChannel]]:
        nl: List[VLAwareQNode] = []
        ll = []

        for i in range(self.nodes_number):
            n = VLAwareQNode(f'n{i}')
            nl.append(n)

        for i in range(11):
            link = QuantumChannel(name=f"l{i}", **self.qchannel_args)
            ll.append(link)

        # build first star
        nl[0].add_qchannel(ll[0])
        nl[2].add_qchannel(ll[0])

        nl[1].add_qchannel(ll[1])
        nl[2].add_qchannel(ll[1])

        nl[3].add_qchannel(ll[3])
        nl[2].add_qchannel(ll[3])

        nl[4].add_qchannel(ll[2])
        nl[2].add_qchannel(ll[2])

        # build bridge
        nl[5].add_qchannel(ll[4])
        nl[2].add_qchannel(ll[4])

        nl[5].add_qchannel(ll[5])
        nl[6].add_qchannel(ll[5])

        nl[6].add_qchannel(ll[6])
        nl[9].add_qchannel(ll[6])

        # build second star
        nl[7].add_qchannel(ll[7])
        nl[9].add_qchannel(ll[7])

        nl[8].add_qchannel(ll[8])
        nl[9].add_qchannel(ll[8])

        nl[11].add_qchannel(ll[9])
        nl[9].add_qchannel(ll[9])

        nl[10].add_qchannel(ll[10])
        nl[9].add_qchannel(ll[10])

        self._add_apps(nl)
        self._add_memories(nl)
        return nl, ll