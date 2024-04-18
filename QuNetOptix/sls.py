from qns.network.network import QuantumNetwork
from qns.network.protocol import EntanglementDistributionApp
from qns.network.protocol.entanglement_distribution import Transmit
from qns.simulator.ts import Time
from qns.entity.node import QNode
from qns.network.topology import Topology 
from qns.models.epr.werner import WernerStateEntanglement
from qns.network.route import RouteImpl 
from qns.network.topology.topo import ClassicTopology 
from qns.entity.memory import QuantumMemory
from qns.simulator.simulator import Simulator
from qns.entity.entity import Entity
from qns.simulator.event import Event, func_to_event
from qns.network.requests import Request
from qns.entity.node.app import Application
from qns.models.core import QuantumModel
from qns.entity.qchannel.qchannel import QuantumChannel, RecvQubitPacket
from qns.entity.cchannel.cchannel import ClassicChannel, ClassicPacket, RecvClassicPacket
from qns.network.topology import Topology, TreeTopology
from typing import Optional, Dict, List, Tuple, Union, Callable
import qns.utils.log as log
import os
import uuid



'''
Quantum network containing special request types called superlinks, that are considered for routing as entanglement links
'''
class VLNetwork(QuantumNetwork):
    def __init__(self, topo: Topology | None = None, route: RouteImpl | None = None, classic_topo: ClassicTopology | None = ClassicTopology.Empty, name: str | None = None):
        super().__init__(topo, route, classic_topo, name)

        self.vlinks: List[Request] = self.virtual_link_selection()


    def virtual_link_selection(self):
        # TODO at this point the network graph is built, based on the graph requests for virtual links need to be produced
        vlinks: List[Request] = []
        vlink_request = Request(src=self.get_node('n2'), dest=self.get_node('n9'), attr={'send_rate': 0.5})
        vlinks.append(vlink_request)
        return vlinks
        
    # TODO generate_lvl2_dot_file
    # TODO viz routing requests as path along the nodes

    def generate_lvl0_dot_file(self, filename: str): # physical graph
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dot_file_path = os.path.join(script_dir, filename)

        with open(dot_file_path, 'w') as f:
            f.write('graph {\n')
            for node in self.nodes:
                f.write(f'{node.name} [label=\"{node.name}\"];\n')
            f.write('\n')
            for qchannel in self.qchannels:
                f.write(f'{qchannel.node_list[0].name}--{qchannel.node_list[1].name};\n')
            f.write('\n')

            f.write('}')

    # TODO this happens after route tables are build => viz routing path
    # TODO this happens after vls => viz virtual link proximity as clusters
    def generate_lvl1_dot_file(self, filename: str): # physical graph + entanglement connectivity
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dot_file_path = os.path.join(script_dir, filename)

        with open(dot_file_path, 'w') as f:
            f.write('graph {\n')
            for node in self.nodes:
                f.write(f'{node.name} [label=\"{node.name}\"];\n')
            f.write('\n')
            for qchannel in self.qchannels:
                f.write(f'{qchannel.node_list[0].name}--{qchannel.node_list[1].name};\n')
            f.write('\n')

            for vlink in self.vlinks:
                f.write(f'{vlink.src.name}--{vlink.dest.name} [color=purple penwidth=5 constraint=False];\n')

            f.write('\n')
            for req in self.requests:
                route_result = self.query_route(req.src, req.dest)            
                path = route_result[0][2]
                for i, n in enumerate(path):
                    if i < len(path) - 1:
                        hop: str = f'{n.name}->{path[i+1].name} [color=red penwidth=2]\n'
                        f.write(hop)

                #path = route_result[2]
                #print(path)

            f.write('}')

    # TODO this happens after route tables are build => viz routing path
    def generate_lvl2_dot_file(self, filename: str): # virtual link enabled overlay graph
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dot_file_path = os.path.join(script_dir, filename)

        with open(dot_file_path, 'w') as f:
            f.write('graph {\n')
            for vlink in self.vlinks:
                src = vlink.src
                dest = vlink.dest
                f.write(f'{src.name} [label=\"{src.name}\"];\n')
                f.write(f'{dest.name} [label=\"{dest.name}\"];\n')
                f.write(f'{src.name}--{dest.name} [color=purple penwidth=5 constraint=False];\n')
                f.write('\n')

            f.write('}')


