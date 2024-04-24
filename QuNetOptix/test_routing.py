from qns.network.protocol.entanglement_distribution import EntanglementDistributionApp
from qns.network.topology.topo import ClassicTopology
from qns.entity.node.app import Application
from qns.entity.qchannel.qchannel import QuantumChannel
from qns.entity.node.node import QNode
from qns.network.topology import Topology

from typing import Dict, List, Optional, Tuple
import pytest

from oracle import NetworkOracle
from config import Config
from routing import VLEnabledDistributionApp


'''
Custom double star topology for testing virtual link routing: minimum topology for virtual link exploitation
'''
class TestTopology(Topology):
    def __init__(self, nodes_apps: List[Application] = [],
                 qchannel_args: Dict = {}, cchannel_args: Dict = {},
                 memory_args: Optional[List[Dict]] = {}):
        super().__init__(12, nodes_apps=nodes_apps,
                         qchannel_args=qchannel_args, cchannel_args=cchannel_args,
                         memory_args=memory_args)

    def build(self) -> Tuple[List[QNode], List[QuantumChannel]]:
        nl: List[QNode] = []
        ll = []

        for i in range(self.nodes_number):
            n = QNode(f'n{i}')
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


if __name__ == '__main__': 
    oracle = NetworkOracle()


    print("success.")
