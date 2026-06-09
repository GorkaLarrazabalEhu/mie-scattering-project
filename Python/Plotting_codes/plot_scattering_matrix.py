import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import matplotlib as mpl


# =========================
# Configuración global
# =========================

# ── Eje Y dual para eficiencias ──────────────────────────────────────────────
# True  → Q_ext y Q_abs en el eje izquierdo, Q_sca en un eje derecho
#          independiente (útil cuando Q_sca es mucho menor que Q_ext / Q_abs)
# False → las tres curvas comparten el mismo eje Y izquierdo
DUAL_Y_AXIS = False

# True  → al plotear eficiencias se abre también una figura separada con n y k
#          interpolados en el mismo rango de longitudes de onda
# False → solo se plotean las eficiencias
PLOT_REFRACTIVE_INDEX = True

# =========================
# Importar mstm_utils para n/k
# =========================
try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Programa", "calculations")))
    import mstm_utils as _mstm_utils  # type: ignore
    _HAS_MSTM_UTILS = True
except Exception:
    _HAS_MSTM_UTILS = False

# =========================
# Estilo global de figuras
# =========================
plt.rcParams.update({
    "xtick.labelsize": 19,
    "ytick.labelsize": 19,
    "axes.titlesize": 20,
    "axes.labelsize": 24,
    "legend.fontsize": 20,    
    
    "font.weight": "bold",
    "axes.titleweight": "bold",
    "axes.labelweight": "bold",
})
plt.rcParams["figure.titlesize"] = 24
plt.rcParams["lines.linewidth"] = 2
plt.rcParams["figure.titleweight"] = "bold"
# =========================
# Utilidades
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
        print(f"Guardado automáticamente: {outfile}")
        plt.close(fig)
    else:
        fig.canvas.draw_idle()
        plt.show(block=True)
        plt.close(fig)


# =========================
# Parseo
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
            raise ValueError("Se esperaban 9 números en la línea de eficiencias totales.")
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
            raise ValueError("Se esperaban 9 números en la línea de eficiencias totales.")
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
# Funciones físicas auxiliares
# =========================
def compute_g(r):
    """
    Parámetro de asimetría  g = <cos theta>  a partir de la matriz S11.

        g = integral[ S11(theta) cos(theta) sin(theta) dtheta ]
            -------------------------------------------------------
            integral[ S11(theta) sin(theta) dtheta ]

    Devuelve np.nan si la matriz S no está disponible.
    """
    if r["S"] is None:
        return np.nan
    S11 = r["S"][:, 0]
    theta = r["radianTheta"]
    num = np.trapz(S11 * np.cos(theta) * np.sin(theta), theta)
    den = np.trapz(S11 * np.sin(theta), theta)
    return num / den if den != 0 else np.nan


# =========================
# Representación gráfica
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
    ax1.set_title("S11 (escala lineal)")
    ax2.set_title("S11 (escala logarítmica)")
    ax2.set_yscale("log")
    ax1.legend(loc="best")
    ax2.legend(loc="best")
    plt.tight_layout()
    set_fig_title(fig, "S11")
    auto_save_or_show(fig, "S11", save_dir)


