import qns.utils.log as log
from oracle import NetworkOracle
from config import Config
from config import Job
from qns.network.topology import RandomTopology
from vl_topo import CustomDoubleStarTopology
from typing import List

# TODO REFACTOR swapping code still duplicate

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

    test_sessions_1: List[Job] = [
        ('n2', 'n9'), 
        ('n9', 'n2'), 

        ('n0', 'n11'),
        ('n11', 'n0'),

        ('n0', 'n10'),
        ('n0', 'n7'),
        ('n0', 'n8'),
    ] 

    test_sessions_2: List[Job] = [
        ('n0', 'n11'), 
        #('n1', 'n3'), 
        #3('n8', 'n7'),
    ]

    config = Config(
        ts=0,
        te=200,
        acc=1000000,
        vlink_send_rate=1,
        send_rate=1,
        topo = CustomDoubleStarTopology(),
        job=Job.custom(sessions=test_sessions_2)
    )
    meta_data = oracle.run(config, loglvl=log.logging.DEBUG, continuous_distro=False, n_vlinks=1, monitor=False)

    print()
    print(f'remaining mem usage: {meta_data.remaining_memory_usage}')
    print(f'send: {meta_data.send_count}, success: {meta_data.success_count}, vlinks: {meta_data.vlink_count}')
    print()


    for key, value in meta_data.distro_results.items():
        print('---- SUCCESSFUL DISTRIBUTION ----')
        print(f'ID: {key}')
        print(f'SRC: {value.src_result}')
        print(f'DST: {value.dst_result}')
        print()

    oracle.entanglement_animation()


