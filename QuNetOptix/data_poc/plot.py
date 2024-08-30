import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('data_poc/poc.csv')

number_nodes = df['n'].tolist()

throughput = df['throughput'].tolist()
vlink_throughput = df['vlink_throughput'].tolist()

generation_latency_max = df['generation_latency_max'].tolist()
vlink_generation_latency_max = df['vlink_generation_latency_max'].tolist()

generation_latency_min = df['generation_latency_min'].tolist()
vlink_generation_latency_min = df['vlink_generation_latency_min'].tolist()

generation_latency_agg = df['generation_latency_agg'].tolist()
vlink_generation_latency_agg = df['vlink_generation_latency_agg'].tolist()

generation_latency_avg = df['generation_latency_avg'].tolist()
vlink_generation_latency_avg = df['vlink_generation_latency_avg'].tolist()

fidelity = df['fidelity_avg'].tolist()
vlink_fidelity = df['vlink_fidelity_avg'].tolist()

swaps = df['swaps'].tolist()
vlink_swaps = df['vlink_swaps'].tolist()
c_message_count = df['c_message_count'].tolist()
vlink_c_message_count = df['vlink_c_message_count'].tolist()
q_message_count = df['q_message_count'].tolist()
vlink_q_message_count = df['vlink_q_message_count'].tolist()

plt.style.use('fivethirtyeight')
plt.style.use('grayscale')
marker = None
markersize = None
linewidth = 3.5

# THROUGHPUT
'''
plt.plot(number_nodes, throughput, label='no vlinks', marker=marker, markersize=markersize, color='red', linewidth=linewidth)    
plt.plot(number_nodes, vlink_throughput, label='vlinks', marker=marker,  markersize=markersize, color='blue', linewidth=linewidth)    
plt.xlabel('# of nodes', fontweight='bold')
plt.ylabel('Througput (ep/s)', fontweight='bold')
plt.legend()
plt.ylim(bottom=0)
plt.tight_layout()
plt.savefig('data_poc/throughput.svg', format='svg')


# MAX LATENCY
plt.plot(number_nodes, generation_latency_max, label='no vlinks', marker=marker, markersize=markersize, color='red', linewidth=linewidth)    
plt.plot(number_nodes, vlink_generation_latency_max, label='vlinks', marker=marker,  markersize=markersize, color='blue', linewidth=linewidth)    
plt.xlabel('# of nodes', fontweight='bold')
plt.ylabel('Latency (s)', fontweight='bold')
plt.legend()
plt.ylim(bottom=0)
plt.tight_layout()
plt.savefig('data_poc/max_latency.svg', format='svg')

# MIN LATENCY
plt.plot(number_nodes, generation_latency_min, label='no vlinks', marker=marker, markersize=markersize, color='red', linewidth=linewidth)    
plt.plot(number_nodes, vlink_generation_latency_min, label='vlinks', marker=marker,  markersize=markersize, color='blue', linewidth=linewidth)    
plt.xlabel('# of nodes', fontweight='bold')
plt.ylabel('Latency (s)', fontweight='bold')
plt.legend()
plt.ylim(bottom=0)
plt.tight_layout()
plt.savefig('data_poc/min_latency.svg', format='svg')

# AVG LATENCY
plt.plot(number_nodes, generation_latency_avg, label='no vlinks', marker=marker, markersize=markersize, color='red', linewidth=linewidth)    
plt.plot(number_nodes, vlink_generation_latency_avg, label='vlinks', marker=marker,  markersize=markersize, color='blue', linewidth=linewidth)    
plt.xlabel('# of nodes', fontweight='bold')
plt.ylabel('Latency (s)', fontweight='bold')
plt.legend()
plt.ylim(bottom=0)
plt.tight_layout()
plt.savefig('data_poc/avg_latency.svg', format='svg')


# AGG LATENCY
plt.plot(number_nodes, generation_latency_agg, label='no vlinks', marker=marker, markersize=markersize, color='red', linewidth=linewidth)    
plt.plot(number_nodes, vlink_generation_latency_agg, label='vlinks', marker=marker,  markersize=markersize, color='blue', linewidth=linewidth)    
plt.xlabel('# of nodes', fontweight='bold')
plt.ylabel('Latency (s)', fontweight='bold')
plt.legend()
plt.ylim(bottom=0)
plt.tight_layout()
plt.savefig('data_poc/agg_latency.svg', format='svg')

'''
# FIDELITY
plt.plot(number_nodes, fidelity, label='no vlinks', marker=marker, markersize=markersize, color='red', linewidth=linewidth)    
plt.plot(number_nodes, vlink_fidelity, label='vlinks', marker=marker,  markersize=markersize, color='blue', linewidth=linewidth)    
plt.xlabel('# of nodes', fontweight='bold')
plt.ylabel('Fidelity', fontweight='bold')
plt.legend()
plt.ylim(bottom=0)
plt.tight_layout()
plt.savefig('data_poc/fidelity.svg', format='svg')


# TRAFFIC

# C MESSAGES
fig, axs = plt.subplots(1, 2, figsize=(12, 4))
axs[0].plot(number_nodes, c_message_count, label='no vlinks', color='r')
axs[0].set_xlabel('# of nodes')
axs[0].set_ylabel('cMsgs sent')
axs[0].set_ylim(bottom=0)
axs[0].legend()
axs[1].plot(number_nodes, vlink_c_message_count, label='vlinks', color='b')
axs[1].set_xlabel('# of nodes')
axs[1].set_ylabel('cMsgs sent')
axs[1].set_ylim(0, 3700)
axs[1].legend()
plt.tight_layout()
plt.savefig('data_poc/traffic_cmsgs.svg', format='svg')

# Q MESSAGES
fig, axs = plt.subplots(1, 2, figsize=(12, 4))
axs[0].plot(number_nodes, q_message_count, label='no vlinks', color='r')
axs[0].set_xlabel('# of nodes')
axs[0].set_ylabel('Qubits sent')
axs[0].set_ylim(bottom=0)
axs[0].legend()
axs[1].plot(number_nodes, vlink_q_message_count, label='vlinks', color='b')
axs[1].set_xlabel('# of nodes')
axs[1].set_ylabel('Qubits sent')
axs[1].set_ylim(bottom=0)
axs[1].legend()
plt.tight_layout()
plt.savefig('data_poc/traffic_qmsgs.svg', format='svg')

# SWAP OPERATIONS
fig, axs = plt.subplots(1, 2, figsize=(12, 4))
axs[0].plot(number_nodes, swaps, label='no vlinks', color='r')
axs[0].set_xlabel('# of nodes')
axs[0].set_ylabel('Average # of\nswap operations')
axs[0].set_ylim(bottom=0)
axs[0].legend()
axs[1].plot(number_nodes, vlink_swaps, label='vlinks', color='b')
axs[1].set_xlabel('# of nodes')
axs[1].set_ylabel('Average # of\nswap operations')
axs[1].set_ylim(bottom=0)
axs[1].legend()
plt.tight_layout()
plt.savefig('data_poc/swap_ops.svg', format='svg')