def plot_S11(runs, run_ids, save_dir=".", skip_run=True, plot_number=5):
    mode = {1, 2}
    mode = {1}
    # mode = {2}
    valid_run_ids = [
        ri for ri in run_ids
        if runs[ri]["S"] is not None
    ]

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
                0.5, 0.5, "Sin datos",
                transform=ax.transAxes,
                ha='center',
                va='center',
                fontsize=14,
                color='grey'
            )

    if 1 in mode:
        ax_map[1].set_title(r"$S_{11}$", y=1.05, fontsize=16)

    if 2 in mode:
        ax_map[2].set_title(r"$S_{11}$ (log)", y=1.05)
        ax_map[2].set_yscale("log")

    handles, labels = axes[0].get_legend_handles_labels()

    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=2,
        bbox_to_anchor=(0.5, 0.93),
        draggable=True,
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
        lbl = f"(ejecución {ri+1})" if len(run_ids) > 1 else ""
        if mode == "DOP":
            ax.plot(r["degreeTheta"], DoP, label=f"DoP {lbl}".strip())
            ax.set_ylabel("Grado de polarización")
        elif mode == "DOLP":
            ax.plot(r["degreeTheta"], DoLP, label=f"DoLP {lbl}".strip())
            ax.set_ylabel("Grado de polarización lineal")
        elif mode == "DOCP":
            ax.plot(r["degreeTheta"], DoCP, label=f"DoCP {lbl}".strip())
            ax.set_ylabel("Grado de polarización circular")
        elif mode == "ALL":
            ax.plot(r["degreeTheta"], DoP,  label=f"DoP {lbl}".strip())
            ax.plot(r["degreeTheta"], DoLP, "--", label=f"DoLP {lbl}".strip())
            ax.plot(r["degreeTheta"], DoCP, ":", label=f"DoCP {lbl}".strip())
            ax.set_ylabel("Grado de polarización")
    ax.set_xlabel("Ángulo de dispersión (grados)")
    ax.set_title("Propiedades de polarización (incidencia no polarizada)")
    ax.legend()
    ax.grid(True)
    set_fig_title(fig, mode)
    auto_save_or_show(fig, mode, save_dir)


def plot_polarization(runs, run_ids, mode, save_dir=".", skip_run=True, plot_number=5):
    valid_run_ids = [
        ri for ri in run_ids
        if runs[ri]["S"] is not None
    ]

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
            ax.set_ylabel("Grado de polarización")

        elif mode == "DOLP":
            ax.plot(r["degreeTheta"], DoLP, label=f"DoLP {wl}")
            ax.set_ylabel("Grado de polarización lineal")

        elif mode == "DOCP":
            ax.plot(r["degreeTheta"], DoCP, label=f"DoCP {wl}")
            ax.set_ylabel("Grado de polarización circular")

        elif mode == "ALL":
            ax.plot(r["degreeTheta"], DoP,  label=f"DoP {wl}")
            ax.plot(r["degreeTheta"], DoLP, "--", label=f"DoLP {wl}")
            ax.plot(r["degreeTheta"], DoCP, ":", label=f"DoCP {wl}")
            ax.set_ylabel("Grado de polarización")

    if not has_data:
        ax.text(
            0.5, 0.5, "Sin datos",
            transform=ax.transAxes,
            ha='center', va='center',
            fontsize=14, color='grey'
        )

    ax.set_xlabel(r"$\theta$º")
    ax.set_title("Propiedades de polarización (incidencia no polarizada)")
    ax.legend(fontsize=14)
    ax.grid(True)

    set_fig_title(fig, mode)
    auto_save_or_show(fig, mode, save_dir)


def _plot_eff_axes(ax, axr, x, y_qext, y_qabs, y_qsca, dual):
    """
    Dibuja Q_ext, Q_abs y Q_sca sobre los ejes proporcionados.
    x debe ser el array de longitudes de onda reales (µm).

    dual=True  → Q_ext y Q_abs en 'ax' (izquierda), Q_sca en 'axr' (derecha).
    dual=False → las tres curvas en 'ax'; 'axr' no se usa.
    """
    ax.plot(x, y_qext, color="#1f77b4", label=r"$Q_\mathrm{ext}$")
    ax.plot(x, y_qabs, color="#d62728", linestyle="--",
            label=r"$Q_\mathrm{abs}$")

    if dual:
        axr.plot(x, y_qsca, color="#2ca02c", linestyle=":",
                 label=r"$Q_\mathrm{sca}$")
        ax.set_ylabel(r"$Q_\mathrm{ext}$,  $Q_\mathrm{abs}$")
        axr.set_ylabel(r"$Q_\mathrm{sca}$")
        axr.tick_params(axis="y", labelcolor="#2ca02c")
        lines = ax.get_lines() + axr.get_lines()
    else:
        ax.plot(x, y_qsca, color="#2ca02c", linestyle=":",
                label=r"$Q_\mathrm{sca}$")
        ax.set_ylabel(r"$Q_\mathrm{ext}$,  $Q_\mathrm{abs}$,  $Q_\mathrm{sca}$")
        axr.set_visible(False)
        lines = ax.get_lines()

    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, loc="upper right")


