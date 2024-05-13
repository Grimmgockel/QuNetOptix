from qns.entity.node.app import Application
from qns.entity.qchannel.qchannel import QuantumChannel
from qns.entity.cchannel.cchannel import ClassicChannel
from qns.network.topology import Topology
from qns.network.topology.linetopo import LineTopology
from vlaware_qnode import VLAwareQNode
from vl_app import VLEnabledDistributionApp, VLMaintenanceApp
#from vl_maintenance import VLMaintenanceApp
#from vl_distro import VLEnabledDistributionApp
from qns.models.delay import NormalDelayModel, DelayModel, ConstantDelayModel, UniformDelayModel

from typing import Dict, List, Tuple
import numpy as np


light_speed = 299791458
length = 20 # CONNECTION_ORIENTED PAPER: 0.5km; SLS PAPER: 20km

channel_delay_model = ConstantDelayModel(delay=length/light_speed)
memory_delay_model = ConstantDelayModel(delay=0.01) # TODO for this to work implement asynchronous read and write

class CustomLineTopology(LineTopology):
    def __init__(self, nodes_number):
        super().__init__(
            nodes_number, 
            nodes_apps=[VLEnabledDistributionApp(), VLMaintenanceApp()], 
            memory_args=[{'capacity': 2, 'delay': memory_delay_model}], 
            qchannel_args={'delay': channel_delay_model, 'length': length},
            cchannel_args={'delay': channel_delay_model, 'length': length},
        )

    def build(self) -> Tuple[List[VLAwareQNode], List[QuantumChannel]]:
        nl: List[VLAwareQNode] = []
        ll = []
        if self.nodes_number >= 1:
            n = VLAwareQNode(f"n{1}")
            nl.append(n)
        pn = n
        for i in range(self.nodes_number - 1):
            n = VLAwareQNode(f"n{i+2}")
            nl.append(n)
            link = QuantumChannel(name=f"l{i+1}", **self.qchannel_args)
            ll.append(link)

            pn.add_qchannel(link)
            n.add_qchannel(link)
            pn = n

        self._add_apps(nl)
        self._add_memories(nl)
        return nl, ll

class CustomDoubleStarTopology(Topology):
    '''
    Custom double star topology for testing virtual link routing: minimum topology for virtual link exploitation
    '''
    def __init__(self, memory_args=[{'capacity': 50}]):
        super().__init__(12, memory_args=memory_args, nodes_apps=[VLEnabledDistributionApp(), VLMaintenanceApp()])

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