import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import matplotlib as mpl


# =========================
# Global plotting style
# =========================
plt.rcParams.update({
    "xtick.labelsize": 16,
    "ytick.labelsize": 16,
    "axes.titlesize": 16,
    "axes.labelsize": 20,
    "legend.fontsize": 14,
})
plt.rcParams["figure.titlesize"] = 18
plt.rcParams["lines.linewidth"] = 2

# =========================
# Utilities
# =========================


def set_fig_title(fig, title: str):
    try:
        fig.canvas.manager.set_window_title(title)
    except Exception:
        pass


def auto_save_or_show(fig, name, save_dir="."):
    autosave = False
    if autosave:
        outdir = os.path.join(save_dir, "plots")
        os.makedirs(outdir, exist_ok=True)
        outfile = os.path.join(outdir, f"{name}.png")
        fig.savefig(outfile, dpi=300, bbox_inches="tight")
        print(f"Auto-saved: {outfile}")
        plt.close(fig)
    else:
        fig.canvas.draw_idle()
        plt.show(block=True)
        plt.close(fig)


# =========================
# Parsing
# =========================
def parse_runs_with_efficiencies2(filepath):
    with open(filepath, "r", errors="ignore") as f:
        lines = f.read().splitlines()

    runs = []
    pending_eff = None
    i = 0
    nlines = len(lines)

    def parse_totals_line(s):
        parts = [float(t.replace("D", "E")) for t in s.split()]
        if len(parts) != 9:
            raise ValueError("Expected 9 numbers for total efficiencies line.")
        U = parts[0:3]
        P = parts[3:6]
        R = parts[6:9]
        return {
            "unpol": {"Qext": U[0], "Qabs": U[1], "Qsca": U[2]},
            "par":   {"Qext": P[0], "Qabs": P[1], "Qsca": P[2]},
            "perp":  {"Qext": R[0], "Qabs": R[1], "Qsca": R[2]},
        }

    while i < nlines:
        s = lines[i].strip()

        if s == "length, ref index scale factors":
            scale_factors = lines[i + 1].split()
            l_scale = float(scale_factors[0])
            n_ref = float(scale_factors[2])
            n_scale = float(scale_factors[1])
            i += 1
            continue

        if s.lower().startswith("calculation results for run"):
            j = i + 1
            while j < nlines and not lines[j].strip().lower().startswith(
                "total extinction, absorption, scattering efficiencies"
            ):
                j += 1
            if j + 1 < nlines:
                pending_eff = parse_totals_line(lines[j + 1])
            i = j + 2
            continue

        if s == "number directions, number SM elements:":
            parts = lines[i + 1].split()
            n_dir, n_el = int(parts[0]), int(parts[1])
            start = i + 3
            block = []
            for k in range(start, start + n_dir):
                vals = [float(tok.replace("D", "E"))
                        for tok in lines[k].split()]
                block.append(vals)
            arr = np.asarray(block, dtype=float)
            degreeTheta = arr[:, 0]
            radianTheta = np.pi * degreeTheta / 180.0
            S = arr[:, 1:17]

            runs.append({
                "l_scale": l_scale,
                "n_ref": n_ref,
                "n_scale": n_scale,
                "degreeTheta": degreeTheta,
                "radianTheta": radianTheta,
                "S": S,
                "n_elements": n_el,
                "n_directions": n_dir,
                "eff": pending_eff or {
                    "unpol": {"Qext": np.nan, "Qabs": np.nan, "Qsca": np.nan},
                    "par":   {"Qext": np.nan, "Qabs": np.nan, "Qsca": np.nan},
                    "perp":  {"Qext": np.nan, "Qabs": np.nan, "Qsca": np.nan},
                }
            })
            pending_eff = None
            i = start + n_dir
            continue

        i += 1

    return runs


