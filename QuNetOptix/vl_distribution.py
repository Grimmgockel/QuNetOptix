from qns.entity.cchannel import ClassicChannel, RecvClassicPacket
from qns.entity.qchannel import QuantumChannel, RecvQubitPacket
from qns.simulator.event import Event
from qns.models.core import QuantumModel
from qns.simulator import Time
from qns.models.epr import WernerStateEntanglement, BellStateEntanglement
import qns.utils.log as log

from vlaware_qnode import VLAwareQNode, Transmit, EprAccount
from vl_app import VLApp
from vl_routing import RoutingResult
from vl_entanglement import StandardEntangledPair

from typing import Type, Optional, Any
import uuid
import queue

class RecvQubitOverVL(Event):
    def __init__(self, t: Optional[Time] = None, qubit: QuantumModel = None, src: VLAwareQNode = None, dest: VLAwareQNode = None, vlink_transmit_id: str = None, by: Optional[Any] = None):
        super().__init__(t=t, name=None, by=by)
        self.qubit = qubit
        self.vlink_transmit_id = vlink_transmit_id
        self.src = src
        self.dest = dest

    def invoke(self) -> None:
        self.dest.handle(self)

'''
Node application for entanglement distribution over physical and virtual links
'''
class VLEnabledDistributionApp(VLApp):
    def __init__(self):
        super().__init__()

        # members
        self.add_handler(self.RecvQubitOverVLHandler, [RecvQubitOverVL])
        self.entanglement_type: Type[QuantumModel] = StandardEntangledPair 
        self.app_name: str = 'vlink enabled routing'

    def RecvQubitOverVLHandler(self, node: VLAwareQNode, event: RecvQubitOverVL):
        src_node = event.src
        epr = event.qubit
        log.debug(f'{self}: received qubit {epr} via vlink from {src_node.name}')
        self.store_received_qubit(event.src, epr)

    # TODO get this into superclass
    def send_qubit(self, epr, routing_result: RoutingResult, transmit: Transmit):
        next_hop: VLAwareQNode = routing_result.next_hop_virtual

        if routing_result.vlink:
            self.own.waiting_for_vlink_buf.put(transmit)
            if self.own.vlink_buf.empty() and next_hop.vlink_buf.empty():
                log.debug(f'{self}: waiting for vlink on {self.own.name} to {next_hop.name} for transmit {transmit.id}')
                self.waiting_for_vlink = True
                return

            self._vlink(next_hop, None, None)
            return

        log.debug(f'{self}: physical transmission of qubit {epr} to {next_hop}')
        qchannel: QuantumChannel = self.own.get_qchannel(next_hop)
        if qchannel is None:
            raise Exception(f"{self}: No such quantum channel.")
        qchannel.send(epr, next_hop=next_hop)

    def _success(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        result_epr = self.memory.read(transmit.charlie.name)
        log.debug(f"{self}: \033[92msuccessful distribution of [result_epr={result_epr}]")
        self.success_eprs.append(result_epr)

        # clear transmission
        self.own.trans_registry[transmit.id] = None
        return

    # # TODO abstract the swapping process, this can probably go into _swap so use classic comm
    def _vlink(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        if self.own.waiting_for_vlink_buf.empty(): # we are either at src or dst of vlink
            return

        vlink_transmit: Transmit = self.own.vlink_buf.get()
        dir = 'backward' if self.own == vlink_transmit.dst else 'forward'
        # remove from other side
        if dir == 'forward':
            vlink_transmit.dst.vlink_buf.get()
        if dir == 'backward':
            vlink_transmit.src.vlink_buf.get()

        transmit_to_teleport: Transmit = self.own.waiting_for_vlink_buf.get()

        first = self.memory.read(transmit_to_teleport.alice.name) # TODO both of charlie's qubits are on this node, charlie gets discarded
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
        backward_node_app.set_epr(new_epr, 'alice')

        # set new EP in Charlie (next in path)
        forward_node = vlink_transmit.dst if dir == 'forward' else vlink_transmit.src
        forward_node_app: VLEnabledDistributionApp = forward_node.get_apps(VLEnabledDistributionApp)[0]
        forward_node_app.set_epr(new_epr, 'charlie')

        # clear vlink transmission, vlink is consumed
        vlink_transmit.dst.trans_registry[vlink_transmit.id]= None
        vlink_transmit.src.trans_registry[vlink_transmit.id]= None
        self.waiting_for_vlink = False

        log.debug(f'{self}: performed swap using vlink (({backward_node.name}, {self.own.name}) - ({self.own.name}, {forward_node.name})) -> ({backward_node.name}, {forward_node.name})')

        # instruct maintenance to clear memory
        #print(vlink_transmit)
        #cchannel: Optional[ClassicChannel] = self.own.get_cchannel(src_node) 
        #self.send_control(cchannel, src_node, vlink_transmit.id, "vlink", "vlink maintenance")

        # treat this same way as physical qubit transmission by sending recvqubitevent
        send_event = RecvQubitOverVL(self._simulator.current_time, qubit=new_epr, src=backward_node, dest=forward_node, vlink_transmit_id=vlink_transmit.id, by=self) # no delay on vlinks, just use current time
        self._simulator.add_event(send_event)

