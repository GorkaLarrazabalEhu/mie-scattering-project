import matplotlib.pyplot as plt
import numpy as np

# Generate some data
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)

# Create a figure with two subplots (one row, two columns)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))

# Plot the first subplot
ax1.plot(x, y1, label='sin(x)')
ax1.set_title('Sine Wave')
ax1.set_xlabel('x')
ax1.set_ylabel('sin(x)')
ax1.legend()

# Plot the second subplot
ax2.plot(x, y2, label='cos(x)', color='orange')
ax2.set_title('Cosine Wave')
ax2.set_xlabel('x')
ax2.set_ylabel('cos(x)')
ax2.legend()

# Adjust the layout to prevent overlap
fig.tight_layout()

# Show the plot
plt.show()
