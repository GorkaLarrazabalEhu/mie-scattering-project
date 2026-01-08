import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import matplotlib as mpl

def set_fig_title(fig, title: str):
    """Set both window title and use a nice default name when saving manually."""
    try:
        fig.canvas.manager.set_window_title(title)
    except Exception:
        pass

def auto_save_or_show(fig, name, save_dir="."):
    if False:  # 👈 lock auto-save here
        outdir = os.path.join(save_dir, "plots")
        os.makedirs(outdir, exist_ok=True)
        outfile = os.path.join(outdir, f"{name}.png")
        fig.savefig(outfile, dpi=300, bbox_inches="tight")
        print(f"Auto-saved: {outfile}")
    else:
        plt.show()

def parse_scattering_runs(filepath):
    """
    Return a list of runs. Each run is a dict with:
      - degreeTheta (N,)
      - radianTheta (N,)
      - S (N,16)   # S11..S44 in row-major blocks [11,12,13,14, 21,22,..., 44]
      - n_elements, n_directions
    """
    with open(filepath, "r", errors="ignore") as f:
        lines = f.read().splitlines()

    runs = []
    i = 0
    nlines = len(lines)
    while i < nlines:
        if lines[i].strip() == "number directions, number SM elements:":
            # counts on next line
            parts = lines[i + 1].split()
            n_dir, n_el = int(parts[0]), int(parts[1])
            # header line with labels at i+2; numeric data starts at i+3
            start = i + 3
            block = []
            for j in range(start, start + n_dir):
                # Support Fortran "D" exponents and variable whitespace
                nums = [float(tok.replace("D", "E")) for tok in lines[j].split()]
                block.append(nums)
            arr = np.asarray(block, dtype=float)
            degreeTheta = arr[:, 0]
            radianTheta = np.pi * degreeTheta / 180.0
            S = arr[:, 1:17]
            runs.append({
                "degreeTheta": degreeTheta,
                "radianTheta": radianTheta,
                "S": S,
                "n_elements": n_el,
                "n_directions": n_dir
            })
            i = start + n_dir
        else:
            i += 1
    return runs

def parse_args(argv):
    """
    Keep compatibility:
      python script.py <file> <mode> [save_folder] [--run N|ALL]
    The --run flag can appear anywhere after <mode>.
    If save_folder is present but no --run, it is used as save dir.
    """
    if len(argv) < 3:
        print("Usage: python plot_scattering_matrix.py <mstm_output_file> <mode> [save_folder] [--run N|ALL]")
        print("Modes: S11, DOP, DOLP, DOCP, ALL")
        sys.exit(1)

    file = argv[1]
    mode = argv[2].upper()
    save_dir = None
    run_selector = "ALL"  # default: ALL run

    # scan remaining args
    rest = argv[3:]
    # find --run if present
    for k, tok in enumerate(rest):
        if tok == "--run" and k + 1 < len(rest):
            run_selector = rest[k + 1].upper()
            # remove the pair from rest
            rest = rest[:k] + rest[k+2:]
            break

    # if anything left in rest, treat first as save_dir (backward compat)
    if rest:
        save_dir = rest[0]

    return file, mode, save_dir, run_selector

def select_runs(runs, selector):
    """Return list of indices to plot given selector ('ALL' or integer string)."""
    if selector == "ALL":
        return list(range(len(runs)))
    try:
        idx = int(selector)
    except ValueError:
        idx = 1
    # clamp to [1, len]
    idx = max(1, min(idx, len(runs)))
    return [idx - 1]

