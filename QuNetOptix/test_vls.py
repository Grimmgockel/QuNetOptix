import qns.utils.log as log

from oracle import NetworkOracle
from config import Config
from config import Job
from vl_topo import TestTopology

if __name__ == '__main__': 
    oracle = NetworkOracle()

    config = Config(
        ts=0,
        te=10,
        acc=1000000,
        send_rate=0.5,
        topo=TestTopology(),
        job=Job.custom(sessions=[('n0', 'n11')])
    )

    oracle.run(config, loglvl=log.logging.DEBUG, monitor=False)

