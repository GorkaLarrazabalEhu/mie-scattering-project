import numpy as np
import matplotlib.pyplot as plt
import sys
import matplotlib.patches as patches
import os
import matplotlib as mpl
from scipy.stats import binned_statistic_2d

if len(sys.argv) > 1:
    # Use command-line arguments
    file = sys.argv[1]
    field_type = sys.argv[2]          # "Electric", "Magnetic", "Poynting"
    selected_options = sys.argv[3:-1]  # all but last arg
    save_dir = sys.argv[-1] if len(sys.argv) > 3 else None
else:
    # Interactive mode
    print("No command-line arguments detected. Switching to interactive mode.\n")

    file = input("Enter file path: ").strip()

    field_type = input(
        'Enter field type ("Electric", "Magnetic", "Poynting"): '
    ).strip()

    options_input = input(
        "Enter selected options (comma separated, or leave empty): "
    ).strip()

    if options_input:
        selected_options = [opt.strip() for opt in options_input.split(",")]
    else:
        selected_options = []

    save_dir = input(
        "Enter save directory (or leave empty for None): "
    ).strip()

    if save_dir == "":
        save_dir = None

# ----------------------------
# Detect if last argument is a folder
# ----------------------------
if save_dir and os.path.isdir(save_dir):
    mpl.rcParams['savefig.directory'] = os.path.abspath(save_dir)
    print(f"Default save folder set to: {mpl.rcParams['savefig.directory']}")
else:
    if len(sys.argv) > 1:
        # If running from CLI and last argument is NOT a folder
        selected_options = sys.argv[3:]
    save_dir = None

with open(file) as f:
    if f.readline().strip() == "run number:":
        runNumber = f.readline().split()
        numberOfSpheres = int(f.readline().strip())
        i = 3
        spheres = []
        for _ in range(numberOfSpheres):
            i += 1
            x, y, z, radius = [float(e) for e in f.readline().strip().split()]
            spheres.append(plt.Circle((x, z), radius, color='black', fill=False))
        numberOfLayers = int(f.readline().strip())
        i += 1
        layers = []
        for _ in range(numberOfLayers):
            i += 1
            height = float(f.readline().strip())
            layers.append(height)
        nfMaxBorder = [float(e) for e in f.readline().strip().split()]
        nfMinBorder = [float(e) for e in f.readline().strip().split()]
        gridlines = [float(e) for e in f.readline().strip().split()]
        i += 3

raw_data = np.loadtxt(file, skiprows=i)

# === Rebin if too many points ===
MAX_GRID = 500
# if len(raw_data) > MAX_GRID**2:
if False:  # disable rebinning for now
    print(f"Large dataset ({len(raw_data)} points), rebinning to {MAX_GRID}x{MAX_GRID} grid...")
    x = raw_data[:, 0]
    z = raw_data[:, 2]
    rebinned = []
    for col in range(raw_data.shape[1]):
        stat, x_edges, z_edges, _ = binned_statistic_2d(
            x, z, raw_data[:, col],
            statistic="mean", bins=[MAX_GRID, MAX_GRID]
        )
        x_centers = 0.5 * (x_edges[:-1] + x_edges[1:])
        z_centers = 0.5 * (z_edges[:-1] + z_edges[1:])
        X, Z = np.meshgrid(x_centers, z_centers, indexing="xy")
        if col == 0:
            x_out, z_out = X.ravel(), Z.ravel()
            rebinned.append(x_out)
            rebinned.append(np.zeros_like(x_out))  # y=0
            rebinned.append(z_out)
        rebinned.append(stat.T.ravel())
    data = np.vstack(rebinned).T
else:
    data = raw_data

# === helpers ===
def getFields(data):
    paralelE = [data[:, 3], data[:, 4], data[:, 5], data[:, 6], data[:, 7], data[:, 8]]
    paralelH = [data[:, 9], data[:, 10], data[:, 11], data[:, 12], data[:, 13], data[:, 14]]
    perpendE = [data[:, 15], data[:, 16], data[:, 17], data[:, 18], data[:, 19], data[:, 20]]
    perpendH = [data[:, 21], data[:, 22], data[:, 23], data[:, 24], data[:, 25], data[:, 26]]
    return paralelE, paralelH, perpendE, perpendH

