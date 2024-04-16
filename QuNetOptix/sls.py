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
from qns.entity.entity import Entity
from qns.simulator.event import Event, func_to_event
from qns.network.requests import Request
from qns.entity.node.app import Application
from qns.models.core import QuantumModel
from qns.entity.qchannel.qchannel import QuantumChannel, RecvQubitPacket
from qns.entity.cchannel.cchannel import ClassicChannel, ClassicPacket, RecvClassicPacket
from qns.network.topology import Topology, TreeTopology
from typing import Optional, Dict, List, Tuple, Union, Callable
import qns.utils.log as log
import os
import uuid



'''
Quantum network containing special request types called superlinks, that are considered for routing as entanglement links
'''
class SLNetwork(QuantumNetwork):
    def __init__(self, topo: Topology | None = None, route: RouteImpl | None = None, classic_topo: ClassicTopology | None = ClassicTopology.Empty, name: str | None = None):
        super().__init__(topo, route, classic_topo, name)

        self.superlinks: List[Request] = self.sls()


    def sls(self):
        # TODO
        superlinks: List[Request] = []
        slrequest = Request(src=self.get_node('n3'), dest=self.get_node('n7'), attr={'send_rate': 0.5})
        superlinks.append(slrequest)

        return superlinks

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
                f.write(f'{req.src.name}--{req.dest.name} [color=purple penwidth=5 constraint=False];\n')


            f.write('}')


#############################################################################################################3