def _get_nk_arrays(wavelengths_um, material, radius):
    """
    Llama a mstm_utils.compute_parameters para cada longitud de onda y devuelve
    (n_arr, k_arr). Devuelve (None, None) si el material es Custom o si
    mstm_utils no está disponible.
    """
    if not _HAS_MSTM_UTILS:
        return None, None
    if not material or material.strip().lower() == "custom":
        return None, None
    if radius is None:
        return None, None
    try:
        n_vals, k_vals = [], []
        for wl in wavelengths_um:
            res = _mstm_utils.compute_parameters(radius, wl, material=material)
            ri = res["refractive_index"]
            n_vals.append(ri.real)
            k_vals.append(ri.imag)
        return np.array(n_vals), np.array(k_vals)
    except Exception as exc:
        print(f"[n/k] No se pudo calcular el índice de refracción: {exc}")
        return None, None


def _build_nk_figure(x, n_arr, k_arr, material):
    """
    Construye dos figuras sin mostrarlas:
      · n y k  (índice de refracción complejo)
      · ε₁ y ε₂ (función dieléctrica), con la línea de resonancia ε₁ = −2

    plt.show() del caller las mostrará todas juntas.
    x debe ser el array de longitudes de onda reales (µm).
    """
    # ── Figura 1: n y k ──────────────────────────────────────────────
    fig_nk, ax_nk = plt.subplots(figsize=(9, 4))
    ax_nk.plot(x, n_arr, color="#1f77b4", label="n (real)")
    ax_nk.plot(x, k_arr, color="#d62728", linestyle="--", label="k (imag)")
    ax_nk.set_xlabel(r"Longitud de onda ($\mu$m)")
    ax_nk.set_ylabel("Índice de refracción")
    ax_nk.set_title(f"Índice de refracción interpolado — {material}")
    ax_nk.legend(fontsize=13).set_draggable(True)
    ax_nk.grid(True)
    fig_nk.tight_layout()
    set_fig_title(fig_nk, f"n/k — {material}")

    # ── Figura 2: ε₁ y ε₂ ───────────────────────────────────────────
    eps1 = n_arr ** 2 - k_arr ** 2   # parte real de ε
    eps2 = 2.0 * n_arr * k_arr       # parte imaginaria de ε

    fig_eps, ax_eps = plt.subplots(figsize=(9, 4))
    ax_eps.plot(x, eps1, color="#1f77b4",
                label=r"$\varepsilon_1 = n^2 - k^2$")
    ax_eps.plot(x, eps2, color="#d62728", linestyle="--",
                label=r"$\varepsilon_2 = 2nk$")
    ax_eps.axhline(-2, color="#2ca02c", linestyle=":", linewidth=1.5,
                   label=r"$\varepsilon_1 = -2$  (resonancia dipolar, vacío)")
    ax_eps.axhline(0, color="gray", linestyle="-", linewidth=0.6)
    ax_eps.set_xlabel(r"Longitud de onda ($\mu$m)")
    ax_eps.set_ylabel(r"$\varepsilon_1$,  $\varepsilon_2$")
    ax_eps.set_title(f"Función dieléctrica — {material}")
    ax_eps.legend(fontsize=13).set_draggable(True)
    ax_eps.grid(True)
    fig_eps.tight_layout()
    set_fig_title(fig_eps, f"ε — {material}")

    return fig_nk, fig_eps


