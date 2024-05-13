from qns.network.network import QuantumNetwork
from qns.entity.qchannel import QuantumChannel
from qns.network.protocol.entanglement_distribution import Transmit
from qns.entity.memory import QuantumMemory
from qns.network.requests import Request
from qns.entity.node.app import Application
from qns.models.core import QuantumModel
from qns.entity.memory.event import MemoryReadRequestEvent, MemoryReadResponseEvent, MemoryWriteRequestEvent, MemoryWriteResponseEvent
from qns.entity.qchannel.qchannel import RecvQubitPacket
from qns.entity.cchannel.cchannel import ClassicChannel, RecvClassicPacket, ClassicPacket
from qns.entity.node import QNode
from qns.simulator.simulator import Simulator
from qns.simulator.event import func_to_event, Event
from qns.simulator.ts import Time
import qns.utils.log as log

from vlaware_qnode import VLAwareQNode, Transmit, EprAccount
from vl_routing import RoutingResult
from vl_entanglement import StandardEntangledPair, VLEntangledPair
from metadata import SimData, DistroResult
from vl_network import VLNetwork
from typing import Optional, Dict, Callable, Type, Any, Tuple
import queue
import random
import simple_colors
import uuid

class RecvQubitOverVL(Event):
    '''
    Received by charlie after swapping over virtual link
    '''
    def __init__(self, t: Optional[Time] = None, qubit: QuantumModel = None, src: VLAwareQNode = None, dest: VLAwareQNode = None, vlink_transmit_id: str = None, by: Optional[Any] = None):
        super().__init__(t=t, name=None, by=by)
        self.qubit = qubit
        self.vlink_transmit_id = vlink_transmit_id
        self.src = src
        self.dest = dest

    def invoke(self) -> None:
        self.dest.handle(self)


