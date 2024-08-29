import qns.utils.log as log
import pandas as pd
import pandas as pd
import time
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
import random

from qns.utils.multiprocess import MPSimulations

# TODO random requests need to have big distance
# TODO vlinks need to be readily available at the start
    # maintenance app established ONE vlink per request and upkeeps the fidelity
# TODO parallel sims

if __name__ == '__main__': 
    ts=0
    te=20
    acc=1_000_000_000
    send_rate = 10
    vlink_send_rate_hz = 3*send_rate

    number_nodes = []
    sessions = []

    throughput = []
    vlink_throughput = []
    genlat_max = []
    genlat_min = []
    genlat_agg = []
    genlat_avg = []
    vlink_genlat_max = []
    vlink_genlat_min = []
    vlink_genlat_agg = []
    vlink_genlat_avg = []

    fidelity_avg = []
    vlink_fidelity_avg = []
    fidelity_loss_avg = []
    vlink_fidelity_loss_avg = []

    swaps = []
    vlink_swaps = []
    c_message_counts = []
    vlink_c_message_counts = []
    q_message_counts = []
    vlink_q_message_counts = []

    start_time = time.time()

    # no vlinks, growing network size, waxman
    for i in range(20,21,10):
        topo=CustomWaxmanTopology(nodes_number=i, seed=i) # same seed for same nodes number
        max_sessions = i/2
        print(f'node_count={i}')
        for k in range(2, 9, 6): # use 20% and 80% utilization
            # get sessions
            utilization = k/10
            session_count = int(utilization * max_sessions)
            if session_count <= 1:
                session_count += 1

            print(f'\tsessions_count={session_count} ({int(utilization*100)}%)')

            throughput_agg = 0
            genlat_max_agg = 0
            genlat_min_agg = 0
            genlat_agg_agg = 0
            genlat_avg_agg = 0
            fidelity_avg_agg = 0
            fidelity_loss_avg_agg = 0
            swaps_agg = 0
            c_message_counts_agg = 0
            q_message_counts_agg = 0

            vlink_throughput_agg = 0
            vlink_genlat_max_agg = 0
            vlink_genlat_min_agg = 0
            vlink_genlat_agg_agg = 0
            vlink_genlat_avg_agg = 0
            vlink_fidelity_avg_agg = 0
            vlink_fidelity_loss_avg_agg = 0
            vlink_swaps_agg = 0
            vlink_c_message_counts_agg = 0
            vlink_q_message_counts_agg = 0

            rounds = 2
            for j in range(rounds):
                print(f'\t\tround ({j+1}/{rounds})\ttime={(time.time()-start_time):2f}')
                jobs = Job.random(session_count=session_count) # sessions have to be the same to be comparable

                # NO VLINKS
                oracle = NetworkOracle()
                config = Config(
                    ts=ts,
                    te=te,
                    acc=acc,
                    vlink_send_rate=vlink_send_rate_hz,
                    send_rate=send_rate,
                    topo=topo,
                    vls=False,
                    continuous_distro=True,
                    job = jobs,
                )
                metadata: SimData = oracle.run(config, loglvl=log.logging.INFO)

                throughput_agg += metadata.throughput
                genlat_max_agg += metadata.gl_max
                genlat_min_agg += metadata.gl_min
                genlat_agg_agg += metadata.generation_latency_agg
                genlat_avg_agg += metadata.generation_latency_avg
                fidelity_avg_agg += metadata.fidelity_avg
                fidelity_loss_avg_agg += metadata.fidelity_loss_avg
                swaps_agg += metadata.avg_swap_count
                c_message_counts_agg += metadata.c_message_count
                q_message_counts_agg += metadata.q_message_count

                # VLINKS
                oracle = NetworkOracle()
                config = Config(
                    ts=ts,
                    te=te,
                    acc=acc,
                    vlink_send_rate=vlink_send_rate_hz,
                    send_rate=send_rate,
                    topo=topo,
                    vls=True,
                    continuous_distro=True,
                    job = jobs,
                )
                metadata: SimData = oracle.run(config, loglvl=log.logging.INFO)

                vlink_throughput_agg += metadata.throughput
                vlink_genlat_max_agg += metadata.gl_max
                vlink_genlat_min_agg += metadata.gl_min
                vlink_genlat_agg_agg += metadata.generation_latency_agg
                vlink_genlat_avg_agg += metadata.generation_latency_avg
                vlink_fidelity_avg_agg += metadata.fidelity_avg
                vlink_fidelity_loss_avg_agg += metadata.fidelity_loss_avg
                vlink_swaps_agg += metadata.avg_swap_count
                vlink_c_message_counts_agg += metadata.c_message_count
                vlink_q_message_counts_agg += metadata.q_message_count



            number_nodes.append(i)
            sessions.append(session_count)
            throughput.append(throughput_agg/rounds)
            genlat_max.append(genlat_max_agg/rounds)
            genlat_min.append(genlat_min_agg/rounds)
            genlat_agg.append(genlat_agg_agg/rounds)
            genlat_avg.append(genlat_avg_agg/rounds)
            fidelity_avg.append(fidelity_avg_agg/rounds)
            fidelity_loss_avg.append(fidelity_loss_avg_agg/rounds)
            swaps.append(swaps_agg/rounds)
            c_message_counts.append(c_message_counts_agg/rounds)
            q_message_counts.append(q_message_counts_agg/rounds)

            vlink_throughput.append(vlink_throughput_agg/rounds)
            vlink_genlat_max.append(vlink_genlat_max_agg/rounds)
            vlink_genlat_min.append(vlink_genlat_min_agg/rounds)
            vlink_genlat_agg.append(vlink_genlat_agg_agg/rounds)
            vlink_genlat_avg.append(vlink_genlat_avg_agg/rounds)
            vlink_fidelity_avg.append(vlink_fidelity_avg_agg/rounds)
            vlink_fidelity_loss_avg.append(vlink_fidelity_loss_avg_agg/rounds)
            vlink_swaps.append(vlink_swaps_agg/rounds)
            vlink_c_message_counts.append(vlink_c_message_counts_agg/rounds)
            vlink_q_message_counts.append(vlink_q_message_counts_agg/rounds)





    df = pd.DataFrame({
        # nodes
        'n': number_nodes,
        'sessions': sessions,

        # performance
        'throughput': throughput,
        'vlink_throughput': vlink_throughput,
        'generation_latency_max': genlat_max,
        'generation_latency_min': genlat_min,
        'generation_latency_agg': genlat_agg,
        'generation_latency_avg': genlat_avg,
        'vlink_generation_latency_max': vlink_genlat_max,
        'vlink_generation_latency_min': vlink_genlat_min,
        'vlink_generation_latency_agg': vlink_genlat_agg,
        'vlink_generation_latency_avg': vlink_genlat_avg,

        # fidelity
        'fidelity_avg': fidelity_avg,
        'fidelity_loss_avg': fidelity_loss_avg,
        'vlink_fidelity_avg': vlink_fidelity_avg,
        'vlink_fidelity_loss_avg': vlink_fidelity_loss_avg,

        # traffic
        'swaps': swaps,
        'c_message_count': c_message_counts,
        'q_message_count': q_message_counts,
        'vlink_swaps': vlink_swaps,
        'vlink_c_message_count': vlink_c_message_counts,
        'vlink_q_message_count': vlink_q_message_counts,
    })
    df.to_csv('data_scale/test4.csv', index=False)




