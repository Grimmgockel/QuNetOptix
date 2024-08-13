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

    number_nodes = []

    throughput = []
    fidelity_avg = []
    fidelity_loss_avg = []

    vlink_throughput = []
    vlink_fidelity_avg = []
    vlink_fidelity_loss_avg = []

    # no vlinks
    for i in range(4, 30):
        ts=0
        te=10
        acc=1_000_000_000
        send_rate = 10
        vlink_send_rate_hz = 2*send_rate
        nodes_number = i

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
            #vlinks=[('n2', f'n{nodes_number-1}')],
            #schedule_n_vlinks=5,
        )

        metadata: SimData = oracle.run(config, loglvl=log.logging.INFO)
        print(f'n={i}; \t eps={metadata.throughput}; \t fid={metadata.fidelity_avg} \t succ={metadata.success_rate_p} \t distros={metadata.success_count}/{metadata.send_count}')

        number_nodes.append(i)
        throughput.append(metadata.throughput)
        fidelity_avg.append(metadata.fidelity_avg)
        fidelity_loss_avg.append(metadata.fidelity_loss_avg)

    # vlinks
    for i in range(4, 30):
        ts=0
        te=10
        acc=1_000_000_000
        send_rate = 10
        vlink_send_rate_hz = 2*send_rate
        nodes_number = i

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

        metadata: SimData = oracle.run(config, loglvl=log.logging.INFO)
        print(f'n={i}; \t eps={metadata.throughput}; \t fid={metadata.fidelity_avg} \t succ={metadata.success_rate_p} \t distros={metadata.success_count}/{metadata.send_count}')


        vlink_throughput.append(metadata.throughput)
        vlink_fidelity_avg.append(metadata.fidelity_avg)
        vlink_fidelity_loss_avg.append(metadata.fidelity_loss_avg)



    plt.style.use('fivethirtyeight')
    plt.style.use('grayscale')
    plt.figure(figsize=(12,6))
    plt.plot(number_nodes, throughput, label='no vlinks', marker='o', markersize=10, color='red')    
    plt.plot(number_nodes, vlink_throughput, label='vlinks', marker='o',  markersize=10, color='blue')    
    plt.xlabel('# of nodes', fontweight='bold')
    plt.ylabel('Througput (ep/s)', fontweight='bold')
    plt.legend()
    plt.show()



    plt.plot(number_nodes, fidelity_avg, label='no vlinks', marker='o', color='b')    
    plt.plot(number_nodes, vlink_fidelity_avg, label='vlinks', marker='s', color='r')    
    plt.xlabel('# of nodes')
    plt.ylabel('fidelity')
    plt.legend()
    plt.show()







        # TODO basic avg throughput/latency for fixed send rates against number of nodes (for w/ and w/o vlinks)
        # TODO find FINAL hardware details (delay models, decoherence models)
            # c node processing delay
            # q node processing delay
            # optical fibre communication delay
            # quantum memory delay
            # optical fibre decoherence
            # quantum memory decoherence

        # TODO absolute values of latency to demonstrate the onboarding process with different vlink send_rate mults, also 0.5x send-rate (ALSO PLOT NO VLINKS) (3d plot with number of nodes)
        # TODO something about congestion with send_rate, mem_cap and success_rate (ref paper on how mem cap influences throughput) (also 3d plot evt)
        # TODO something with fidelity

        # TODO ask chatgpt with all parametres for a calculation about how realistic that result is compared to the SimQN results
        # TODO maybe even reproduce the simqn results

        # FOR CLUSTERING
        # TODO start with lower memory cap, if bottlenecks appear, cite connection-oriented paper and increase mem (storytelling)
        # TODO really dig into k-means and plot against k










