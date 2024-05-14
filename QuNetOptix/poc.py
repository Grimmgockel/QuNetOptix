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


# TODO implement basic proof of concept 'poc.py' for shortcut links, where paths with increasing lengths are shortcutted and EP are constantly distributed
# TODO save experiments into results.csv

# TODO think about error/loss/decoherence models, entanglement models and hardware details -> make qubits decohere and restart the distro
# TODO look into docs for multicore sim
# TODO overhaul plotting
# TODO implement vlink selection
# TODO implement custom waxman topology
if __name__ == '__main__': 
    oracle = NetworkOracle()

    no_vlinks_df = pd.DataFrame(columns=['nodes_number', 'throughput', 'generation_latency', 'success_rate'])
    for i in range(5, 50):
        nodes_number = i
        config = Config(
            ts=0,
            te=20,
            acc=10000000000000,
            vlink_send_rate=5,
            send_rate=5,
            topo=CustomLineTopology(nodes_number=nodes_number),
            job = Job.custom(sessions=[('n1', f'n{nodes_number}')]),
            continuous_distro=True,
            #vlinks=[('n2', f'n{nodes_number-1}')],
            schedule_n_vlinks=0,
        )

        metadata: SimData = oracle.run(config, loglvl=log.logging.INFO)
        new_row = {
            'nodes_number': nodes_number,
            'throughput': metadata.throughput,
            'generation_latency': metadata.generation_latency,
            'success_rate': metadata.success_rate_p,
        }
        no_vlinks_df.loc[len(no_vlinks_df)] = new_row
        #print(f'distros: {metadata.success_count}/{metadata.send_count}, vlinks: {metadata.df['vlink_success_count'][0]}/{metadata.df['vlink_send_count'][0]}')
        #print(f'remaining memory usage: {metadata.df['remaining_mem_usage'][0]}')

        print('nodes number: {:.0f}\tthroughput: {:.2f} EP/s\tlatency: {:.2f} seconds\tsuccess rate: {:.0f}%'.format(nodes_number, metadata.throughput, metadata.generation_latency, metadata.success_rate_p))

        #for key, value in metadata.distro_results.items():
            #print(f'---- SUCCESSFUL DISTRIBUTION ----\nID: {key}\nSRC: {value.src_result}\nDST: {value.dst_result}')
        #ga: GraphAnimation = oracle.entanglement_animation(f'demo.gif', fps=5) # TODO OVERHAUL COMPLETELY, NEEDS TO BE RELIABLE AND ROBUST FOR DEBUGGING






