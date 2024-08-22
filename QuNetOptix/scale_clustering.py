import qns.utils.log as log
import pandas as pd
from oracle import NetworkOracle
from metadata import SimData
from config import Config
from vl_animation import GraphAnimation
from config import Job
from qns.network.topology import RandomTopology
from vl_topo import CustomDoubleStarTopology, CustomLineTopology, CustomWaxmanTopology
from qns.network.protocol import EntanglementDistributionApp
from typing import List
import matplotlib.pyplot as plt
import os

from qns.utils.multiprocess import MPSimulations

if __name__ == '__main__': 
    ts=0
    te=10
    acc=1_000_000_000
    send_rate = 10
    vlink_send_rate_hz = 2*send_rate

    oracle = NetworkOracle()
    config = Config(
        ts=ts,
        te=te,
        acc=acc,
        vlink_send_rate=vlink_send_rate_hz,
        send_rate=send_rate,
        #topo=RandomTopology(nodes_number=20, lines_number=25),
        #topo=CustomDoubleStarTopology(),
        topo=CustomWaxmanTopology(alpha=0.15, beta=0.8, nodes_number=20),
        vlinks_active=False,
        continuous_distro=True,
        job = Job.random(session_count=4),
    )

    metadata: SimData = oracle.run(config, loglvl=log.logging.INFO)
    print(f'eps={metadata.throughput}; lat={metadata.generation_latency_avg}; fid={metadata.fidelity_avg}; fid_loss={metadata.fidelity_loss_avg}; succ={metadata.success_rate_p}; distros={metadata.success_count}/{metadata.send_count}; mem={metadata.remaining_mem_usage}; swaps={metadata.avg_swap_count}')

# TODO scaling in a realistic setting
# - avg swap count/path length of no vlinks and vlinks against growing network size
# - comparison to random topo (leverage the structure of existing infrastructure ...) (performance in a realistic setting)

# TODO performance at scale
# - avg throughput against vlinks vs no vlinks
#   - number of s,d pairs
#   - number of nodes
#   
# - avg latency against growing network size vs no vlinks
# - max latency against growing network size vs no vlinks
# - total latency against growing network size vs no vlinks

# TODO data
# - no vlinks, growing network size (waxman)
# - no vlinks, growing session count (waxman)
# - vlinks, growing network size (waxman)
# - vlinks, growing session count (waxman)

# - no vlinks, growing network size (random)
# - no vlinks, growing session count (random)
# - vlinks, growing network size (random)
# - vlinks, growing session count (random)


# traffic metrics (qubits sent, cmsg sent, swap count)
# fidelity (agg, avg)
# throughput (ep/s, latency agg/total/avg)


