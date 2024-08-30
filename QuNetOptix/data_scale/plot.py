import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import norm

# TODO election pllot

df = pd.read_csv('data_scale/5x_vlink_sendrate.csv')

df = df.iloc[0::2]
nodes_number = df['n'].tolist()
throughput = df['throughput'].tolist()
vlink_throughput = df['vlink_throughput'].tolist()

plt.style.use('fivethirtyeight')
plt.style.use('grayscale')

def save_plot(x, y, y_vlink):
    marker = None
    linewidth = 3.5
    alpha = 0.5
    line_alpha = 1
    plt.scatter(x, y, label='no vlinks', color='r', marker='o', alpha=alpha)
    plt.scatter(x, y_vlink, label='vlinks', color='b', marker='s', alpha=alpha)

    def falling_exp(x, a, b, c):
        return a * np.exp(-b * x) + c

    params, cov = curve_fit(falling_exp, x, y, p0=[100, 0.01, 0])
    vlink_params, vlink_cov = curve_fit(falling_exp, x, y_vlink, p0=[100, 0.01, 0])

    x_fit = np.linspace(min(x), max(x), 100)
    y_fit = falling_exp(x_fit, *params)
    vlink_y_fit = falling_exp(x_fit, *vlink_params)

    plt.plot(x_fit, y_fit, color='r', linestyle='dashed', alpha=line_alpha, linewidth=linewidth)
    plt.plot(x_fit, vlink_y_fit, color='b', linestyle='dashed', alpha=line_alpha, linewidth=linewidth)


    plt.ylabel('Throughput (ep/s)', fontweight='bold')
    plt.xlabel('# of nodes', fontweight='bold')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('data_scale/5x_vlink_rate.svg', format='svg')

save_plot(nodes_number, throughput, vlink_throughput)




