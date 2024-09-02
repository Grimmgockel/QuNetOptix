import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import FancyArrowPatch

# Create a graph object
G = nx.Graph()

# Add nodes
G.add_nodes_from(range(1, 6))

# Add edges to form a line topology
G.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 5)])

# Define position for each node in a line layout
pos = {1: (0, 0), 2: (1, 0), 3: (2, 0), 4: (3, 0), 5: (4, 0)}

# Define edge styles and widths
edge_styles = ['dotted' if (u == 2 and v == 3) or (u == 3 and v == 4) else 'solid'
                for u, v in G.edges()]
edge_widths = [2 if (u == 2 and v == 3) or (u == 3 and v == 4) else 3
               for u, v in G.edges()]  # Adjust width values as needed

# Define custom labels for nodes
custom_labels = {4: 'n-1', 5: 'n'}

# Draw the graph with larger nodes
fig, ax = plt.subplots()

# Draw nodes and edges using NetworkX
nx.draw(G, pos, with_labels=True, node_size=2000, node_color='white', edge_color='gray', 
        linewidths=2, edgecolors=['black' if node != 3 else 'white' for node in G.nodes()],
        font_size=16, font_weight='bold', labels={**{n: '' if n == 3 else n for n in G.nodes()}, **custom_labels},
        style=edge_styles, width=edge_widths, ax=ax)

# Draw the curved line between nodes 2 and 4
curve_pos = [(pos[2][0], pos[2][1]), 
             (0.5 * (pos[2][0] + pos[4][0]), 0.5 * (pos[2][1] + pos[4][1]) - 0.5),  # More curvature
             (pos[4][0], pos[4][1])]

# Draw the curve manually
curve = FancyArrowPatch(curve_pos[0], curve_pos[2], connectionstyle="arc3,rad=.5", color="blue", linewidth=2, arrowstyle='-|>', mutation_scale=10)
ax.add_patch(curve)

# Add label to the curve at the bottom
label_pos = (0.5 * (curve_pos[0][0] + curve_pos[2][0]), 0.5 * (curve_pos[0][1] + curve_pos[2][1]) - 0.6)
ax.text(label_pos[0], label_pos[1], 'vlink', fontsize=16, ha='center', color='blue')

# Set title and show plot
plt.axis('off')
plt.savefig('final_plots/poc/net_setup.svg', format='svg')
