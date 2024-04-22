from typing import Any
from qns.entity.monitor.monitor import Monitor, MonitorEvent
from qns.network.topology import RandomTopology
from qns.simulator.ts import Time
from qns.simulator.event import Event, func_to_event
from qns.network.protocol import EntanglementDistributionApp
from qns.entity.cchannel import RecvClassicPacket
from qns.network.network import QuantumNetwork
from qns.simulator.simulator import Simulator
from qns.network.topology.topo import Topology
from qns.network.topology.topo import ClassicTopology
import qns.utils.log as log

from vls import VLNetwork
from base_routing import BaseApp

import os
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from typing import Optional

class NetworkOracle():
    def __init__(self) -> None:
        self._sim: Optional[Simulator] = None
        self._net: Optional[QuantumNetwork] = None
        self._monitor: Optional[Monitor] = None
        self.data = pd.DataFrame()

    # TODO make setup more general with network.json file
    def run(self, sim: Simulator, topo: Topology, 
            request_count: int = 1, send_rate: int = 10, 
            loglvl: int = log.logging.INFO):

        # Simulator
        self._sim = sim

        # Logger
        log.logger.setLevel(loglvl)
        log.install(self._sim)

        # Network
        self._net = VLNetwork(topo=topo, classic_topo=ClassicTopology.All)
        self._net.build_route()
        self._net.random_requests(number=request_count, attr={'send_rate': send_rate})
        self._net.install(self._sim)

        # Monitor
        self._monitor = Monitor(network=self._net)

        self._monitor.add_attribution(name="success", calculate_func=lambda s, n, e: (
            [req.src.apps[0].success_count for req in n.requests][0]
        ))
        self._monitor.add_attribution(name="node_count", calculate_func=lambda s, n, e: (
            len(self._net.nodes)
        ))
        self._monitor.add_attribution(name="generation_latency_avg", calculate_func=self._gather_gen_latency)

        self._monitor.at_finish()
        self._monitor.install(self._sim)

        log.info(f'start new sim') # TODO more detail, 
        self._sim.run()
        self.data = pd.concat([self.data, self._monitor.data], ignore_index=True)

    def _gather_gen_latency(self, s, n, e):
        agg: float = 0.0
        count: int = 0
        for node in self._net.nodes:
            if node.apps[0].generation_latency > 0:
                agg += node.apps[0].generation_latency 
                count += 1
        running_avg: float = agg / count
        return running_avg
        
    '''
    Plot data
    '''
    def plot(self):
        # TODO get cooler plot framework than matplotlib
        # TODO 3d plot for fidelity
        # TODO 2d plots for throughput against ? (concurrency paper)
        # TODO 2d plots for latency against cost budget, edge density, # of nodes, # of sd pairs (sls paper)

        x = self.data['node_count']
        y = self.data['generation_latency_avg']

        plt.plot(x, y)
        plt.xlabel("# of nodes")
        plt.ylabel("average gen latency")

        plt.title("2d plot")

        plt.show()

    '''
    Vizualize network level as dot file (https://arxiv.org/abs/2306.05982)
    '''
    def generate_dot_file(self, filename: str, lvl=0): 
        if lvl < 0 or lvl > 2:
            print("Invalid plot level")

        script_dir = os.path.dirname(os.path.abspath(__file__))
        dot_file_path = os.path.join(script_dir, filename)

        with open(dot_file_path, 'w') as f:
            f.write('graph {\n')

            if lvl == 0 or lvl == 1:
                for node in self.network.nodes:
                    f.write(f'{node.name} [label=\"{node.name}\"];\n')
                f.write('\n')

                for qchannel in self.network.qchannels:
                    f.write(f'{qchannel.node_list[0].name}--{qchannel.node_list[1].name};\n')

            f.write('\n')

            if lvl == 1:
                for vlink in self.network.vlinks:
                    print(type(vlink))
                    print(self.network.vlinks)
                    f.write(f'{vlink.src.name}--{vlink.dest.name} [color=purple penwidth=5 constraint=False];\n')

            if lvl == 2:
                for vlink in self.network.vlinks:
                    src = vlink.src
                    dest = vlink.dest
                    f.write(f'{src.name} [label=\"{src.name}\"];\n')
                    f.write(f'{dest.name} [label=\"{dest.name}\"];\n')
                    f.write(f'{src.name}--{dest.name} [color=purple penwidth=5 constraint=False];\n')
                    f.write('\n')

            f.write('}')