def parse_runs_with_efficiencies(filepath):
    with open(filepath, "r", errors="ignore") as f:
        lines = f.read().splitlines()

    runs = []
    pending_eff = None
    l_scale = n_scale = n_ref = np.nan
    i = 0
    nlines = len(lines)

    def parse_totals_line(s):
        parts = [float(t.replace("D", "E")) for t in s.split()]
        if len(parts) != 9:
            raise ValueError("Expected 9 numbers for total efficiencies line.")
        U, P, R = parts[0:3], parts[3:6], parts[6:9]
        return {
            "unpol": {"Qext": U[0], "Qabs": U[1], "Qsca": U[2]},
            "par":   {"Qext": P[0], "Qabs": P[1], "Qsca": P[2]},
            "perp":  {"Qext": R[0], "Qabs": R[1], "Qsca": R[2]},
        }

    while i < nlines:
        s = lines[i].strip()

        if s == "length, ref index scale factors":
            scale_factors = lines[i + 1].split()
            l_scale = float(scale_factors[0])
            n_scale = float(scale_factors[1])
            n_ref = float(scale_factors[2])
            i += 1
            continue

        if s.lower().startswith("calculation results for run"):
            j = i + 1
            while j < nlines and not lines[j].strip().lower().startswith(
                "total extinction, absorption, scattering efficiencies"
            ):
                j += 1
            if j + 1 < nlines:
                pending_eff = parse_totals_line(lines[j + 1])
            i = j + 2
            continue

        if s == "number directions, number SM elements:":
            parts = lines[i + 1].split()
            n_dir, n_el = int(parts[0]), int(parts[1])
            start = i + 3
            block = []
            for k in range(start, start + n_dir):
                vals = [float(tok.replace("D", "E"))
                        for tok in lines[k].split()]
                block.append(vals)
            arr = np.asarray(block, dtype=float)
            degreeTheta = arr[:, 0]
            radianTheta = np.pi * degreeTheta / 180.0
            S = arr[:, 1:17]

            runs.append({
                "l_scale": l_scale,
                "n_ref": n_ref,
                "n_scale": n_scale,
                "degreeTheta": degreeTheta,
                "radianTheta": radianTheta,
                "S": S,
                "n_elements": n_el,
                "n_directions": n_dir,
                "eff": pending_eff or {
                    "unpol": {"Qext": np.nan, "Qabs": np.nan, "Qsca": np.nan},
                    "par":   {"Qext": np.nan, "Qabs": np.nan, "Qsca": np.nan},
                    "perp":  {"Qext": np.nan, "Qabs": np.nan, "Qsca": np.nan},
                }
            })
            pending_eff = None
            i = start + n_dir
            continue

        i += 1

    if pending_eff is not None:
        runs.append({
            "l_scale": l_scale,
            "n_ref": n_ref,
            "n_scale": n_scale,
            "degreeTheta": None,
            "radianTheta": None,
            "S": None,
            "n_elements": 0,
            "n_directions": 0,
            "eff": pending_eff
        })

    return runs


# =========================
# Physics helpers
# =========================
def compute_g(r):
    """
    Asymmetry parameter  g = <cos theta>  from the scattering matrix S11.

        g = integral[ S11(theta) cos(theta) sin(theta) dtheta ]
            -------------------------------------------------------
            integral[ S11(theta) sin(theta) dtheta ]

    Returns np.nan when the S matrix is not available.
    """
    if r["S"] is None:
        return np.nan
    S11 = r["S"][:, 0]
    theta = r["radianTheta"]
    num = np.trapz(S11 * np.cos(theta) * np.sin(theta), theta)
    den = np.trapz(S11 * np.sin(theta), theta)
    return num / den if den != 0 else np.nan


# =========================
# Plotting (original functions — unchanged)
# =========================
def plot_S11_old(runs, run_ids, save_dir="."):
    fig, (ax1, ax2) = plt.subplots(
        1, 2, subplot_kw={'projection': 'polar'}, figsize=(12, 6)
    )
    for ri in run_ids:
        l_scale = runs[ri]["l_scale"]
        wl = f"{2*np.pi/l_scale:.2f} um"
        r = runs[ri]
        ax1.plot(r["radianTheta"], r["S"][:, 0], label=wl)
        ax2.plot(r["radianTheta"], r["S"][:, 0], label=wl)
    ax1.set_title("S11 (linear scale)")
    ax2.set_title("S11 (log scale)")
    ax2.set_yscale("log")
    ax1.legend(loc="best")
    ax2.legend(loc="best")
    plt.tight_layout()
    set_fig_title(fig, "S11")
    auto_save_or_show(fig, "S11", save_dir)


