from qns.network.topology.topo import ClassicTopology
from qns.network.topology import RandomTopology
from qns.network.requests import Request
from qns.network.protocol.entanglement_distribution import EntanglementDistributionApp
from qns.simulator.simulator import Simulator
from qns.network.topology.treetopo import TreeTopology
from qns.network.topology.waxmantopo import WaxmanTopology
from qns.network.topology.linetopo import LineTopology
import qns.utils.log as log

from sls import SuperlinkApp, SLNetwork

# TODO IMPLEMENTIERE ICH UEBERHAUPT ANDERES ROUTING ODER NUR SUPERLINKS???
# TODO make communication more readable and better logging
# TODO abstract ES into linear swapping and tree swapping algorithm (error models for tree swapping)
# TODO swapping order in APP and swapping tree selection in Routing
# TODO look for other routing algorithms

# TODO implement superlinks (superlinks don't decohere for simplicity? superlink are static requests vs dynamic ones?)
# TODO kpis
# TODO why werner entanglement 
if __name__ == '__main__':

    # different topologies
    random = RandomTopology(
        nodes_number=50,
        lines_number=75,
        qchannel_args={"delay": 0.05},
        cchannel_args={"delay": 0.05},
        memory_args=[{"capacity": 3}],
        nodes_apps=[SuperlinkApp()],
    )
    wax = WaxmanTopology(
        nodes_number=20,
        size=10,
        alpha=0.25,
        beta=20,
        nodes_apps=[SuperlinkApp()],
    )
    tree = TreeTopology(
        nodes_number=30,
        children_number=2,
        nodes_apps=[SuperlinkApp()],
    )
    line = LineTopology(
        nodes_number=10,
        nodes_apps=[SuperlinkApp()],
    )

    # set topology
    topo = line

    # network
    net = SLNetwork(topo=topo, classic_topo=ClassicTopology.All)
    net.build_route()
    #net.random_requests(2, attr={"send_rate": 10}) # 10 hz
    net.add_request(src=net.get_node('n3'), dest=net.get_node('n7'), attr={"send_rate": 0.5}) 
    for req in net.requests:
        log.info(f"Process request: {req.src.name}->{req.dest.name}")


    # generate dot for net viz
    net.generate_dot_file("net.dot")

    # start sim
    s = Simulator(0, 20, accuracy=1000000)
    log.logger.setLevel(log.logging.DEBUG)
    log.install(s)
    net.install(s)
    s.run()


    success_count = [req.src.apps[0].success_count for req in net.requests][0]
    print(f'Success count: {success_count}')