def main():
    file, mode, save_dir, run_selector = parse_args(sys.argv)

    # set save directory if provided
    if save_dir is not None:
        plot_dir = os.path.join(os.path.abspath(save_dir), "plots")
        os.makedirs(plot_dir, exist_ok=True)
        mpl.rcParams['savefig.directory'] = plot_dir
        print(f"Default save folder set to: {mpl.rcParams['savefig.directory']}")

    print(f"Reading file: {file}")
    print(f"Plot mode: {mode}")

    runs = parse_scattering_runs(file)
    if not runs:
        raise ValueError("No scattering matrix sections found.")
    print(f"Found {len(runs)} run(s).")

    run_ids = select_runs(runs, run_selector)
    print("Selected run(s):", ", ".join(str(i+1) for i in run_ids))

    # === Plotting ===
    if mode == "S11":
        # Polar plots: overlay each selected run
        fig, (ax1, ax2) = plt.subplots(
            1, 2, subplot_kw={'projection': 'polar'}, figsize=(12, 6)
        )
        for ri in run_ids:
            r = runs[ri]
            ax1.plot(r["radianTheta"], r["S"][:, 0], label=f"Run {ri+1}")
            ax2.plot(r["radianTheta"], r["S"][:, 0], label=f"Run {ri+1}")
        ax1.set_title("S11 (linear scale)")
        ax2.set_yscale("log")
        ax2.set_title("S11 (log scale)")
        ax1.legend(loc="best")
        ax2.legend(loc="best")
        plt.tight_layout()
        title = "S11" if len(run_ids) == 1 else "S11 (multiple runs)"
        set_fig_title(fig, title)
        save_name = f"S11_run{'_'.join(str(i+1) for i in run_ids)}"
        auto_save_or_show(fig, save_name, save_dir if save_dir else ".")

    elif mode in ["DOP", "DOLP", "DOCP", "ALL"]:
        # Overlay curves per selected run
        fig, ax = plt.subplots()
        for ri in run_ids:
            r = runs[ri]
            S = r["S"]
            S11, S21, S31, S41 = S[:, 0], S[:, 4], S[:, 8], S[:, 12]
            DoP  = np.sqrt(S21**2 + S31**2 + S41**2)
            DoLP = np.sqrt(S21**2 + S31**2)
            DoCP = np.abs(S41)
            label_suffix = f"(run {ri+1})" if len(run_ids) > 1 else None

            if mode == "DOP":
                ax.plot(r["degreeTheta"], DoP, label=f"DoP {label_suffix or ''}".strip())
                ax.set_ylabel("Degree of Polarization")
            elif mode == "DOLP":
                ax.plot(r["degreeTheta"], DoLP, label=f"DoLP {label_suffix or ''}".strip())
                ax.set_ylabel("Degree of Linear Polarization")
            elif mode == "DOCP":
                ax.plot(r["degreeTheta"], DoCP, label=f"DoCP {label_suffix or ''}".strip())
                ax.set_ylabel("Degree of Circular Polarization")
            elif mode == "ALL":
                ax.plot(r["degreeTheta"], DoP,  label=f"DoP {label_suffix or ''}".strip())
                ax.plot(r["degreeTheta"], DoLP, "--", label=f"DoLP {label_suffix or ''}".strip())
                ax.plot(r["degreeTheta"], DoCP, ":", label=f"DoCP {label_suffix or ''}".strip())
                ax.set_ylabel("Polarization degree")

        ax.set_xlabel("Scattering angle (deg)")
        ax.set_title("Polarization properties (unpolarized incidence)")
        ax.legend()
        ax.grid(True)
        set_fig_title(fig, mode)
        save_name = f"{mode}_run{'_'.join(str(i+1) for i in run_ids)}"
        auto_save_or_show(fig, save_name, save_dir if save_dir else ".")


    elif mode == "DASHBOARD":
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

            # S11 polar
            ax_s11_lin.plot(rad, S11, label=lbl)
            ax_s11_log.plot(rad, S11, label=lbl)

            # Scalars vs angle
            ax_dop.plot(deg,  DoP,  label=lbl)
            ax_dolp.plot(deg, DoLP, label=lbl)
            ax_docp.plot(deg, DoCP, label=lbl)

        ax_s11_lin.set_title("S11 (linear)")
        ax_s11_log.set_title("S11 (log)")
        ax_s11_log.set_yscale("log")

        ax_dop.set_title("DoP");   ax_dop.set_xlabel("Angle (deg)");   ax_dop.set_ylabel("Value");   ax_dop.grid(True)
        ax_dolp.set_title("DoLP"); ax_dolp.set_xlabel("Angle (deg)");  ax_dolp.set_ylabel("Value");  ax_dolp.grid(True)
        ax_docp.set_title("DoCP"); ax_docp.set_xlabel("Angle (deg)");  ax_docp.set_ylabel("Value");  ax_docp.grid(True)

        # Put a shared legend below
        handles, labels = ax_dop.get_legend_handles_labels()
        if len(run_ids) > 1:
            fig.legend(handles, labels, loc="lower center", ncol=min(5, len(run_ids)), bbox_to_anchor=(0.5, -0.02))
            fig.subplots_adjust(bottom=0.1)

        fig.tight_layout()
        set_fig_title(fig, "Dashboard")
        save_name = f"DASHBOARD_run{'_'.join(str(i+1) for i in run_ids)}"
        auto_save_or_show(fig, save_name, save_dir if save_dir else ".")

    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)

if __name__ == "__main__":
    main()
