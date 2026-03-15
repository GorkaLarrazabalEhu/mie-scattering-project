import numpy as np
import matplotlib.pyplot as plt
import sys
import matplotlib.patches as patches
import os
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter
from scipy.stats import binned_statistic_2d

# ===== AJUSTES DE TAMAÑO =====
TITLE_SIZE = 16
LABEL_SIZE = 14
TICK_SIZE = 12
COLORBAR_LABEL_SIZE = 14

FIG_WIDTH_PER_COL = 6
FIG_HEIGHT_PER_ROW = 5

plt.rcParams.update({
    "axes.titlesize": TITLE_SIZE,
    "axes.labelsize": LABEL_SIZE,
    "xtick.labelsize": TICK_SIZE,
    "ytick.labelsize": TICK_SIZE,
    "lines.linewidth": 1.5,
})

if len(sys.argv) > 1:
    # Use command-line arguments
    file = sys.argv[1]
    field_type = sys.argv[2]          # "Electric", "Magnetic", "Poynting"
    Ls = float(sys.argv[-2])
    selected_options = sys.argv[3:-2]  # all but last arg
    save_dir = sys.argv[-1] if len(sys.argv) > 4 else None
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
    x_plot = data[:, 0] / Ls
    z_plot = data[:, 2] / Ls
    # Scale spheres (x,z centers and radius)
    spheres_plot = []
    for sph in spheres:
        (xc, zc) = sph.get_center()
        r = sph.radius
        spheres_plot.append(plt.Circle((xc / Ls, zc / Ls),
                            r / Ls, color="black", fill=False))

    # Scale layer heights (z positions)
    layers_plot = [h / Ls for h in layers]
# === helpers ===
def getFields(data):
    paralelE = [data[:, 3], data[:, 4], data[:, 5], data[:, 6], data[:, 7], data[:, 8]]
    paralelH = [data[:, 9], data[:, 10], data[:, 11], data[:, 12], data[:, 13], data[:, 14]]
    perpendE = [data[:, 15], data[:, 16], data[:, 17], data[:, 18], data[:, 19], data[:, 20]]
    perpendH = [data[:, 21], data[:, 22], data[:, 23], data[:, 24], data[:, 25], data[:, 26]]
    return paralelE, paralelH, perpendE, perpendH

paralelE, paralelH, perpendE, perpendH = getFields(data)

# Esto no se puede hacer porque no son coherentes
# E1 = np.array(paralelE) + np.array(perpendE)
# H1 = np.array(paralelH) + np.array(perpendH)
# E = [E1[0] + 1.0j*E1[1], E1[2] + 1.0j*E1[3], E1[4] + 1.0j*E1[5]]
# H = [H1[0] + 1.0j*H1[1], H1[2] + 1.0j*H1[3], H1[4] + 1.0j*H1[5]]
E_paralel = [paralelE[0] + 1.0j*paralelE[1], paralelE[2] + 1.0j*paralelE[3], paralelE[4] + 1.0j*paralelE[5]]
H_paralel = [paralelH[0] + 1.0j*paralelH[1], paralelH[2] + 1.0j*paralelH[3], paralelH[4] + 1.0j*paralelH[5]]

E_perp = [perpendE[0] + 1.0j*perpendE[1], perpendE[2] + 1.0j*perpendE[3], perpendE[4] + 1.0j*perpendE[5]]
H_perp = [perpendH[0] + 1.0j*perpendH[1], perpendH[2] + 1.0j*perpendH[3], perpendH[4] + 1.0j*perpendH[5]]

def poynting_vector(vec1, vec2):
    return 0.5 * np.real(np.cross(vec1, np.conjugate(vec2), axis=0))


def plot_contour_subplot(ax, x, z, field_data, title, spheres, layers):
    grid_size = int(np.sqrt(len(x)))
    x = x.reshape((grid_size, grid_size))
    z = z.reshape((grid_size, grid_size))
    field_data = field_data.reshape((grid_size, grid_size))

    contour = ax.contour(x, z, field_data, colors="black",
                         levels=50, linewidths=0.1)
    contourf = ax.contourf(
        x, z, field_data, cmap="viridis", levels=100, extend="both")


    # set the greek letters mu for the units
    ax.set_xlabel('x ($\mu$m)', fontsize=LABEL_SIZE)
    ax.set_ylabel('z ($\mu$m)', fontsize=LABEL_SIZE)
    ax.set_title(title, fontsize=TITLE_SIZE)
    ax.tick_params(axis='both', labelsize=TICK_SIZE)

    for sphere in spheres:
        ax.add_patch(patches.Circle(sphere.get_center(), sphere.radius,
                                    color='black', fill=False))
    for height in layers:
        ax.axhline(y=height, color='black')


    return contourf


