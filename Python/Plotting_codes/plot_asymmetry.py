"""
plot_asymmetry.py
=================

Calcula y representa el parámetro de asimetría g para un barrido de radios
o de longitudes de onda a partir del fichero de salida de MSTM.

Métodos:
  - NUMÉRICO:
        g = ∫ S11(theta) cos(theta) sin(theta) dtheta
            ------------------------------------------
              ∫ S11(theta) sin(theta) dtheta

  - EXPANSIÓN:
        Lee los coeficientes de expansión angular si existen.

        Si hay coeficientes n=0 y n=1:
            g = c1 / (3*c0)

        Si solo aparece n=1:
            g = c1 / 3
        pero se imprime un aviso porque se asume c0 = 1.

Uso:
    python plot_asymmetry.py output.dat --config_json config.json

Sweep de radio manual:
    python plot_asymmetry.py output.dat --radii 0.001 0.010 0.020 --lambda_um 0.520

Sweep de longitud de onda manual:
    python plot_asymmetry.py output.dat --wavelengths 0.300 0.400 0.500 --radius_um 0.050

Solo imprimir valores:
    python plot_asymmetry.py output.dat --config_json config.json --no_plot

Modo debug:
    python plot_asymmetry.py output.dat --config_json config.json --debug
"""

import sys
import json
import os
import re
import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import trapezoid


# ─────────────────────────────────────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────────────────────────────────────

FLOAT_RE = r"[+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[EeDd][+-]?\d+)?"

X_RE = re.compile(r"\bx\s*=\s*(" + FLOAT_RE + r")", re.IGNORECASE)
R_RE = re.compile(r"\br\s*=\s*(" + FLOAT_RE + r")", re.IGNORECASE)


def fnum(s):
    """
    Convierte strings numéricos, incluyendo notación Fortran.

    Ejemplos:
        1.23E-04 -> 1.23e-4
        1.23D-04 -> 1.23e-4
    """
    return float(str(s).replace("D", "E").replace("d", "e"))


def format_value(value, fmt="{:.6g}", missing="?"):
    if value is None:
        return missing
    try:
        if not np.isfinite(value):
            return "nan"
    except TypeError:
        return missing
    return fmt.format(value)


def is_scattering_matrix_start(line):
    """
    Detecta el inicio de un bloque de matriz de dispersión, evitando confundirlo
    con bloques de expansión.
    """
    low = line.lower()

    if "scattering matrix" not in low:
        return False

    excluded = [
        "expansion",
        "periodic",
        "coefficients",
    ]

    return not any(word in low for word in excluded)


def is_theta_header(line):
    """
    Detecta la cabecera de la tabla angular.

    Formato típico:
        theta      11      12      13 ...
    """
    return line.strip().lower().startswith("theta")


def new_run():
    return {
        "theta_raw": [],
        "s11_raw": [],

        "theta": None,
        "s11": None,

        "g_exp": None,
        "g_exp_note": None,

        "radius": None,
        "x": None,

        "qext": None,
        "qabs": None,
        "qsca": None,

        "warnings": [],
    }


def parse_radius_or_x(line, run):
    """
    Intenta leer x=... y r=... en una línea.
    """
    if run is None:
        return

    x_match = X_RE.search(line)
    r_match = R_RE.search(line)

    if x_match:
        try:
            run["x"] = fnum(x_match.group(1))
        except ValueError:
            pass

    if r_match:
        try:
            run["radius"] = fnum(r_match.group(1))
        except ValueError:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# PARSER MSTM
# ─────────────────────────────────────────────────────────────────────────────

def fold_angles(theta_raw, s11_raw):
    """
    Convierte una tabla angular [-180, +180] a [0, 180].

    Para cada |theta| promedia los valores disponibles:

        S11_fold(theta) = mean[S11(+theta), S11(-theta)]

    Esto evita depender de si MSTM imprime la tabla como 0...180 o -180...180.
    """
    theta_raw = np.asarray(theta_raw, dtype=float)
    s11_raw = np.asarray(s11_raw, dtype=float)

    groups = {}

    for theta, s11 in zip(theta_raw, s11_raw):
        key = abs(theta)

        if np.isclose(key, 0.0, atol=1e-10):
            key = 0.0
        elif np.isclose(key, 180.0, atol=1e-10):
            key = 180.0

        key = round(key, 8)

        if key not in groups:
            groups[key] = []

        groups[key].append(s11)

    theta = np.array(sorted(groups.keys()), dtype=float)
    s11 = np.array([np.mean(groups[key]) for key in theta], dtype=float)

    return theta, s11


