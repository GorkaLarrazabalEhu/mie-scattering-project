import numpy as np
import matplotlib.pyplot as plt

# Define the function
def f(x, y):
    return np.sin(x) * np.cos(y)

# Generate 1D arrays for x and y coordinates
x = np.linspace(0, 2*np.pi, 10000)
y = np.linspace(0, 2*np.pi, 10000)

# Create the meshgrid
X, Y = np.meshgrid(x, y)

# Evaluate the function over the grid
Z = f(X, Y)

# Plot the result
plt.contourf(X, Y, Z, cmap='plasma', levels=20)
plt.colorbar()
plt.xlabel('X')
plt.ylabel('Y')
plt.title('Contour Plot of f(x, y)')
plt.show()