def plot_efficiencies(runs, run_ids, save_dir=".", pol="unpol", mode="EFF",
                      material=None, radius=None):

    # Eje X: longitudes de onda reales (µm) — el ratón mostrará valores correctos
    x = np.array([2 * np.pi / runs[ri]["l_scale"] for ri in run_ids])

    y_qext, y_qabs, y_qsca = [], [], []
    for ri in run_ids:
        eff = runs[ri]["eff"][pol]
        y_qext.append(eff["Qext"])
        y_qabs.append(eff["Qabs"])
        y_qsca.append(eff["Qsca"])

    invert_x = False
    if invert_x:
        inv_x = 1 / x
        order = np.argsort(inv_x)
        x      = inv_x[order]
        y_qext = np.array(y_qext)[order]
        y_qabs = np.array(y_qabs)[order]
        y_qsca = np.array(y_qsca)[order]

    mode = mode.upper()
    valid_modes = ["EFF", "QEXT", "QABS", "QSCA"]
    if mode not in valid_modes:
        raise ValueError(f"Modo no válido '{mode}'. Elige entre {valid_modes}.")

    # Calcular n/k y construir figura antes del show (se mostrará a la vez)
    n_arr, k_arr = _get_nk_arrays(x.tolist(), material, radius) if PLOT_REFRACTIVE_INDEX else (None, None)

    C_EXT = "#1f77b4"
    C_ABS = "#d62728"
    C_SCA = "#2ca02c"

    if mode == "EFF":
        fig, ax = plt.subplots(figsize=(9, 5))
        axr = ax.twinx()

        _plot_eff_axes(ax, axr, x, y_qext, y_qabs, y_qsca, dual=DUAL_Y_AXIS)

        ax.set_xlabel(r"Longitud de onda ($\mu$m)")
        ax.grid(True)
        # fig.suptitle(f"Eficiencias ({pol.capitalize()})")
        fig.suptitle("Eficiencias espectrales")

        leg = ax.get_legend()
        if leg:
            leg.set_draggable(True)

        fig.tight_layout()
        set_fig_title(fig, f"Eficiencias - {pol.capitalize()}")

        if n_arr is not None:
            _build_nk_figure(x, n_arr, k_arr, material)

        auto_save_or_show(fig, f"EFF_{pol.upper()}", save_dir)

    else:
        y_map = {"QEXT": y_qext, "QABS": y_qabs, "QSCA": y_qsca}
        title_map = {
            "QEXT": r"$Q_\mathrm{ext}$",
            "QABS": r"$Q_\mathrm{abs}$",
            "QSCA": r"$Q_\mathrm{sca}$",
        }
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(x, y_map[mode], marker="")
        ax.set_xlabel(r"Longitud de onda ($\mu$m)")
        ax.set_ylabel(f"{title_map[mode]} ({pol})")
        max_index = np.argmax(y_map[mode])
        print(f"Máximo de {mode} en longitud de onda {x[max_index]:.4f} um: {y_map[mode][max_index]}")
        print(f"Albedo de dispersión (Qsca/Qext) en ese punto: {y_qsca[max_index]/y_qext[max_index]:.4f}")
        ax.grid(True)
        ax.set_title(f"{title_map[mode]} ({pol.capitalize()})")
        set_fig_title(fig, f"{mode} - {pol.capitalize()}")

        if n_arr is not None:
            _build_nk_figure(x, n_arr, k_arr, material)

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
        lbl = f"Ejecución {ri+1}"
        ax_s11_lin.plot(rad, S11, label=lbl)
        ax_s11_log.plot(rad, S11, label=lbl)
        ax_dop.plot(deg, DoP, label=lbl)
        ax_dolp.plot(deg, DoLP, label=lbl)
        ax_docp.plot(deg, DoCP, label=lbl)
    ax_s11_lin.set_title("S11 (lineal)")
    ax_s11_log.set_title("S11 (logarítmica)")
    ax_s11_log.set_yscale("log")
    for a, ttl in [(ax_dop, "DoP"), (ax_dolp, "DoLP"), (ax_docp, "DoCP")]:
        a.set_title(ttl)
        a.set_xlabel("Ángulo (grados)")
        a.set_ylabel("Valor")
        a.grid(True)
    handles, labels = ax_dop.get_legend_handles_labels()
    if len(run_ids) > 1:
        fig.legend(handles, labels, loc="lower center",
                   ncol=min(5, len(run_ids)), bbox_to_anchor=(0.5, -0.02))
        fig.subplots_adjust(bottom=0.1)
    fig.tight_layout()
    set_fig_title(fig, "Panel principal")
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
    ax_s11_lin.set_title("S11 (lineal)")
    ax_s11_log.set_title("S11 (logarítmica)")
    ax_s11_log.set_yscale("log")
    for a, ttl in [(ax_dop, "DoP"), (ax_dolp, "DoLP"), (ax_docp, "DoCP")]:
        a.set_title(ttl)
        a.set_xlabel("Ángulo (grados)")
        a.set_ylabel("Valor")
        a.grid(True)
    if not has_data:
        for ax in [ax_s11_lin, ax_s11_log, ax_dop, ax_dolp, ax_docp]:
            ax.text(0.5, 0.5, "Sin datos", transform=ax.transAxes,
                    ha='center', va='center', fontsize=14, color='grey')
    handles, labels = ax_dop.get_legend_handles_labels()
    if len(run_ids) > 1:
        fig.legend(handles, labels, loc="lower center",
                   ncol=min(5, len(run_ids)), bbox_to_anchor=(0.5, -0.02))
        fig.subplots_adjust(bottom=0.1)
    fig.tight_layout()
    set_fig_title(fig, "Panel principal")
    auto_save_or_show(fig, "DASHBOARD", save_dir)