def read_scattering_table(lines, i, run):
    """
    Lee filas consecutivas de la tabla angular después de la cabecera theta.

    Se detiene cuando encuentra una línea vacía, no numérica o con un ángulo
    fuera del intervalo [-180, 180].
    """
    started = False

    while i < len(lines):
        stripped = lines[i].strip()

        if not stripped:
            i += 1
            if started:
                break
            continue

        parts = stripped.split()

        if len(parts) < 2:
            if started:
                break
            i += 1
            continue

        try:
            theta_val = fnum(parts[0])
            s11_val = fnum(parts[1])
        except ValueError:
            if started:
                break
            i += 1
            continue

        if -180.000001 <= theta_val <= 180.000001:
            run["theta_raw"].append(theta_val)
            run["s11_raw"].append(s11_val)
            started = True
            i += 1
        else:
            if started:
                break
            i += 1

    return i


def read_expansion_block(lines, i, run):
    """
    Lee el bloque de coeficientes de expansión.

    Busca coeficientes de la columna 11 para n=0 y n=1.
    """
    coeffs = {}

    # Saltar línea actual: cabecera del bloque.
    i += 1

    started = False

    while i < len(lines):
        row = lines[i].strip()

        if not row:
            i += 1
            if started:
                break
            continue

        parts = row.split()

        if len(parts) < 2:
            if started:
                break
            i += 1
            continue

        try:
            n_idx = int(parts[0])
            c11 = fnum(parts[1])
        except ValueError:
            if started:
                break
            i += 1
            continue

        coeffs[n_idx] = c11
        started = True
        i += 1

    if run is not None and 1 in coeffs:
        c1 = coeffs[1]

        if 0 in coeffs:
            c0 = coeffs[0]

            if abs(c0) > 1e-30:
                run["g_exp"] = c1 / (3.0 * c0)
                run["g_exp_note"] = "g_exp = c1 / (3*c0)"
            else:
                run["g_exp"] = None
                run["warnings"].append(
                    "Se encontró c0 = 0 en la expansión. No se puede calcular g_exp."
                )
        else:
            run["g_exp"] = c1 / 3.0
            run["g_exp_note"] = "g_exp = c1 / 3, asumiendo c0 = 1"
            run["warnings"].append(
                "No se encontró coeficiente n=0 en la expansión. Se asumió c0 = 1."
            )

    return i


def read_efficiencies(lines, i, run):
    """
    Lee qext, qabs y qsca en la línea siguiente a la cabecera correspondiente.
    """
    i += 1

    if i >= len(lines):
        return i

    parts = lines[i].strip().split()

    if len(parts) >= 3 and run is not None:
        try:
            run["qext"] = fnum(parts[0])
            run["qabs"] = fnum(parts[1])
            run["qsca"] = fnum(parts[2])
        except ValueError:
            run["warnings"].append("No se pudieron leer qext, qabs y qsca.")

    return i + 1


def finalize_run(run):
    """
    Convierte theta_raw/s11_raw en arrays theta/s11 y añade avisos básicos.
    """
    theta, s11 = fold_angles(run["theta_raw"], run["s11_raw"])

    mask = np.isfinite(theta) & np.isfinite(s11)
    theta = theta[mask]
    s11 = s11[mask]

    order = np.argsort(theta)
    theta = theta[order]
    s11 = s11[order]

    run["theta"] = theta
    run["s11"] = s11

    if len(theta) == 0:
        run["warnings"].append("No hay datos angulares válidos.")
        return run

    if len(theta) < 2:
        run["warnings"].append("Hay menos de dos puntos angulares. No se puede integrar bien.")

    if theta[0] > 1e-6:
        run["warnings"].append(
            f"La tabla angular no empieza en 0°. Empieza en {theta[0]:.6g}°."
        )

    if theta[-1] < 180.0 - 1e-6:
        run["warnings"].append(
            f"La tabla angular no llega a 180°. Termina en {theta[-1]:.6g}°."
        )

    if np.any(s11 < 0):
        run["warnings"].append(
            "Hay valores negativos de S11. Revisa el parser o la normalización de la salida."
        )

    return run