def plot_S11(runs, run_ids, save_dir=".", skip_run=True, plot_number=5):
    mode = {1, 2}
    mode = {1}
    # mode = 2
    # Filtrar primero los runs que tienen datos
    valid_run_ids = [
        ri for ri in run_ids
        if runs[ri]["S"] is not None
    ]

    # Seleccionar solo algunos runs homogéneamente
    if skip_run and len(valid_run_ids) > plot_number:
        indices = np.linspace(
            0,
            len(valid_run_ids) - 1,
            plot_number,
            dtype=int
        )
        valid_run_ids = [valid_run_ids[i] for i in indices]

    fig, axes = plt.subplots(
        1, len(mode),
        subplot_kw={'projection': 'polar'},
        figsize=(12, 6)
    )

    if not isinstance(axes, (list, np.ndarray)):
        axes = [axes]

    ax_map = {}
    i = 0

    if 1 in mode:
        ax_map[1] = axes[i]
        i += 1

    if 2 in mode:
        ax_map[2] = axes[i]

    has_data = False

    for ri in valid_run_ids:
        r = runs[ri]
        has_data = True

        l_scale = r.get("l_scale", 1.0)
        wl = f"{2*np.pi/l_scale:.2f} $\mu$m"

        if 1 in mode:
            ax_map[1].plot(
                r["radianTheta"],
                r["S"][:, 0],
                label=wl
            )

        if 2 in mode:
            ax_map[2].plot(
                r["radianTheta"],
                r["S"][:, 0],
                label=wl
            )

    if not has_data:
        for ax in axes:
            ax.text(
                0.5, 0.5, "No data",
                transform=ax.transAxes,
                ha='center',
                va='center',
                fontsize=14,
                color='grey'
            )

    if 1 in mode:
        ax_map[1].set_title("S11 (linear scale)", y=1.05, fontsize=16)

    if 2 in mode:
        ax_map[2].set_title("S11 (log scale)", y=1.05)
        ax_map[2].set_yscale("log")

    handles, labels = axes[0].get_legend_handles_labels()

    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=2,
        bbox_to_anchor=(0.5, 0.93),
        fontsize=10
    )

    plt.tight_layout()
    set_fig_title(fig, "S11")
    auto_save_or_show(fig, "S11", save_dir)


def plot_polarization2(runs, run_ids, mode, save_dir="."):
    fig, ax = plt.subplots()
    for ri in run_ids:
        r = runs[ri]
        S = r["S"]
        S11, S21, S31, S41 = S[:, 0], S[:, 4], S[:, 8], S[:, 12]
        DoP = np.sqrt(S21**2 + S31**2 + S41**2)
        DoLP = np.sqrt(S21**2 + S31**2)
        DoCP = np.abs(S41)
        lbl = f"(run {ri+1})" if len(run_ids) > 1 else ""
        if mode == "DOP":
            ax.plot(r["degreeTheta"], DoP, label=f"DoP {lbl}".strip())
            ax.set_ylabel("Degree of Polarization")
        elif mode == "DOLP":
            ax.plot(r["degreeTheta"], DoLP, label=f"DoLP {lbl}".strip())
            ax.set_ylabel("Degree of Linear Polarization")
        elif mode == "DOCP":
            ax.plot(r["degreeTheta"], DoCP, label=f"DoCP {lbl}".strip())
            ax.set_ylabel("Degree of Circular Polarization")
        elif mode == "ALL":
            ax.plot(r["degreeTheta"], DoP,  label=f"DoP {lbl}".strip())
            ax.plot(r["degreeTheta"], DoLP, "--", label=f"DoLP {lbl}".strip())
            ax.plot(r["degreeTheta"], DoCP, ":", label=f"DoCP {lbl}".strip())
            ax.set_ylabel("Polarization degree")
    ax.set_xlabel("Scattering angle (deg)")
    ax.set_title("Polarization properties (unpolarized incidence)")
    ax.legend()
    ax.grid(True)
    set_fig_title(fig, mode)
    auto_save_or_show(fig, mode, save_dir)


