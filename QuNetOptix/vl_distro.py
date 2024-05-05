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
import simple_colors

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
        self.app_name: str = 'distro'

    def RecvQubitOverVLHandler(self, node: VLAwareQNode, event: RecvQubitOverVL):
        self.store_received_qubit(event.src, event.qubit)

    def _success(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        result_epr: QuantumModel = self.memory.read(transmit.charlie.name)
        self.log_trans(simple_colors.green(f"successful distribution of [result_epr={result_epr}]"), transmit=transmit)

        # meta data
        self.net.metadata.distro_results[transmit.id].src_result = (transmit, result_epr)
        self.net.metadata.success_count += 1

        # clear transmission
        self.own.trans_registry[transmit.id] = None
        return

    # # TODO abstract the swapping process, this can probably go into _swap so use classic comm
    def _vlink(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        if self.own.waiting_for_vlink_buf.empty(): 
            raise Exception("Race condition probably :)")

        try:
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
        except Exception:
            return

        if other_side.id != vlink_transmit.id:
            raise ValueError("Removed wrong transmit from other side while using vlink")

        second = self.memory.read(vlink_transmit.charlie.name) # TODO this is sometimes none with really scarce memory resources

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
        self.log_trans(f'consumed: {first} and {second} | new: {new_epr}', transmit=transmit_to_teleport)

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
