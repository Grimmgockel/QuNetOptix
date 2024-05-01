import qns.utils.log as log

from oracle import NetworkOracle
from config import Config
from config import Job
from vl_topo import TestTopology

# TODO does not work for when it starts on the vlink node
# TODO implement success and tear down for distribution app
# TODO make routing work, even when vlink is established first, think about shared resource buffer
# TODO make vlink maintance loop in a constant send rate
# TODO multiple vlinks?

# TODO test everything before sls
# TODO test general case
# TODO test case where vlink is at the start node
# TODO test case where vlink points to the end node
# TODO test case where vlink is longer
# TODO test teardown with revoke

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

    config = Config(
        ts=0,
        te=50,
        acc=1000000,
        send_rate=0.5,
        topo=TestTopology(),
        job=Job.custom(sessions=[('n0', 'n5')])
    )

    oracle.run(config, loglvl=log.logging.DEBUG, monitor=False)