def plot_polarization(runs, run_ids, mode, save_dir=".", skip_run=True, plot_number=5):
    # Filtrar runs que sí tienen datos
    valid_run_ids = [
        ri for ri in run_ids
        if runs[ri]["S"] is not None
    ]

    # Seleccionar solo algunos runs homogéneamente
    if skip_run and len(valid_run_ids) > plot_number:
        indices = np.linspace(
            0,
            len(valid_run_ids) - 1,
            plot_number,
            dtype=int
        )
        valid_run_ids = [valid_run_ids[i] for i in indices]

    fig, ax = plt.subplots()
    has_data = False

    for ri in valid_run_ids:
        r = runs[ri]
        has_data = True

        S = r["S"]
        S11, S21, S31, S41 = S[:, 0], S[:, 4], S[:, 8], S[:, 12]

        DoP = np.sqrt(S21**2 + S31**2 + S41**2)
        DoLP = np.sqrt(S21**2 + S31**2)
        DoCP = np.abs(S41)

        l_scale = r.get("l_scale", 1.0)
        wl = f"{2*np.pi/l_scale:.2f} um"

        if mode == "DOP":
            ax.plot(r["degreeTheta"], DoP, label=f"DoP {wl}")
            ax.set_ylabel("Degree of Polarization")

        elif mode == "DOLP":
            ax.plot(r["degreeTheta"], DoLP, label=f"DoLP {wl}")
            ax.set_ylabel("Degree of Linear Polarization")

        elif mode == "DOCP":
            ax.plot(r["degreeTheta"], DoCP, label=f"DoCP {wl}")
            ax.set_ylabel("Degree of Circular Polarization")

        elif mode == "ALL":
            ax.plot(r["degreeTheta"], DoP,  label=f"DoP {wl}")
            ax.plot(r["degreeTheta"], DoLP, "--", label=f"DoLP {wl}")
            ax.plot(r["degreeTheta"], DoCP, ":", label=f"DoCP {wl}")
            ax.set_ylabel("Polarization degree")

    if not has_data:
        ax.text(
            0.5, 0.5, "No data",
            transform=ax.transAxes,
            ha='center', va='center',
            fontsize=14, color='grey'
        )

    ax.set_xlabel(r"$\theta$º")
    ax.set_title("Polarization properties (unpolarized incidence)")
    ax.legend(fontsize=14)
    ax.grid(True)

    set_fig_title(fig, mode)
    auto_save_or_show(fig, mode, save_dir)

