from qns.network.network import QuantumNetwork
from qns.simulator.simulator import Simulator
from qns.network.topology.topo import ClassicTopology
from qns.entity.monitor import Monitor
import qns.utils.log as log

from vl_network import VLNetwork
from config import Config

import os
from typing import Any 
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

    def run(self, config: Config, loglvl: int = log.logging.INFO, monitor: bool = True):

        # Simulator
        self._sim = Simulator(config.ts, config.te, accuracy=config.acc)

        # Logger
        log.logger.setLevel(loglvl)
        log.install(self._sim)

        # Network
        self._net = VLNetwork(topo=config.topo)
        self._net.build_route()
        if config.job.sessions is None:
            self._net.random_requests(number=config.job.session_count, attr={'send_rate': config.send_rate})
        else: # custom sessions
            for session in config.job.sessions:
                self._net.add_request(
                    src=self._net.get_node(session[0]),
                    dest=self._net.get_node(session[1]),
                    attr={'send_rate': config.send_rate}
                )
        self._net.install(self._sim)

        # Monitor
        if monitor:
            self._monitor = Monitor(network=self._net)

            self._monitor.add_attribution(name="success", calculate_func=lambda s, n, e: [req.src.apps[0].success_count for req in n.requests][0])
            self._monitor.add_attribution(name="node_count", calculate_func=lambda s, n, e: len(self._net.nodes))
            self._monitor.add_attribution(name="generation_latency_avg", calculate_func=self._gather_gen_latency)
            self._monitor.add_attribution(name="session_count", calculate_func=lambda s, n, e: config.job.session_count)
            self._monitor.add_attribution(name="send_rate", calculate_func=lambda s, n, e: config.send_rate)
            self._monitor.add_attribution(name="mem_cap", calculate_func=lambda s, n, e: config.topo.memory_args[0]['capacity'])
            self._monitor.add_attribution(name="throughput", calculate_func=self._gather_throughput)
            # TODO success_count / send_count (success_rate)
    
            self._monitor.at_finish() # when to collect
            self._monitor.install(self._sim)
    
        # run sim and concat data to pd dataframe
        self._sim.run()

        if monitor: 
            self.data = pd.concat([self.data, self._monitor.data], ignore_index=True)

    def _gather_gen_latency(self, s, n, e):
        agg_gen_latency: float = 0.0
        count: int = 0
        for node in self._net.nodes:
            if node.apps[0].generation_latency_avg > 0:
                agg_gen_latency += node.apps[0].generation_latency_avg
                count += 1
        try:
            running_avg: float = agg_gen_latency / count
        except ZeroDivisionError:
            return -1
        return running_avg

    def _gather_throughput(self, s, n, e):
        agg_success_count = 0
        for node in self._net.nodes:
            agg_success_count += node.apps[0].success_count
        throughput = float(agg_success_count) / s.te.sec
        return throughput


    '''
    Vizualize network level as dot file (https://arxiv.org/abs/2306.05982)
    TODO plot with networkx
    '''
    def generate_dot_file(self, filename: str, lvl=0):
        if lvl not in range(3):
            print("Invalid plot level")
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        dot_file_path = os.path.join(script_dir, filename)

        with open(dot_file_path, 'w') as f:
            f.write('graph {\n')

            if lvl in [0, 1]:
                for node in self._net.nodes:
                    f.write(f'{node.name} [label="{node.name}"];\n')
                f.write('\n')

                for qchannel in self._net.qchannels:
                    f.write(f'{qchannel.node_list[0].name}--{qchannel.node_list[1].name};\n')

            f.write('\n')

            if lvl == 1:
                for vlink in self._net.vlinks:
                    f.write(f'{vlink.src.name}--{vlink.dest.name} [color=purple penwidth=5 constraint=False];\n')

            if lvl == 2:
                for vlink in self._net.vlinks:
                    src = vlink.src
                    dest = vlink.dest
                    f.write(f'{src.name} [label="{src.name}"];\n')
                    f.write(f'{dest.name} [label="{dest.name}"];\n')
                    f.write(f'{src.name}--{dest.name} [color=purple penwidth=5 constraint=False];\n')
                    f.write('\n')

            if lvl == 0:
                for req in self._net.requests:
                    path = self._net.query_route(src=req.src, dest=req.dest)[0][-1]
                    for src, dest in zip(path, path[1:]):
                        f.write(f'{src.name}--{dest.name} [color=red penwidth=1 constraint=False];\n')

            f.write('}')


