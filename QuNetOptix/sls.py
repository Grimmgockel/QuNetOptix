from qns.network.network import QuantumNetwork
from qns.network.protocol import EntanglementDistributionApp
from qns.network.protocol.entanglement_distribution import Transmit
from qns.simulator.ts import Time
from qns.entity.node import QNode
from qns.network.topology import Topology 
from qns.models.epr.werner import WernerStateEntanglement
from qns.network.route import RouteImpl 
from qns.network.topology.topo import ClassicTopology 
from qns.entity.memory import QuantumMemory
from qns.simulator.simulator import Simulator
from qns.simulator.event import Event, func_to_event
from qns.network.requests import Request
from qns.entity.node.app import Application
from qns.models.core import QuantumModel
from qns.entity.qchannel.qchannel import QuantumChannel, RecvQubitPacket
from qns.entity.cchannel.cchannel import ClassicChannel, ClassicPacket, RecvClassicPacket
from typing import Optional, Dict, List, Tuple, Union, Callable
import qns.utils.log as log
import os
import uuid

class Superlink(Request):
    def __init__(self, src, dest, attr: Dict = ...) -> None:
        super().__init__(src, dest, attr)

class SLS():
    def __init__():
        # TODO
        pass

    def select() -> List[Superlink]:
        # TODO 
        # TODO parametres in paper
        superlinks: List[Superlink] = []
        return superlinks

'''
Quantum network containing special request types called superlinks, that are considered for routing as entanglement links
'''
class SuperlinkNetwork(QuantumNetwork):
    def __init__(self, sls: SLS, topo: Topology | None = None, route: RouteImpl | None = None, classic_topo: ClassicTopology | None = ClassicTopology.Empty, name: str | None = None):
        super().__init__(topo, route, classic_topo, name)

        self._sls = sls
        self.superlinks: List[Superlink] = sls.select()

    def generate_dot_file(self, filename: str):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dot_file_path = os.path.join(script_dir, filename)

        with open(dot_file_path, 'w') as f:
            f.write('graph {\n')
            for node in self.nodes:
                f.write(f'{node.name} [label=\"{node.name}\"];\n')
            f.write('\n')
            for qchannel in self.qchannels:
                f.write(f'{qchannel.node_list[0].name}--{qchannel.node_list[1].name};\n')
            f.write('\n')

            # TODO this should be superlinks
            for req in self.requests:
                f.write(f'{req.src.name}--{req.dest.name} [color=purple penwidth=5];\n')


            f.write('}')