def plot_efficiencies(runs, run_ids, save_dir=".", pol="unpol", mode="EFF"):
    x = np.arange(1, len(run_ids) + 1)
    xlabels = []
    for ri in run_ids:
        l_scale = runs[ri]["l_scale"]
        xlabels.append(f"{2*np.pi/l_scale:.2f}")

    y_qext, y_qabs, y_qsca = [], [], []
    for ri in run_ids:
        eff = runs[ri]["eff"][pol]
        y_qext.append(eff["Qext"])
        y_qabs.append(eff["Qabs"])
        y_qsca.append(eff["Qsca"])

    invert_x = False
    if invert_x:
        wavelengths = np.array([float(v) for v in xlabels])
        inv_x = 1 / wavelengths
        order = np.argsort(inv_x)
        inv_x = inv_x[order]
        y_qext = np.array(y_qext)[order]
        y_qabs = np.array(y_qabs)[order]
        y_qsca = np.array(y_qsca)[order]
        x = inv_x
        xlabels = [f"{val:.3f}" for val in inv_x]

    mode = mode.upper()
    valid_modes = ["EFF", "QEXT", "QABS", "QSCA"]
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode '{mode}'. Choose from {valid_modes}.")

    if mode == "EFF":
        C_EXT = "#1f77b4"   # blue  — Q_ext
        C_ABS = "#d62728"   # red   — Q_abs
        C_SCA = "#2ca02c"   # green — Q_sca (secondary axis)

        fig, ax = plt.subplots(figsize=(9, 5))
        axr = ax.twinx()

        ax.plot(x, y_qext, color=C_EXT, label=r"$Q_\mathrm{ext}$")
        ax.plot(x, y_qabs, color=C_ABS, linestyle="--",
                label=r"$Q_\mathrm{abs}$")
        axr.plot(x, y_qsca, color=C_SCA, linestyle=":",
                 label=r"$Q_\mathrm{sca}$")

        ax.set_xlabel(r"Wavelength ($\mu$m)")
        ax.set_ylabel(r"$Q_\mathrm{ext}$,  $Q_\mathrm{abs}$", color="black")
        ax.tick_params(axis="y", labelcolor="black")
        axr.set_ylabel(r"$Q_\mathrm{sca}$", color="black")
        axr.tick_params(axis="y", labelcolor="black")

        # unified legend
        lines = ax.get_lines() + axr.get_lines()
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc="upper right", fontsize=13)

        ax.grid(True)

        max_labels = 10
        step = max(1, len(xlabels) // max_labels)
        x_ticks_to_show = x[::step]
        x_labels_to_show = [xlabels[i] for i in range(0, len(xlabels), step)]
        ax.set_xticks(x_ticks_to_show)
        ax.set_xticklabels(x_labels_to_show, rotation=0)

        fig.suptitle(f"Efficiencies ({pol.capitalize()})")
        fig.tight_layout()
        set_fig_title(fig, f"Efficiencies - {pol.capitalize()}")
        auto_save_or_show(fig, f"EFF_{pol.upper()}", save_dir)
    else:
        y_map = {"QEXT": y_qext, "QABS": y_qabs, "QSCA": y_qsca}
        title = mode.capitalize()
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(x, y_map[mode], marker="")
        ax.set_xlabel("Wavelength (um)")
        ax.set_ylabel(f"{title} ({pol})")
        max_index = np.argmax(y_map[mode])
        print(
            f"Max {title} at wavelength {xlabels[max_index]} um: {y_map[mode][max_index]}")
        max_labels = 10
        step = max(1, len(xlabels) // max_labels)
        x_ticks_to_show = x[::step]
        x_labels_to_show = [xlabels[i] for i in range(0, len(xlabels), step)]
        ax.set_xticks(x_ticks_to_show)
        ax.set_xticklabels(x_labels_to_show, rotation=0)
        ax.grid(True)
        ax.set_title(f"{title} ({pol.capitalize()})")
        set_fig_title(fig, f"{title} - {pol.capitalize()}")
        auto_save_or_show(fig, f"{mode}_{pol.upper()}", save_dir)


def plot_dashboard2(runs, run_ids, save_dir="."):
    import matplotlib.gridspec as gridspec
    fig = plt.figure(figsize=(14, 9))
    gs = gridspec.GridSpec(2, 3, figure=fig)
    ax_s11_lin = fig.add_subplot(gs[0, 0], projection='polar')
    ax_s11_log = fig.add_subplot(gs[0, 1], projection='polar')
    ax_dop = fig.add_subplot(gs[1, 0])
    ax_dolp = fig.add_subplot(gs[1, 1])
    ax_docp = fig.add_subplot(gs[1, 2])
    for ri in run_ids:
        r = runs[ri]
        S = r["S"]
        rad = r["radianTheta"]
        deg = r["degreeTheta"]
        S11, S21, S31, S41 = S[:, 0], S[:, 4], S[:, 8], S[:, 12]
        DoP = np.sqrt(S21**2 + S31**2 + S41**2)
        DoLP = np.sqrt(S21**2 + S31**2)
        DoCP = np.abs(S41)
        lbl = f"Run {ri+1}"
        ax_s11_lin.plot(rad, S11, label=lbl)
        ax_s11_log.plot(rad, S11, label=lbl)
        ax_dop.plot(deg, DoP, label=lbl)
        ax_dolp.plot(deg, DoLP, label=lbl)
        ax_docp.plot(deg, DoCP, label=lbl)
    ax_s11_lin.set_title("S11 (linear)")
    ax_s11_log.set_title("S11 (log)")
    ax_s11_log.set_yscale("log")
    for a, ttl in [(ax_dop, "DoP"), (ax_dolp, "DoLP"), (ax_docp, "DoCP")]:
        a.set_title(ttl)
        a.set_xlabel("Angle (deg)")
        a.set_ylabel("Value")
        a.grid(True)
    handles, labels = ax_dop.get_legend_handles_labels()
    if len(run_ids) > 1:
        fig.legend(handles, labels, loc="lower center",
                   ncol=min(5, len(run_ids)), bbox_to_anchor=(0.5, -0.02))
        fig.subplots_adjust(bottom=0.1)
    fig.tight_layout()
    set_fig_title(fig, "Dashboard")
    auto_save_or_show(fig, "DASHBOARD", save_dir)


def plot_dashboard(runs, run_ids, save_dir="."):
    import matplotlib.gridspec as gridspec
    fig = plt.figure(figsize=(14, 9))
    gs = gridspec.GridSpec(2, 3, figure=fig)
    ax_s11_lin = fig.add_subplot(gs[0, 0], projection='polar')
    ax_s11_log = fig.add_subplot(gs[0, 1], projection='polar')
    ax_dop = fig.add_subplot(gs[1, 0])
    ax_dolp = fig.add_subplot(gs[1, 1])
    ax_docp = fig.add_subplot(gs[1, 2])
    has_data = False
    for ri in run_ids:
        r = runs[ri]
        if r["S"] is not None:
            has_data = True
            S = r["S"]
            rad = r["radianTheta"]
            deg = r["degreeTheta"]
            S11, S21, S31, S41 = S[:, 0], S[:, 4], S[:, 8], S[:, 12]
            DoP = np.sqrt(S21**2 + S31**2 + S41**2)
            DoLP = np.sqrt(S21**2 + S31**2)
            DoCP = np.abs(S41)
            l_scale = r.get("l_scale", 1.0)
            wl = f"{2*np.pi/l_scale:.2f} um"
            ax_s11_lin.plot(rad, S11, label=wl)
            ax_s11_log.plot(rad, S11, label=wl)
            ax_dop.plot(deg, DoP, label=wl)
            ax_dolp.plot(deg, DoLP, label=wl)
            ax_docp.plot(deg, DoCP, label=wl)
    ax_s11_lin.set_title("S11 (linear)")
    ax_s11_log.set_title("S11 (log)")
    ax_s11_log.set_yscale("log")
    for a, ttl in [(ax_dop, "DoP"), (ax_dolp, "DoLP"), (ax_docp, "DoCP")]:
        a.set_title(ttl)
        a.set_xlabel("Angle (deg)")
        a.set_ylabel("Value")
        a.grid(True)
    if not has_data:
        for ax in [ax_s11_lin, ax_s11_log, ax_dop, ax_dolp, ax_docp]:
            ax.text(0.5, 0.5, "No data", transform=ax.transAxes,
                    ha='center', va='center', fontsize=14, color='grey')
    handles, labels = ax_dop.get_legend_handles_labels()
    if len(run_ids) > 1:
        fig.legend(handles, labels, loc="lower center",
                   ncol=min(5, len(run_ids)), bbox_to_anchor=(0.5, -0.02))
        fig.subplots_adjust(bottom=0.1)
    fig.tight_layout()
    set_fig_title(fig, "Dashboard")
    auto_save_or_show(fig, "DASHBOARD", save_dir)


# =========================
# NEW: Small-sphere / Rayleigh analysis
# =========================
def plot_small_sphere(runs, run_ids, save_dir=".", pol="unpol"):
    """
    Four-panel figure designed for Rayleigh-regime single-sphere analysis.

    (0,0) Efficiencies — Q_ext and Q_abs on the left y-axis (same scale),
          Q_sca on a secondary right y-axis.  Both axes share the wavelength
          x-axis.  This makes the huge contrast between absorption and
          scattering immediately visible without three separate subplots.

    (0,1) Single-scattering albedo  omega_0 = Q_sca / Q_ext.
          For gold in the Rayleigh regime omega_0 << 1 everywhere (the
          particle absorbs almost all the energy it removes from the beam).
          The value at the plasmon peak is annotated automatically.

    (1,0) Asymmetry parameter  g = <cos theta>, computed by numerical
          integration of S11 over the scattering angle.  Rayleigh theory
          predicts g ≈ 0 (symmetric forward/backward dipole lobe).
          Requires the scattering matrix; shows a message otherwise.

    (1,1) Rayleigh scaling verification.
          Plots  Q_abs * lambda  and  Q_sca * lambda^4, each normalised to
          their median over the sweep, so both curves sit near 1.0.
          A flat line confirms the theoretical scalings
              C_abs ∝ lambda^{-1}   and   C_sca ∝ lambda^{-4}.
          Deviations near the plasmon resonance are expected and physical.
    """
    # --- collect per-run quantities ---
    wl_um = []
    Qext_v = []
    Qabs_v = []
    Qsca_v = []
    g_vals = []

    for ri in run_ids:
        r = runs[ri]
        l_scale = r.get("l_scale", np.nan)
        # wavelength in same units as l_scale (um)
        lam = 2.0 * np.pi / l_scale
        wl_um.append(lam)
        eff = r["eff"][pol]
        Qext_v.append(eff["Qext"])
        Qabs_v.append(eff["Qabs"])
        Qsca_v.append(eff["Qsca"])
        g_vals.append(compute_g(r))

    wl_um = np.array(wl_um)
    Qext_v = np.array(Qext_v)
    Qabs_v = np.array(Qabs_v)
    Qsca_v = np.array(Qsca_v)
    g_vals = np.array(g_vals)

    # sort by wavelength ascending
    order = np.argsort(wl_um)
    wl_um = wl_um[order]
    Qext_v = Qext_v[order]
    Qabs_v = Qabs_v[order]
    Qsca_v = Qsca_v[order]
    g_vals = g_vals[order]

    omega0 = np.where(Qext_v > 0, Qsca_v / Qext_v, np.nan)

    # Rayleigh scaling products — normalise to median so curves sit near 1
    with np.errstate(invalid="ignore", divide="ignore"):
        prod_abs = Qabs_v * wl_um           # const if C_abs ∝ λ^{-1}
        prod_sca = Qsca_v * wl_um**4        # const if C_sca ∝ λ^{-4}
        med_abs = np.nanmedian(prod_abs)
        med_sca = np.nanmedian(prod_sca)
        norm_abs = prod_abs / med_abs if med_abs != 0 else prod_abs
        norm_sca = prod_sca / med_sca if med_sca != 0 else prod_sca

    # colours
    C_EXT = "#1f77b4"   # blue
    C_ABS = "#d62728"   # red
    C_SCA = "#2ca02c"   # green
    C_ALB = "#9467bd"   # purple
    C_G = "#8c564b"   # brown

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        f"Rayleigh-regime analysis — single gold sphere  ({pol})", fontsize=18)

    # ── (0,0) Efficiencies with dual y-axis ───────────────────────────
    ax0 = axes[0, 0]
    ax0r = ax0.twinx()

    ax0.plot(wl_um, Qext_v, color=C_EXT, label=r"$Q_\mathrm{ext}$")
    ax0.plot(wl_um, Qabs_v, color=C_ABS, linestyle="--",
             label=r"$Q_\mathrm{abs}$")
    ax0r.plot(wl_um, Qsca_v, color=C_SCA, linestyle=":",
              label=r"$Q_\mathrm{sca}$")

    ax0.set_xlabel(r"Wavelength ($\mu$m)")
    ax0.set_ylabel(r"$Q_\mathrm{ext}$,  $Q_\mathrm{abs}$  (left)")
    ax0r.set_ylabel(r"$Q_\mathrm{sca}$  (right)", color=C_SCA)
    ax0r.tick_params(axis="y", labelcolor=C_SCA)

    lines0 = ax0.get_lines() + ax0r.get_lines()
    labels0 = [l.get_label() for l in lines0]
    ax0.legend(lines0, labels0, loc="upper right", fontsize=13)
    ax0.set_title("Efficiencies")
    ax0.grid(True)

    # ── (0,1) Single-scattering albedo ────────────────────────────────
    ax1 = axes[0, 1]
    ax1.plot(wl_um, omega0, color=C_ALB)
    ax1.set_xlabel(r"Wavelength ($\mu$m)")
    ax1.set_ylabel(r"$\omega_0 = Q_\mathrm{sca}\,/\,Q_\mathrm{ext}$")
    ax1.set_ylim(bottom=0)
    ax1.set_title(r"Single-scattering albedo  $\omega_0$")
    ax1.grid(True)

    # annotate the value at the plasmon peak (max Q_ext)
    idx_peak = int(np.nanargmax(Qext_v))
    lam_peak = wl_um[idx_peak]
    om_peak = omega0[idx_peak]
    x_offset = (wl_um[-1] - wl_um[0]) * 0.08
    ax1.annotate(
        f"plasmon peak\n$\\lambda$ = {lam_peak:.3f} $\\mu$m\n$\\omega_0$ = {om_peak:.4f}",
        xy=(lam_peak, om_peak),
        xytext=(lam_peak + x_offset, om_peak +
                (ax1.get_ylim()[1] - om_peak) * 0.3),
        fontsize=12,
        arrowprops=dict(arrowstyle="->", color="gray"),
    )

    # ── (1,0) Asymmetry parameter g ───────────────────────────────────
    ax2 = axes[1, 0]
    has_g = not np.all(np.isnan(g_vals))

    if has_g:
        ax2.plot(wl_um, g_vals, color=C_G)
        ax2.axhline(0, color="gray", linewidth=1,
                    linestyle="--", label="g = 0  (isotropic)")
        ax2.legend(fontsize=12)
    else:
        ax2.text(
            0.5, 0.5,
            "S matrix not available\n(enable scattering matrix output in MSTM)",
            transform=ax2.transAxes, ha="center", va="center",
            fontsize=13, color="gray",
        )

    ax2.set_xlabel(r"Wavelength ($\mu$m)")
    ax2.set_ylabel(r"$g = \langle\cos\theta\rangle$")
    ax2.set_title(r"Asymmetry parameter  $g$  (Rayleigh: $g \approx 0$)")
    ax2.grid(True)

    # ── (1,1) Rayleigh scaling verification ───────────────────────────
    ax3 = axes[1, 1]
    ax3.plot(wl_um, norm_abs, color=C_ABS,
             label=r"$Q_\mathrm{abs} \cdot \lambda \;/\; \mathrm{median}$"
                   "\n" r"(flat $\Rightarrow$ $C_\mathrm{abs}\propto\lambda^{-1}$)")
    ax3.plot(wl_um, norm_sca, color=C_SCA, linestyle="--",
             label=r"$Q_\mathrm{sca} \cdot \lambda^4 \;/\; \mathrm{median}$"
                   "\n" r"(flat $\Rightarrow$ $C_\mathrm{sca}\propto\lambda^{-4}$)")
    ax3.axhline(1.0, color="gray", linewidth=1,
                linestyle=":", label="Reference (= 1)")

    ax3.set_xlabel(r"Wavelength ($\mu$m)")
    ax3.set_ylabel("Normalised product  (≈ 1 if Rayleigh scaling holds)")
    ax3.set_title("Rayleigh scaling verification")
    ax3.legend(fontsize=11)
    ax3.grid(True)

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    set_fig_title(fig, "Rayleigh analysis")
    auto_save_or_show(fig, "RAYLEIGH", save_dir)


# =========================
# CLI
# =========================
def parse_args(argv):
    """
    Usage:
      python plot_scattering_matrix.py <file> [mode] [save_folder] [--run N|ALL] [--pol POL]

    Modes:
      S11, DOP, DOLP, DOCP, ALL, EFF, QEXT, QABS, QSCA, DASHBOARD, RAYLEIGH
    Polarizations:
      unpol (default), par, perp
    """
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Plot scattering or efficiency data.")
    parser.add_argument("file", help="Input scattering matrix file")
    parser.add_argument("mode", nargs="?", default="DASHBOARD",
                        help="S11 | DOP | DOLP | DOCP | ALL | EFF | QEXT | QABS | QSCA | DASHBOARD | RAYLEIGH")
    parser.add_argument("save_folder", nargs="?", default=".",
                        help="Folder to save plots")
    parser.add_argument("--run",  default="ALL", help="Run index or ALL")
    parser.add_argument("--pol",  choices=["unpol", "par", "perp"], default="unpol",
                        help="Polarization for efficiency plots")

    args = parser.parse_args(argv[1:])
    return args.file, args.mode.upper(), args.save_folder, args.run.upper(), args.pol


def select_runs(runs, selector):
    if selector == "ALL":
        return list(range(len(runs)))
    try:
        idx = int(selector)
    except ValueError:
        idx = 1
    return [max(0, min(idx - 1, len(runs) - 1))]


# =========================
# Main
# =========================
def main():
    file, mode, save_dir, run_selector, pol = parse_args(sys.argv)

    if save_dir:
        plot_dir = os.path.join(os.path.abspath(save_dir), "plots")
        os.makedirs(plot_dir, exist_ok=True)
        mpl.rcParams["savefig.directory"] = plot_dir

    print(f"Reading file : {file}")
    print(f"Mode        : {mode}")
    print(f"Polarization: {pol}")

    runs = parse_runs_with_efficiencies(file)
    if not runs:
        raise ValueError("No scattering matrix sections found.")
    print(f"Found {len(runs)} run(s).")

    run_ids = select_runs(runs, run_selector)

    if mode == "S11":
        plot_S11(runs, run_ids, save_dir)
    elif mode in ["DOP", "DOLP", "DOCP", "ALL"]:
        plot_polarization(runs, run_ids, mode, save_dir)
    elif mode in ["EFF", "QEXT", "QABS", "QSCA"]:
        plot_efficiencies(runs, run_ids, save_dir, pol, mode)
    elif mode == "DASHBOARD":
        plot_dashboard(runs, run_ids, save_dir)
    elif mode == "RAYLEIGH":
        plot_small_sphere(runs, run_ids, save_dir, pol)
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
