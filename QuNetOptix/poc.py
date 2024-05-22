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

# TODO make multicore work
# TODO think about error/loss/decoherence models, entanglement models and hardware details -> make qubits decohere and restart the distro

# TODO overhaul plotting animation
# TODO implement vlink selection
# TODO implement custom waxman topology

from qns.utils.multiprocess import MPSimulations

'''
class VLEPRDistroSimulation(MPSimulations):
    def run(self, setting):

        vlink_send_rate_hz = setting['vlink_send_rate']
        oracle = NetworkOracle()
        df = pd.DataFrame(columns=['nodes_number', 'send_count', 'success_count', 'throughput', 'generation_latency', 'success_rate', 'fidelity_avg', 'fidelity_loss_avg'])
        filename = f'vlink_poc_{vlink_send_rate_hz}hz.csv'

        if os.path.exists(filename):
            os.remove(filename)

        ts=0
        te=50
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
'''

class Sim(MPSimulations):
    def run(self, settings):
        vlink_send_rate_hz = settings['vlink_send_rate']
        nodes_number = settings['nodes_number']

        ts=0
        te=50
        acc=1_000_000_000
        send_rate = 5

        oracle = NetworkOracle()

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
        #return {
            #'nodes_number': nodes_number,
            #'send_count': metadata.send_count,
            #'success_count': metadata.success_count,
            #'throughput': metadata.throughput,
            #'generation_latency': metadata.generation_latency_avg,
            #'success_rate': metadata.success_rate_p,
            #'fidelity_avg': metadata.fidelity_avg,
            #'fidelity_loss_avg': metadata.fidelity_loss_avg,
        #}


from qns.network.route.dijkstra import DijkstraRouteAlgorithm
from qns.network.topology.topo import ClassicTopology
from qns.simulator.simulator import Simulator
from qns.network import QuantumNetwork
from qns.network.topology import LineTopology
from qns.network.protocol.entanglement_distribution import EntanglementDistributionApp

class EPRDistributionSimulation(MPSimulations):
    def run(self, settings):

        # get input variables
        nodes_number = settings['nodes_number']
        delay = settings['delay']
        memory_capacity = settings['memory_capacity']
        send_rate = settings['send_rate']

        s = Simulator(0, 10, accuracy=1000000000)
        topo = LineTopology(
            nodes_number=nodes_number,
            qchannel_args={'delay': delay, "drop_rate": 0.3},
            cchannel_args={'delay': delay},
            memory_args={'capacity': memory_capacity, 'store_error_model_args': {'a': 0.3}},
            nodes_apps=[EntanglementDistributionApp(init_fidelity=0.99)]
        )

        net = QuantumNetwork(
            topo=topo,
            classic_topo=ClassicTopology.All,
            route=DijkstraRouteAlgorithm()
        )
        net.build_route()

        src = net.get_node('n1')
        dst = net.get_node(f'n{nodes_number}')
        net.add_request(src=src, dest=dst, attr={'send_rate': send_rate})
        net.install(s)
        s.run()

        return {'count': src.apps[0].success_count}


if __name__ == '__main__': 
    '''
    df = pd.DataFrame(columns=['nodes_number', 'send_count', 'success_count', 'throughput', 'generation_latency', 'success_rate', 'fidelity_avg', 'fidelity_loss_avg'])

    vlink_send_rate = [0, 10]
    for rate in vlink_send_rate:
        filename = f'vlink_poc_{rate}hz.csv'
        if os.path.exists(filename):
            os.remove(filename)

    ss = Sim(
        settings={
            'vlink_send_rate': vlink_send_rate,
            'nodes_number': range(5, 21),
        },
        aggregate=True,
        iter_count=10,
        cores=4
    )
    ss.start()

    '''

    ss = EPRDistributionSimulation(
        settings={
            'nodes_number': [5, 10, 15, 20],
            'delay': [0.05],
            'memory_capacity': [10, 20],
            'send_rate': [10, 20]
        }, 
        aggregate=True, 
        iter_count=10, 
        cores=4
    )
    ss.start()
    











