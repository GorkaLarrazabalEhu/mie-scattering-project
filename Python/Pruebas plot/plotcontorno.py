import numpy as np
import matplotlib.pyplot as plt

data = np.loadtxt("C:\\Gorka\\UNI\\TFG\\code\\Python\\Pruebas plot\\nf-fig3a.dat", skiprows=9)
x = data[:, 0]
y = data[:,1]
z = data[:, 2]

#paralel E, H 
# pae = [data[:, 3], data[:, 4], data[:, 5], data[:, 6], data[:, 7], data[:, 8]]
# pah = [data[:, 9], data[:, 10], data[:, 11], data[:, 12], data[:, 13], data[:, 14]]

#perpendicular E, H
pee = [data[:, 15], data[:, 16], data[:, 17], data[:, 18], data[:, 19], data[:, 20]]
# peh = [data[:, 21], data[:, 22], data[:, 23], data[:, 24], data[:, 25], data[:, 26]]

reEx = pee[2]
imEx = pee[3]


# determinar las dimensiones de la red (grid)
grid_size = int(np.sqrt(len(x)))
x = x.reshape((grid_size, grid_size))
z = z.reshape((grid_size, grid_size))
reEx = reEx.reshape((grid_size, grid_size))
imEx = imEx.reshape((grid_size, grid_size))

num_levels = 19  # Ajustar el numero de niveles
data_min = np.min(reEx)
data_max = np.max(reEx)
contour_levels = np.linspace(data_min, data_max, num_levels)

# Crear el contorno
plt.figure(figsize=(8, 6))
plt.contour(x, z, reEx,colors = "black",extend="both", levels = 19,linewidths=0.6)
plt.contourf(x, z, reEx, cmap="viridis", levels=contour_levels ,extend="both")
plt.xlabel('x')
plt.ylabel('z')
plt.title('Magnitud del campo eléctrico')
plt.colorbar(label='Magnitud del campo Eléctrico')
plt.grid(False)

sphere1 = plt.Circle((-2.500, -10.000), 10, color='black', fill=False)  # Centered at (0,0) with radius 1.5
sphere2 = plt.Circle((5.000, 10.900), 5, color='black', fill=False)  # Centered at (0,0) with radius 1.5
plt.gca().add_patch(sphere1)
plt.gca().add_patch(sphere2)

plt.axhline(y=0, color='black')    # Horizontal line at height 0
plt.axhline(y=5.9, color='black')  # Horizontal line at height 5.9
plt.show()