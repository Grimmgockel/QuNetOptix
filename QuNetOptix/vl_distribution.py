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
        result_epr = self.memory.read(transmit.charlie.name)
        self.log_trans(simple_colors.green(f"successful distribution of [result_epr={result_epr}]"), transmit=transmit)
        #self.success_eprs.append(result_epr)
        self.net.metadata.result_eprs[transmit] = result_epr

        # clear transmission
        self.own.trans_registry[transmit.id] = None
        return

    # # TODO abstract the swapping process, this can probably go into _swap so use classic comm
    def _vlink(self, src_node: VLAwareQNode, src_cchannel: ClassicChannel, transmit: Transmit):
        if self.own.waiting_for_vlink_buf.empty(): # we are either at src or dst of vlink
            return

        transmit_to_teleport: Transmit = self.own.waiting_for_vlink_buf.get()
        vlink_transmit: Transmit = self.own.vlink_buf.get()

        dir = 'backward' if self.own == vlink_transmit.dst else 'forward'
        if dir == 'forward':
            vlink_transmit.dst.vlink_buf.get() # remove from other side
            if transmit_to_teleport.alice is None and vlink_transmit.src == transmit_to_teleport.src: # start node is vlink node forward if alice is none
                first = self.memory.read(transmit_to_teleport.charlie.name) 
            else:
                first = self.memory.read(transmit_to_teleport.alice.name) 
        if dir == 'backward':
            if transmit_to_teleport.alice is None and vlink_transmit.dst == transmit_to_teleport.src: # start node is vlink node forward if alice is none
                first = self.memory.read(transmit_to_teleport.charlie.name)
            else:
                first = self.memory.read(transmit_to_teleport.alice.name)
            vlink_transmit.src.vlink_buf.get() # remove from other side

        second = self.memory.read(vlink_transmit.charlie.name)

        #print(dir)
        #print(transmit_to_teleport)
        #print(vlink_transmit)


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
        forward_node_app.set_alice(new_epr, backward_node)
        backward_node_app.set_charlie(new_epr, forward_node)

        # clear vlink transmission, vlink is consumed
        #vlink_transmit.dst.trans_registry[vlink_transmit.id]= None
        #vlink_transmit.src.trans_registry[vlink_transmit.id]= None
        self.waiting_for_vlink = False

        self.log_trans(f'performed swap using vlink (({backward_node.name}, {self.own.name}) - ({self.own.name}, {forward_node.name})) -> ({backward_node.name}, {forward_node.name})', transmit=transmit)

        # instruct maintenance to clear memory
        #print(vlink_transmit)
        #cchannel: Optional[ClassicChannel] = self.own.get_cchannel(src_node) 
        #self.send_control(cchannel, src_node, vlink_transmit.id, "vlink", "vlink maintenance")

        # treat this same way as physical qubit transmission by sending recvqubitevent
        send_event = RecvQubitOverVL(self._simulator.current_time, qubit=new_epr, src=backward_node, dest=forward_node, vlink_transmit_id=vlink_transmit.id, by=self) # no delay on vlinks, just use current time
        self._simulator.add_event(send_event)

