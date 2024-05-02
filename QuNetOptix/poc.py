import qns.utils.log as log
from oracle import NetworkOracle
from config import Config
from config import Job
from vl_topo import CustomDoubleStarTopology

# TODO make trans registry global
# TODO fix quantum memory issues
# TODO REFACTOR
# TODO test cases for vlink routing (everything for send rate slower and faster than maintenance)
# - general case
# - physical case
# - vlink only forward 
# - vlink only backward 
# - start node is vlink start node 
# - start node is vlink end node
# - end node is vlink end node
# - end node is vlink start node
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

    config = Config(
        ts=0,
        te=10,
        acc=1000000,
        send_rate=1,
        topo=CustomDoubleStarTopology(),
        job=Job.custom(sessions=[('n11', 'n0')])
    )

    oracle.run(config, loglvl=log.logging.DEBUG, monitor=False)