'''
Routes requests over superlinks using entanglement swapping
'''
class SuperlinkApp(EntanglementDistributionApp):
    def __init__(self, send_rate: int | None = None, init_fidelity: int = 0.99):
        super().__init__(send_rate, init_fidelity)

        # TODO init kpis here to aggregate after sim run, also events, use monitor for this (tutorial)

    def install(self, node: QNode, simulator: Simulator):
        super().install(node, simulator)

        try:
            # this only works for src and dst node of sl
            self.own.sl = True
            slrequest: Request = self.own.superlinks[0] 
            print(slrequest)
        except IndexError:
            pass



    '''
    Kick off entanglement distribution
    '''
    def new_distribution(self):
        log.debug(f'{self.own} new_distribution')

        # TODO not looping for easier to understand log
        # insert the next send event
        #t = self._simulator.tc + Time(sec=1 / self.send_rate)
        #event = func_to_event(t, self.new_distribution, by=self)
        #self._simulator.add_event(event)
        #log.debug(f"{self.own}: start new request")

        # generate new entanglement with random 16 bytes as transmit id
        epr = self.generate_qubit(self.own, self.dst, None)
        #log.debug(f"{self.own}: generate epr {epr.name}")

        self.state[epr.transmit_id] = Transmit(
            id=epr.transmit_id,
            src=self.own,
            dst=self.dst,
            second_epr_name=epr.name)

        #log.debug(f"{self.own}: generate transmit {self.state[epr.transmit_id]}")
        if not self.memory.write(epr):
            self.memory.read(epr)
            self.state[epr.transmit_id] = None
        self.send_count += 1
        self.request_distrbution(epr.transmit_id)



    '''
    TODO what is state variable?? -> find better name or document
    gets called at the start and for 'next' cmd
    '''
    def request_distrbution(self, transmit_id: str):
        log.debug(f'{self.own} request_distribution')
        transmit = self.state.get(transmit_id)
        if transmit is None:
            return
        epr_name = transmit.second_epr_name
        epr = self.memory.get(epr_name)
        if epr is None:
            return

        dst = transmit.dst
        # get next hop
        route_result = self.net.query_route(self.own, dst)
        try:
            next_hop: QNode = route_result[0][1]
        except IndexError:
            raise Exception("Route error")

        qchannel: QuantumChannel = self.own.get_qchannel(next_hop)
        if qchannel is None:
            raise Exception("No such quantum channel")

        # send the entanglement
        log.debug(f"{self.own}: send epr {epr.name} to {next_hop} over quantum channel")
        qchannel.send(epr, next_hop)


    '''
    Response to qubit transmission
    '''
    def response_distribution(self, packet: RecvQubitPacket):
        log.debug(f'{self.own} response_distribution')
        qchannel: QuantumChannel = packet.qchannel

        # get sender of qubit
        from_node: QNode = qchannel.node_list[0] \
            if qchannel.node_list[1] == self.own else qchannel.node_list[1]

        cchannel: ClassicChannel = self.own.get_cchannel(from_node)
        if cchannel is None:
            raise Exception("No such classic channel")

        # receive the first epr
        epr: WernerStateEntanglement = packet.qubit
        log.debug(f"{self.own}: recv epr {epr.name} from {from_node} over quantum channel")

        # generate the second epr
        next_epr = self.generate_qubit(
            src=epr.src, dst=epr.dst, transmit_id=epr.transmit_id)
        #log.debug(f"{self.own}: generate epr {next_epr.name}")
        self.state[epr.transmit_id] = Transmit(
            id=epr.transmit_id,
            src=epr.src,
            dst=epr.dst,
            first_epr_name=epr.name,
            second_epr_name=next_epr.name)
        #log.debug(f"{self.own}: generate transmit {self.state[epr.transmit_id]}")

        #log.debug(f"{self.own}: store {epr.name} and {next_epr.name}")
        ret1 = self.memory.write(epr)
        ret2 = self.memory.write(next_epr)
        if not ret1 or not ret2:
            #log.debug(f"{self.own}: store fail, destory {epr} and {next_epr}")
            # if failed (memory is full), destory all entanglements
            self.memory.read(epr)
            self.memory.read(next_epr)
            classic_packet = ClassicPacket(
                msg={"cmd": "revoke", "transmit_id": epr.transmit_id}, src=self.own, dest=from_node)
            cchannel.send(classic_packet, next_hop=from_node)
            #log.debug(f"{self.own}: send {classic_packet.msg} to {from_node}")
            return

        classic_packet = ClassicPacket(
            msg={"cmd": "swap", "transmit_id": epr.transmit_id}, src=self.own, dest=from_node)
        cchannel.send(classic_packet, next_hop=from_node)
        log.debug(
            f"{self.own}: send {classic_packet.msg} from {self.own} to {from_node} over classic channel")

    '''
    ORCHESTRATE NODE COMMUNICATION
    '''
    def handle_response(self, packet: RecvClassicPacket):
        log.debug(f'{self.own} handle_response')
        msg = packet.packet.get()
        cchannel = packet.cchannel

        from_node: QNode = cchannel.node_list[0] \
            if cchannel.node_list[1] == self.own else cchannel.node_list[1]

        log.debug(f"{self.own}: recv {msg} from {from_node} over classical channel")

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
                log.debug(swap_order_log + epr_log + new_epr_log)

                src: QNode = transmit.src
                app: SuperlinkApp = src.get_apps(
                    SuperlinkApp)[0]
                app.set_second_epr(new_epr, transmit_id=transmit_id)

                app: SuperlinkApp = from_node.get_apps(
                    SuperlinkApp)[0]
                app.set_first_epr(new_epr, transmit_id=transmit_id)

            classic_packet = ClassicPacket(
                msg={"cmd": "next", "transmit_id": transmit_id}, src=self.own, dest=from_node)
            cchannel.send(classic_packet, next_hop=from_node)
            log.debug(f"{self.own}: send {classic_packet.msg} to {from_node} over classic channel")
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
                        f"{self.own}: send {classic_packet.msg} to {from_node} over classic channel")
                    cchannel.send(classic_packet, next_hop=transmit.src)
            else:
                log.debug(f"{self.own}: begin new request {transmit_id}")
                self.request_distrbution(transmit_id)
        elif cmd == "succ":
            # the source notice that entanglement distribution is succeed.
            result_epr = self.memory.read(transmit.second_epr_name)
            log.debug(f"{self.own}: recv success distribution {result_epr} over classic channel")
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
                        f"{self.own}: send {classic_packet} to {from_node} over classic channel")
                    cchannel.send(classic_packet, next_hop=transmit.src)

    def generate_qubit(self, src: QNode, dst: QNode, transmit_id: str | None = None) -> QuantumModel:
        epr = WernerStateEntanglement(fidelity=self.init_fidelity, name=uuid.uuid4().hex)
        epr.src = src
        epr.dst = dst
        epr.transmit_id = transmit_id if transmit_id is not None else uuid.uuid4().hex
        return epr