paralelE, paralelH, perpendE, perpendH = getFields(data)

E1 = np.array(paralelE) + np.array(perpendE)
H1 = np.array(paralelH) + np.array(perpendH)
E = [E1[0] + 1.0j*E1[1], E1[2] + 1.0j*E1[3], E1[4] + 1.0j*E1[5]]
H = [H1[0] + 1.0j*H1[1], H1[2] + 1.0j*H1[3], H1[4] + 1.0j*H1[5]]

def poynting_vector(vec1, vec2):
    return 0.5 * np.real(np.cross(vec1, np.conjugate(vec2), axis=0))

def plot_contour_subplot(ax, x, z, field_data, title, spheres, layers):
    grid_size = int(np.sqrt(len(x)))
    x = x.reshape((grid_size, grid_size))
    z = z.reshape((grid_size, grid_size))
    field_data = field_data.reshape((grid_size, grid_size))
    contour = ax.contour(x, z, field_data, colors="black", levels=50, linewidths=0.1)
    contourf = ax.contourf(x, z, field_data, cmap="viridis", levels=100, extend="both") 
    ax.set_xlabel('x')
    ax.set_ylabel('z')
    ax.set_title(title)
    for sphere in spheres:
        ax.add_patch(patches.Circle(sphere.get_center(), sphere.radius, color='black', fill=False))
    for height in layers:
        ax.axhline(y=height, color='black')
    return contourf

# === Build fields & titles based on selection ===
fields, titles = [], []
if field_type == "Poynting":
    S = poynting_vector(E, H)
    component_map = {"Sx": S[0], "Sy": S[1], "Sz": S[2]}
    for opt in selected_options:
        if opt in component_map:
            fields.append(component_map[opt])
            titles.append(opt)
else:
    component_map = {
        # Electric
        "Re Ex ‖": paralelE[0], "Im Ex ‖": paralelE[1],
        "Re Ey ‖": paralelE[2], "Im Ey ‖": paralelE[3],
        "Re Ez ‖": paralelE[4], "Im Ez ‖": paralelE[5],
        "Re Ex ⟂": perpendE[0], "Im Ex ⟂": perpendE[1],
        "Re Ey ⟂": perpendE[2], "Im Ey ⟂": perpendE[3],
        "Re Ez ⟂": perpendE[4], "Im Ez ⟂": perpendE[5],
        # Magnetic
        "Re Hx ‖": paralelH[0], "Im Hx ‖": paralelH[1],
        "Re Hy ‖": paralelH[2], "Im Hy ‖": paralelH[3],
        "Re Hz ‖": paralelH[4], "Im Hz ‖": paralelH[5],
        "Re Hx ⟂": perpendH[0], "Im Hx ⟂": perpendH[1],
        "Re Hy ⟂": perpendH[2], "Im Hy ⟂": perpendH[3],
        "Re Hz ⟂": perpendH[4], "Im Hz ⟂": perpendH[5],
    }
    for opt in selected_options:
        if opt in component_map:
            fields.append(component_map[opt])
            titles.append(opt)

nplots = len(fields)
ncols = min(3, nplots)
nrows = int(np.ceil(nplots / ncols))
fig, axs = plt.subplots(nrows, ncols, figsize=(6*ncols, 5*nrows))
if nplots == 1:
    axs = np.array([axs])
axs = axs.flatten()

fig.subplots_adjust(right=0.8)
cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])

for ax, field_data, title in zip(axs, fields, titles):
    contourf = plot_contour_subplot(ax, data[:,0], data[:,2], field_data, title, spheres, layers)

fig.colorbar(contourf, cax=cbar_ax, label='Field Magnitude')
plt.show()
