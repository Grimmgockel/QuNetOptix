from qns.entity.cchannel.cchannel import RecvClassicPacket
from qns.models.core.backend import QuantumModel
from qns.network.topology.topo import ClassicTopology
from qns.network.requests import Request
from qns.network.protocol.entanglement_distribution import EntanglementDistributionApp
from qns.simulator.simulator import Simulator
from qns.network.topology.treetopo import TreeTopology
from qns.network.topology.waxmantopo import WaxmanTopology
from qns.network.topology.linetopo import LineTopology 
from qns.entity.monitor.monitor import Monitor, MonitorEvent
from qns.entity.node.node import QNode
from qns.simulator.event import Event
from qns.entity.qchannel.qchannel import QuantumChannel, RecvQubitPacket
from qns.network.topology import RandomTopology
import qns.utils.log as log

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from vl_network import VLNetwork
from oracle import NetworkOracle
from config import Config
from config import Job


if __name__ == '__main__':

    oracle = NetworkOracle()

    for i in range(50, 301, 50):
        # arbitrary config struct
        config = Config(
            ts=0,
            te=50,
            acc=1000000,
            send_rate= 0.05,
            topo=RandomTopology(
                nodes_number=i,
                lines_number=int(i*1.5),
                qchannel_args={"delay": 0.05},
                cchannel_args={"delay": 0.05},
                memory_args=[{"capacity": 10}],
                nodes_apps=[base_routing.BaseApp(init_fidelity=0.99)],
            ),
            job=Job.random(int(i/2)),
        )
        print(config)
        oracle.run(config, loglvl=log.logging.INFO)

    fig, ax = plt.subplots()
    ax.plot(oracle.data['node_count'], oracle.data['throughput'], label=f'1Hz')

    ax.set_xlabel('node count')
    ax.set_ylabel('throughput (EP/s)')

    ax.set_title('throughput analysis')
    ax.legend()
    plt.show()





