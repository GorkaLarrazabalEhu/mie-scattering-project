import numpy as np
import matplotlib.pyplot as plt
import sys
import matplotlib.patches as patches


# file = "C:\\Gorka\\UNI\\TFG\\code\\Python\\Pruebas plot\\nf-fig3a.dat"
# file = "C:\\Gorka\\UNI\\TFG\\code\\Fortran\\Programa\\dos esferas en linea\\mas grandes\\nf-2-a-gauss.dat"
# file = "C:\\Gorka\\UNI\\TFG\\code\\Fortran\\Programa\\nf-2-esferas-en-linea.dat"
# file = "C:\\Gorka\\UNI\\TFG\\code\\Fortran\\Programa\\nf-1-esfera.dat"
file = sys.argv[1]
isPoynting = True
if sys.argv[2] != "Poynting Vector":
    isPoynting = False
# print("isPoynting = ", isPoynting)

with open(file) as f:
    if f.readline().strip() == "run number:":
        runNumber = f.readline().split()
        numberOfSpheres = int(f.readline().strip())
        i = 3
        spheres = []
        for _ in range(numberOfSpheres):
            i += 1
            #por ahora voy a hacerlo asi porque no se hacer la esfera
            x, y, z, radius = [float(element) for element in f.readline().strip().split()]

            sphere1 = plt.Circle((x, z), radius, color='black', fill=False)  # Centered at (x, z) with radius "radius"
            spheres.append(sphere1)
        numberOfLayers = int(f.readline().strip())
        i += 1
        layers = []
        for _ in range(numberOfLayers):
            i += 1
            height = float(f.readline().strip())
            layers.append(height)
        nfMaxBorder = [float(element) for element in f.readline().strip().split()]
        nfMinBorder = [float(element) for element in f.readline().strip().split()]
        gridlines = [float(element) for element in f.readline().strip().split()]
        i += 3

# print(*spheres)
data = np.loadtxt(file, skiprows=i)
x = data[:, 0]
y = data[:, 1]
z = data[:, 2]

def extractData(data):
    x = data[:, 0]
    y = data[:, 1]
    z = data[:, 2]
    return x, y, z

def getFields(data):
    # paralel E, H
    #               Re Ex,       Im Ex,     Re Ey,   Im Ey         Re Ez      Im Ez
    paralelE = [data[:, 3], data[:, 4], data[:, 5], data[:, 6], data[:, 7], data[:, 8]]
    paralelH = [data[:, 9], data[:, 10], data[:, 11], data[:, 12], data[:, 13], data[:, 14]]

    # perpendicular E, H
    perpendE = [data[:, 15], data[:, 16], data[:, 17], data[:, 18], data[:, 19], data[:, 20]]
    perpendH = [data[:, 21], data[:, 22], data[:, 23], data[:, 24], data[:, 25], data[:, 26]]
    return paralelE, paralelH, perpendE, perpendH

paralelE, paralelH, perpendE, perpendH = getFields(data)
E1 = np.array(paralelE) + np.array(perpendE)
H1 = np.array(paralelH) + np.array(perpendH)

E = [E1[0] + 1.0j * E1[1], E1[2] + 1.0j * E1[3], E1[4] + 1.0j * E1[5]]
H = [H1[0] + 1.0j * H1[1], H1[2] + 1.0j * H1[3], H1[4] + 1.0j * H1[5]]

def poynting_vetor(vec1, vec2):
    return 0.5 * np.real(np.cross(vec1, np.conjugate(vec2), axis=0))
    # vec = []
    # vec.append(vec1[1] * np.conjugate(vec2[2]) - vec1[2] * np.conjugate(vec2[1]))
    # vec.append(vec1[2] * np.conjugate(vec2[0]) - vec1[0] * np.conjugate(vec2[2]))
    # vec.append(vec1[0] * np.conjugate(vec2[1]) - vec1[1] * np.conjugate(vec2[0]))
    # return [1/2.0 * vec[0].real, 1/2.0 * vec[1].real, 1/2.0 * vec[2].real]
    # Asi tengo a numpy que me lo haga