def parse_mstm_output(filepath):
    """
    Lee el fichero de salida de MSTM y devuelve una lista de runs.
    """
    runs = []
    current = None

    with open(filepath, "r", errors="replace") as f:
        lines = f.readlines()

    i = 0

    while i < len(lines):
        line = lines[i]
        low = line.lower()

        if current is not None:
            parse_radius_or_x(line, current)

        # Inicio de bloque de matriz de dispersión.
        if is_scattering_matrix_start(line):
            if current is not None and len(current["theta_raw"]) > 0:
                runs.append(finalize_run(current))

            current = new_run()

            i += 1

            # Buscar cabecera theta.
            while i < len(lines) and not is_theta_header(lines[i]):
                parse_radius_or_x(lines[i], current)
                i += 1

            if i >= len(lines):
                current["warnings"].append(
                    "Se encontró un bloque de scattering matrix, pero no se encontró cabecera theta."
                )
                break

            # Saltar cabecera theta.
            i += 1

            # Leer exclusivamente la tabla angular.
            i = read_scattering_table(lines, i, current)
            continue

        # Bloque de coeficientes de expansión.
        if current is not None and "azimuthal averaged scattering matrix expansion coefficients" in low:
            i = read_expansion_block(lines, i, current)
            continue

        # Eficiencias.
        if current is not None and "total extinction, absorption, scattering efficiencies" in low:
            i = read_efficiencies(lines, i, current)
            continue

        i += 1

    if current is not None and len(current["theta_raw"]) > 0:
        runs.append(finalize_run(current))

    for run in runs:
        if "theta_raw" in run:
            del run["theta_raw"]
        if "s11_raw" in run:
            del run["s11_raw"]

    return runs


# ─────────────────────────────────────────────────────────────────────────────
# CÁLCULO DE g
# ─────────────────────────────────────────────────────────────────────────────

def compute_g_numerical(theta_deg, s11):
    """
    Calcula:

        g = ∫ S11(theta) cos(theta) sin(theta) dtheta
            ------------------------------------------
              ∫ S11(theta) sin(theta) dtheta

    con theta en grados.
    """
    theta_deg = np.asarray(theta_deg, dtype=float)
    s11 = np.asarray(s11, dtype=float)

    if len(theta_deg) < 2:
        return np.nan

    mask = np.isfinite(theta_deg) & np.isfinite(s11)
    theta_deg = theta_deg[mask]
    s11 = s11[mask]

    if len(theta_deg) < 2:
        return np.nan

    order = np.argsort(theta_deg)
    theta_deg = theta_deg[order]
    s11 = s11[order]

    theta_rad = np.deg2rad(theta_deg)

    sin_t = np.sin(theta_rad)
    cos_t = np.cos(theta_rad)

    numerator = trapezoid(s11 * cos_t * sin_t, theta_rad)
    denominator = trapezoid(s11 * sin_t, theta_rad)

    if abs(denominator) < 1e-30:
        return np.nan

    return numerator / denominator


# debug

