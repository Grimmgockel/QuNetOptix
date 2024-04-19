from qns.entity.cchannel.cchannel import RecvClassicPacket
from qns.models.core.backend import QuantumModel
from qns.network.topology.topo import ClassicTopology
from qns.network.topology import RandomTopology
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
import qns.utils.log as log

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from vls import VLNetwork
from oracle import NetworkOracle

# TODO implement viz and methodology for basic entanglement distribution via monitor on random topology DECIDE ON A TOPOLOGY
# -> think about error/loss/decoherence models, entanglement models and hardware details
# TODO SETUP CUSTOM CLUSTER TOPOLOGY FOR TESTING ROUTING OVER VIRTUAL LINKS
# - have virtual links as requests in the net (entanglement that doesn't decohere?)
# - each node has its next virtual link next to it, this is taken into account for routing 
# - implement routing with virtual links
# TODO implement selection algo for virtual links
if __name__ == '__main__':

    oracle = NetworkOracle()

    for i in range(10, 151, 10):
        s = Simulator(0, 10, accuracy=1000000)

        log.logger.setLevel(log.logging.INFO)
        log.install(s)

        nodes_number = i
        random = RandomTopology(
            nodes_number=nodes_number,
            lines_number=int(nodes_number*1.5),
            qchannel_args={"delay": 0.05},
            cchannel_args={"delay": 0.05},
            memory_args=[{"capacity": 10}],
            nodes_apps=[EntanglementDistributionApp(init_fidelity=0.99)],
        )
        net = VLNetwork(topo=random, classic_topo=ClassicTopology.All)
        net.build_route()
        net.random_requests(number=1, attr={'send_rate': 10})
        net.install(s)

        # install and run
        oracle.set_simulator(s)
        oracle.set_network(net)
        oracle.start_monitor()
        s.run()
        oracle.collect_monitor()

    oracle.plot()


