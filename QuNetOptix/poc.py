import qns.utils.log as log
from oracle import NetworkOracle
from metadata import SimData
from config import Config
from vl_net_graph import GraphAnimation
from config import Job
from qns.network.topology import RandomTopology
from vl_topo import CustomDoubleStarTopology, CustomLineTopology
from typing import List
import matplotlib.pyplot as plt

# TODO REFACTOR swapping code still duplicate
# TODO a lot of clunky plotting code left in the application classes

# TODO implement basic proof of concept 'poc.py' for shortcut links, where paths with increasing lengths are shortcutted and EP are constantly distributed
# TODO entanglement tracker (observer pattern) -> animation??
# TODO plot networkx pretty
# TODO save experiments into results.csv
# TODO look into docs for multicore sim

# TODO implement vlink selection
# TODO implement custom waxman topology
# TODO compare base routing with custom routing in basic plot
# TODO think about error/loss/decoherence models, entanglement models and hardware details
if __name__ == '__main__': 
    oracle = NetworkOracle()


    #for i in range(5, 16):
    nodes_number = 10
    config = Config(
        ts=0,
        te=10,
        acc=1000000,
        vlink_send_rate=5,
        send_rate=5,
        topo = CustomLineTopology(nodes_number=nodes_number),
    )
    test_sessions: List[Job] = [
        ('n1', f'n{nodes_number}'), 
    ]
    config.job = Job.custom(sessions=test_sessions)

    metadata: SimData = oracle.run(config, loglvl=log.logging.DEBUG, continuous_distro=False, schedule_n_vlinks=1)
    print(f'distros: {metadata.df['success_count'][0]}/{metadata.df['send_count'][0]}, vlinks: {metadata.df['vlink_success_count'][0]}/{metadata.df['vlink_send_count'][0]}')
    print(f'remaining memory usage: {metadata.df['remaining_mem_usage'][0]}')

    #for key, value in metadata.distro_results.items():
        #print(f'---- SUCCESSFUL DISTRIBUTION ----\nID: {key}\nSRC: {value.src_result}\nDST: {value.dst_result}')
    #ga: GraphAnimation = oracle.entanglement_animation(f'demo.gif', fps=5)



