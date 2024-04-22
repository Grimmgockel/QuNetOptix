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
import qns.utils.log as log

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from vls import VLNetwork
from oracle import NetworkOracle

# TODO viz: sls and concurrency paper in one plot, second plot 3d fidelity
# TODO viz: implement custom Time class for millisecond plot
# TODO viz: look into random topo and waxman topo to FIND A TOPOLOGY WHERE MEANINGFUL PLOTS EMERGE
# TODO think about error/loss/decoherence models, entanglement models and hardware details
# TODO SETUP CUSTOM CLUSTER TOPOLOGY FOR TESTING ROUTING OVER VIRTUAL LINKS
# - have virtual links as requests in the net (entanglement that doesn't decohere?)
# - each node has its next virtual link next to it, this is taken into account for routing 
# - implement routing with virtual links
# TODO implement selection algo for virtual links
if __name__ == '__main__':

    oracle = NetworkOracle()

    for i in range(10, 151, 5):
        oracle.setup(i)
        oracle.run()

    oracle.plot()


