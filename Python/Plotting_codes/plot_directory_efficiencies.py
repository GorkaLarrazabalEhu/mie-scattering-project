#!/usr/bin/env python3
import os
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt


# =====================================================
# DEFAULT VALUES — used if no arguments are given
# =====================================================
DEFAULT_DIRECTORY = r"C:\Users\txuel\UNI\TFG Fisika\code\Simulaciones\caracterizacion\2e\EW\sep0nm"
DEFAULT_EFFICIENCY = "Qabs"    # "Qext", "Qabs", or "Qsca"
DEFAULT_POLARIZATION = "unpol"  # "unpol", "par", or "perp"
DEFAULT_SAVE = True
# =====================================================


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


def plot_multiple_runs(base_dir, efficiency="Qext", pol="unpol", save_fig=False):
    subfolders = [d for d in os.listdir(base_dir)
                  if os.path.isdir(os.path.join(base_dir, d))]

    plt.figure(figsize=(8, 5))
    plt.title(f"{efficiency} ({pol}) across runs")
    plt.xlabel("Wavelength (μm)")
    plt.ylabel(f"{efficiency} ({pol})")

    found_any = False

    for folder in sorted(subfolders):
        folder_path = os.path.join(base_dir, folder)
        dat_path = os.path.join(folder_path, f"{folder}.dat")
        if not os.path.exists(dat_path):
            print(f"[skip] No matching .dat file in {folder}")
            continue

        try:
            runs = parse_runs_with_efficiencies(dat_path)
        except Exception as e:
            print(f"[error] Failed parsing {folder}: {e}")
            continue

        x_vals, y_vals = [], []

        for run in runs:
            if np.isnan(run["l_scale"]):
                continue
            wl = 2 * np.pi / run["l_scale"]
            x_vals.append(wl)
            y_vals.append(run["eff"][pol][efficiency])

        if x_vals and y_vals:
            found_any = True
            plt.plot(x_vals, y_vals, marker=".", label=folder)
        else:
            print(f"[warn] No valid efficiencies in {folder}")

    if not found_any:
        print("No valid data found to plot.")
        return

    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    if save_fig:
        out_path = os.path.join(base_dir, f"combined_{efficiency}_{pol}.png")
        plt.savefig(out_path, dpi=300)
        print(f"Saved figure to: {out_path}")
        plt.show()
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Plot multiple efficiency runs.")
    parser.add_argument("directory", nargs="?", default=None,
                        help="Base directory containing simulation folders")
    parser.add_argument("--eff", default=None, choices=["Qext", "Qabs", "Qsca"],
                        help="Efficiency type")
    parser.add_argument("--pol", default=None, choices=["unpol", "par", "perp"],
                        help="Polarization type")
    parser.add_argument("--save", action="store_true",
                        help="Save figure instead of showing it")

    # If no args, use defaults
    if len(sys.argv) == 1:
        base_dir = DEFAULT_DIRECTORY
        eff = DEFAULT_EFFICIENCY
        pol = DEFAULT_POLARIZATION
        save_fig = DEFAULT_SAVE
    else:
        args = parser.parse_args()
        base_dir = args.directory or DEFAULT_DIRECTORY
        eff = args.eff or DEFAULT_EFFICIENCY
        pol = args.pol or DEFAULT_POLARIZATION
        save_fig = args.save or DEFAULT_SAVE

    print("=== Plot Directory Efficiencies ===")
    print(f"Base directory: {base_dir}")
    print(f"Efficiency type: {eff}")
    print(f"Polarization: {pol}")
    print(f"Save figure: {save_fig}")
    print("==================================")

    plot_multiple_runs(base_dir, eff, pol, save_fig)


if __name__ == "__main__":
    main()
