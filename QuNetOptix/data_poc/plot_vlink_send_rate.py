import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata

# DATA
df = pd.read_csv('data_poc/poc_vlink_send_rate.csv')
send_rates = df['vlink_send_rates'].tolist()
i = len(send_rates)
number_requests = [(i % 10) + 1 for i in range(10 * 10)]
throughputs = df['vlink_throughput'].tolist()
x = number_requests
y = send_rates
z = throughputs

# PLOT
plt.style.use('fivethirtyeight')
plt.style.use('grayscale')
grid_x, grid_y = np.meshgrid(np.linspace(min(x), max(x), 100),
                             np.linspace(min(y), max(y), 100))

# Interpolate the z values on the grid
grid_z = griddata((x, y), z, (grid_x, grid_y), method='cubic')

# Create the plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Plot the surface
surface = ax.plot_surface(grid_x, grid_y, grid_z, cmap='RdBu')

# Add a color bar which maps values to colors
#fig.colorbar(surface, ax=ax, shrink=0.5, aspect=10)

ax.set_xlabel('# of requests', fontweight='bold')
ax.set_ylabel('Vlink rate (Hz)', fontweight='bold')
ax.set_zlabel('Throughput (ep/s)', fontweight='bold')

# Show the plot
plt.tight_layout()
plt.savefig('data_poc/vlink_send_rate_impact.svg', format='svg')