import qns.utils.log as log
from oracle import NetworkOracle
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


    for i in range(5, 16):
        nodes_number = i
        config = Config(
            ts=0,
            te=10,
            acc=1000000,
            vlink_send_rate=2,
            send_rate=1,
            topo = CustomLineTopology(nodes_number=nodes_number),
        )
        test_sessions: List[Job] = [
            ('n1', f'n{nodes_number}'), 
        ]
        config.job = Job.custom(sessions=test_sessions)
        meta_data = oracle.run(config, loglvl=log.logging.DEBUG, monitor=False)
        #print(f'send: {meta_data.send_count}, success: {meta_data.success_count}, vlinks: {meta_data.vlink_count}, remaining_mem: {meta_data.remaining_memory_usage}')
        '''
        for key, value in meta_data.distro_results.items():
            print('---- SUCCESSFUL DISTRIBUTION ----')
            print(f'ID: {key}')
            print(f'SRC: {value.src_result}')
            print(f'DST: {value.dst_result}')
        '''

        ga: GraphAnimation = oracle.entanglement_animation(f'path_demo{i-5}.gif', fps=10)



