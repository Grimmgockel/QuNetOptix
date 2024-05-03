import qns.utils.log as log
from oracle import NetworkOracle
from config import Config
from config import Job
from vl_topo import CustomDoubleStarTopology
from typing import List

# TODO fix quantum memory issues by testing vlinks and their consumption
# TODO REFACTOR swapping code still duplicate

# TODO make multiple links work
# TODO entanglement tracker (observer pattern) -> animation??
# TODO plot networkx pretty
# TODO save experiments into results.csv
# TODO look into docs for multicore sim
# TODO implement basic proof of concept 'poc.py' for shortcut links, where paths with increasing lengths are shortcutted and EP are constantly distributed

# TODO implement vlink selection
# TODO implement custom waxman topology
# TODO compare base routing with custom routing in basic plot
# TODO think about error/loss/decoherence models, entanglement models and hardware details
if __name__ == '__main__': 
    oracle = NetworkOracle()

    test_sessions_parallel: List[Job] = [
        ('n0', 'n11'), 
        ('n2', 'n3'), 
        ('n9', 'n2'), 
        ('n11', 'n1'),
        ('n8', 'n7'),
    ]

    config = Config(
        ts=0,
        te=10,
        acc=1000000,
        send_rate=1,
        topo=CustomDoubleStarTopology(),
        job=Job.custom(sessions=test_sessions_parallel),
    )
    meta_data = oracle.run(config, loglvl=log.logging.DEBUG, monitor=False)

    #for key, value in meta_data.distro_results.items():
        #print(key)
        #print(f'SRC: {value.src_result}')
        #print(f'DST: {value.dst_result}')


