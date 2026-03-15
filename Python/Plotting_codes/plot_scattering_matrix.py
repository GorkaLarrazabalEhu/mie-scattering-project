import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import matplotlib as mpl


# =========================
# Global plotting style
# =========================
plt.rcParams.update({
    "xtick.labelsize": 16,   # numbers on x axis
    "ytick.labelsize": 16,   # numbers on y axis
    "axes.titlesize": 16,    # subplot titles
    "axes.labelsize": 20,    # axis labels
    "legend.fontsize": 14,   # legend text
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
    autosave = False  # set True to auto-save instead of showing
    if autosave:
        outdir = os.path.join(save_dir, "plots")
        os.makedirs(outdir, exist_ok=True)
        outfile = os.path.join(outdir, f"{name}.png")
        fig.savefig(outfile, dpi=300, bbox_inches="tight")
        print(f"Auto-saved: {outfile}")
        plt.close(fig)  # ensure figure is closed after saving
    else:
        fig.canvas.draw_idle()
        plt.show(block=True)  # block until this window is closed
        plt.close(fig)        # close so it won't be shown again later

# =========================
# Parsing
# =========================
def parse_runs_with_efficiencies2(filepath):
    """
    Parse file into a list of runs.
    Each run dict has:
      - degreeTheta (N,)
      - radianTheta (N,)
      - S (N,16)
      - n_elements, n_directions
      - eff: {
          'unpol': {'Qext':..., 'Qabs':..., 'Qsca':...},
          'par':   {'Qext':..., 'Qabs':..., 'Qsca':...},
          'perp':  {'Qext':..., 'Qabs':..., 'Qsca':...},
        }
    """
    with open(filepath, "r", errors="ignore") as f:
        lines = f.read().splitlines()

    runs = []
    pending_eff = None
    i = 0
    nlines = len(lines)

    def parse_totals_line(s):
        # 9 numbers: (unpol Qext,Qabs,Qsca,  par Qext,Qabs,Qsca,  perp Qext,Qabs,Qsca)
        parts = [float(t.replace("D", "E")) for t in s.split()]
        if len(parts) != 9:
            raise ValueError("Expected 9 numbers for total efficiencies line.")
        U = parts[0:3]  # unpol
        P = parts[3:6]  # par
        R = parts[6:9]  # perp
        return {
            "unpol": {"Qext": U[0], "Qabs": U[1], "Qsca": U[2]},
            "par":   {"Qext": P[0], "Qabs": P[1], "Qsca": P[2]},
            "perp":  {"Qext": R[0], "Qabs": R[1], "Qsca": R[2]},
        }

    while i < nlines:
        s = lines[i].strip()

        # Capture scale factors for wavelength and refractive index
        if s == "length, ref index scale factors":
            scale_factors = lines[i + 1].split()
            l_scale = float(scale_factors[0])
            n_ref = float(scale_factors[2])
            n_scale = float(scale_factors[1])
            i +=1
            continue

        # Capture totals in "calculation results for run" block
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



        # Scattering matrix block
        if s == "number directions, number SM elements:":
            parts = lines[i + 1].split()
            n_dir, n_el = int(parts[0]), int(parts[1])
            start = i + 3  # i+2 is the header labels line
            block = []
            for k in range(start, start + n_dir):
                vals = [float(tok.replace("D", "E")) for tok in lines[k].split()]
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
    """
    Parse file into a list of runs.
    Each run dict has:
      - degreeTheta (N,) or None if S missing
      - radianTheta (N,) or None if S missing
      - S (N,16) or None if S missing
      - n_elements, n_directions (or 0 if S missing)
      - eff: efficiencies always parsed if present
    """
    with open(filepath, "r", errors="ignore") as f:
        lines = f.read().splitlines()

    runs = []
    pending_eff = None
    l_scale = n_scale = n_ref = np.nan  # default if missing
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

        # Capture scale factors
        if s == "length, ref index scale factors":
            scale_factors = lines[i + 1].split()
            l_scale = float(scale_factors[0])
            n_scale = float(scale_factors[1])
            n_ref = float(scale_factors[2])
            i += 1
            continue

        # Capture totals in "calculation results for run" block
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

        # Scattering matrix block
        if s == "number directions, number SM elements:":
            parts = lines[i + 1].split()
            n_dir, n_el = int(parts[0]), int(parts[1])
            start = i + 3  # skip header labels line
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

    # Handle runs with efficiencies but no scattering matrix
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
# Plotting
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


def plot_S11(runs, run_ids, save_dir="."):

    mode = {1, 2}   # choose plots here: {1}, {2}, or {1,2}
    # mode = {1}
    # mode = {2}

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

    for ri in run_ids:
        r = runs[ri]
        if r["S"] is None:
            continue

        has_data = True
        l_scale = r.get("l_scale", 1.0)
        wl = f"{2*np.pi/l_scale:.2f} $\mu$m"

        if 1 in mode:
            ax_map[1].plot(r["radianTheta"], r["S"][:, 0], label=wl)

        if 2 in mode:
            ax_map[2].plot(r["radianTheta"], r["S"][:, 0], label=wl)

    if not has_data:
        for ax in axes:
            ax.text(0.5, 0.5, "No data", transform=ax.transAxes,
                    ha='center', va='center', fontsize=14, color='grey')

    if 1 in mode:
        ax_map[1].set_title("S11 (linear scale)", y=1.05, fontsize=16)

    if 2 in mode:
        ax_map[2].set_title("S11 (log scale)", y=1.05)
        ax_map[2].set_yscale("log")

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels,
               loc="upper center",
               ncol=2,
               bbox_to_anchor=(0.5, 0.93))

    plt.tight_layout()
    set_fig_title(fig, "S11")
    auto_save_or_show(fig, "S11", save_dir)

def plot_polarization2(runs, run_ids, mode, save_dir="."):
    # One cartesian plot for DOP/DOLP/DOCP/ALL
    fig, ax = plt.subplots()
    for ri in run_ids:
        r = runs[ri]
        S = r["S"]
        S11, S21, S31, S41 = S[:, 0], S[:, 4], S[:, 8], S[:, 12]
        DoP  = np.sqrt(S21**2 + S31**2 + S41**2)
        DoLP = np.sqrt(S21**2 + S31**2)
        DoCP = np.abs(S41)
        lbl  = f"(run {ri+1})" if len(run_ids) > 1 else ""

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


def plot_polarization(runs, run_ids, mode, save_dir="."):
    fig, ax = plt.subplots()
    has_data = False
    for ri in run_ids:
        r = runs[ri]
        if r["S"] is None:
            continue  # skip runs without S
        has_data = True
        S = r["S"]
        S11, S21, S31, S41 = S[:, 0], S[:, 4], S[:, 8], S[:, 12]
        DoP = np.sqrt(S21**2 + S31**2 + S41**2)
        DoLP = np.sqrt(S21**2 + S31**2)
        DoCP = np.abs(S41)
        lbl = f"(run {ri+1})" if len(run_ids) > 1 else ""
        l_scale = r.get("l_scale", 1.0)
        wl = f"{2*np.pi/l_scale:.2f} um"
        if mode == "DOP":
            # ax.plot(r["degreeTheta"], DoP, label=f"DoP {lbl}".strip())
            ax.plot(r["degreeTheta"], DoP, label=f"DoP {wl}")
            ax.set_ylabel("Degree of Polarization")
        elif mode == "DOLP":
            # ax.plot(r["degreeTheta"], DoLP, label=f"DoLP {lbl}".strip())
            ax.plot(r["degreeTheta"], DoLP, label=f"DoLP {wl}")
            ax.set_ylabel("Degree of Linear Polarization")
        elif mode == "DOCP":
            ax.plot(r["degreeTheta"], DoCP, label=f"DoCP {lbl}".strip())
            ax.set_ylabel("Degree of Circular Polarization")
        elif mode == "ALL":
            # ax.plot(r["degreeTheta"], DoP,  label=f"DoP {lbl}".strip())
            # ax.plot(r["degreeTheta"], DoLP, "--", label=f"DoLP {lbl}".strip())
            # ax.plot(r["degreeTheta"], DoCP, ":", label=f"DoCP {lbl}".strip())
            ax.plot(r["degreeTheta"], DoP,  label=f"DoP {wl}")
            ax.plot(r["degreeTheta"], DoLP, "--", label=f"DoLP {wl}")
            ax.plot(r["degreeTheta"], DoCP, ":", label=f"DoCP {wl}")
            ax.set_ylabel("Polarization degree")
    if not has_data:
        ax.text(0.5, 0.5, "No data", transform=ax.transAxes,
                ha='center', va='center', fontsize=14, color='grey')

    ax.set_xlabel("Scattering angle (deg)")
    ax.set_title("Polarization properties (unpolarized incidence)")
    ax.legend()
    ax.grid(True)
    set_fig_title(fig, mode)
    auto_save_or_show(fig, mode, save_dir)


def plot_efficiencies(runs, run_ids, save_dir=".", pol="unpol", mode="EFF"):
    x = np.arange(1, len(run_ids) + 1)
    # xlabels = [str(ri + 1) for ri in run_ids]
    # Create xlabels using 2π/l_scale

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


    # === Optional: Invert x-axis (true 1/value scaling) ===
    invert_x = False  # toggle this ON when you want inverse scaling

    if invert_x:
        # Convert wavelength labels (strings) → numeric
        wavelengths = np.array([float(v) for v in xlabels])
        inv_x = 1 / wavelengths  # true numeric inverse

        # Sort by increasing inverse value (optional: reverse for descending)
        order = np.argsort(inv_x)
        inv_x = inv_x[order]
        y_qext = np.array(y_qext)[order]
        y_qabs = np.array(y_qabs)[order]
        y_qsca = np.array(y_qsca)[order]

        # Update axis data
        x = inv_x
        xlabels = [f"{val:.3f}" for val in inv_x]
    # ======================================================

    # Handle modes
    mode = mode.upper()
    valid_modes = ["EFF", "QEXT", "QABS", "QSCA"]
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode '{mode}'. Choose from {valid_modes}.")

    if mode == "EFF":
        # Plot all three
        fig, axes = plt.subplots(3, 1, figsize=(8, 9), sharex=True)
        titles = ["Qext", "Qabs", "Qsca"]
        y_data = [y_qext, y_qabs, y_qsca]

        for ax, y, title in zip(axes, y_data, titles):
            ax.plot(x, y, marker="")
            ax.set_ylabel(f"{title} ({pol})")
            ax.grid(True)

        axes[-1].set_xlabel("Wavelength (um)")
        # axes[-1].set_xticks(x, xlabels)


        # Dynamically thin out x-axis labels
        max_labels = 10  # maximum number of x labels to show
        step = max(1, len(xlabels) // max_labels)
        x_ticks_to_show = x[::step]
        x_labels_to_show = [xlabels[i] for i in range(0, len(xlabels), step)]

        axes[-1].set_xticks(x_ticks_to_show)
        axes[-1].set_xticklabels(x_labels_to_show, rotation=0)

        fig.suptitle(f"Efficiencies ({pol.capitalize()})")
        fig.tight_layout(rect=[0, 0, 1, 0.97])
        set_fig_title(fig, f"Efficiencies - {pol.capitalize()}")
        auto_save_or_show(fig, f"EFF_{pol.upper()}", save_dir)

    else:
        # Plot only one
        y_map = {"QEXT": y_qext, "QABS": y_qabs, "QSCA": y_qsca}
        title = mode.capitalize()

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(x, y_map[mode], marker="")
        ax.set_xlabel("Wavelength (um)")
        ax.set_ylabel(f"{title} ({pol})")
        # ax.set_xticks(x, xlabels)

        # find index of max y value
        max_index = np.argmax(y_map[mode])
        print(f"Max {title} at wavelength {xlabels[max_index]} um: {y_map[mode][max_index]}")

        max_labels = 10  # maximum number of x labels to show
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
    # 2x3 grid: [S11 lin polar, S11 log polar, DoP, DoLP, DoCP]
    import matplotlib.gridspec as gridspec
    fig = plt.figure(figsize=(14, 9))
    gs = gridspec.GridSpec(2, 3, figure=fig)

    ax_s11_lin = fig.add_subplot(gs[0, 0], projection='polar')
    ax_s11_log = fig.add_subplot(gs[0, 1], projection='polar')
    ax_dop     = fig.add_subplot(gs[1, 0])
    ax_dolp    = fig.add_subplot(gs[1, 1])
    ax_docp    = fig.add_subplot(gs[1, 2])

    for ri in run_ids:
        r = runs[ri]
        S = r["S"]
        rad = r["radianTheta"]
        deg = r["degreeTheta"]
        S11, S21, S31, S41 = S[:, 0], S[:, 4], S[:, 8], S[:, 12]
        DoP  = np.sqrt(S21**2 + S31**2 + S41**2)
        DoLP = np.sqrt(S21**2 + S31**2)
        DoCP = np.abs(S41)
        lbl  = f"Run {ri+1}"

        ax_s11_lin.plot(rad, S11, label=lbl)
        ax_s11_log.plot(rad, S11, label=lbl)
        ax_dop.plot(deg,  DoP,  label=lbl)
        ax_dolp.plot(deg, DoLP, label=lbl)
        ax_docp.plot(deg, DoCP, label=lbl)

    ax_s11_lin.set_title("S11 (linear)")
    ax_s11_log.set_title("S11 (log)")
    ax_s11_log.set_yscale("log")

    for a, ttl in [(ax_dop,"DoP"), (ax_dolp,"DoLP"), (ax_docp,"DoCP")]:
        a.set_title(ttl); a.set_xlabel("Angle (deg)"); a.set_ylabel("Value"); a.grid(True)

    # Shared legend (if multiple runs)
    handles, labels = ax_dop.get_legend_handles_labels()
    if len(run_ids) > 1:
        fig.legend(handles, labels, loc="lower center", ncol=min(5, len(run_ids)), bbox_to_anchor=(0.5, -0.02))
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
            lbl = f"Run {ri+1}"
            l_scale = r.get("l_scale", 1.0)
            wl = f"{2*np.pi/l_scale:.2f} um"

            # ax_s11_lin.plot(rad, S11, label=lbl)
            # ax_s11_log.plot(rad, S11, label=lbl)
            # ax_dop.plot(deg,  DoP,  label=lbl)
            # ax_dolp.plot(deg, DoLP, label=lbl)
            # ax_docp.plot(deg, DoCP, label=lbl)   
            
            ax_s11_lin.plot(rad, S11, label=wl)
            ax_s11_log.plot(rad, S11, label=wl)
            ax_dop.plot(deg,  DoP,  label=wl)
            ax_dolp.plot(deg, DoLP, label=wl)
            ax_docp.plot(deg, DoCP, label=wl)
        else:
            # If S missing, optionally just skip S11 plots, efficiencies could be plotted elsewhere
            continue

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

    # Shared legend
    handles, labels = ax_dop.get_legend_handles_labels()
    if len(run_ids) > 1:
        fig.legend(handles, labels, loc="lower center", ncol=min(
            5, len(run_ids)), bbox_to_anchor=(0.5, -0.02))
        fig.subplots_adjust(bottom=0.1)

    fig.tight_layout()
    set_fig_title(fig, "Dashboard")    
    auto_save_or_show(fig, "DASHBOARD", save_dir)



# =========================
# CLI
# =========================


def parse_args(argv):
    """
    Usage:
      python plot_scattering_matrix.py <file> [mode] [save_folder] [--run N|ALL] [--pol POL]

    Modes:
      S11, DOP, DOLP, DOCP, ALL, EFF, QEXT, QABS, QSCA, DASHBOARD
    Polarizations:
      unpol (default), par, perp
    """
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Plot scattering or efficiency data.")
    parser.add_argument("file", help="Input scattering matrix file")
    parser.add_argument("mode", nargs="?", default="DASHBOARD",
                        help="Plot mode: S11, DOP, DOLP, DOCP, ALL, EFF, QEXT, QABS, QSCA, DASHBOARD")
    parser.add_argument("save_folder", nargs="?", default=".",
                        help="Folder to save plots")
    parser.add_argument("--run", default="ALL", help="Run index or ALL")
    parser.add_argument("--pol", choices=["unpol", "par", "perp"], default="unpol",
                        help="Polarization to use for efficiency plots")

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
        mpl.rcParams['savefig.directory'] = plot_dir

    print(f"Reading file: {file}")
    print(f"Mode: {mode}")
    print(f"Polarization: {pol}")

    runs = parse_runs_with_efficiencies(file)
    if not runs:
        raise ValueError("No scattering matrix sections found.")
    print(f"Found {len(runs)} run(s).")

    run_ids = select_runs(runs, run_selector)
    # print("Selected run(s):", ", ".join(str(i + 1) for i in run_ids))
    # --- Dispatch ---
    if mode == "S11":
        plot_S11(runs, run_ids, save_dir)
    elif mode in ["DOP", "DOLP", "DOCP", "ALL"]:
        plot_polarization(runs, run_ids, mode, save_dir)
    elif mode in ["EFF", "QEXT", "QABS", "QSCA"]:
        plot_efficiencies(runs, run_ids, save_dir, pol, mode)
        
    elif mode == "DASHBOARD":
        plot_dashboard(runs, run_ids, save_dir)
        # plot_efficiencies(runs, run_ids, save_dir, pol, "EFF")
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
