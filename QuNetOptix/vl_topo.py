from qns.entity.node.app import Application
import itertools
import numpy as np

from qns.utils.rnd import get_randint
from qns.utils.rnd import get_rand
from qns.entity.node.node import QNode
from qns.entity.qchannel.qchannel import QuantumChannel
from qns.entity.cchannel.cchannel import ClassicChannel
from qns.network.topology import Topology
from qns.network.protocol.node_process_delay import NodeProcessDelayApp
from qns.network.topology.linetopo import LineTopology
from qns.network.topology.randomtopo import RandomTopology
from qns.network.topology.waxmantopo import WaxmanTopology
from vlaware_qnode import VLAwareQNode
from vl_app import VLEnabledDistributionApp, VLMaintenanceApp, RecvQubitOverVL, RecvClassicPacket, RecvQubitPacket
#from vl_maintenance import VLMaintenanceApp
#from vl_distro import VLEnabledDistributionApp
from qns.models.delay import NormalDelayModel, DelayModel, ConstantDelayModel, UniformDelayModel
from qns.entity.memory import QuantumMemory

from typing import Dict, List, Tuple
import numpy as np
import networkx as nx


# TODO SEEK OUT PARAMETRES FOR REALISTIC SETTING
# --------- PARAMETRES --------- 
light_speed = 299791458 
length = 200_000 # in m
memory_capacity = 50000

coherence_time = 1 # 1ms to 1s for crystal based stuff
decoherence_rate = 1 / coherence_time
memory_delay = 50e-6 # 50 microseconds for crystal based stuff

c_node_process_delay = 100e-6 # 100 microseconds
q_node_process_delay = 0.001 # 1 ms
init_fidelity = 0.99
# --------- PARAMETRES --------- 

channel_delay_model = NormalDelayModel(mean_delay=length/light_speed, std=(length/light_speed)/10)
memory_delay_model = NormalDelayModel(mean_delay=memory_delay, std=memory_delay/10) 
apps_list = [
    NodeProcessDelayApp(delay=q_node_process_delay, delay_event_list=(RecvQubitPacket)), 
    NodeProcessDelayApp(delay=c_node_process_delay, delay_event_list=(RecvClassicPacket)), 
    VLEnabledDistributionApp(init_fidelity=init_fidelity), 
    VLMaintenanceApp(),
]
memory_args = [{'delay': memory_delay_model, 'capacity': memory_capacity, 'decoherence_rate': decoherence_rate}]
qchannel_args = {'delay': channel_delay_model, 'length': length}
cchannel_args = {'delay': channel_delay_model, 'length': length}


class CustomLineTopology(LineTopology):
    def __init__(self, nodes_number):
        super().__init__(
            nodes_number, 
            nodes_apps=apps_list, 
            memory_args=memory_args, 
            qchannel_args=qchannel_args,
            cchannel_args=cchannel_args,
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
    def __init__(self):
        super().__init__(
            nodes_number=12, 
            memory_args=memory_args, 
            qchannel_args=qchannel_args, 
            cchannel_args=cchannel_args, 
            nodes_apps=apps_list
        )

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

    


class CustomWaxmanTopology(Topology):
    def __init__(self, nodes_number, seed):
        super().__init__(
            nodes_number=nodes_number,
            memory_args=memory_args,
            qchannel_args=qchannel_args,
            cchannel_args=cchannel_args,
            nodes_apps=apps_list
        )
        self.seed = seed

    def build(self) -> Tuple[List[VLAwareQNode], List[QuantumChannel]]:
        # create waxman_graph
        #waxman_graph = nx.waxman_graph(self.nodes_number, alpha=0.15, beta=0.3)
        waxman_graph = nx.barabasi_albert_graph(self.nodes_number, 1, seed=self.seed)

        # create nodes
        nl: List[VLAwareQNode] = [VLAwareQNode(f'n{i}') for i in range(self.nodes_number)]

        # create channels based on waxman edges
        ll = []
        for i, (u, v) in enumerate(waxman_graph.edges()):
            link = QuantumChannel(name=f'l{i}', **self.qchannel_args)
            ll.append(link)
            nl[u].add_qchannel(link)
            nl[v].add_qchannel(link)

        self._add_apps(nl)
        self._add_memories(nl)

        return nl, ll



class CustomRandomTopology(RandomTopology):
    def __init__(self, nodes_number, lines_number: int, nodes_apps: List[Application] = ..., qchannel_args: Dict = ..., cchannel_args: Dict = ..., memory_args: List[Dict] | None = ...):
        super().__init__(nodes_number, lines_number, nodes_apps, qchannel_args, cchannel_args, memory_args)

    def build(self) -> Tuple[List[VLAwareQNode] | List[QuantumChannel]]:
        nl: List[VLAwareQNode] = []
        ll: List[QuantumChannel] = []

        mat = [[0 for i in range(self.nodes_number)] for j in range(self.nodes_number)]

        if self.nodes_number >= 1:
            n = VLAwareQNode(f"n{1}")
            nl.append(n)

        for i in range(self.nodes_number - 1):
            n = VLAwareQNode(f"n{i+2}")
            nl.append(n)

            idx = get_randint(0, i)
            pn = nl[idx]
            mat[idx][i + 1] = 1
            mat[i + 1][idx] = 1

            link = QuantumChannel(name=f"l{idx+1},{i+2}", **self.qchannel_args)
            ll.append(link)
            pn.add_qchannel(link)
            n.add_qchannel(link)

        if self.lines_number > self.nodes_number - 1:
            for i in range(self.nodes_number - 1, self.lines_number):
                while True:
                    a = get_randint(0, self.nodes_number - 1)
                    b = get_randint(0, self.nodes_number - 1)
                    if mat[a][b] == 0:
                        break
                mat[a][b] = 1
                mat[b][a] = 1
                n = nl[a]
                pn = nl[b]
                link = QuantumChannel(name=f"l{a+1},{b+1}", **self.qchannel_args)
                ll.append(link)
                pn.add_qchannel(link)
                n.add_qchannel(link)

        self._add_apps(nl)
        self._add_memories(nl)
        return nl, ll