def plot_contour_subplot(ax, x, z, field_data, title, spheres, layers):
    # Determine grid dimensions
    grid_size = int(np.sqrt(len(x)))
    x = x.reshape((grid_size, grid_size))
    z = z.reshape((grid_size, grid_size))
    field_data = field_data.reshape((grid_size, grid_size))

    num_levels = 100  # Adjust the number of levels as needed
    data_min = np.min(field_data)
    data_max = np.max(field_data)
    contour_levels = np.linspace(data_min, data_max, num_levels)

    # Create contour plot on the given axis
    contour = ax.contour(x, z, field_data, colors="black", extend="both", levels=num_levels, linewidths=0.1)
    contourf = ax.contourf(x, z, field_data, cmap="viridis", levels=contour_levels, extend="both") 
    ax.set_xlabel('x')
    ax.set_ylabel('z')
    ax.set_title(title)
    
    # Add the spheres to the plot
    for sphere in spheres:
        sphere_copy = patches.Circle(sphere.get_center(), sphere.radius, color='black', fill=False)
        ax.add_patch(sphere_copy)

    # Add the possible layers to the plot
    for height in layers:
        ax.axhline(y=height, color='black')

    return contourf

def create_spheres_and_layers(file_path):
    with open(file_path, 'r') as f:
        numberOfSpheres = int(f.readline().strip())
        spheres = []
        for _ in range(numberOfSpheres):
            x, y, z, radius = [float(element) for element in f.readline().strip().split()]
            sphere = patches.Circle((x, z), radius, color='black', fill=False)  # Centered at (x, z) with radius "radius"
            spheres.append(sphere)
        
        numberOfLayers = int(f.readline().strip())
        layers = []
        for _ in range(numberOfLayers):
            height = float(f.readline().strip())
            layers.append(height)

    return spheres, layers

def doPlot():
    # Plot each field component in a subplot
    for ax, field_data, title in zip(axs.flat, fields, titles):
        contourf = plot_contour_subplot(ax, x, z, field_data, title, spheres, layers)
    # Add a colorbar
    fig.colorbar(contourf, cax=cbar_ax, label='Field Magnitude')
    plt.show()

if isPoynting:
    poynting = poynting_vetor(E, H)
    fields = poynting
    titles = ["S_x", "S_y", "S_z"]

    fig, axs = plt.subplots(1, len(fields), figsize=(18, 6))
    fig.subplots_adjust(right=0.8)
    # fig.subplots_adjust(hspace=0.8, wspace=0.4, right=0.8)
    cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
    doPlot()

else:            
    reEx, imEx, reEy, imEy, reEz, imEz = perpendE[0], perpendE[1], perpendE[2], perpendE[3], perpendE[4], perpendE[5]
    reHx, imHx, reHy, imHy, reHz, imHz = perpendH[0], perpendH[1], perpendH[2], perpendH[3], perpendH[4], perpendH[5]
    repEx, impEx, repEy, impEy, repEz, impEz = paralelE[0], paralelE[1], paralelE[2], paralelE[3], paralelE[4], paralelE[5]
    repHx, impHx, repHy, impHy, repHz, impHz = paralelH[0], paralelH[1], paralelH[2], paralelH[3], paralelH[4], paralelH[5]

    fieldsE = [reEx, imEx, reEy, imEy, reEz, imEz]
    titlesE = ['reEx', 'imEx', 'reEy', 'imEy', 'reEz', 'imEz']

    fieldsH = [reHx, imHx, reHy, imHy, reHz, imHz]
    titlesH = ['reHx', 'imHx', 'reHy', 'imHy', 'reHz', 'imHz']

    fieldsParalelE = [repEx, impEx, repEy, impEy, repEz, impEz]
    titlesParalelE = ['reExPar', 'imExPar', 'reEyPar', 'imEyPar', 'reEzPar', 'imEzPar']

    fieldsParalelH = [repHx, impHx, repHy, impHy, repHz, impHz]
    titlesParalelH = ['reHxPar', 'imHxPar', 'reHyPar', 'imHyPar', 'reHzPar', 'imHzPar']


    fields = fieldsE + fieldsParalelE
    titles = titlesE + titlesParalelE
    
    fig, axs = plt.subplots(4, 3, figsize=(18, 6))
    fig.subplots_adjust(right=0.8)
    # fig.subplots_adjust(hspace=0.8, wspace=0.4, right=0.8)
    cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
    doPlot()
