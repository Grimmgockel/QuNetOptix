from typing import Any
from qns.entity.monitor.monitor import Monitor, MonitorEvent
from qns.simulator.ts import Time
from qns.simulator.event import Event, func_to_event
from qns.network.protocol import EntanglementDistributionApp
from qns.entity.cchannel import RecvClassicPacket
import os
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class NetworkOracle():
    def __init__(self) -> None:
        self.sim=None
        self.success_data = pd.DataFrame()

    def set_simulator(self, s):
        self.sim=s

    def set_network(self, n):
        self.net=n

    def start_monitor(self, period_time=1):
        assert(self.sim is not None)
        assert(self.net is not None)

        self.m = Monitor(network=self.net)

        # attributions
        self.m.add_attribution(name="success", calculate_func=lambda s, n, e: (
            [req.src.apps[0].success_count for req in n.requests][0]
        ))

        # when to collect attributions
        self.m.at_start()
        self.m.at_period(period_time)
        self.m.at_finish()

        # install
        self.m.install(self.sim)

    def collect_monitor(self):
        assert(self.sim is not None)
        assert(self.net is not None)

        node_count = len(self.net.nodes)
        df_3d = self.m.data.assign(node_count=node_count)
        self.success_data = pd.concat([self.success_data, df_3d], ignore_index=True)
        
    '''
    Plot data
    '''
    def plot(self):
        # TODO 3d plot for fidelity
        # TODO 2d plots for throughput
        x = self.success_data['node_count']
        y = self.success_data['time']
        z = self.success_data['success']

        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(x, y, z, c='b', marker='o')
        #surf = ax.plot_surface(x,y,z,cmap='viridis')
        #fig.colorbar(surf)

        ax.set_xlabel('# of nodes')
        ax.set_ylabel('time in s')
        ax.set_zlabel('# of distributions')
        ax.set_title("3d plot")

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
