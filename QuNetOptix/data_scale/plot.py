import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline

df = pd.read_csv('data_scale/net_size_waxman.csv')

df = df.groupby('n').mean().reset_index()
nodes_number = df['n'].tolist()
throughput = df['throughput'].tolist()
vlink_throughput = df['vlink_throughput'].tolist()

gen_latency_avg = df['generation_latency_avg'].tolist()
vlink_gen_latency_avg = df['vlink_generation_latency_avg'].tolist()

gen_latency_max = df['generation_latency_max'].tolist()
vlink_gen_latency_max = df['vlink_generation_latency_max'].tolist()

gen_latency_min = df['generation_latency_min'].tolist()
vlink_gen_latency_min = df['vlink_generation_latency_min'].tolist()

gen_latency_agg = df['generation_latency_agg'].tolist()
vlink_gen_latency_agg = df['vlink_generation_latency_agg'].tolist()


plt.style.use('fivethirtyeight')
plt.style.use('grayscale')
marker = None
linewidth = 2

plt.figure(figsize=(18,10))
plt.plot(nodes_number, throughput, label='no vlinks', color='r', marker=marker, linestyle='-')
plt.plot(nodes_number, vlink_throughput, label='vlinks', color='b', marker=marker, linestyle='-')
plt.xlabel('throughput (ep/s)')
plt.ylabel('# of nodes')
plt.legend()
plt.show()

plt.figure(figsize=(18,10))
plt.plot(nodes_number, gen_latency_avg, label='no vlinks', color='r', marker=marker, linestyle='-')
plt.plot(nodes_number, vlink_gen_latency_avg, label='vlinks', color='b', marker=marker, linestyle='-')
plt.xlabel('latency (s)')
plt.ylabel('# of nodes')
plt.legend()
plt.show()

plt.figure(figsize=(18,10))
plt.plot(nodes_number, gen_latency_max, label='no vlinks', color='r', marker=marker, linestyle='-')
plt.plot(nodes_number, vlink_gen_latency_max, label='vlinks', color='b', marker=marker, linestyle='-')
plt.xlabel('latency (s)')
plt.ylabel('# of nodes')
plt.legend()
plt.show()

plt.figure(figsize=(18,10))
plt.plot(nodes_number, gen_latency_min, label='no vlinks', color='r', marker=marker, linestyle='-')
plt.plot(nodes_number, vlink_gen_latency_min, label='vlinks', color='b', marker=marker, linestyle='-')
plt.xlabel('latency (s)')
plt.ylabel('# of nodes')
plt.legend()
plt.show()

plt.figure(figsize=(18,10))
plt.plot(nodes_number, gen_latency_agg, label='no vlinks', color='r', marker=marker, linestyle='-')
plt.plot(nodes_number, vlink_gen_latency_agg, label='vlinks', color='b', marker=marker, linestyle='-')
plt.xlabel('latency (s)')
plt.ylabel('# of nodes')
plt.legend()
plt.show()




