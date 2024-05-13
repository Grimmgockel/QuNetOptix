import qns.utils.log as log
from oracle import NetworkOracle
from metadata import SimData
from config import Config
from vl_net_graph import GraphAnimation
from config import Job
from qns.network.topology import RandomTopology
from vl_topo import CustomDoubleStarTopology, CustomLineTopology
from qns.network.protocol import EntanglementDistributionApp
from typing import List
import matplotlib.pyplot as plt

# TODO FOR NAVIGATION
from qns.models.epr import BaseEntanglement, BellStateEntanglement, MixedStateEntanglement, WernerStateEntanglement
from qns.models.delay import DelayModel, NormalDelayModel, UniformDelayModel, ConstantDelayModel
from qns.entity.cchannel import ClassicChannel
from qns.entity.qchannel import QuantumChannel, QubitLossChannel
from qns.entity.memory import QuantumMemory
# TODO i need all the hardware params now - LOOK AT GUUS DISSERTATION
# WernerStateEntanglement - make it work

# ClassicChannel
# - bandwidth
# - delay
# - length
# - drop_rate
# - max_buffer_size

# QubitLossChannel
# - bandwidth
# - delay
# - p_init
# - attenuation_rate
# - max_buffer_size
# - length
# - decoherence_rate
# - store_error_model

# ClassicChannel
# - bandwidth
# - delay
# - drop_rate
# - max_buffer_size
# - length

# QuantumMemory
# - delay
# - decoherence_rate
# - store_error_model

# MISC 
# - vlink to distro send_rate ratio


# TODO implement basic proof of concept 'poc.py' for shortcut links, where paths with increasing lengths are shortcutted and EP are constantly distributed
# TODO save experiments into results.csv
# TODO look into docs for multicore sim

# TODO REFACTOR swapping code still duplicate
# TODO a lot of clunky plotting code left in the application classes

# TODO implement vlink selection
# TODO implement custom waxman topology
# TODO compare base routing with custom routing in basic plot
# TODO think about error/loss/decoherence models, entanglement models and hardware details
if __name__ == '__main__': 
    oracle = NetworkOracle()

    for i in range(5, 16):
        nodes_number = 10
        config = Config(
            ts=0,
            te=10,
            acc=10000000000000,
            vlink_send_rate=5,
            send_rate=5,
            topo=CustomLineTopology(nodes_number=nodes_number),
            job = Job.custom(sessions=[('n1', f'n{nodes_number}')]),
            #continuous_distro=False,
            vlinks=[('n2', f'n{nodes_number-1}')],
            #schedule_n_vlinks=1,
        )

        metadata: SimData = oracle.run(config, loglvl=log.logging.INFO)
        print(f'distros: {metadata.success_count}/{metadata.send_count}, vlinks: {metadata.df['vlink_success_count'][0]}/{metadata.df['vlink_send_count'][0]}')
        #print(f'remaining memory usage: {metadata.df['remaining_mem_usage'][0]}')
        #print(metadata.df['success_count'][0])
        #print(metadata.throughput)

        #for key, value in metadata.distro_results.items():
            #print(f'---- SUCCESSFUL DISTRIBUTION ----\nID: {key}\nSRC: {value.src_result}\nDST: {value.dst_result}')
        #ga: GraphAnimation = oracle.entanglement_animation(f'demo.gif', fps=5)




# TODO IMPLEMENT THE ASYNC READ/WRITE
# TODO MAKE PLOTS OF POC EXPERIMENT
# TODO SHOOT MSG TO BECKE
# TODO WRITE CV AND START APPLYING
# TODO WRITE BASICS CHAPTER AND WATCH OUT FOR PHYSICAL PARAMS WHILE READING