class VLApp(Application):
    def __init__(self, name: str):
        super().__init__()

        # members
        self.app_name: str = name
        self.entanglement_type: Type[QuantumModel] = None
        if name != 'distro' and name != 'maint':
            raise ValueError('Invalid name')

        self.control: Dict[str, Callable[..., Any]] = {
            "swap": self.swap,
            "next": self.next,
            "success": self.success,
            "revoke": self.revoke,
            "vlink": self._vlink,
        }
        self.own: VLAwareQNode = None 
        self.memory: QuantumMemory = None 
        self.net: VLNetwork = None 
        self.waiting_for_vlink: bool = False # always false for maintenance app
        self.vlinks_scheduled: int = 0

        # ep info can be vlink or standard ep
        self.src: Optional[VLAwareQNode] = None
        self.dst: Optional[VLAwareQNode] = None

        # communication
        self.add_handler(self.MemoryWriteResponseHandler, [MemoryWriteResponseEvent])
        self.add_handler(self.MemoryReadResponseHandler, [MemoryReadResponseEvent])
        self.add_handler(self.RecvQubitOverVLHandler, [RecvQubitOverVL])
        self.add_handler(self.RecvQubitHandler, [RecvQubitPacket])
        self.add_handler(self.RecvClassicPacketHandler, [RecvClassicPacket])

        # meta data
        self.success_eprs = []
        self.success_count: int = 0
        self.send_count: int = 0
        self.generation_latency_agg: float = 0.0

    def RecvQubitOverVLHandler(self, node: VLAwareQNode, event: RecvQubitOverVL):
        if not isinstance(event.qubit, self.entanglement_type): 
            return
        self.store_received_qubit(event.src, event.qubit)

    def RecvQubitHandler(self, node: VLAwareQNode, event: RecvQubitPacket):
        if not isinstance(event.qubit, self.entanglement_type): 
            return
        qchannel: QuantumChannel = event.qchannel 
        src_node: VLAwareQNode = qchannel.node_list[0] if qchannel.node_list[1] == self.own else qchannel.node_list[1]
        # receive epr
        epr = event.qubit
        self.store_received_qubit(src_node, epr)

    def RecvClassicPacketHandler(self, node: VLAwareQNode, event: RecvClassicPacket):
        msg = event.packet.get()
        if msg['app_name'] != self.app_name:
            return

        self.receive_control(node, event)

    def install(self, node: QNode, simulator: Simulator):
        super().install(node, simulator)

        self.own: VLAwareQNode = self._node
        self.memory: QuantumMemory = self.own.memories[0]
        self.net: VLNetwork = self.own.network

        requests = self.own.requests if self.app_name == 'distro' else self.own.vlinks
        for request in requests:
            if self.own == request.src: # i am a sender
                # save into session registry
                session_id = uuid.uuid4().hex 
                self.own.session_registry[session_id] = {'src': request.src, 'dst': request.dest}
                request.dest.session_registry[session_id] = {'src': request.src, 'dst': request.dest} 

                # start first ep distro
                self.send_rate = request.attr['send_rate'] 
                event = func_to_event(simulator.ts, self.start_ep_distribution, by=self, session_id=session_id)
                self._simulator.add_event(event)

    def schedule_next_ep_distribution(self, session_id: str):
        t = self._simulator.tc + Time(sec=1 / self.send_rate)
        event = func_to_event(t, self.start_ep_distribution, by=self, session_id=session_id)
        self._simulator.add_event(event)

    def start_ep_distribution(self, session_id: str = None):
        if session_id is None:
            raise ValueError('Session id required for new distribution')

        if self.app_name == 'maint':
            if self.net.schedule_n_vlinks is not None: # only distribute n_vlinks virtual links (for testing purposes)
                if self.vlinks_scheduled >= self.net.schedule_n_vlinks:
                    return
                self.vlinks_scheduled += 1
            self.schedule_next_ep_distribution(session_id)

        elif self.app_name == 'distro':
            if self.net.continuous_distro: # one distribution per session
                if self.waiting_for_vlink:
                    return # don't send new when there is an active distribution on that session
                self.schedule_next_ep_distribution(session_id)
        else:
            raise Exception("Unknown app name")

        # generate base epr
        session_src: VLAwareQNode = self.own.session_registry[session_id]['src']
        session_dst: VLAwareQNode = self.own.session_registry[session_id]['dst']
        epr: self.entanglement_type = self.generate_qubit(session_src, session_dst, session_id, transmit_id=None)

        # save transmission
        transmit: Transmit = Transmit(
            id=epr.account.transmit_id,
            session=session_id,
            src=session_src,
            dst=session_dst,
            charlie=epr.account, # only set forward for first node
            start_time_s=self._simulator.current_time.sec
        )
        self.own.trans_registry[epr.account.transmit_id] = transmit
        self.log_trans(f'start new ep distribution: {transmit.src} -> {transmit.dst} [epr={epr.name}]', transmit=transmit)

        store_success = self.memory.write(epr)
        if not store_success:
            self.memory.read(epr)
            self.own.trans_registry[epr.account.transmit_id] = None
            self.log_trans(f'failed starting new distribution {transmit.src} -> {transmit.dst} \t[{epr}]', transmit=transmit)
            return
        self.log_trans(f"stored qubit {epr}", transmit=transmit)

        self.send_count += 1
        self.distribute_qubit_adjacent(epr.account.transmit_id)

    def distribute_qubit_adjacent(self, transmit_id: str):
        transmit = self.own.trans_registry.get(transmit_id)
        if transmit is None:
            return
        epr = self.memory.get(transmit.charlie.name)
        if epr is None: 
            return

        routing_result: RoutingResult = self.net.query_route(self.own, transmit.dst)
        if not routing_result:
            raise Exception(f"{self}: Route error.")


        next_hop: VLAwareQNode = routing_result.next_hop_physical

        # put into queue and exit if its vlink distro
        if routing_result.vlink and self.app_name == 'distro':
            next_hop: VLAwareQNode = routing_result.next_hop_virtual
            self.own.waiting_for_vlink_buf.put_nowait(transmit)
            if self.own.vlink_buf.empty() and next_hop.vlink_buf.empty():
                self.log_trans(f'waiting for vlink on {self.own.name} to {next_hop.name}\t[{epr}]', transmit=transmit)
                self.waiting_for_vlink = True
                return
            self.log_trans(f'using available vlink on {self.own.name} to {next_hop.name}\t[{epr}]', transmit=transmit)
            self._vlink(next_hop, None, None)
            return

        self.log_trans(f'physical transmission of qubit {epr.name} to {next_hop}', transmit=transmit)
        qchannel: QuantumChannel = self.own.get_qchannel(next_hop)
        if qchannel is None:
            raise Exception(f"{self}: No such quantum channel.")
        qchannel.send(epr, next_hop=next_hop)

    def MemoryWriteResponseHandler(self, node, event: MemoryWriteResponseEvent):
        app, epr, transmit, src_node = event.request.by
        if app is not self:
            return

        if self.own.storage_log[epr.name] is None: # previous storage failed and revoke already started
            return

        storage_log_entry = self.own.storage_log[epr.name]

        if event.result == False:
            self.log_trans(f'failed storage of qubit {epr.name}', transmit=transmit)
            for ep_name in storage_log_entry.keys():
                self.own.storage_log[epr.name] = None
                self.log_trans(f'read request for {ep_name}', transmit=transmit)
                read_request = MemoryReadRequestEvent(memory=self.memory, key=ep_name, t=self._simulator.current_time, by=(app, epr, transmit, src_node, 'revoke'))
                self._simulator.add_event(read_request)
            return

        storage_log_entry[epr.name] = event.result
        self.log_trans(f"stored qubit {epr.name}", transmit=transmit)

        success: bool = all(status for status in storage_log_entry.values())
        if success:
            self.own.storage_log[epr.name] = None
            self.send_control(src_node, transmit, 'swap', self.app_name)

    def MemoryReadResponseHandler(self, node, event: MemoryReadResponseEvent):
        app, epr, transmit, src_node, command = event.request.by
        if app is not self:
            return

        if command == 'revoke':
            if event.result is not None:
                self.log_trans(f'revoked qubit {event.result}', transmit=transmit)

            if not transmit.revoked:
                transmit.revoked = True
                self.own.trans_registry[transmit.id] = None # clear
                if self.own != transmit.src:
                    self.send_control(transmit.src, transmit, 'revoke', self.app_name)
            return

    def store_received_qubit(self, src_node: VLAwareQNode, epr: QuantumModel):
        # bookkeeping
        updated_transmit: Transmit = Transmit(
            id=epr.account.transmit_id,
            session=epr.account.session_id,
            src=epr.account.src,
            dst=epr.account.dst,
            alice=epr.account,
        )
        updated_transmit.alice.locB = self.own
        self.own.trans_registry[epr.account.transmit_id] = updated_transmit
        self.log_trans(f"received qubit from {src_node.name}\t[{epr}]", transmit=updated_transmit)

        # async storage 
        self.log_trans(f'storage request for {epr.name}', transmit=updated_transmit)
        write_request_1 = MemoryWriteRequestEvent(memory=self.memory, qubit=epr,t=self._simulator.current_time,  by=(self, epr, updated_transmit, src_node))
        storage_log = {epr.name: None}
        if self.own is not epr.account.dst: # no forward epr if dst is reached
            forward_epr = self.generate_qubit(src=epr.account.src, dst=epr.account.dst, session_id=epr.account.session_id, transmit_id=epr.account.transmit_id) 
            updated_transmit.charlie = forward_epr.account 
            self.log_trans(f'storage request for {forward_epr.name}', transmit=updated_transmit)
            write_request_2 = MemoryWriteRequestEvent(memory=self.memory, qubit=forward_epr, t=self._simulator.current_time, by=(self, forward_epr, updated_transmit, src_node))
            storage_log[forward_epr.name] = None

        self.own.storage_log[epr.name] = storage_log
        self._simulator.add_event(write_request_1)
        if self.own is not epr.account.dst: # no forward epr if dst is reached
            self.own.storage_log[forward_epr.name] = storage_log
            self._simulator.add_event(write_request_2)

    def send_control(self, dst: VLAwareQNode, transmit: Transmit, control: str, app_name: str):
        # get sender channel 
        cchannel: ClassicChannel = self.own.get_cchannel(dst)
        if cchannel is None:
            raise Exception(f"{self}: No such classic channel")
        # build packet
        classic_packet = ClassicPacket(
            msg={"cmd": control, "transmit_id": transmit.id, 'app_name': app_name}, 
            src=self.own, 
            dest=dst
        )
        self.log_trans(f'sending \'{control}\' to {dst.name}', transmit=transmit)
        cchannel.send(classic_packet, next_hop=dst)

    def receive_control(self, node: VLAwareQNode, e: RecvClassicPacket):
        # get sender and channel
        src_cchannel: ClassicChannel = e.by
        src_node: VLAwareQNode = src_cchannel.node_list[0] if src_cchannel.node_list[1] == self.own else src_cchannel.node_list[1]
        if src_cchannel is None:
            raise Exception(f"{self}: No such classic channel")
        
        # receive message
        msg = e.packet.get()
        cmd = msg['cmd']
        transmit = self.own.trans_registry[msg["transmit_id"]] 

        self.log_trans(f'received \'{cmd}\' from {src_node.name}', transmit=transmit)

        # handle classical message
        self.control.get(cmd)(src_node, src_cchannel, transmit)

    def swap(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        if self.own != transmit.src: # dont swap for first node

            # swap and manage new epr
            first: self.entanglement_type = self.memory.read(transmit.alice.name)
            second: self.entanglement_type = self.memory.read(transmit.charlie.name)
            new_epr: self.entanglement_type = self.entanglement_type(first.swapping(second))
            new_epr.name = uuid.uuid4().hex
            new_epr.account = EprAccount(
                transmit_id=transmit.id,
                name=new_epr.name,
                src=transmit.src,
                dst=transmit.dst,
                locA=first.account.locA,
                locB=second.account.locB,
            )

            # set new EP in Alice (request src)
            backward_node: VLAwareQNode = new_epr.account.locA
            backward_node_app = backward_node.get_apps(type(self))[0]

            # set new EP in Charlie (next in path)
            forward_node: VLAwareQNode = new_epr.account.locB
            forward_node_app = forward_node.get_apps(type(self))[0]

            # set alicea and charlie after swap
            backward_node_app.set_charlie(new_epr, first, second)
            forward_node_app.set_alice(new_epr, first, second)

            # clear for repeater node
            self.own.trans_registry[transmit.id] = None

            self.log_trans(f'performed swap (({backward_node.name}, {self.own.name}) - ({self.own.name}, {forward_node.name})) -> ({backward_node.name}, {forward_node.name})', transmit=transmit)

        # send next
        self.send_control(src_node, transmit, 'next', self.app_name)

    def next(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        if self.own == transmit.dst: # successful distribution
            self.own.trans_registry[transmit.id] = transmit

            # meta data
            if self.app_name == 'distro':
                result_epr: QuantumModel = self.memory.read(transmit.alice.name)
                self.net.metadata.distro_results[transmit.id] = DistroResult(dst_result=(transmit, result_epr))

            self.send_control(transmit.src, transmit, 'success', self.app_name)
            return

        self.distribute_qubit_adjacent(transmit.id)

    def revoke(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        # revoke transmission fully

        for ep in [transmit.alice, transmit.charlie]:
            if ep is not None:
                self.own.storage_log[ep.name] = None
                self.log_trans(f'read request for {ep.name}', transmit=transmit)
                read_request = MemoryReadRequestEvent(memory=self.memory, key=ep.name, t=self._simulator.current_time, by=(self, ep, transmit, src_node, 'revoke'))
                self._simulator.add_event(read_request)


    def success(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        if self.app_name == 'distro':
            result_epr: QuantumModel = self.memory.read(transmit.charlie.name)
            self.log_trans(simple_colors.green(f"successful distribution of [result_epr={result_epr}]"), transmit=transmit)

            # KPIs
            self.net.metadata.distro_results[transmit.id].src_result = (transmit, result_epr)
            self.success_count += 1
            gen_latency: float = self._simulator.current_time.sec - transmit.start_time_s
            self.generation_latency_agg += gen_latency

            # clear transmission
            self.own.trans_registry[transmit.id] = None
            return

        self.log_trans(simple_colors.magenta(f'established vlink ({self.own.name}, {src_node.name})'), transmit=transmit)
        self.success_count += 1

        self.own.vlink_buf.put_nowait(transmit)
        src_node.vlink_buf.put_nowait(transmit)

        # decide where to notify about new vlink
        src_waiting = not self.own.waiting_for_vlink_buf.empty()
        dst_waiting = not transmit.dst.waiting_for_vlink_buf.empty()
        tgt: Optional[VLAwareQNode] = None

        if src_waiting and not dst_waiting:
            tgt = self.own
        elif not src_waiting and dst_waiting:
            tgt = transmit.dst
        elif src_waiting and dst_waiting:
            # flip a coin
            coinflip_result =  random.choice([True, False])
            tgt = self.own if coinflip_result else transmit.dst

        if tgt is not None:
            self.send_control(tgt, transmit, "vlink", "distro") 

    def _vlink(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        if self.own.waiting_for_vlink_buf.empty() or self.own.vlink_buf.empty(): # someone else was faster
            return
            #raise Exception("Race condition probably :)")

        transmit_to_teleport: Transmit = self.own.waiting_for_vlink_buf.get_nowait()
        vlink_transmit: Transmit = self.own.vlink_buf.get_nowait()


        dir = 'backward' if self.own == vlink_transmit.dst else 'forward'
        if dir == 'forward':
            other_side: Transmit = vlink_transmit.dst.vlink_buf.get_nowait() # remove from other side
            if transmit_to_teleport.alice is None and vlink_transmit.src == transmit_to_teleport.src: # start node is vlink node forward if alice is none
                first = self.memory.read(transmit_to_teleport.charlie.name) 
            else:
                first = self.memory.read(transmit_to_teleport.alice.name) 
        if dir == 'backward':
            other_side: Transmit = vlink_transmit.src.vlink_buf.get_nowait() # remove from other side
            if transmit_to_teleport.alice is None and vlink_transmit.dst == transmit_to_teleport.src: # start node is vlink node forward if alice is none
                first = self.memory.read(transmit_to_teleport.charlie.name)
            else:
                first = self.memory.read(transmit_to_teleport.alice.name)

        if other_side.id != vlink_transmit.id:
            raise ValueError("Removed wrong transmit from other side while using vlink")

        second = self.memory.read(vlink_transmit.charlie.name) 

        # swap with vlink
        new_epr: self.entanglement_type = self.entanglement_type(first.swapping(second))
        new_epr.name = uuid.uuid4().hex
        new_epr.account = EprAccount(
            transmit_id=transmit_to_teleport.id,
            name=new_epr.name,
            src=transmit_to_teleport.src,
            dst=transmit_to_teleport.dst,
            locA=first.account.locA,
            locB=second.account.locB,
        )

        # set new EP in Alice (request src)
        backward_node: VLAwareQNode = transmit_to_teleport.src
        backward_node_app: VLEnabledDistributionApp = backward_node.get_apps(VLEnabledDistributionApp)[0]


        # set new EP in Charlie (next in path)
        forward_node = vlink_transmit.dst if dir == 'forward' else vlink_transmit.src
        forward_node_app: VLEnabledDistributionApp = forward_node.get_apps(VLEnabledDistributionApp)[0]

        # update forward and backward nodes
        forward_node_app.set_alice(new_epr, first, second, used_vlink=vlink_transmit)
        backward_node_app.set_charlie(new_epr, first, second, used_vlink=vlink_transmit)
        self.log_trans(f'performed swap using vlink (({backward_node.name}, {self.own.name}) - ({self.own.name}, {forward_node.name})) -> ({backward_node.name}, {forward_node.name})', transmit=transmit_to_teleport)

        # clean up after vlink usage
        if backward_node != self.own:
            self.memory.read(transmit_to_teleport.charlie.name) # forward ep no longer of use because of vlink
        node_to_clear = vlink_transmit.src if self.own == vlink_transmit.dst else vlink_transmit.dst 
        node_to_clear_app: VLEnabledDistributionApp = node_to_clear.get_apps(VLEnabledDistributionApp)[0] # clear other node of vlink
        node_to_clear_app.memory.read(second.name)
        vlink_transmit.dst.trans_registry[vlink_transmit.id]= None
        vlink_transmit.src.trans_registry[vlink_transmit.id]= None
        self.waiting_for_vlink = False

        # treat this same way as physical qubit transmission by sending recvqubitevent
        send_event = RecvQubitOverVL(self._simulator.current_time, qubit=new_epr, src=backward_node, dest=forward_node, vlink_transmit_id=vlink_transmit.id, by=self) # no delay on vlinks, just use current time
        self._simulator.add_event(send_event)


    def generate_qubit(self, src: VLAwareQNode, dst: VLAwareQNode, session_id: str,
                       transmit_id: Optional[str] = None) -> QuantumModel:
        epr = self.entanglement_type(name=uuid.uuid4().hex) 
        epr.account = EprAccount(
            transmit_id=transmit_id if transmit_id is not None else uuid.uuid4().hex,
            session_id=session_id,
            name=epr.name,
            src = src,
            dst = dst,
            locA=self.own,
            locB=self.own,
        )
        return epr

    def set_charlie(self, epr: QuantumModel, first_old: QuantumModel, second_old: QuantumModel, used_vlink: Transmit = None):
        transmit = self.own.trans_registry.get(epr.account.transmit_id)
        if transmit is None:
            return

        transmit.charlie = epr.account

        # cleanup
        self.memory.read(first_old.name) # read out old alice
        self.memory.read(second_old.name) # read out old alice
        self.memory.read(epr.account.name) # read out new epr name before writing

        # safe new epr
        self.memory.write(epr)

    def set_alice(self, epr: QuantumModel, first_old: QuantumModel, second_old: QuantumModel, used_vlink: Transmit = None):
        transmit = self.own.trans_registry.get(epr.account.transmit_id)
        if transmit is None:
            return

        transmit.alice = epr.account

        # cleanup
        self.memory.read(first_old.name) # read out old alice
        self.memory.read(second_old.name) # read out old alice
        self.memory.read(epr.account.name) # read out new epr name before writing

        # safe new epr
        self.memory.write(epr)

    def log_trans(self, str: str, transmit: Transmit = None):
        if transmit is None:
            log.debug(f'\t[{self.own.name}]\t{self.memory._usage}/{self.memory.capacity}\t{self.app_name}\tNone:\t{str}')
        else:
            log.debug(f'\t[{self.own.name}]\t{self.memory._usage}/{self.memory.capacity}\t{self.app_name}\t{transmit}:\t{str}')


class VLEnabledDistributionApp(VLApp):
    def __init__(self):
        super().__init__('distro')
        self.entanglement_type: Type[QuantumModel] = StandardEntangledPair 

class VLMaintenanceApp(VLApp):
    def __init__(self):
        super().__init__('maint')
        self.entanglement_type: Type[QuantumModel] = VLEntangledPair 