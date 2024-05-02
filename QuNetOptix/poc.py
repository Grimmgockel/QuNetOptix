import qns.utils.log as log
from oracle import NetworkOracle
from config import Config
from config import Job
from vl_topo import CustomDoubleStarTopology
from typing import List

# TODO fix quantum memory issues
# TODO TEST ROUTING
# TODO REFACTOR
# TODO multiple vlinks?

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

    test_jobs: List[Job] = [
        Job.custom(sessions=[('n0', 'n2')]), # physical (no vlink)

        Job.custom(sessions=[('n0', 'n11')]), # general forward
        Job.custom(sessions=[('n11', 'n0')]), # general backward

        Job.custom(sessions=[('n2', 'n11')]), # vlink start forward
        Job.custom(sessions=[('n9', 'n0')]), # vlink start backward
        Job.custom(sessions=[('n0', 'n9')]), # vlink end forward
        Job.custom(sessions=[('n11', 'n2')]), # vlink end backward

        Job.custom(sessions=[('n2', 'n9')]), # vlink only forward
        Job.custom(sessions=[('n9', 'n2')]), # vlink only backward
    ]
    for job in test_jobs:
        config = Config(
            ts=0,
            te=10,
            acc=1000000,
            send_rate=1,
            topo=CustomDoubleStarTopology(),
            job=job,
        )
        print(config)
        oracle.run(config, loglvl=log.logging.DEBUG, monitor=False)
        print()
        print()