# =========================
# Análisis de esfera pequeña / régimen de Rayleigh
# =========================
def plot_small_sphere(runs, run_ids, save_dir=".", pol="unpol"):
    """
    Figura de cuatro paneles para el análisis de una esfera individual en
    régimen de Rayleigh.

    (0,0) Eficiencias — Q_ext y Q_abs en el eje izquierdo, Q_sca en un eje
          derecho independiente (si DUAL_Y_AXIS=True) o los tres en el mismo
          eje (si DUAL_Y_AXIS=False).

    (0,1) Albedo de dispersión simple  omega_0 = Q_sca / Q_ext.

    (1,0) Parámetro de asimetría  g = <cos theta>, calculado por integración
          numérica de S11 sobre el ángulo de dispersión.

    (1,1) Verificación del escalado de Rayleigh:
          Q_abs * lambda  y  Q_sca * lambda^4, normalizados a su mediana.
    """
    wl_um = []
    Qext_v = []
    Qabs_v = []
    Qsca_v = []
    g_vals = []

    for ri in run_ids:
        r = runs[ri]
        l_scale = r.get("l_scale", np.nan)
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

    order = np.argsort(wl_um)
    wl_um = wl_um[order]
    Qext_v = Qext_v[order]
    Qabs_v = Qabs_v[order]
    Qsca_v = Qsca_v[order]
    g_vals = g_vals[order]

    omega0 = np.where(Qext_v > 0, Qsca_v / Qext_v, np.nan)

    with np.errstate(invalid="ignore", divide="ignore"):
        prod_abs = Qabs_v * wl_um
        prod_sca = Qsca_v * wl_um**4
        med_abs = np.nanmedian(prod_abs)
        med_sca = np.nanmedian(prod_sca)
        norm_abs = prod_abs / med_abs if med_abs != 0 else prod_abs
        norm_sca = prod_sca / med_sca if med_sca != 0 else prod_sca

    C_EXT = "#1f77b4"
    C_ABS = "#d62728"
    C_SCA = "#2ca02c"
    C_ALB = "#9467bd"
    C_G   = "#8c564b"

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        f"Análisis en régimen de Rayleigh — esfera de oro individual  ({pol})",
        fontsize=18)

    # ── (0,0) Eficiencias ─────────────────────────────────────────────
    ax0 = axes[0, 0]
    ax0r = ax0.twinx()

    _plot_eff_axes(ax0, ax0r, wl_um, Qext_v, Qabs_v, Qsca_v, dual=DUAL_Y_AXIS)

    ax0.set_xlabel(r"Longitud de onda ($\mu$m)")
    ax0.set_title("Eficiencias")
    ax0.grid(True)

    # ── (0,1) Albedo de dispersión simple ─────────────────────────────
    ax1 = axes[0, 1]
    ax1.plot(wl_um, omega0, color=C_ALB)
    ax1.set_xlabel(r"Longitud de onda ($\mu$m)")
    ax1.set_ylabel(r"$\omega_0 = Q_\mathrm{sca}\,/\,Q_\mathrm{ext}$")
    ax1.set_ylim(bottom=0)
    ax1.set_title(r"Albedo de dispersión simple  $\omega_0$")
    ax1.grid(True)

    idx_peak = int(np.nanargmax(Qext_v))
    lam_peak = wl_um[idx_peak]
    om_peak = omega0[idx_peak]
    x_offset = (wl_um[-1] - wl_um[0]) * 0.08
    ax1.annotate(
        f"pico del plasmón\n$\\lambda$ = {lam_peak:.3f} $\\mu$m\n$\\omega_0$ = {om_peak:.4f}",
        xy=(lam_peak, om_peak),
        xytext=(lam_peak + x_offset, om_peak +
                (ax1.get_ylim()[1] - om_peak) * 0.3),
        fontsize=12,
        arrowprops=dict(arrowstyle="->", color="gray"),
    )

    # ── (1,0) Parámetro de asimetría g ────────────────────────────────
    ax2 = axes[1, 0]
    has_g = not np.all(np.isnan(g_vals))

    if has_g:
        ax2.plot(wl_um, g_vals, color=C_G)
        ax2.axhline(0, color="gray", linewidth=1,
                    linestyle="--", label="g = 0  (isotrópico)")
        ax2.legend(fontsize=12)
    else:
        ax2.text(
            0.5, 0.5,
            "Matriz S no disponible\n(activa la salida de la matriz de dispersión en MSTM)",
            transform=ax2.transAxes, ha="center", va="center",
            fontsize=13, color="gray",
        )

    ax2.set_xlabel(r"Longitud de onda ($\mu$m)")
    ax2.set_ylabel(r"$g = \langle\cos\theta\rangle$")
    ax2.set_title(r"Parámetro de asimetría  $g$  (Rayleigh: $g \approx 0$)")
    ax2.grid(True)

    # ── (1,1) Verificación del escalado de Rayleigh ───────────────────
    ax3 = axes[1, 1]
    ax3.plot(wl_um, norm_abs, color=C_ABS,
             label=r"$Q_\mathrm{abs} \cdot \lambda \;/\; \mathrm{mediana}$"
                   "\n" r"(plano $\Rightarrow$ $C_\mathrm{abs}\propto\lambda^{-1}$)")
    ax3.plot(wl_um, norm_sca, color=C_SCA, linestyle="--",
             label=r"$Q_\mathrm{sca} \cdot \lambda^4 \;/\; \mathrm{mediana}$"
                   "\n" r"(plano $\Rightarrow$ $C_\mathrm{sca}\propto\lambda^{-4}$)")
    ax3.axhline(1.0, color="gray", linewidth=1,
                linestyle=":", label="Referencia (= 1)")

    ax3.set_xlabel(r"Longitud de onda ($\mu$m)")
    ax3.set_ylabel("Producto normalizado  (≈ 1 si se cumple el escalado de Rayleigh)")
    ax3.set_title("Verificación del escalado de Rayleigh")
    ax3.legend(fontsize=11)
    ax3.grid(True)

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    set_fig_title(fig, "Análisis de Rayleigh")
    auto_save_or_show(fig, "RAYLEIGH", save_dir)