def diagnose_g_contribution(theta_deg, s11, label=""):
    """
    Diagnóstico para entender por qué g no sube tanto como parece en la polar.

    Imprime:
      - S11 máximo y en qué ángulo ocurre
      - S11 en ángulos importantes
      - fracción de dispersión acumulada dentro de conos forward
      - contribución al valor de g
    """

    theta_deg = np.asarray(theta_deg, dtype=float)
    s11 = np.asarray(s11, dtype=float)

    mask = np.isfinite(theta_deg) & np.isfinite(s11)
    theta_deg = theta_deg[mask]
    s11 = s11[mask]

    if len(theta_deg) < 2:
        print(f"\nDIAGNÓSTICO {label}: no hay suficientes puntos.")
        return

    order = np.argsort(theta_deg)
    theta_deg = theta_deg[order]
    s11 = s11[order]

    theta_rad = np.deg2rad(theta_deg)

    den_integrand = s11 * np.sin(theta_rad)
    num_integrand = s11 * np.cos(theta_rad) * np.sin(theta_rad)

    den_total = trapezoid(den_integrand, theta_rad)
    num_total = trapezoid(num_integrand, theta_rad)

    if abs(den_total) < 1e-30:
        print(f"\nDIAGNÓSTICO {label}: denominador casi cero.")
        return

    g = num_total / den_total

    print("\n" + "=" * 72)
    print(f"DIAGNÓSTICO DE g {label}")
    print("=" * 72)

    print(f"g calculado = {g:.8f}")
    print(f"theta min/max = {theta_deg.min():.6f}°, {theta_deg.max():.6f}°")
    print(f"n puntos = {len(theta_deg)}")

    idx_max = np.argmax(s11)
    print(f"S11 máximo = {s11[idx_max]:.6e} en theta = {theta_deg[idx_max]:.6f}°")

    print("\nValores puntuales de S11:")
    for angle in [0, 0.1, 0.5, 1, 2, 5, 10, 20, 30, 60, 90, 120, 150, 180]:
        idx = np.argmin(np.abs(theta_deg - angle))
        print(f"  S11({theta_deg[idx]:8.4f}°) = {s11[idx]:.6e}")

    print("\nContribución acumulada desde forward:")
    print(f"{'Cono':>12}  {'Frac. denom':>14}  {'Contrib. a g':>14}  {'g medio cono':>14}")
    print("-" * 64)

    for angle in [0.1, 0.5, 1, 2, 5, 10, 20, 30, 45, 60, 90]:
        cone_mask = theta_deg <= angle

        if np.count_nonzero(cone_mask) < 2:
            continue

        den_part = trapezoid(den_integrand[cone_mask], theta_rad[cone_mask])
        num_part = trapezoid(num_integrand[cone_mask], theta_rad[cone_mask])

        frac_den = den_part / den_total
        contrib_g = num_part / den_total
        g_cone = num_part / den_part if abs(den_part) > 1e-30 else np.nan

        print(f"0–{angle:<8g}°  {frac_den:14.6f}  {contrib_g:14.6f}  {g_cone:14.6f}")

    back_mask = theta_deg >= 90

    if np.count_nonzero(back_mask) >= 2:
        den_back = trapezoid(den_integrand[back_mask], theta_rad[back_mask])
        num_back = trapezoid(num_integrand[back_mask], theta_rad[back_mask])

        print("-" * 64)
        print(f"90–180°       {den_back / den_total:14.6f}  {num_back / den_total:14.6f}")

    print("=" * 72)



# ─────────────────────────────────────────────────────────────────────────────
# CONFIG Y SWEEP
# ─────────────────────────────────────────────────────────────────────────────

def get_first_float(cfg, keys):
    """
    Busca la primera clave existente en cfg y la convierte a float.
    """
    for key in keys:
        if key in cfg and cfg[key] not in [None, ""]:
            try:
                return float(cfg[key])
            except Exception:
                pass
    return None


def build_linear_sweep(section):
    """
    Construye una lista de valores desde una sección tipo:

        {"enabled": true, "min": ..., "max": ..., "n": ...}

    También acepta opcionalmente:
        {"values": [ ... ]}
    """
    if not section:
        return None

    if "values" in section and section["values"] is not None:
        try:
            return [float(v) for v in section["values"]]
        except Exception:
            return None

    required = ["min", "max", "n"]

    if not all(key in section for key in required):
        return None

    try:
        v_min = float(section["min"])
        v_max = float(section["max"])
        n = int(section["n"])
    except Exception:
        return None

    if n <= 0:
        return None

    return list(np.linspace(v_min, v_max, n))


