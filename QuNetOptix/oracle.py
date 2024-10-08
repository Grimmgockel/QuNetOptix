from qns.network.network import QuantumNetwork
import random
from qns.simulator.simulator import Simulator
from qns.network.topology.topo import ClassicTopology
from qns.entity.monitor import Monitor
import qns.utils.log as log
from typing import List, Tuple

from vl_network import VLNetwork
from vlaware_qnode import VLAwareQNode
from config import Config
from metadata import SimData
from vl_animation import GraphAnimation

import os
from typing import Any 
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from typing import Optional
import networkx as nx

class NetworkOracle():
    def __init__(self) -> None:
        self._sim: Optional[Simulator] = None
        self._net: Optional[VLNetwork] = None
        self._monitor: Optional[Monitor] = None
        self.data = pd.DataFrame()

    def get_random_requests(self, graph: nx.Graph, n: int, seed: int = None):
        if seed is not None:
            random.seed(seed)
        path_lengths = dict(nx.all_pairs_shortest_path_length(graph))
        pairs_with_distances = [
            (source, target, dist)
            for source, targets in path_lengths.items()
            for target, dist in targets.items()
            if source != target
        ]
        weighted_pairs = [(source, target) for source, target, dist in pairs_with_distances if dist > 0]
        weights = [dist**2 for _, _, dist in pairs_with_distances if dist > 0]
        selected_pairs = random.choices(weighted_pairs, weights=weights, k=n)
        return selected_pairs

    def run(self, config: Config, loglvl: int = log.logging.INFO) -> SimData:

        # Simulator
        self._sim = Simulator(config.ts, config.te, accuracy=config.acc)

        # Logger
        log.logger.setLevel(loglvl)
        log.install(self._sim)

        # Network
        metadata = SimData()
        self._net: VLNetwork = VLNetwork(topo=config.topo, metadata=metadata, continuous_distro=config.continuous_distro, schedule_n_vlinks=config.schedule_n_vlinks, custom_vlinks=config.vlinks, vlink_send_rate=config.vlink_send_rate, vls=config.vls, session_count=config.job.session_count)
        self._net.build_route()
        if config.job.sessions is None:
            #self._net.random_requests(number=config.job.session_count, attr={'send_rate': config.send_rate})
            sessions = self.get_random_requests(self._net.physical_graph.graph, config.job.session_count, config.session_seed)
            for session in sessions:
                self._net.add_request(
                    src=self._net.get_node(f'n{session[0].index}'),
                    dest=self._net.get_node(f'n{session[1].index}'),
                    attr={'send_rate': config.send_rate}
                )

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
        self._monitor.add_attribution(name="success_count", calculate_func=lambda s, n, e: sum(app.success_count for req in n.requests for app in req.src.apps if hasattr(app, 'app_name') and app.app_name == 'distro'))
        self._monitor.add_attribution(name="vlink_success_count", calculate_func=lambda s, n, e: sum(app.success_count for req in n.vlinks for app in req.src.apps if hasattr(app, 'app_name') and app.app_name == 'maint'))
        self._monitor.add_attribution(name="send_count", calculate_func=lambda s, n, e: sum(app.send_count for req in n.requests for app in req.src.apps if hasattr(app, 'app_name') and app.app_name == 'distro'))
        self._monitor.add_attribution(name="vlink_send_count", calculate_func=lambda s, n, e: sum(app.send_count for req in n.vlinks for app in req.src.apps if hasattr(app, 'app_name') and app.app_name == 'maint'))
        self._monitor.add_attribution(name="remaining_mem_usage", calculate_func=lambda s, n, e: sum(app.memory._usage for node in n.nodes for app in node.apps if hasattr(app, 'memory')))
        self._monitor.add_attribution(name="swap_count", calculate_func=lambda s, n, e: sum(app.swap_count for node in n.nodes for app in node.apps if hasattr(app, 'app_name') and app.app_name == 'distro'))
        self._monitor.add_attribution(name="generation_latency_agg", calculate_func=lambda s, n, e: sum(app.generation_latency_agg for req in n.requests for app in req.src.apps if hasattr(app, 'app_name') and app.app_name == 'distro'))
        self._monitor.add_attribution(name="fidelity_agg", calculate_func=lambda s, n, e: sum(app.fidelity_agg for req in n.requests for app in req.src.apps if hasattr(app, 'app_name') and app.app_name == 'distro'))
        self._monitor.add_attribution(name="q_message_count", calculate_func=lambda s, n, e: sum(app.q_message_count for node in n.nodes for app in node.apps if hasattr(app, 'app_name') and (app.app_name == 'distro' or app.app_name == 'maint')))
        self._monitor.add_attribution(name="c_message_count", calculate_func=lambda s, n, e: sum(app.c_message_count for node in n.nodes for app in node.apps if hasattr(app, 'app_name') and (app.app_name == 'distro' or app.app_name == 'maint')))

        #self._monitor.add_attribution(
            #name="gen_latencies", 
            #calculate_func=lambda s, n, e: 
        #)

        # TODO primitive or higher level? 
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