# =========================
# CLI
# =========================
def parse_args(argv):
    """
    Uso:
      python plot_scattering_matrix.py <fichero> [modo] [carpeta_guardado] [--run N|ALL] [--pol POL]
                                       [--material MAT] [--radius R]

    Modos:
      S11, DOP, DOLP, DOCP, ALL, EFF, QEXT, QABS, QSCA, DASHBOARD, RAYLEIGH
    Polarizaciones:
      unpol (por defecto), par, perp
    Materiales (para figura n/k):
      Au, Ag, Al, Cu, Fe, H2O  (se ignora si es Custom)
    """
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Representar datos de la matriz de dispersión o de eficiencias.")
    parser.add_argument("file", help="Fichero de entrada con la matriz de dispersión")
    parser.add_argument("mode", nargs="?", default="DASHBOARD",
                        help="S11 | DOP | DOLP | DOCP | ALL | EFF | QEXT | QABS | QSCA | DASHBOARD | RAYLEIGH")
    parser.add_argument("save_folder", nargs="?", default=".",
                        help="Carpeta donde guardar las figuras")
    parser.add_argument("--run",      default="ALL", help="Índice de ejecución o ALL")
    parser.add_argument("--pol",      choices=["unpol", "par", "perp"], default="unpol",
                        help="Polarización para las gráficas de eficiencias")
    parser.add_argument("--material", default=None,
                        help="Material para figura n/k (Au, Ag, Al, Cu, Fe, H2O)")
    parser.add_argument("--radius",   type=float, default=None,
                        help="Radio de la esfera en µm (necesario para la figura n/k)")

    args = parser.parse_args(argv[1:])
    return args.file, args.mode.upper(), args.save_folder, args.run.upper(), args.pol, args.material, args.radius


