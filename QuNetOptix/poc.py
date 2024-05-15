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

# TODO think about error/loss/decoherence models, entanglement models and hardware details -> make qubits decohere and restart the distro
# TODO look into docs for multicore sim

# TODO overhaul plotting animation
# TODO implement vlink selection
# TODO implement custom waxman topology

def poc(vlink_send_rate_hz: int):
    oracle = NetworkOracle()
    df = pd.DataFrame(columns=['nodes_number', 'send_count', 'success_count', 'throughput', 'generation_latency', 'success_rate', 'fidelity_avg', 'fidelity_loss_avg'])
    filename = f'vlink_poc_{vlink_send_rate_hz}hz.csv'

    if os.path.exists(filename):
        os.remove(filename)

    ts=0
    te=20
    acc=1_000_000_000
    send_rate = 5

    with open(filename, 'a') as f:
        print(f'\n{filename}')
        df.to_csv(f, header=True, index=False)
        for i in range(5, 101):
            nodes_number = i
            config = Config(
                ts=ts,
                te=te,
                acc=acc,
                vlink_send_rate=vlink_send_rate_hz,
                send_rate=send_rate,
                topo=CustomLineTopology(nodes_number=nodes_number),
                job = Job.custom(sessions=[('n1', f'n{nodes_number}')]),
                continuous_distro=True,
            )

            if vlink_send_rate_hz == 0:
                config.vlinks = None
                config.schedule_n_vlinks = 0
            else:
                config.vlinks=[('n2', f'n{nodes_number-1}')]
                config.schedule_n_vlinks = None

            metadata: SimData = oracle.run(config, loglvl=log.logging.INFO)
            new_row = {
                'nodes_number': nodes_number,
                'send_count': metadata.send_count,
                'success_count': metadata.success_count,
                'throughput': metadata.throughput,
                'generation_latency': metadata.generation_latency_avg,
                'success_rate': metadata.success_rate_p,
                'fidelity_avg': metadata.fidelity_avg,
                'fidelity_loss_avg': metadata.fidelity_loss_avg,
            }
            df.loc[len(df)] = new_row
            new_row_df = pd.DataFrame([new_row], columns=df.columns)
            new_row_df.to_csv(f, header=False, index=False)
            print(f'[{i} nodes]\t\tdistros: {metadata.success_count}/{metadata.send_count}, vlinks: {metadata.df['vlink_success_count'][0]}/{metadata.df['vlink_send_count'][0]}')


if __name__ == '__main__': 

    for i in range(0, 11, 10):
        poc(vlink_send_rate_hz=i)