'''
    # no vlinks, growing network size, random
    print('----------------\nNO VLINKS | GROWING NET SIZE | RANDOM\n----------------')
    for i in range(10,401,5):
        print(f'{i}/400')

    # vlinks, growing network size, random
    print('----------------\nVLINKS | GROWING NET SIZE | RANDOM\n----------------')
    for i in range(10,401,5):
        print(f'{i}/400')

    df.to_csv('data_scale/net_size_random.csv', index=False)




    # no vlinks, growing session count, waxman
    print('----------------\nNO VLINKS | GROWING SESSION COUNT | WAXMAN\n----------------')
    for i in range(5,101,5):
        print(i)

    # vlinks, growing session count, waxman
    print('----------------\nVLINKS | GROWING SESSION COUNT | WAXMAN\n----------------')
    for i in range(5,101,5):
        print(i)

    # no vlinks, growing session count, random
    print('----------------\nNO VLINKS | GROWING SESSION COUNT | RANDOM\n----------------')
    for i in range(5,101,5):
        print(i)

    # vlinks, growing session count, random
    print('----------------\nVLINKS | GROWING SESSION COUNT | RANDOM\n----------------')
    for i in range(5,101,5):
        print(i)
'''

'''

    oracle = NetworkOracle()
    config = Config(
        ts=ts,
        te=te,
        acc=acc,
        vlink_send_rate=vlink_send_rate_hz,
        send_rate=send_rate,
        #topo=RandomTopology(nodes_number=20, lines_number=25),
        #topo=CustomDoubleStarTopology(),
        topo=CustomWaxmanTopology(alpha=0.15, beta=0.75, nodes_number=20),
        vlinks_active=False,
        continuous_distro=True,
        job = Job.random(session_count=4),
    )

    metadata: SimData = oracle.run(config, loglvl=log.logging.INFO)
    print(f'eps={metadata.throughput}; lat={metadata.generation_latency_avg}; fid={metadata.fidelity_avg}; fid_loss={metadata.fidelity_loss_avg}; succ={metadata.success_rate_p}; distros={metadata.success_count}/{metadata.send_count}; mem={metadata.remaining_mem_usage}; swaps={metadata.avg_swap_count}')
'''

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


