from qns.network.network import QuantumNetwork
from qns.simulator.simulator import Simulator
from qns.network.topology.topo import ClassicTopology
from qns.entity.monitor import Monitor
import qns.utils.log as log
from typing import List, Tuple

from vl_network import VLNetwork
from vlaware_qnode import VLAwareQNode
from config import Config
from metadata import SimData
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

    def run(self, config: Config, loglvl: int = log.logging.INFO) -> SimData:

        # Simulator
        self._sim = Simulator(config.ts, config.te, accuracy=config.acc)

        # Logger
        log.logger.setLevel(loglvl)
        log.install(self._sim)

        # Network
        metadata = SimData()
        self._net: VLNetwork = VLNetwork(topo=config.topo, metadata=metadata, continuous_distro=config.continuous_distro, schedule_n_vlinks=config.schedule_n_vlinks, custom_vlinks=config.vlinks, vlink_send_rate=config.vlink_send_rate)
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
        self._monitor = Monitor(network=self._net)

        # get from config, no change during sim
        self._monitor.add_attribution(name="sim_time_s", calculate_func=lambda s, n, e: config.te)
        self._monitor.add_attribution(name="send_rate", calculate_func=lambda s, n, e: config.send_rate)
        self._monitor.add_attribution(name="mem_cap", calculate_func=lambda s, n, e: config.topo.memory_args[0]['capacity'])
        self._monitor.add_attribution(name="session_count", calculate_func=lambda s, n, e: config.job.session_count)
        self._monitor.add_attribution(name="node_count", calculate_func=lambda s, n, e: len(self._net.nodes))

        # performance primitives
        self._monitor.add_attribution(name="success_count", calculate_func=lambda s, n, e: sum(app.success_count for req in n.requests for app in req.src.apps if app.app_name == 'distro'))
        self._monitor.add_attribution(name="vlink_success_count", calculate_func=lambda s, n, e: sum(app.success_count for req in n.vlinks for app in req.src.apps if app.app_name == 'maint'))
        self._monitor.add_attribution(name="send_count", calculate_func=lambda s, n, e: sum(app.send_count for req in n.requests for app in req.src.apps if app.app_name == 'distro'))
        self._monitor.add_attribution(name="vlink_send_count", calculate_func=lambda s, n, e: sum(app.send_count for req in n.vlinks for app in req.src.apps if app.app_name == 'maint'))
        self._monitor.add_attribution(name="remaining_mem_usage", calculate_func=lambda s, n, e: sum(app.memory._usage for node in n.nodes for app in node.apps))
        self._monitor.add_attribution(name="generation_latency_agg", calculate_func=lambda s, n, e: sum(app.generation_latency_agg for req in n.requests for app in req.src.apps if app.app_name == 'distro'))
        #self._monitor.add_attribution(name="fidelity_agg", calculate_func=self._gather_throughput)

        # TODO primitive or higher level? 
        #self._monitor.add_attribution(name="mem_utilization_p", calculate_func=lambda s, n, e: len(self._net.nodes))
        #self._monitor.add_attribution(name="generation_latency_avg", calculate_func=self._gather_gen_latency)
        #self._monitor.add_attribution(name="generation_latency_max", calculate_func=self._gather_gen_latency)
        #self._monitor.add_attribution(name="throughput_avg", calculate_func=self._gather_throughput)
        #self._monitor.add_attribution(name="congestion_p", calculate_func=self._gather_throughput) (send_rate vs throughput normed to be between 0% and 100%)
        #self._monitor.add_attribution(name="success_rate", calculate_func=self._gather_throughput)
        #self._monitor.add_attribution(name="fidelity_avg", calculate_func=self._gather_throughput)
        #self._monitor.add_attribution(name="fidelity_loss", calculate_func=self._gather_throughput)

        self._monitor.at_finish() # when to collect
        self._monitor.install(self._sim)
    
        # run sim and concat data to pd dataframe
        self._sim.run()

        metadata.df = self._monitor.data
        return metadata 

    def entanglement_animation(self, filename: str, fps: int) -> GraphAnimation:
        return GraphAnimation(filename, fps, self._net.physical_graph.graph, self._net.metadata.entanglement_log)