def load_sweep_params(args):
    """
    Detecta el tipo de sweep y devuelve:

        sweep_mode   : 'radius', 'wavelength' o None
        sweep_values : lista de radios o longitudes de onda en µm
        radius_um    : radio fijo en µm
        lambda_um    : longitud de onda fija en µm
        cfg          : diccionario config.json
    """
    sweep_mode = None
    sweep_values = None

    radius_um = args.radius_um
    lambda_um = args.lambda_um

    cfg = {}

    if args.config_json and os.path.isfile(args.config_json):
        try:
            with open(args.config_json, "r") as f:
                cfg = json.load(f)
        except Exception as e:
            print(f"AVISO: no se pudo leer config.json ({e}).")
            cfg = {}

    if cfg:
        rs = cfg.get("radius_sweep", {})
        ws = cfg.get("wavelength_sweep", {})

        radius_enabled = bool(rs.get("enabled"))
        wavelength_enabled = bool(ws.get("enabled"))

        if radius_enabled and wavelength_enabled:
            print(
                "AVISO: radius_sweep y wavelength_sweep están ambos activos. "
                "Se usará radius_sweep."
            )
            sweep_mode = "radius"
        elif radius_enabled:
            sweep_mode = "radius"
        elif wavelength_enabled:
            sweep_mode = "wavelength"

        # Leer parámetros fijos desde config si no vienen por argumento.
        if lambda_um is None:
            lambda_um = get_first_float(
                cfg,
                ["lambda_um", "wavelength_um", "wavelength", "lambda"]
            )

        if radius_um is None:
            radius_um = get_first_float(
                cfg,
                ["radius_um", "sphere_radius_um", "sphere_radius", "radius"]
            )

        if sweep_mode == "radius":
            sweep_values = build_linear_sweep(rs)

            if sweep_values is not None:
                print(
                    f"  → Sweep de radio detectado: "
                    f"{sweep_values[0]:.6g}–{sweep_values[-1]:.6g} µm "
                    f"({len(sweep_values)} pasos)"
                )
            else:
                print("AVISO: radius_sweep está activo, pero no se pudieron leer sus valores.")

        elif sweep_mode == "wavelength":
            sweep_values = build_linear_sweep(ws)

            if sweep_values is not None:
                print(
                    f"  → Sweep de longitud de onda detectado: "
                    f"{sweep_values[0] * 1000:.6g}–{sweep_values[-1] * 1000:.6g} nm "
                    f"({len(sweep_values)} pasos)"
                )
            else:
                print(
                    "AVISO: wavelength_sweep está activo, "
                    "pero no se pudieron leer sus valores."
                )

    # Fallback manual.
    if sweep_values is None:
        if args.radii is not None:
            sweep_mode = "radius"
            sweep_values = args.radii
            print(f"  → Radios leídos de --radii: {len(sweep_values)} valores")

        elif args.wavelengths is not None:
            sweep_mode = "wavelength"
            sweep_values = args.wavelengths
            print(
                f"  → Longitudes de onda leídas de --wavelengths: "
                f"{len(sweep_values)} valores"
            )

    return sweep_mode, sweep_values, radius_um, lambda_um, cfg


def get_run_parameters(run, k, sweep_mode, sweep_values, radius_um, lambda_um):
    """
    Determina a, lambda y x para un run.
    """
    a = None
    lam = None

    if sweep_mode == "radius":
        if sweep_values is not None and k < len(sweep_values):
            a = sweep_values[k]
        else:
            a = run.get("radius")

        lam = lambda_um

    elif sweep_mode == "wavelength":
        if sweep_values is not None and k < len(sweep_values):
            lam = sweep_values[k]
        else:
            lam = lambda_um

        if radius_um is not None:
            a = radius_um
        else:
            a = run.get("radius")

    else:
        a = run.get("radius") if run.get("radius") is not None else radius_um
        lam = lambda_um

    if lam is None:
        lam = 0.520

    if run.get("x") is not None:
        x = run["x"]
    elif a is not None and lam is not None and abs(lam) > 1e-30:
        x = 2.0 * np.pi * a / lam
    else:
        x = None

    return a, lam, x


# ─────────────────────────────────────────────────────────────────────────────
# DEBUG
# ─────────────────────────────────────────────────────────────────────────────

