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

from vls import VLNetwork
from oracle import NetworkOracle
from config import Config
import base_routing



# TODO ROUTING
# have virtual links as requests in the net (entanglement that doesn't decohere?)
# each node has its next virtual link next to it, this is taken into account for routing 
# implement routing with virtual links

# TODO VIRTUAL LINK SELECTION
# implement selection algo for virtual links

# TODO VIZ
# viz: look into random topo and waxman topo to FIND A TOPOLOGY WHERE MEANINGFUL PLOTS EMERGE
# get basic plot for 2 curves comparing base routing with custom routing
# look into routing papers for more meaningful methodology
# look into docs for multicore sim
# save experiments into results.csv
# get cooler plot framework than matplotlib
# think about error/loss/decoherence models, entanglement models and hardware details
if __name__ == '__main__':

    oracle = NetworkOracle()

    for i in range(50, 301, 50):
        # arbitrary config struct
        config = Config(
            te=0,
            ts=50,
            acc=1000000,
            node_count=i,
            line_count=int(i*1.5),
            qchannel_delay = 0.05,
            cchannel_delay= 0.05,
            mem_cap = 10,
            sessions= 50,
            send_rate= 0.05,
            app = base_routing.BaseApp(init_fidelity=0.99),
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





