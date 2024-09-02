import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import norm

def poly(x, a, b, c, d):
    return a*x**3 + b*x**2 + c*x + d

def falling_exp(x, a, b, c):
    return a * np.exp(-b * x) + c

reg_func = falling_exp

def custom_plot(x, y, color, marker, label):
    linewidth = 3
    alpha = 0.4
    line_alpha = 0.8
    plt.plot(x, y, label=label, color=color, marker=marker, alpha=alpha, linestyle='dotted', linewidth=2)


    params, cov = curve_fit(reg_func, x, y, p0=[max(y), 0.01, min(y)], maxfev=10000)

    x_fit = np.linspace(min(x), max(x), 100)
    y_fit = reg_func(x_fit, *params)

    plt.plot(x_fit, y_fit, color=color, alpha=line_alpha, linewidth=linewidth)



df = pd.read_csv('data_poc/poc.csv')

df = df[0::5]
X = df['n'].tolist()
Y = df['generation_latency_agg'].tolist()
Y_vlink = df['vlink_generation_latency_agg'].tolist()


# convert to ms
#Y = [time * 1000 for time in Y]
#Y_vlink = [time * 1000 for time in Y_vlink]


plt.style.use('fivethirtyeight')
plt.style.use('grayscale')
plt.plot(X, Y, 'r', marker='o', label='no vlinks', alpha=0.8, linewidth=2)
plt.plot(X, Y_vlink, 'b', marker='s', label='vlinks', alpha=0.8, linewidth=2)

plt.annotate('~5s', 
             xy=(85, 5),  # Mid-point for annotation
             xytext=(85, 24),  # Adjust text position
             arrowprops=dict(arrowstyle='->', color='black', lw=1),
             fontsize=12, color='black')

plt.ylabel('Latency (s)', fontweight='bold')
plt.xlabel('# of nodes', fontweight='bold')
plt.ylim(bottom=0)
plt.legend()
plt.grid(True, alpha=0.7, linewidth=0.5)
plt.tight_layout()

#plt.show()
plt.savefig("final_plots/poc/latency/agg.svg", format='svg')