def print_debug_info(run, run_index, g_num):
    theta = run["theta"]
    s11 = run["s11"]

    print(f"\nDEBUG run {run_index}")

    if theta is None or s11 is None or len(theta) == 0:
        print("  Sin datos angulares.")
        return

    print(f"  puntos angulares: {len(theta)}")
    print(f"  theta min/max: {theta.min():.6g}, {theta.max():.6g}")
    print(f"  S11 min/max: {s11.min():.6e}, {s11.max():.6e}")

    idx_0 = np.argmin(np.abs(theta - 0.0))
    idx_180 = np.argmin(np.abs(theta - 180.0))

    s11_0 = s11[idx_0]
    s11_180 = s11[idx_180]

    print(f"  S11(0°) aprox:   {s11_0:.6e}")
    print(f"  S11(180°) aprox: {s11_180:.6e}")

    if abs(s11_0) > 1e-30:
        print(f"  S11(180°)/S11(0°): {s11_180 / s11_0:.6e}")

    print(f"  g_num: {g_num:.8g}")

    if run.get("g_exp") is not None:
        print(f"  g_exp: {run['g_exp']:.8g}")
        if run.get("g_exp_note"):
            print(f"  nota g_exp: {run['g_exp_note']}")

    if run["warnings"]:
        print("  avisos:")
        for warning in run["warnings"]:
            print(f"    - {warning}")


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICA
# ─────────────────────────────────────────────────────────────────────────────

