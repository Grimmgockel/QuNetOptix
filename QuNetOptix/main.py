from qns.network.topology.topo import ClassicTopology
from qns.network.topology import RandomTopology
from qns.network.requests import Request
from qns.network.protocol.entanglement_distribution import EntanglementDistributionApp
from qns.simulator.simulator import Simulator
from qns.network.topology.treetopo import TreeTopology
from qns.network.topology.waxmantopo import WaxmanTopology
from qns.network.topology.linetopo import LineTopology
import qns.utils.log as log

from sls import VLNetwork


# TODO implement viz and methodology for basic entanglement distribution via monitor

# TODO SETUP CUSTOM CLUSTER TOPOLOGY FOR TESTING
# - have virtual links as requests in the net (entanglement that doesn't decohere?)
# - each node has its next virtual link next to it, this is taken into account for routing 
# - implement routing with virtual links

# TODO think about error/loss/decoherence models, entanglement models and hardware details
# TODO implement selection algo for virtual links
if __name__ == '__main__':

    # different topologies
    random = RandomTopology(
        nodes_number=10,
        lines_number=9,
        qchannel_args={"delay": 0.05},
        cchannel_args={"delay": 0.05},
        memory_args=[{"capacity": 3}],
        nodes_apps=[EntanglementDistributionApp()],
    )
    wax = WaxmanTopology(
        nodes_number=8,
        size=2,
        alpha=0.25,
        beta=20,
        nodes_apps=[EntanglementDistributionApp()],
    )
    tree = TreeTopology(
        nodes_number=9,
        children_number=3,
        nodes_apps=[EntanglementDistributionApp()],
    )
    line = LineTopology(
        nodes_number=10,
        nodes_apps=[EntanglementDistributionApp()],
    )

    from test_topo import TestTopology
    # set topology
    topo = TestTopology(nodes_apps=[EntanglementDistributionApp()])

    # network
    net = VLNetwork(topo=topo, classic_topo=ClassicTopology.All)
    net.build_route()
    net.add_request(src=net.get_node('n2'), dest=net.get_node('n9'), attr={"send_rate": 0.5}) 
    for req in net.requests:
        log.info(f"Process request: {req.src.name}->{req.dest.name}")

    # generate dot for net viz
    net.generate_lvl0_dot_file("lvl0_net.dot")
    net.generate_lvl1_dot_file("lvl1_net.dot")

    # start sim
    s = Simulator(0, 20, accuracy=1000000)
    log.logger.setLevel(log.logging.DEBUG)
    log.install(s)
    net.install(s)
    s.run()


    success_count = [req.src.apps[0].success_count for req in net.requests][0]
    print(f'Success count: {success_count}')