def select_runs(runs, selector):
    if selector == "ALL":
        return list(range(len(runs)))
    try:
        idx = int(selector)
    except ValueError:
        idx = 1
    return [max(0, min(idx - 1, len(runs) - 1))]


# =========================
# Punto de entrada
# =========================
def main():
    file, mode, save_dir, run_selector, pol, material, radius = parse_args(sys.argv)

    if save_dir:
        plot_dir = os.path.join(os.path.abspath(save_dir), "plots")
        os.makedirs(plot_dir, exist_ok=True)
        mpl.rcParams["savefig.directory"] = plot_dir

    print(f"Fichero de entrada : {file}")
    print(f"Modo               : {mode}")
    print(f"Polarización       : {pol}")
    if material:
        print(f"Material (n/k)     : {material}  |  radio: {radius} µm")

    runs = parse_runs_with_efficiencies(file)
    if not runs:
        raise ValueError("No se encontraron secciones de matriz de dispersión.")
    print(f"Ejecuciones encontradas: {len(runs)}.")

    run_ids = select_runs(runs, run_selector)

    if mode == "S11":
        plot_S11(runs, run_ids, save_dir)
    elif mode in ["DOP", "DOLP", "DOCP", "ALL"]:
        plot_polarization(runs, run_ids, mode, save_dir)
    elif mode in ["EFF", "QEXT", "QABS", "QSCA"]:
        plot_efficiencies(runs, run_ids, save_dir, pol, mode,
                          material=material, radius=radius)
    elif mode == "DASHBOARD":
        plot_dashboard(runs, run_ids, save_dir)
    elif mode == "RAYLEIGH":
        plot_small_sphere(runs, run_ids, save_dir, pol)
    else:
        print(f"Modo desconocido: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()