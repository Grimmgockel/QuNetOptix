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
    swaps = []
    q_message_counts = []
    c_message_counts = []

    vlink_throughput = []
    vlink_fidelity_avg = []
    vlink_fidelity_loss_avg = []
    vlink_swaps = []
    vlink_q_message_counts = []
    vlink_c_message_counts = []

    # no vlinks
    for i in range(5, 20):
        ts=0
        te=10
        acc=1_000_000_000
        send_rate = 10
        vlink_send_rate_hz = 1.5*send_rate
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
        print(f'n={i}; eps={metadata.throughput}; lat={metadata.generation_latency_avg}; fid={metadata.fidelity_avg}; fid_loss={metadata.fidelity_loss_avg}; succ={metadata.success_rate_p}; distros={metadata.success_count}/{metadata.send_count}; mem={metadata.remaining_mem_usage}; swaps={metadata.avg_swap_count}')


        number_nodes.append(i)
        throughput.append(metadata.throughput)
        fidelity_avg.append(metadata.fidelity_avg)
        fidelity_loss_avg.append(metadata.fidelity_loss_avg)
        swaps.append(metadata.avg_swap_count)
        c_message_counts.append(metadata.c_message_count)
        q_message_counts.append(metadata.q_message_count)

    # vlinks
    for i in range(5, 20):
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
        print(f'n={i}; eps={metadata.throughput}; lat={metadata.generation_latency_avg}; fid={metadata.fidelity_avg}; fid_loss={metadata.fidelity_loss_avg}; succ={metadata.success_rate_p}; distros={metadata.success_count}/{metadata.send_count}; mem={metadata.remaining_mem_usage}; swaps={metadata.avg_swap_count}')


        vlink_throughput.append(metadata.throughput)
        vlink_fidelity_avg.append(metadata.fidelity_avg)
        vlink_fidelity_loss_avg.append(metadata.fidelity_loss_avg)
        vlink_swaps.append(metadata.avg_swap_count)
        vlink_c_message_counts.append(metadata.c_message_count)
        vlink_q_message_counts.append(metadata.q_message_count)

    plt.style.use('fivethirtyeight')
    plt.style.use('grayscale')
    marker = None
    markersize = None
    linewidth = 5

    # THROUGHPUT
    plt.figure(figsize=(12,6))
    plt.plot(number_nodes, throughput, label='no vlinks', marker=marker, markersize=markersize, color='red', linewidth=linewidth)    
    plt.plot(number_nodes, vlink_throughput, label='vlinks', marker=marker,  markersize=markersize, color='blue', linewidth=linewidth)    
    plt.xlabel('# of nodes', fontweight='bold')
    plt.ylabel('Througput (ep/s)', fontweight='bold')
    plt.legend()
    plt.ylim(0, 150)
    plt.tight_layout()
    plt.savefig('plots/throughput_poc.svg', format='svg')

    # FIDELITY
    plt.figure(figsize=(12,6))
    plt.plot(number_nodes, fidelity_avg, label='no vlinks', marker=marker, markersize=markersize, color='b', linewidth=linewidth)    
    plt.plot(number_nodes, vlink_fidelity_avg, label='vlinks', marker=marker, markersize=markersize, color='r', linewidth=linewidth)    
    plt.xlabel('# of nodes')
    plt.ylabel('fidelity')
    plt.ylim(0, 1)
    plt.legend()
    plt.tight_layout()
    plt.savefig('plots/fidelity_poc.svg', format='svg')

    # TRAFFIC
    fig, axs = plt.subplots(3, 2, figsize=(12, 12))
    line1, = axs[0, 0].plot(number_nodes, c_message_counts, label='no vlinks', color='r')
    axs[0, 0].set_xlabel('# of nodes')
    axs[0, 0].set_ylabel('classical messages sent')
    axs[0, 0].set_ylim(bottom=0)
    axs[0, 0].legend()
    line2, = axs[0, 1].plot(number_nodes, vlink_c_message_counts, label='vlinks', color='b')
    axs[0, 1].set_xlabel('# of nodes')
    axs[0, 1].set_ylabel('classical messages sent')
    axs[0, 1].set_ylim(bottom=0)
    axs[0, 1].legend()
    line3, = axs[1, 0].plot(number_nodes, q_message_counts, label='no vlinks', color='r')
    axs[1, 0].set_xlabel('# of nodes')
    axs[1, 0].set_ylabel('qubits sent')
    axs[1, 0].set_ylim(bottom=0)
    axs[1, 0].legend()
    line4, = axs[1, 1].plot(number_nodes, vlink_q_message_counts, label='vlinks', color='b')
    axs[1, 1].set_xlabel('# of nodes')
    axs[1, 1].set_ylabel('qubits sent')
    axs[1, 1].set_ylim(bottom=0)
    axs[1, 1].legend()
    axs[2, 0].plot(number_nodes, swaps, label='no vlinks', color='r')
    axs[2, 0].set_xlabel('# of nodes')
    axs[2, 0].set_ylabel('# of swap\noperations')
    axs[2, 0].set_ylim(bottom=0)
    axs[2, 0].legend()
    axs[2, 1].plot(number_nodes, vlink_swaps, label='vlinks', color='b')
    axs[2, 1].set_xlabel('# of nodes')
    axs[2, 1].set_ylabel('# of swap\noperations')
    axs[2, 1].set_ylim(bottom=0)
    axs[2, 1].legend()
    plt.tight_layout()
    plt.savefig('plots/traffic.svg', format='svg')


        # TODO start distro as soon as vlinks are established
        # TODO classical and quantum communication traffic
        # TODO avg swap number in text only, show simple calculation for how may swaps (use this as justification for something)


            # TODO basic avg throughput/latency for fixed send rates against number of nodes (for w/ and w/o vlinks)
            # TODO find FINAL hardware details (delay models, decoherence models)
                # c node processing delay
                # q node processing delay
                # optical fibre communication delay
                # quantum memory delay
                # optical fibre decoherence
                # quantum memory decoherence

            # FOR CLUSTERING
            # TODO start with lower memory cap, if bottlenecks appear, cite connection-oriented paper and increase mem (storytelling)
            # TODO really dig into k-means and plot against k










