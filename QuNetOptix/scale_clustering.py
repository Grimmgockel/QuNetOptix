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
        topo=CustomDoubleStarTopology(),
        continuous_distro=True,
        job = Job.custom(sessions=[('n0', 'n11')]),
    )

    metadata: SimData = oracle.run(config, loglvl=log.logging.INFO)
    print(f'eps={metadata.throughput}; lat={metadata.generation_latency_avg}; fid={metadata.fidelity_avg}; fid_loss={metadata.fidelity_loss_avg}; succ={metadata.success_rate_p}; distros={metadata.success_count}/{metadata.send_count}; mem={metadata.remaining_mem_usage}; swaps={metadata.avg_swap_count}')