def make_plot(results, sweep_mode, radius_um, lambda_um, output_path):
    if sweep_mode == "wavelength":
        xs = [
            r["lam"] * 1000.0 if r["lam"] is not None else r["run"]
            for r in results
        ]
        xlabel = r"Longitud de onda $\lambda$ (nm)"

        if radius_um is not None:
            title = (
                f"Asymmetry parameter, "
                f"$a = {radius_um * 1000:.0f}$ nm"
            )
        else:
            title = "Asymmetry parameter"

    elif sweep_mode == "radius":
        xs = [
            r["x"] if r["x"] is not None else r["run"]
            for r in results
        ]
        # xlabel = r"Parámetro de tamaño $x = 2\pi a/\lambda$"
        xlabel = r"Size parameter $x = 2\pi a/\lambda$"

        if lambda_um is not None:
            title = (
                f"Rayleigh → Mie, "
                f"$\\lambda = {lambda_um * 1000:.0f}$ nm"
            )
        else:
            title = "Transición Rayleigh → Mie"

    else:
        xs = [
            r["x"] if r["x"] is not None else r["run"]
            for r in results
        ]
        xlabel = r"Size parameter $x$ or run number"
        title = "Asymmetry parameter g"

    g_num_vals = [r["g_num"] for r in results]
    g_exp_vals = [r["g_exp"] for r in results]

    has_exp = any(g is not None for g in g_exp_vals)

    fig, ax = plt.subplots(figsize=(7, 4.5))

    ax.plot(
        xs,
        g_num_vals,
        "o-",
        color="steelblue",
        lw=1.8,
        ms=5,
        # label=r"$g$ numérico",
    )

    if has_exp:
        g_exp_clean = [
            g if g is not None else np.nan
            for g in g_exp_vals
        ]

        ax.plot(
            xs,
            g_exp_clean,
            "s--",
            color="tomato",
            lw=1.8,
            ms=5,
            label=r"$g$ expansión",
        )

    ax.axhline(0.0, color="gray", lw=0.8, ls=":")

    ax.set_xlabel(xlabel, fontsize=18)
    ax.set_ylabel(r"$g = \langle \cos\theta \rangle$", fontsize=18)
    ax.set_title(title, fontsize=19)

    # ax.set_ylim(-0.05, 1.0)

    ax.grid(True, alpha=0.3)
    # ax.legend(fontsize=9)

    fig.tight_layout()

    # outdir = os.path.join(output_path, "plots")
    
    fig.savefig(output_path, dpi=150)

    print(f"\nFigura guardada en: {output_path}")

    plt.show()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "filepath",
        help="Fichero de salida de MSTM."
    )

    parser.add_argument(
        "--config_json",
        type=str,
        default=None,
        help="config.json de la simulación."
    )

    parser.add_argument(
        "--save_dir",
        type=str,
        default=None,
        help="Carpeta donde guardar la figura."
    )

    parser.add_argument(
        "--lambda_um",
        type=float,
        default=None,
        help="Longitud de onda fija en µm para sweep de radio."
    )

    parser.add_argument(
        "--radii",
        type=float,
        nargs="+",
        default=None,
        help="Lista manual de radios en µm."
    )

    parser.add_argument(
        "--radius_um",
        type=float,
        default=None,
        help="Radio fijo en µm para sweep de longitud de onda."
    )

    parser.add_argument(
        "--wavelengths",
        type=float,
        nargs="+",
        default=None,
        help="Lista manual de longitudes de onda en µm."
    )

    parser.add_argument(
        "--no_plot",
        action="store_true",
        help="Solo imprime valores, sin generar figura."
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Imprime información de diagnóstico para cada run."
    )

    args = parser.parse_args()

    filepath = Path(args.filepath)

    if not filepath.exists():
        print(f"ERROR: no existe el fichero: {filepath}")
        sys.exit(1)

    print(f"Leyendo: {filepath}")

    runs = parse_mstm_output(filepath)

    print(f"  → {len(runs)} run(s) encontrados")

    if len(runs) == 0:
        print("ERROR: no se encontraron bloques válidos de matriz de dispersión.")
        sys.exit(1)

    sweep_mode, sweep_values, radius_um, lambda_um, cfg = load_sweep_params(args)

    if sweep_values is not None and len(sweep_values) != len(runs):
        print(f"AVISO: hay {len(sweep_values)} valores de sweep para {len(runs)} runs.")

    if sweep_mode == "radius":
        print(f"\n{'Run':>4}  {'a (µm)':>10}  {'λ (nm)':>10}  {'x':>10}  {'g_num':>12}  {'g_exp':>12}")

    elif sweep_mode == "wavelength":
        print(f"\n{'Run':>4}  {'λ (nm)':>10}  {'a (µm)':>10}  {'x':>10}  {'g_num':>12}  {'g_exp':>12}")

    else:
        print(f"\n{'Run':>4}  {'a (µm)':>10}  {'λ (nm)':>10}  {'x':>10}  {'g_num':>12}  {'g_exp':>12}")

    print("-" * 76)

    results = []

    for k, run in enumerate(runs):
        a, lam, x = get_run_parameters(
            run=run,
            k=k,
            sweep_mode=sweep_mode,
            sweep_values=sweep_values,
            radius_um=radius_um,
            lambda_um=lambda_um,
        )

        g_num = compute_g_numerical(run["theta"], run["s11"])
        g_exp = run["g_exp"]

        #debug
        if k + 1 == 1:
            diagnose_g_contribution(run['theta'], run['s11'], label=f"run {k+1}")

        if np.isfinite(g_num) and not (-1.0 <= g_num <= 1.0):
            run["warnings"].append(
                f"g_num = {g_num:.6g} está fuera del rango físico [-1, 1]."
            )

        if sweep_mode == "wavelength":
            col1 = format_value(lam * 1000.0 if lam is not None else None, "{:.4f}")
            col2 = format_value(a, "{:.6g}")
        else:
            col1 = format_value(a, "{:.6g}")
            col2 = format_value(lam * 1000.0 if lam is not None else None, "{:.4f}")

        x_str = format_value(x, "{:.6g}")
        g_num_str = format_value(g_num, "{:.6g}", missing="nan")
        g_exp_str = format_value(g_exp, "{:.6g}", missing="N/A")

        print(f"{k+1:>4}  {col1:>10}  {col2:>10}  {x_str:>10}  {g_num_str:>12}  {g_exp_str:>12}")

        if args.debug:
            print_debug_info(run, k + 1, g_num)

        results.append(
            {
                "run": k + 1,
                "a": a,
                "lam": lam,
                "x": x,
                "g_num": g_num,
                "g_exp": g_exp,
                "qext": run["qext"],
                "qabs": run["qabs"],
                "qsca": run["qsca"],
            }
        )

    if args.no_plot:
        return

    if args.save_dir:
        os.makedirs(args.save_dir, exist_ok=True)
        output_path = Path(args.save_dir) / "plots" / f"{filepath.stem}_asymmetry.png"
    else:
        output_path = filepath.with_name(f"{filepath.stem}_asymmetry.png")

    make_plot(
        results=results,
        sweep_mode=sweep_mode,
        radius_um=radius_um,
        lambda_um=lambda_um,
        output_path=output_path,
    )


if __name__ == "__main__":
    main()