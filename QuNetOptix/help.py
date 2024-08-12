import qns.utils.log as log
import pandas as pd
from oracle import NetworkOracle
from metadata import SimData
from config import Config
from vl_animation import GraphAnimation
from config import Job
from qns.network.topology import RandomTopology
from vl_topo import CustomDoubleStarTopology, CustomLineTopology
from qns.network.protocol import EntanglementDistributionApp
from typing import List
import matplotlib.pyplot as plt
import os

# TODO implement vlinks only occupying half of memory !!! vlinks are scheduling beyond cap/4
# TODO think about error/loss/decoherence models, entanglement models and hardware details -> make qubits decohere and restart the distro

# TODO make multicore work
# TODO overhaul plotting animation
# TODO implement vlink selection
# TODO implement custom waxman topology

# TODO implement overlooking vlinks OR NOT FIRST GET SOME RESULTS

from qns.utils.multiprocess import MPSimulations

if __name__ == '__main__': 
    ts=0
    te=20
    acc=1_000_000_000
    send_rate = 10
    vlink_send_rate_hz = 2*send_rate
    nodes_number = 4

    oracle = NetworkOracle()
    config = Config(
        ts=ts,
        te=te,
        acc=acc,
        vlink_send_rate=vlink_send_rate_hz,
        send_rate=send_rate,
        topo=CustomLineTopology(nodes_number=nodes_number),
        #job = Job.custom(sessions=[('n1', f'n{nodes_number}'), ('n1', f'n{nodes_number}')]),
        job = Job.custom(sessions=[('n1', f'n{nodes_number}')]),
        continuous_distro=True,
        vlinks=[('n2', f'n{nodes_number-1}')],
        #schedule_n_vlinks=5,
    )

    metadata: SimData = oracle.run(config, loglvl=log.logging.DEBUG)
    print(f'n={i}; \t eps={metadata.throughput}; \t fid={metadata.fidelity_avg} \t succ={metadata.success_rate_p} \t distros={metadata.success_count}/{metadata.send_count}')
