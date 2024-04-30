import qns.utils.log as log

from oracle import NetworkOracle
from config import Config
from config import Job
from vl_topo import TestTopology

# TODO implement success and tear down for distribution app
# TODO make routing work, even when vlink is established first, think about shared resource buffer
# TODO make vlink maintance loop in a constant send rate
# TODO implement vlink selection
# TODO plot networkx pretty
# TODO look into docs for multicore sim
# TODO implement custom waxman topology
# TODO compare base routing with custom routing in basic plot
# TODO save experiments into results.csv
# TODO think about error/loss/decoherence models, entanglement models and hardware details
if __name__ == '__main__': 
    oracle = NetworkOracle()

    config = Config(
        ts=0,
        te=50,
        acc=1000000,
        send_rate=0.5,
        topo=TestTopology(),
        job=Job.custom(sessions=[('n0', 'n11')])
    )

    oracle.run(config, loglvl=log.logging.DEBUG, monitor=False)