def sort_key(title: str):
    # Order within each family
    comp_priority = {"Ex": 0, "Ey": 1, "Ez": 2,
                     "Hx": 0, "Hy": 1, "Hz": 2,
                     "Sx": 0, "Sy": 1, "Sz": 2}
    ri_priority = {"Re": 0, "Im": 1}
    pol_priority = {"‖": 0, "⟂": 1, "": 0}  # no pol -> treat as "first"

    parts = title.split()

    # Defaults for missing pieces
    ri = ""      # no Re/Im
    comp = ""    # component token
    pol = ""     # no polarization

    if len(parts) == 1:
        # e.g. "Sx", "Sy", "Sz"
        comp = parts[0]

    elif len(parts) == 2:
        # e.g. "Re Sx" (if you ever do this) or "Im Sz"
        ri, comp = parts

    else:
        # e.g. "Re Ex ‖"
        ri, comp, pol = parts[0], parts[1], parts[2]

    # Family priority (optional): put E first, then H, then S (or whatever you want)
    # Remove if you don't care.
    if comp.startswith("E"):
        family = 0
    elif comp.startswith("H"):
        family = 1
    elif comp.startswith("S"):
        family = 2
    else:
        family = 99

    return (
        family,
        comp_priority.get(comp, 99),
        ri_priority.get(ri, 99),
        pol_priority.get(pol, 99),
        title  # final stable tie-breaker
    )
# === Build fields & titles based on selection ===
fields, titles = [], []
if field_type == "Poynting":
    # ESTO NO SE PUEDE PQ NO ES COHERENTE
    # S = poynting_vector(E, H)
    
    S_par = poynting_vector(E_paralel, H_paralel)
    S_perp = poynting_vector(E_perp, H_perp)
    S = 0.5 * (S_par + S_perp)
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

# sort everything before plotting
sorted_pairs = sorted(zip(titles, fields), key=lambda x: sort_key(x[0]))
titles, fields = zip(*sorted_pairs)

titles = list(titles)
fields = list(fields)

nplots = len(fields)

if nplots <= 3:
    nrows, ncols = 1, nplots          # 1x2, 1x3
elif nplots == 4:
    nrows, ncols = 2, 2               # 2x2
elif nplots in (5, 6):
    nrows, ncols = 2, 3               # 2x3 
else:
    ncols = 3
    nrows = int(np.ceil(nplots / ncols))

fig, axs = plt.subplots(
    nrows, ncols,
    figsize=(FIG_WIDTH_PER_COL*ncols, FIG_HEIGHT_PER_ROW*nrows),
    sharex=True, sharey=True,
    constrained_layout=True
)

# axs = np.atleast_1d(axs).ravel()
axs = np.atleast_1d(axs)

# If 2D grid, transpose first
if axs.ndim == 2:
    axs = axs.T.ravel()
else:
    axs = axs.ravel()


contourf_last = None
for i in range(nrows * ncols):
    ax = axs[i]

    if i < nplots:
        contourf_last = plot_contour_subplot(
            ax, x_plot, z_plot,
            fields[i], titles[i],
            spheres_plot, layers_plot
        )

        # Only keep labels where they help (layout cleaner, content same)
        r = i % nrows
        c = i // nrows

        if r != nrows - 1:
            ax.set_xlabel("")
        if c != 0:
            ax.set_ylabel("")
    else:
        # Hide unused axes so the grid looks tidy
        ax.set_visible(False)

# One shared colorbar (same data as before: last contourf)
if contourf_last is not None:
    cbar = fig.colorbar(contourf_last, ax=axs[:nplots], shrink=0.95, pad=0.02)
    cbar.set_label('Field Magnitude', fontsize=COLORBAR_LABEL_SIZE)
    cbar.ax.tick_params(labelsize=TICK_SIZE)

plt.show()