'''
Routes requests over superlinks using entanglement swapping
'''
class SuperlinkApp(EntanglementDistributionApp):
    def __init__(self, send_rate: int | None = None, init_fidelity: int = 0.99):
        super().__init__(send_rate, init_fidelity)

        # TODO init kpis here to aggregate after sim run, also events, use monitor for this (tutorial)

    def new_distribution(self):
        # TODO loop this
        # insert the next send event
        #t = self._simulator.tc + Time(sec=1 / self.send_rate)
        #event = func_to_event(t, self.new_distribution, by=self)
        #self._simulator.add_event(event)
        log.debug(f"{self.own}: start new request")

        # generate new entanglement
        epr = self.generate_qubit(self.own, self.dst, None)
        log.debug(f"{self.own}: generate epr {epr.name}")

        self.state[epr.transmit_id] = Transmit(
            id=epr.transmit_id,
            src=self.own,
            dst=self.dst,
            second_epr_name=epr.name)

        log.debug(f"{self.own}: generate transmit {self.state[epr.transmit_id]}")
        if not self.memory.write(epr):
            self.memory.read(epr)
            self.state[epr.transmit_id] = None
        self.send_count += 1
        self.request_distrbution(epr.transmit_id)

    def handle_response(self, packet: RecvClassicPacket):
        msg = packet.packet.get()
        cchannel = packet.cchannel

        from_node: QNode = cchannel.node_list[0] \
            if cchannel.node_list[1] == self.own else cchannel.node_list[1]

        log.debug(f"{self.own}: recv {msg} from {from_node}")

        cmd = msg["cmd"]
        transmit_id = msg["transmit_id"]
        transmit = self.state.get(transmit_id)

        if cmd == "swap":
            if self.own != transmit.src:
                # perfrom entanglement swapping
                first_epr: WernerStateEntanglement = self.memory.read(
                    transmit.first_epr_name)
                second_epr: WernerStateEntanglement = self.memory.read(
                    transmit.second_epr_name)
                new_epr = first_epr.swapping(second_epr, name=uuid.uuid4().hex)

                # logging
                swap_order_log: str = f'{self.own}:\t[SWAP]\t{transmit.src.name}-{self.own.name}-{from_node.name}\t=> \t{transmit.src.name}-{from_node.name}'
                epr_log: str = f'\t\t[EPRs consumed: {first_epr.name}; {second_epr.name}'
                new_epr_log: str = f'\t|\tnew EPR: {new_epr.name}]'
                log.info(swap_order_log + epr_log + new_epr_log)

                src: QNode = transmit.src
                app: EntanglementDistributionApp = src.get_apps(
                    EntanglementDistributionApp)[0]
                app.set_second_epr(new_epr, transmit_id=transmit_id)

                app: EntanglementDistributionApp = from_node.get_apps(
                    EntanglementDistributionApp)[0]
                app.set_first_epr(new_epr, transmit_id=transmit_id)

            classic_packet = ClassicPacket(
                msg={"cmd": "next", "transmit_id": transmit_id}, src=self.own, dest=from_node)
            cchannel.send(classic_packet, next_hop=from_node)
            log.debug(f"{self.own}: send {classic_packet.msg} to {from_node}")
        elif cmd == "next":
            # finish or request to the next hop
            if self.own == transmit.dst:
                result_epr = self.memory.read(transmit.first_epr_name)
                self.memory.read(transmit.second_epr_name)
                self.success.append(result_epr)
                self.state[transmit_id] = None
                self.success_count += 1
                log.debug(f"{self.own}: successful distribute {result_epr}")

                classic_packet = ClassicPacket(
                    msg={"cmd": "succ", "transmit_id": transmit_id},
                    src=self.own, dest=transmit.src)
                cchannel = self.own.get_cchannel(transmit.src)
                if cchannel is not None:
                    log.debug(
                        f"{self.own}: send {classic_packet} to {from_node}")
                    cchannel.send(classic_packet, next_hop=transmit.src)
            else:
                log.debug(f"{self.own}: begin new request {transmit_id}")
                self.request_distrbution(transmit_id)
        elif cmd == "succ":
            # the source notice that entanglement distribution is succeed.
            result_epr = self.memory.read(transmit.second_epr_name)
            log.debug(f"{self.own}: recv success distribution {result_epr}")
            self.state[transmit_id] = None
            self.success_count += 1
        elif cmd == "revoke":
            # clean memory
            log.debug(
                f"{self.own}: clean memory {transmit.first_epr_name}\
                    and {transmit.second_epr_name}")
            self.memory.read(transmit.first_epr_name)
            self.memory.read(transmit.second_epr_name)
            self.state[transmit_id] = None
            if self.own != transmit.src:
                classic_packet = ClassicPacket(
                    msg={"cmd": "revoke", "transmit_id": transmit_id},
                    src=self.own, dest=transmit.src)
                cchannel = self.own.get_cchannel(transmit.src)
                if cchannel is not None:
                    log.debug(
                        f"{self.own}: send {classic_packet} to {from_node}")
                    cchannel.send(classic_packet, next_hop=transmit.src)



'''
SwappingTree routing algorithm for optimized entanglement swapping
'''
class SwappingTreeRoutingAlgorithm(RouteImpl):
    def __init__(self, name: str = "swappingtree",
                 metric_func: Callable[[Union[QuantumChannel, ClassicChannel]], float] = None) -> None:
        self.name = name
        self.route_table = []
        if metric_func is None:
            self.metric_func = lambda _: 1
        else:
            self.metric_func = metric_func

    def build(self, nodes: List[QNode], channels: List[Union[QuantumChannel, ClassicChannel]]):
        pass

    def query(self, src: QNode, dest: QNode) -> List[Tuple[float, QNode, List[QNode]]]:
        '''
        query metric, nexthop and path
        '''
        return []