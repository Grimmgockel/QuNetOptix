from qns.network.network import QuantumNetwork
from qns.simulator.simulator import Simulator
from qns.network.topology.topo import ClassicTopology
from qns.entity.monitor import Monitor
import qns.utils.log as log

from vl_network import VLNetwork
from config import Config
from metadata import MetaData
from vl_net_graph import GraphAnimation

import os
from typing import Any 
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from typing import Optional

class NetworkOracle():
    def __init__(self) -> None:
        self._sim: Optional[Simulator] = None
        self._net: Optional[VLNetwork] = None
        self._monitor: Optional[Monitor] = None
        self.data = pd.DataFrame()

    def run(self, config: Config, loglvl: int = log.logging.INFO, continuous_distro: bool = True, n_vlinks: Optional[int] = None, monitor: bool = True) -> MetaData:

        # Simulator
        self._sim = Simulator(config.ts, config.te, accuracy=config.acc)

        # Logger
        log.logger.setLevel(loglvl)
        log.install(self._sim)

        # Network
        metadata = MetaData()
        self._net: VLNetwork = VLNetwork(topo=config.topo, metadata=metadata, continuous_distro=continuous_distro, n_vlinks=n_vlinks, vlink_send_rate=config.vlink_send_rate)
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
        metadata.remaining_memory_usage = sum(1 for node in self._net.nodes for app in node.apps if app.memory._usage > 0)

        if monitor: 
            self.data = pd.concat([self.data, self._monitor.data], ignore_index=True)

        return metadata        

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

    def entanglement_animation(self, filename: str, fps: int) -> GraphAnimation:
        return GraphAnimation(filename, fps, self._net.physical_graph.graph, self._net.metadata.entanglement_log)
