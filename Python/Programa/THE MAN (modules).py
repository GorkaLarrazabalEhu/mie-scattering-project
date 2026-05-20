import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import numpy as np
import os
import subprocess as sb
import calculations.mstm_utils as mstm
import datetime
import json
import threading


# Constants
DEFAULT_FOLDER_LOCATION = "C:\\Users\\txuel\\UNI\\TFG Fisika\\code\\Simulaciones"
DEFAULT_PYTHON_PLOT_LOCATION = "C:\\Users\\txuel\\UNI\\TFG Fisika\\code\\Python\\Plotting_codes"
current_dir = os.path.dirname(os.path.abspath(__file__))


class Config:
    """Store simulation configuration parameters."""

    def __init__(self):
        self.folder_location = DEFAULT_FOLDER_LOCATION
        self.plot_location = DEFAULT_PYTHON_PLOT_LOCATION

        self.data = {
            "output_file": "",
            "num_spheres": "",
            "positions": [],
            "incident_beta": "0.d0",
            "incident_alpha": "0.d0",
            "length_scale": "1.d0",
            "scattering_angle": "1.d0",
            "gaussian_beam_constant": "0.1d0",
            "is_gaussian_beam": False,
            "near_field": False,
            "near_field_file": "",
            "near_field_stepsize": "",
            "near_field_stepsize_auto": True,
            "separation": "",
            "geometry": "(none)",
            "material": "Custom",
            "custom_n": "",
            "custom_k": "",
            "wavelength_sweep": {
                "enabled": False,
                "min": "",
                "max": "",
                "n": ""
            },
            "radius_sweep": {
                "enabled": False,
                "min": "",
                "max": "",
                "n": ""
            }
        }

    # Save/Load last config (but in a better way!)
    def save_to_json(self, filepath="last_config.json"):
        with open(filepath, "w") as f:
            json.dump(self.data, f, indent=4)

    def load_from_json(self, filepath="last_config.json"):
        if not os.path.exists(filepath):
            return False
        with open(filepath, "r") as f:
            self.data = json.load(f)
        return True

class MieTheoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MSTM GUI")
        self.root.state("zoomed")  # Start maximized
        current_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            self.root.iconbitmap(os.path.join(current_dir, "favicon.ico"))
        except:
            pass  # if favicon not found, skip

        # Initialize Config object to store parameters
        self.config = Config()

        # === Build GUI sections ===
        self.build_gui()
        self.load_previous_data()

    def build_gui(self):
        """Build GUI with two-column grid layout."""
        # Configure two main columns to expand equally
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)

        self.root.rowconfigure(0, weight=1)

        # ===== Container for the whole LEFT side, split into two subcolumns =====
        left = tk.Frame(self.root)
        left.grid(row=0, column=0, rowspan=99, sticky="nsew")  # span enough rows
        left.columnconfigure(0, weight=1)  # left-left subcolumn
        left.columnconfigure(1, weight=1)  # left-right subcolumn
        # optional: left.rowconfigure(index, weight=1) if you want vertical stretch

        # ---- File Options (spans BOTH subcolumns) ----
        frame_files = tk.LabelFrame(left, text="File Options", padx=5, pady=5)
        frame_files.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        tk.Label(frame_files, text="Folder Location").grid(row=0, column=0, sticky="w")
        self.folder_location_entry = tk.Entry(frame_files, width=60)
        self.folder_location_entry.grid(row=0, column=1, sticky="ew")

        tk.Button(frame_files, text="New Simulation Folder",
                command=self.create_new_simulation_folder).grid(row=0, column=2, padx=5)

        tk.Button(frame_files, text="Load Simulation Folder",
                command=self.load_simulation_folder).grid(row=0, column=3, padx=5)

        tk.Label(frame_files, text="Output File Name").grid(row=1, column=0, sticky="w")
        self.output_file_entry = tk.Entry(frame_files, width=60)
        self.output_file_entry.grid(row=1, column=1, sticky="ew")

        tk.Button(frame_files, text="Open Simulation Folder",
                command=self.open_simulation_folder).grid(row=1, column=2, padx=5)

        tk.Label(frame_files, text="Number of Spheres").grid(row=2, column=0, sticky="w")
        self.num_spheres_entry = tk.Entry(frame_files, width=10)
        self.num_spheres_entry.grid(row=2, column=1, sticky="w")

        tk.Label(frame_files, text="Sphere Position (x,y,z,r,n)").grid(row=3, column=0, sticky="nw")
        self.position_entry = tk.Text(frame_files, height=10, width=75)
        self.position_entry.grid(row=3, column=1, sticky="ew")

        frame_files.grid_columnconfigure(1, weight=1)  # let the Text expand

        # --- live preview (to the right of the text box) ---
        tk.Label(frame_files, text="Preview (XZ)").grid(row=2, column=2, columnspan=2, sticky="w", padx=5)
        self.sphere_canvas = tk.Canvas(
            frame_files, width=320, height=240, bg="white", highlightthickness=1, relief="sunken")
        self.sphere_canvas.grid(row=3, column=2, columnspan=2, sticky="n", padx=5, pady=0)

        # redraw when the positions text changes
        self.position_entry.bind("<<Modified>>", self.on_positions_modified)

        # ---- Incident Parameters (ONLY left-left subcolumn) ----
        frame_incident = tk.LabelFrame(left, text="Incident Parameters", padx=5, pady=5)
        frame_incident.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        tk.Label(frame_incident, text="Incident Beta (deg)").grid(row=0, column=0, sticky="w")
        self.incident_beta_entry = tk.Entry(frame_incident, width=10)
        self.incident_beta_entry.grid(row=0, column=1, padx=5)

        tk.Label(frame_incident, text="Incident Alpha (deg)").grid(row=0, column=2, sticky="w")
        self.incident_alpha_entry = tk.Entry(frame_incident, width=10)
        self.incident_alpha_entry.grid(row=0, column=3, padx=5)

        tk.Label(frame_incident, text="Scattering angle (deg)").grid(row=0, column=4, sticky="w")
        self.scattering_angle_entry = tk.Entry(frame_incident, width=10)
        self.scattering_angle_entry.grid(row=0, column=5, padx=5)

        tk.Label(frame_incident, text="Length Scale Factor").grid(row=1, column=0, sticky="w")
        self.length_scale_entry = tk.Entry(frame_incident, width=30)
        self.length_scale_entry.grid(row=1, column=1, padx=5)


        # ---- Multipole Expansion Order ----
        tk.Label(frame_incident, text="Multipole Order (n)").grid(row=2, column=0, sticky="w")

        self.multipole_order = tk.StringVar()
        self.multipole_combo = ttk.Combobox(
            frame_incident,
            textvariable=self.multipole_order,
            values=[str(i) for i in range(20)],  # 0 to 5
            width=8,
            state="readonly"
        )
        self.multipole_combo.grid(row=2, column=1, padx=5)
        self.multipole_combo.current(0)  # default = 0


        # ---- Beam Options (ONLY left-left subcolumn) ----
        frame_beam = tk.LabelFrame(left, text="Beam Options", padx=5, pady=5)
        frame_beam.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)

        self.beam_type_var = tk.StringVar(value="Plane Wave")
        tk.Label(frame_beam, text="Beam Type").grid(row=0, column=0, sticky="w")
        tk.Radiobutton(frame_beam, text="Plane Wave", variable=self.beam_type_var, value="Plane Wave").grid(row=0, column=1, sticky="w")
        tk.Radiobutton(frame_beam, text="Gaussian", variable=self.beam_type_var, value="Gaussian").grid(row=0, column=2, sticky="w")

        tk.Label(frame_beam, text="Gaussian Beam Constant").grid(row=1, column=0, sticky="w")
        self.gaussian_constant_entry = tk.Entry(frame_beam, width=10)
        self.gaussian_constant_entry.grid(row=1, column=1, sticky="w")

        # ---- Near Field (ONLY left-left subcolumn) ----
        frame_near = tk.LabelFrame(left, text="Near Field", padx=5, pady=5)
        frame_near.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)

        self.near_field_var = tk.BooleanVar()
        tk.Checkbutton(
            frame_near,
            text="Calculate Near Field",
            variable=self.near_field_var
        ).grid(row=0, column=0, sticky="w")

        tk.Label(frame_near, text="Near Field Output File").grid(row=1, column=0, sticky="w")
        self.near_field_file_entry = tk.Entry(frame_near, width=20)
        self.near_field_file_entry.grid(row=1, column=1, sticky="w")

        self.near_field_stepsize_auto_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            frame_near,
            text="Auto step size",
            variable=self.near_field_stepsize_auto_var,
            command=self.toggle_near_field_stepsize_mode
        ).grid(row=2, column=0, sticky="w")

        tk.Label(frame_near, text="Near Field Step Size").grid(row=3, column=0, sticky="w")
        self.near_field_stepsize_entry = tk.Entry(frame_near, width=12)
        self.near_field_stepsize_entry.grid(row=3, column=1, sticky="w")

        self.near_field_stepsize_label = tk.Label(frame_near, text="Calculated: --")
        self.near_field_stepsize_label.grid(row=3, column=2, sticky="w", padx=5)

        self.toggle_near_field_stepsize_mode()

        # ---- Scattering Matrix plot options (LEFT container, right subcolumn) ----
        frame_scattering = tk.LabelFrame(left, text="Scattering Matrix Plot Options", padx=5, pady=5)
        frame_scattering.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        for c in range(3):
            frame_scattering.grid_columnconfigure(c, weight=1)

        self.scat_option_vars = {
            "S11":  tk.BooleanVar(value=True),
            "DOP":  tk.BooleanVar(value=False),
            "DOCP": tk.BooleanVar(value=False),
            "DOLP": tk.BooleanVar(value=False),
        }
        tk.Checkbutton(frame_scattering, text="S11",  variable=self.scat_option_vars["S11"]).grid(row=0, column=0, sticky="w")
        tk.Checkbutton(frame_scattering, text="DoP",  variable=self.scat_option_vars["DOP"]).grid(row=0, column=1, sticky="w")
        tk.Checkbutton(frame_scattering, text="DoCP", variable=self.scat_option_vars["DOCP"]).grid(row=1, column=0, sticky="w")
        tk.Checkbutton(frame_scattering, text="DoLP", variable=self.scat_option_vars["DOLP"]).grid(row=1, column=1, sticky="w")

        # ---- Efficiencies plot options (LEFT container, right subcolumn) ----
        frame_efficiencies = tk.LabelFrame(left, text="Efficiencies Plot Options", padx=5, pady=5)
        frame_efficiencies.grid(row=2, column=1, sticky="nsew", padx=10, pady=5)
        for c in range(3):
            frame_efficiencies.grid_columnconfigure(c, weight=1)

        # Row 0: Polarization (three checkbuttons)
        tk.Label(frame_efficiencies, text="Polarization").grid(row=0, column=0, columnspan=3, sticky="w")
        self.pol_vars = {
            "unpol": tk.BooleanVar(value=True),
            "perp":  tk.BooleanVar(value=False),
            "par":   tk.BooleanVar(value=False),
        }
        tk.Checkbutton(frame_efficiencies, text="Unpolarized", variable=self.pol_vars["unpol"]).grid(row=1, column=0, sticky="w")
        tk.Checkbutton(frame_efficiencies, text="Perpendicular", variable=self.pol_vars["perp"]).grid(row=1, column=1, sticky="w")
        tk.Checkbutton(frame_efficiencies, text="Parallel",     variable=self.pol_vars["par"]).grid(row=1, column=2, sticky="w")

        # Row 2: Efficiencies (three checkbuttons)
        tk.Label(frame_efficiencies, text="Efficiencies").grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))
        self.q_vars = {
            "Qext": tk.BooleanVar(value=True),
            "Qabs": tk.BooleanVar(value=False),
            "Qsca": tk.BooleanVar(value=False),
        }
        tk.Checkbutton(frame_efficiencies, text="Qext", variable=self.q_vars["Qext"]).grid(row=3, column=0, sticky="w")
        tk.Checkbutton(frame_efficiencies, text="Qabs", variable=self.q_vars["Qabs"]).grid(row=3, column=1, sticky="w")
        tk.Checkbutton(frame_efficiencies, text="Qsca", variable=self.q_vars["Qsca"]).grid(row=3, column=2, sticky="w")

        # =============================== Column 1: Right side ============================
        # ---- Physical Parameters ----
        frame_params = tk.LabelFrame(
            self.root, text="Physical Parameters", padx=5, pady=5)
        frame_params.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)

        # Row 0
        tk.Label(frame_params, text="Wavelength (μm)").grid(
            row=0, column=0, sticky="w")
        self.wavelength_entry = tk.Entry(frame_params, width=10)
        self.wavelength_entry.grid(row=0, column=1, padx=5)
        tk.Button(frame_params, text="Compute Parameters",
                command=self.compute_mstm_params).grid(row=0, column=2, padx=5)

        # Row 1 — Sphere Radius + "All equal" checkbox + dynamic input area
        radius_hdr = tk.Frame(frame_params)
        radius_hdr.grid(row=1, column=0, sticky="w")
        tk.Label(radius_hdr, text="Sphere Radius (μm)").pack(side="left")
        self.radii_equal_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            radius_hdr, text="All equal",
            variable=self.radii_equal_var,
            command=self.toggle_radius_mode,
        ).pack(side="left", padx=(6, 0))

        # Container that will hold either one Entry (equal mode)
        # or N labelled entries (individual mode)
        self.radius_input_frame = tk.Frame(frame_params)
        self.radius_input_frame.grid(row=1, column=1, sticky="w", padx=5)

        self.individual_radius_entries = []
        # Build initial single-entry view
        self.radius_entry = tk.Entry(self.radius_input_frame, width=10)
        self.radius_entry.grid(row=0, column=0)

        tk.Button(frame_params, text="Apply to Positions",
                command=self.apply_general_to_positions).grid(row=1, column=2, padx=5)

        # Row 2
        tk.Label(frame_params, text="Material").grid(row=2, column=0, sticky="w")
        self.material_var = tk.StringVar(value="Custom")
        tk.OptionMenu(frame_params, self.material_var, "Au", "Ag",
                    "SiO2", "H2O", "Custom").grid(row=2, column=1, sticky="w")
        
        tk.Label(frame_params, text="custom n, k:").grid(row=2, column=2, sticky="w", padx=1)
        self.custom_n_entry = tk.Entry(frame_params, width=8)
        self.custom_n_entry.grid(row=2, column=3, sticky="w", padx=1)
        self.custom_k_entry = tk.Entry(frame_params, width=8)
        self.custom_k_entry.grid(row=2, column=4, sticky="w", padx=1)
        self.material_var.trace_add("write", self.on_material_change)
        self.on_material_change()


        # Row 3 — Separation (new, own row)
        tk.Label(frame_params, text="Separation (μm):").grid(
            row=3, column=0, sticky="w", padx=5, pady=2)
        self.separation_entry = tk.Entry(frame_params, width=10)
        self.separation_entry.grid(row=3, column=1, sticky="w", padx=5, pady=2)

        # Row 4 — Geometry selector (new, own row)
        tk.Label(frame_params, text="Geometry:").grid(
            row=4, column=0, sticky="w", padx=5, pady=2)
        self.geometry_var = tk.StringVar(value="(none)")
        geo_options = [
            "(none)",
            "4 in line (North–South)",
            "4 in line (East–West)",
            "4 in a square",
            "4 in a square (45°)",
            "2 in line (NS)",
            "2 in line (EW)",
        ]
        self.geometry_combo = ttk.Combobox(
            frame_params, textvariable=self.geometry_var,
            values=geo_options, state="readonly", width=22
        )
        self.geometry_combo.grid(row=4, column=1, sticky="w", padx=5, pady=2)

        # Multiple run options for different wavelengths

        # Row 5 — Wavelength sweep (μm)
        sweep_frame = ttk.LabelFrame(frame_params, text="Wavelength sweep (μm)")
        sweep_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=(6, 0))

        self.sweep_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            sweep_frame, text="Wavelength Sweep", 
            command=lambda: self.on_sweep_toggle("wavelength"), 
            variable=self.sweep_var
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=(6, 10), pady=2)

        tk.Label(sweep_frame, text="min:").grid(row=1, column=0, sticky="w", padx=(6, 4), pady=2)
        self.min_wavelength_entry = tk.Entry(sweep_frame, width=10)
        self.min_wavelength_entry.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=2)

        tk.Label(sweep_frame, text="max:").grid(row=1, column=2, sticky="w", padx=(6, 4), pady=2)
        self.max_wavelength_entry = tk.Entry(sweep_frame, width=10)
        self.max_wavelength_entry.grid(row=1, column=3, sticky="w", padx=(0, 10), pady=2)

        tk.Label(sweep_frame, text="#steps:").grid(row=1, column=4, sticky="w", padx=(6, 4), pady=2)
        self.step_wavelength_entry = tk.Entry(sweep_frame, width=10)
        self.step_wavelength_entry.grid(row=1, column=5, sticky="w", padx=(0, 8), pady=2)

        # Multiple run options for different wavelengths

        # Row 6 — Radius sweep (μm)
        sweep_radius_frame = ttk.LabelFrame(frame_params, text="Radius Sweep (μm)")
        sweep_radius_frame.grid(row=6, column=0, columnspan=3, sticky="ew", padx=5, pady=(6, 0))

        self.sweep_radius_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            sweep_radius_frame, 
            text="Radius Sweep", 
            command=lambda: self.on_sweep_toggle("radius"),
            variable=self.sweep_radius_var
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=(6, 10), pady=2)

        tk.Label(sweep_radius_frame, text="min:").grid(row=1, column=0, sticky="w", padx=(6, 4), pady=2)
        self.min_radius_entry = tk.Entry(sweep_radius_frame, width=10)
        self.min_radius_entry.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=2)

        tk.Label(sweep_radius_frame, text="max:").grid(row=1, column=2, sticky="w", padx=(6, 4), pady=2)
        self.max_radius_entry = tk.Entry(sweep_radius_frame, width=10)
        self.max_radius_entry.grid(row=1, column=3, sticky="w", padx=(0, 10), pady=2)

        tk.Label(sweep_radius_frame, text="#steps:").grid(row=1, column=4, sticky="w", padx=(6, 4), pady=2)
        self.step_radius_entry = tk.Entry(sweep_radius_frame, width=10)
        self.step_radius_entry.grid(row=1, column=5, sticky="w", padx=(0, 8), pady=2)

        # Row 2 — Plot button + status label
        self.plot_sweep_btn = tk.Button(
            sweep_radius_frame,
            text="\U0001F4CA Plot Radius Sweep",
            command=self.plot_radius_sweep,
            # bg="#4A90D9", fg="white",
            activebackground="#000000", activeforeground="white",
            relief="raised", padx=6,
        )
        self.plot_sweep_btn.grid(row=2, column=0, columnspan=3, sticky="w",
                                 padx=(6, 10), pady=(4, 6))

        self.plot_sweep_status = tk.Label(sweep_radius_frame, text="", fg="gray")
        self.plot_sweep_status.grid(row=2, column=3, columnspan=3, sticky="w",
                                    padx=(0, 8), pady=(4, 6))


        # ---- Results Panel ----
        frame_results = tk.LabelFrame(self.root, text="Computed Parameters", padx=5, pady=5)
        frame_results.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=10, pady=5)
        self.results_text = tk.Text(frame_results, height=12, width=40, state="disabled")
        self.results_text.pack(fill="both", expand=True)

        # ---- Plot Options ----
        frame_plot = tk.LabelFrame(self.root, text="NF Plot Options", padx=5, pady=5)
        frame_plot.grid(row=3, column=1, sticky="nsew", padx=10, pady=5)

        self.plot_type_var = tk.StringVar(value="Poynting")
        tk.Radiobutton(frame_plot, text="Electric Field", variable=self.plot_type_var, value="Electric", command=self.update_plot_options).grid(row=0, column=0, sticky="w")
        tk.Radiobutton(frame_plot, text="Magnetic Field", variable=self.plot_type_var, value="Magnetic", command=self.update_plot_options).grid(row=0, column=1, sticky="w")
        tk.Radiobutton(frame_plot, text="Poynting Vector", variable=self.plot_type_var, value="Poynting", command=self.update_plot_options).grid(row=0, column=2, sticky="w")
        tk.Radiobutton(frame_plot, text="|E|²", variable=self.plot_type_var, value="absE", command=self.update_plot_options).grid(row=0, column=3, sticky="w")

        self.frame_plot_options = tk.Frame(frame_plot)
        self.frame_plot_options.grid(row=1, column=0, columnspan=3, pady=5)

        self.select_all_button = tk.Button(frame_plot, text="Select All", command=self.toggle_select_all)
        self.select_all_button.grid(row=1, column=4, pady=5, sticky="w")

        self.plot_option_vars = []
        self.plot_option_labels = []
        self.update_plot_options()

        # ---- Control Buttons ----
        frame_buttons = tk.Frame(self.root)
        frame_buttons.grid(row=4, column=0, columnspan=2, pady=10)
        
        
        self.matrix = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_buttons, text="Scattering Matrix", variable=self.matrix).grid(row=0, column=0, padx=5)

        tk.Button(frame_buttons, text="Write mstm.inp", command=self.write_input_file).grid(row=0, column=1, padx=5)
        self.load_write_status_label = tk.Label(frame_buttons, text="Loading")
        self.load_write_status_label.grid(row=0, column=2, padx=5)
        tk.Button(frame_buttons, text="Run MSTM Simulation", command=self.run_simulation).grid(row=1, column=0, padx=5)
        self.status_label = tk.Label(frame_buttons, text="  Ready   ")
        self.status_label.grid(row=1, column=1, padx=10)
        tk.Button(frame_buttons, text="\U0001F4CA Plot Scattering Matrix", command=self.plot_scattering_matrix).grid(row=1, column=2, padx=5)
        tk.Button(frame_buttons, text="\U0001F4CA Plot Near Field", command=self.plot_near_field).grid(row=1, column=3, padx=5)
        tk.Button(frame_buttons, text="\U0001F4CA Plot Asymmetry g", command=self.plot_asymmetry).grid(row=1, column=4, padx=5)

    def compute_mstm_params(self):
        try:
            r = float(self.radius_entry.get())
            wl = float(self.wavelength_entry.get())

            # Example: you might also fetch material from dropdown
            material = self.material_var.get()
            if material != "Custom":
                results = mstm.compute_parameters(r, wl, material=material)
            else:
                n_real = float(self.custom_n_entry.get().strip())
                n_imag = float(self.custom_k_entry.get().strip())
                results = mstm.compute_parameters(r, wl, n_real=n_real, n_imag=n_imag)
            
            
            # Format numeric strings for MSTM friendliness
            ls_d0 = f"{results['length_scale_factor']:.10f}d0"
            size_param = f"{results['size_parameter']:.10f}"

            n_re, n_im = None, None
            if "refractive_index" in results:
                n = results["refractive_index"]
                n_re = f"{n.real:.10f}d0"
                n_im = f"{n.imag:.10f}d0"
            else:
                raise ValueError("Refractive index not found for the given material and wavelength.")

            # Strict, parseable preview (do not change the labels/shape below)
            lines = []
            lines.append(f"Input radius        : {r}")
            lines.append(f"Input wavelength    : {wl}")
            lines.append(f"Length scale factor : {ls_d0}")
            lines.append(f"Size parameter      : {size_param}")
            if n_re is not None and n_im is not None:
                lines.append(f"Refractive index    : ({n_re}, {n_im})")

            geom_points = self.compute_geometry_points()  # list of (x,y,z) strings
            if geom_points:
                lines.append("Geometry (x,y,z):")
                for (x, y, z) in geom_points:
                    lines.append(f"{x},{y},{z}")

            preview = "\n".join(lines)

            self.results_text.config(state="normal")
            self.results_text.delete("1.0", "end")
            self.results_text.insert("end", preview)
            self.results_text.config(state="disabled")

            # If individual-radius mode is active, refresh the entry count
            # so it matches the current geometry / number of spheres.
            if not self.radii_equal_var.get():
                self._rebuild_radius_ui()

        except Exception as e:
            self.results_text.config(state="normal")
            self.results_text.delete("1.0", "end")
            self.results_text.insert("end", f"Error: {e}")
            self.results_text.config(state="disabled")


    def get_computed_params_dict(self):
        """Return a dict from the lines in the Computed Parameters box."""
        text = self.results_text.get("1.0", "end-1c")
        params = {}
        for line in text.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            params[key.strip()] = value.strip()
        return params


    def get_computed_params_and_geometry(self):
        """
        Parse the 'Computed parameters' box into:
        params: dict of the key:value lines
        geometry: list of (x,y,z) strings if a 'Geometry (x,y,z):' section exists
        """
        text = self.results_text.get("1.0", "end-1c")
        params = {}
        geometry = []

        lines = text.splitlines()
        reading_geom = False
        for ln in lines:
            if reading_geom:
                ln = ln.strip()
                if ln:
                    parts = [p.strip() for p in ln.split(",")]
                    if len(parts) >= 3:
                        geometry.append((parts[0], parts[1], parts[2]))
                continue

            if ":" in ln:
                key, value = ln.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key.lower().startswith("geometry"):
                    reading_geom = True
                else:
                    params[key] = value

        return params, geometry


    def get_refractive_index_and_length_scale(self, r, wl):
        material = (self.material_var.get() or "Custom").strip()

        # length scale siempre puede venir de la geometría óptica
        # si mstm.compute_parameters te da length_scale_factor sin problema, úsalo
        if material != "Custom":
            results = mstm.compute_parameters(r, wl, material=material)
            n = results["refractive_index"]
            ls = results["length_scale_factor"]
            size_param = results.get("size_parameter")
            return n, ls, size_param

        # --- Custom ---
        n_txt = self.custom_n_entry.get().strip()
        k_txt = self.custom_k_entry.get().strip()

        if not n_txt or not k_txt:
            raise ValueError("For Custom material, both n and k must be provided.")

        n_re = float(n_txt)
        n_im = float(k_txt)

        # Convención típica: m = n + i k
        # si tu Fortran/MSTM espera absorción como parte imaginaria positiva, esto está bien.
        # si en tu implementación usan n - i k, aquí habría que cambiarlo.
        m = complex(n_re, n_im)

        # seguir usando mstm para length_scale y size_parameter si esa parte no depende del material
        results = mstm.compute_parameters(r, wl)
        ls = results["length_scale_factor"]
        size_param = results.get("size_parameter")

        return m, ls, size_param


    def on_material_change(self, *args):
        is_custom = self.material_var.get().strip() == "Custom"
        state = "normal" if is_custom else "disabled"
        self.custom_n_entry.config(state=state)
        self.custom_k_entry.config(state=state)


    def toggle_near_field_stepsize_mode(self):
        """Enable manual step input only when auto mode is disabled."""
        if self.near_field_stepsize_auto_var.get():
            self.near_field_stepsize_entry.config(state="disabled")
            current = self.near_field_stepsize_entry.get().strip()
            if current:
                self.near_field_stepsize_label.config(text=f"Calculated: {current}")
            else:
                self.near_field_stepsize_label.config(text="Calculated automatically")
        else:
            self.near_field_stepsize_entry.config(state="normal")
            self.near_field_stepsize_label.config(text="Manual value will be written")

    def update_plot_options(self):
        """Rebuild the plot options based on selected plot type."""
        for widget in self.frame_plot_options.winfo_children():
            widget.destroy()
        self.plot_option_vars.clear()
        self.plot_option_labels = []

        field_type = self.plot_type_var.get()

        if field_type in ("Electric", "Magnetic"):
            components = ["Ex", "Ey", "Ez"]
            componentsH = ["Hx", "Hy", "Hz"]
            if field_type == "Magnetic":
                components = componentsH
            parts = ["Re", "Im"]
            pols = ["‖", "⟂"]

            options = []
            for pol in pols:
                for comp in components:
                    for part in parts:
                        options.append(f"{part} {comp} {pol}")

            for i, label in enumerate(options):
                var = tk.BooleanVar()
                cb = tk.Checkbutton(self.frame_plot_options, text=label, variable=var)
                row, col = divmod(i, 6)
                cb.grid(row=row, column=col, padx=5, pady=2, sticky="w")
                self.plot_option_vars.append(var)
                self.plot_option_labels.append(label)

        elif field_type == "Poynting":
            for i, comp in enumerate(["Sx", "Sy", "Sz", "S_quiver"]):
                var = tk.BooleanVar()
                cb = tk.Checkbutton(self.frame_plot_options, text=comp, variable=var)
                cb.grid(row=0, column=i, padx=5, pady=2, sticky="w")
                self.plot_option_vars.append(var)
                self.plot_option_labels.append(comp)
        
        elif field_type == "absE":
            for i, comp in enumerate(["|E_avg|^2", "|E‖|^2", "|E⟂|^2"]):
                var = tk.BooleanVar()
                cb = tk.Checkbutton(self.frame_plot_options, text=comp, variable=var)
                cb.grid(row=0, column=i, padx=5, pady=2, sticky="w")
                self.plot_option_vars.append(var)
                self.plot_option_labels.append(comp)


    def on_sweep_toggle(self, source):
        """Ensure only one sweep type is active at a time."""
        if source == "wavelength" and self.sweep_var.get():
            self.sweep_radius_var.set(False)
        elif source == "radius" and self.sweep_radius_var.get():
            self.sweep_var.set(False)


    # ------------------------------------------------------------------ #
    #  Radius mode helpers                                                  #
    # ------------------------------------------------------------------ #

    def toggle_radius_mode(self):
        """Switch between single-radius and per-sphere-radius UI."""
        self._rebuild_radius_ui()

    def _get_num_spheres_for_radii(self):
        """Return how many individual radius entries to create."""
        try:
            n = int(self.num_spheres_entry.get().strip())
            if n > 0:
                return n
        except (ValueError, AttributeError):
            pass
        # Fall back to geometry count
        geo = (self.geometry_var.get() or "").strip()
        geo_counts = {
            "2 in line (NS)": 2, "2 in line (EW)": 2,
            "4 in line (North–South)": 4, "4 in line (East–West)": 4,
            "4 in a square": 4, "4 in a square (45°)": 4,
        }
        return geo_counts.get(geo, 1)

    def _rebuild_radius_ui(self, preserve_values=True):
        """
        Destroy and recreate the widgets inside radius_input_frame.
        If preserve_values=True, carry over whatever is already in the entries.
        """
        # Collect current values before destroying
        old_single = ""
        old_individual = []
        if preserve_values:
            try:
                old_single = self.radius_entry.get().strip()
            except Exception:
                pass
            for e in self.individual_radius_entries:
                try:
                    old_individual.append(e.get().strip())
                except Exception:
                    old_individual.append("")

        # Destroy all children
        for w in self.radius_input_frame.winfo_children():
            w.destroy()
        self.individual_radius_entries = []

        if self.radii_equal_var.get():
            # ---- Single entry mode ----
            self.radius_entry = tk.Entry(self.radius_input_frame, width=10)
            self.radius_entry.grid(row=0, column=0)
            # Restore value: prefer old single; fall back to first individual
            val = old_single or (old_individual[0] if old_individual else "")
            if val:
                self.radius_entry.insert(0, val)
        else:
            # ---- Individual entries mode ----
            n = self._get_num_spheres_for_radii()
            for i in range(n):
                tk.Label(self.radius_input_frame, text=f"Sphere {i+1}:").grid(
                    row=i, column=0, sticky="e", padx=(0, 2))
                e = tk.Entry(self.radius_input_frame, width=10)
                e.grid(row=i, column=1, pady=1)
                # Restore value: use matching old individual, or broadcast old_single
                if i < len(old_individual) and old_individual[i]:
                    e.insert(0, old_individual[i])
                elif old_single:
                    e.insert(0, old_single)
                self.individual_radius_entries.append(e)
            # Make radius_entry point to the first entry for backward-compat code paths
            if self.individual_radius_entries:
                self.radius_entry = self.individual_radius_entries[0]

    def get_sphere_radii(self, n_spheres=None):
        """
        Return a list of radius strings for all spheres.
        In equal mode:      returns [r] * n_spheres.
        In individual mode: returns the list from the individual entries
                            (padded with first value if shorter than n_spheres).
        """
        if self.radii_equal_var.get():
            r = self.radius_entry.get().strip()
            count = n_spheres if n_spheres is not None else self._get_num_spheres_for_radii()
            return [r] * count
        else:
            vals = [e.get().strip() for e in self.individual_radius_entries]
            if n_spheres is not None and len(vals) < n_spheres:
                pad = vals[0] if vals else ""
                vals += [pad] * (n_spheres - len(vals))
            return vals[:n_spheres] if n_spheres is not None else vals


    def toggle_select_all(self):
        """Toggle all currently visible checkbuttons."""
        if any(not v.get() for v in self.plot_option_vars):
            # Select all
            for v in self.plot_option_vars:
                v.set(True)
            self.select_all_button.config(text="Deselect All")
        else:
            # Deselect all
            for v in self.plot_option_vars:
                v.set(False)
            self.select_all_button.config(text="Select All")


    def create_entry(self, default_text=""):
        entry = tk.Entry(self.root)
        entry.insert(0, default_text)
        entry.pack()
        return entry


    def create_label_entry(self, label, default_text=""):
        tk.Label(self.root, text=label).pack()
        entry = self.create_entry(default_text)
        return entry


    def create_button(self, text, command):
        button = tk.Button(self.root, text=text, command=command)
        button.pack()


    def generate_geometry_positions(self):
        """
        Create sphere positions from selected geometry + separation + radius,
        and write them into the positions box with aligned columns:
        x, y, z, r, (Re, Im)
        XZ plane layout:
        - Z = North–South
        - X = East–West
        - Y = 0 always

        Center-to-center spacing is computed per-pair as r_i + r_j + s,
        so the surface gap between adjacent spheres is always exactly s.
        For square geometries with unequal radii a symmetric mean is used.
        """
        geo = (self.geometry_var.get() or "").strip()
        s_txt = (self.separation_entry.get() or "").strip()

        if geo == "(none)":
            return

        # How many radii does this geometry need?
        geo_n = {
            "2 in line (NS)": 2, "2 in line (EW)": 2,
            "4 in line (North–South)": 4, "4 in line (East–West)": 4,
            "4 in a square": 4, "4 in a square (45°)": 4,
        }
        n_needed = geo_n.get(geo, 0)
        if n_needed == 0:
            messagebox.showwarning("Unknown geometry",
                                   f"Geometry not handled: {geo}")
            return

        # ---- Validate radii ----
        radii_str = self.get_sphere_radii(n_needed)
        if not radii_str or not radii_str[0]:
            messagebox.showwarning("Missing radius",
                                   "Please enter a Sphere Radius first.")
            return
        try:
            R = [float(t) for t in radii_str]
        except ValueError as exc:
            messagebox.showerror("Invalid radius", str(exc))
            return

        # ---- Validate separation ----
        if not s_txt:
            messagebox.showwarning("Missing separation",
                                   "Please enter Separation (μm).")
            return
        try:
            s = float(s_txt)
        except ValueError:
            messagebox.showerror("Invalid separation",
                                 f"Not a number: {s_txt}")
            return

        # ---- Compute centers using per-sphere radii ----
        centers = []

        if geo in ("2 in line (NS)", "2 in line (EW)"):
            r1, r2 = R[0], R[1]
            d = r1 + r2 + s          # exact center-to-center distance
            if geo.endswith("(NS)"):
                centers = [(0.0, 0.0, -d / 2), (0.0, 0.0, d / 2)]
            else:
                centers = [(-d / 2, 0.0, 0.0), (d / 2, 0.0, 0.0)]

        elif geo in ("4 in line (North–South)", "4 in line (East–West)"):
            r1, r2, r3, r4 = R
            d12 = r1 + r2 + s
            d23 = r2 + r3 + s
            d34 = r3 + r4 + s
            total = d12 + d23 + d34
            # Centered: sphere 1 at -total/2, each next displaced by its gap
            p1 = -total / 2
            p2 = p1 + d12
            p3 = p2 + d23
            p4 = p3 + d34
            if "North–South" in geo:
                centers = [(0.0, 0.0, p) for p in (p1, p2, p3, p4)]
            else:
                centers = [(p, 0.0, 0.0) for p in (p1, p2, p3, p4)]

        elif geo == "4 in a square":
            r = R[0]   # squares always used with equal spheres
            d = 2.0 * r + s
            a = d / 2.0
            centers = [(-a, 0.0, -a), (a, 0.0, -a), (-a, 0.0, a), (a, 0.0, a)]

        elif geo == "4 in a square (45°)":
            r = R[0]   # squares always used with equal spheres
            d = 2.0 * r + s
            a = d / (2 ** 0.5)
            centers = [(-a, 0.0, 0.0), (a, 0.0, 0.0),
                       (0.0, 0.0, -a), (0.0, 0.0, a)]
            centers = [(-a, 0.0, 0.0), (a, 0.0, 0.0),
                       (0.0, 0.0, -a), (0.0, 0.0, a)]

        # ---- Build rows [x, y, z, r_i] ----
        rows = []
        for i, (x, _y, z) in enumerate(centers):
            r_i = radii_str[i] if i < len(radii_str) else radii_str[-1]
            rows.append([f"{x}", "0", f"{z}", r_i])

        # ---- Alignment (sign-slot method) ----
        def mag_only(t: str) -> str:
            t = t.strip()
            return t[1:] if t.startswith(("+", "-")) else t

        col_mag_w = [0, 0, 0, 0]
        for fields in rows:
            for i, val in enumerate(fields):
                col_mag_w[i] = max(col_mag_w[i], len(mag_only(val)))

        rendered_lines = []
        for fields in rows:
            pieces = []
            for i, val in enumerate(fields):
                v = val.strip()
                sign_char = "-" if v.startswith("-") else " "
                mag = mag_only(v)
                pad = " " * (col_mag_w[i] - len(mag))
                pieces.append(sign_char + mag + pad)
            numeric = pieces[0]
            for f in pieces[1:]:
                numeric += "," + f
            rendered_lines.append(numeric + ", ( , )")

        self.position_entry.delete("1.0", "end")
        self.position_entry.insert("1.0", "\n".join(rendered_lines))


    def compute_geometry_points(self):
        """
        Pure function: returns a list of (x,y,z) *strings* derived from
        current Geometry selector + Separation + Radius.
        If geometry is '(none)' or inputs invalid → returns [].
        Coordinates lie in the XZ plane (y=0).
        Line geometries use per-sphere radii (r_i + r_j + s per pair).
        Square geometries use the single/first radius (equal spheres assumed).
        """
        geo = (self.geometry_var.get() or "").strip()
        if geo == "(none)":
            return []

        s_txt = (self.separation_entry.get() or "").strip()
        try:
            s = float(s_txt) if s_txt else 0.0
        except ValueError:
            return []

        centers = []

        if geo in ("2 in line (NS)", "2 in line (EW)"):
            radii = self.get_sphere_radii(2)
            try:
                r1, r2 = float(radii[0]), float(radii[1])
            except (ValueError, IndexError):
                return []
            d = r1 + r2 + s
            if geo.endswith("(NS)"):
                centers = [(0.0, 0.0, -d / 2), (0.0, 0.0, d / 2)]
            else:
                centers = [(-d / 2, 0.0, 0.0), (d / 2, 0.0, 0.0)]

        elif geo in ("4 in line (North–South)", "4 in line (East–West)"):
            radii = self.get_sphere_radii(4)
            try:
                r1, r2, r3, r4 = [float(x) for x in radii[:4]]
            except (ValueError, IndexError):
                return []
            d12 = r1 + r2 + s
            d23 = r2 + r3 + s
            d34 = r3 + r4 + s
            total = d12 + d23 + d34
            p1 = -total / 2
            p2 = p1 + d12
            p3 = p2 + d23
            p4 = p3 + d34
            if "North–South" in geo:
                centers = [(0.0, 0.0, p) for p in (p1, p2, p3, p4)]
            else:
                centers = [(p, 0.0, 0.0) for p in (p1, p2, p3, p4)]

        else:
            # Square geometries — single radius (equal spheres)
            r_txt = (self.radius_entry.get() or "").strip()
            try:
                r = float(r_txt)
            except ValueError:
                return []
            d = 2.0 * r + s
            if geo == "4 in a square":
                a = d / 2.0
                centers = [(-a, 0.0, -a), (a, 0.0, -a), (-a, 0.0, a), (a, 0.0, a)]
            elif geo == "4 in a square (45°)":
                a = d / (2 ** 0.5)
                centers = [(-a, 0.0, 0.0), (a, 0.0, 0.0),
                           (0.0, 0.0, -a), (0.0, 0.0, a)]

        return [(f"{x}", "0", f"{z}") for (x, _y, z) in centers]

    def format_fortran_number(self, s):
        s = s.strip()
        if not s:
            return s
        # normalize any D/E exponent to lowercase d
        s = s.replace("D", "d").replace("E", "d")

        if "d" in s:
            return s
        return s + "d0"


    def apply_general_to_positions(self):
        params, geom = self.get_computed_params_and_geometry()
        if not params:
            messagebox.showerror(
                "Missing data", "Please click 'Compute Parameters' first.")
            return

        r_str = params.get("Input radius", "")
        length_scale = params.get("Length scale factor", "")
        refr_index = params.get("Refractive index", "")

        if not (r_str and refr_index):
            messagebox.showerror(
                "Incomplete data", "Computed parameters must include radius and refractive index.")
            return

        # Update length scale factor entry
        if length_scale:
            self.length_scale_entry.delete(0, "end")
            self.length_scale_entry.insert(0, length_scale)

        fmt = self.format_fortran_number

        # === Geometry present ===
        if geom:
            n_spheres = len(geom)
            sphere_radii = self.get_sphere_radii(n_spheres)
            lines = []
            for i, (x, y, z) in enumerate(geom):
                r_i = sphere_radii[i] if i < len(sphere_radii) else sphere_radii[-1]
                xs, ys, zs, rs = fmt(x), fmt(y), fmt(z), fmt(r_i)
                line = f"{xs}, {ys}, {zs}, {rs}, {refr_index}"
                line = ", ".join(part.strip() for part in line.split(","))
                line = line.replace(", -", ",-")
                lines.append(line)

            self.position_entry.delete("1.0", "end")
            self.position_entry.insert("1.0", "\n".join(lines))

            try:
                self.num_spheres_entry.delete(0, "end")
                self.num_spheres_entry.insert(0, str(n_spheres))
            except Exception:
                pass
            return

        # === Fallback: rewrite existing positions ===
        raw = self.position_entry.get("1.0", "end-1c").strip()
        if not raw:
            # Single sphere at origin — use first radius
            r_first = self.get_sphere_radii(1)[0] or r_str
            line = f"0.d0, 0.d0, 0.d0, {fmt(r_first)}, {refr_index}"
            line = ", ".join(part.strip() for part in line.split(","))
            line = line.replace(", -", ",-")
            self.position_entry.delete("1.0", "end")
            self.position_entry.insert("1.0", line)
            self.num_spheres_entry.delete(0, "end")
            self.num_spheres_entry.insert(0, "1")
            return

        new_lines = []
        count = 0
        for line in raw.splitlines():
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 3:
                new_lines.append(line)
                continue
            x, y, z = parts[:3]
            # Per-sphere radius: use individual entry at index `count`, else last
            sphere_radii = self.get_sphere_radii()
            if sphere_radii:
                r_i = sphere_radii[count] if count < len(sphere_radii) else sphere_radii[-1]
            else:
                r_i = r_str
            xs, ys, zs, rs = fmt(x), fmt(y), fmt(z), fmt(r_i)
            formatted = f"{xs}, {ys}, {zs}, {rs}, {refr_index}"
            formatted = ", ".join(part.strip() for part in formatted.split(","))
            formatted = formatted.replace(", -", ",-")
            new_lines.append(formatted)
            count += 1

        self.position_entry.delete("1.0", "end")
        self.position_entry.insert("1.0", "\n".join(new_lines))
        if count:
            self.num_spheres_entry.delete(0, "end")
            self.num_spheres_entry.insert(0, str(count))


    def on_positions_modified(self, event=None):
        # Tk Text sets a modified-flag; we must clear it to receive the next event.
        try:
            self.position_entry.edit_modified(False)
        except Exception:
            pass
        self.redraw_sphere_preview()


    def _to_float(self, s: str) -> float:
        """Robust float: accepts Fortran 'd'/'D' exponents as well as normal floats."""
        return float((s or "").strip().replace("D", "e").replace("d", "e"))


    def _parse_positions(self):
        """
        Read the positions Text widget and yield tuples (x,z,r).
        We ignore y for the 2D XZ preview. Lines may include refractive index.
        Format expected per line: x, y, z, r, [n...]
        """
        lines = self.position_entry.get("1.0", "end-1c").splitlines()
        parsed = []
        for ln in lines:
            if not ln.strip():
                continue
            parts = [p.strip() for p in ln.split(",")]
            if len(parts) < 4:
                continue
            try:
                x = self._to_float(parts[0])
                # y = self._to_float(parts[1])   # ignored in 2D preview
                z = self._to_float(parts[2])
                r = self._to_float(parts[3])
                if r <= 0:   # skip non-physical radii
                    continue
                parsed.append((x, z, r))
            except Exception:
                # If a line has strings we can't parse, just skip that line.
                continue
        return parsed


    # def save_canvas_as_png(self, filename="sphere_preview.png"):
    #     """
    #     Save the current contents of the Tkinter canvas as a PNG image.
    #     Requires Pillow (PIL) to be installed.
    #     """
    #     import PIL.ImageGrab
    #     import time

    #     directory = self.folder_location_entry.get()
    #     final = os.path.join(directory, filename)


    #     cv = getattr(self, "sphere_canvas", None)
    #     if not cv:
    #         print("No canvas found to save.")
    #         return

    #      # Force Tkinter to update geometry before measuring
    #     cv.update_idletasks()
    #     time.sleep(0.05)  # short delay helps ensure proper layout on Windows

    #     # Get absolute coordinates of the canvas on the screen
    # # Get canvas absolute screen coordinates
    #     x0 = cv.winfo_rootx()
    #     y0 = cv.winfo_rooty()
    #     x1 = x0 + cv.winfo_width()
    #     y1 = y0 + cv.winfo_height()

    #     border = int(cv.cget("bd")) + int(cv.cget("highlightthickness"))
    #     x0 += border
    #     y0 += border
    #     x1 -= border
    #     y1 -= border

    #     # Capture *exactly* that region
    #     bbox = (x0, y0, x1, y1)
    #     img = PIL.ImageGrab.grab(bbox)
    #     img.save(final)
    #     print(f"Canvas saved as {final}")


    def redraw_sphere_preview(self):
        """
        Draw simple 2D circles in the XZ plane that fit inside the canvas.
        Handles empty/invalid input gracefully.
        """
        cv = getattr(self, "sphere_canvas", None)
        if not cv:
            return

        cv.delete("all")

        spheres = self._parse_positions()  # list of (x,z,r)
        w = int(cv.cget("width"))
        h = int(cv.cget("height"))

        # Draw axes (optional): X horizontal, Z vertical through canvas center
        cx, cz = w // 2, h // 2
        cv.create_line(0, cz, w, cz, dash=(2, 2))
        cv.create_line(cx, 0, cx, h, dash=(2, 2))

        if not spheres:
            # No valid spheres → draw a placeholder
            cv.create_text(cx, cz, text="No valid spheres", anchor="c")
            return

        # Compute world bounds from sphere extents
        xs = []
        zs = []
        for (x, z, r) in spheres:
            xs.extend([x - r, x + r])
            zs.extend([z - r, z + r])

        xmin, xmax = min(xs), max(xs)
        zmin, zmax = min(zs), max(zs)

        # Add a small margin
        dx = xmax - xmin
        dz = zmax - zmin
        if dx == 0 and dz == 0:
            dx = dz = 1.0  # avoid zero-size bbox

        margin = 0.05 * max(dx, dz)
        xmin -= margin
        xmax += margin
        zmin -= margin
        zmax += margin

        # Fit world bounds into canvas, keep aspect ratio (y axis downwards on canvas)
        world_w = xmax - xmin
        world_h = zmax - zmin
        world_w = xmax - xmin


        world_h = zmax - zmin
        scale = min((w - 10) / world_w, (h - 10) / world_h)  # 5 px base padding

        # Compute actual drawn size and center offsets
        draw_w = world_w * scale
        draw_h = world_h * scale
        x_offset = (w - draw_w) / 2.0
        y_offset = (h - draw_h) / 2.0


        def world_to_canvas(x, z):
            # Center the content; flip Z so positive is up
            X = x_offset + (x - xmin) * scale
            Z = h - y_offset - (z - zmin) * scale
            return X, Z

        # Draw spheres
        for (x, z, r) in spheres:
            Xc, Zc = world_to_canvas(x, z)
            R = r * scale
            cv.create_oval(Xc - R, Zc - R, Xc + R, Zc + R, outline="black")

        # Optional: draw a neat border
        cv.create_rectangle(1, 1, w - 2, h - 2)


    def _iter_wavelengths(self):
        """
        Return a list of wavelengths (floats) for the sweep (inclusive).
        Uses min/max and number of steps. If invalid, returns [].
        """
        try:
            wl_min = float(self.min_wavelength_entry.get())
            wl_max = float(self.max_wavelength_entry.get())
            nsteps = int(self.step_wavelength_entry.get())
            if nsteps < 2 or wl_max <= wl_min:
                return []
            step = (wl_max - wl_min) / (nsteps - 1)
            return [wl_min + i * step for i in range(nsteps)]
        except Exception:
            return []


    def _iter_radii(self):
        """Return list of radii (μm) for the radius sweep (inclusive)."""
        try:
            r_min = float(self.min_radius_entry.get())
            r_max = float(self.max_radius_entry.get())
            nsteps = int(self.step_radius_entry.get())
            if nsteps < 2 or r_max <= r_min:
                return []
            step = (r_max - r_min) / (nsteps - 1)
            return [r_min + i * step for i in range(nsteps)]
        except Exception:
            return []


    def _centers_for_geometry(self, r_um: float, sep_um: float):
        """
        Compute sphere centers (x,y,z) for the selected geometry, using
        center-to-center spacing d = 2*r + separation. y=0 for all.
        Returns list of (x,y,z) floats, or [] if geometry is '(none)'.
        """
        geo = (self.geometry_var.get() or "").strip()
        if geo == "(none)":
            return []

        d = 2.0 * r_um + sep_um
        centers = []

        if geo in ("2 in line (NS)", "2 in line (EW)"):
            if geo.endswith("(NS)"):
                centers = [(0.0, 0.0, -d/2), (0.0, 0.0, d/2)]
            else:
                centers = [(-d/2, 0.0, 0.0), (d/2, 0.0, 0.0)]

        elif geo in ("4 in line (North–South)", "4 in line (East–West)"):
            offsets = [-1.5*d, -0.5*d, 0.5*d, 1.5*d]
            if "North–South" in geo:
                centers = [(0.0, 0.0, z) for z in offsets]
            else:
                centers = [(x, 0.0, 0.0) for x in offsets]

        elif geo == "4 in a square":
            a = d / 2.0
            centers = [(-a, 0.0, -a), (a, 0.0, -a), (-a, 0.0, a), (a, 0.0, a)]

        elif geo == "4 in a square (45°)":
            a = d / (2**0.5)
            centers = [(-a, 0.0, 0.0), (a, 0.0, 0.0), (0.0, 0.0, -a), (0.0, 0.0, a)]

        return centers

    def _min_pair_distance(self, centers):
        """Return the minimum pairwise center distance among (x,y,z) centers."""
        if len(centers) < 2:
            return float("inf")
        import math
        m = float("inf")
        for i in range(len(centers)):
            xi, yi, zi = centers[i]
            for j in range(i+1, len(centers)):
                xj, yj, zj = centers[j]
                d = math.sqrt((xi-xj)**2 + (yi-yj)**2 + (zi-zj)**2)
                if d < m:
                    m = d
        return m


    def _parse_positions_as_xyzr(self):
        """
        Parse the text box lines and extract only x,y,z,r (ignore any existing n).
        Returns a list of 4-tuples of strings (x,y,z,r) as written.
        """
        xyzr = []
        for raw in self.config.data.get("positions", []):
            line = raw.split("#")[0].strip()
            if not line:
                continue
            # remove any parentheses in case "(Re,Im)" is present
            parts = [p.strip() for p in line.replace("(", "").replace(")", "").split(",")]
            if len(parts) < 4:
                continue
            x, y, z, r = parts[:4]
            xyzr.append((x, y, z, r))
        return xyzr


    def create_new_simulation_folder(self):
        """Create a new folder for this simulation run, exactly where the user specifies."""
        folder_input = self.folder_location_entry.get().strip()

        if not folder_input:
            messagebox.showwarning(
                "Missing path", "Please enter a folder path in 'Folder Location' before creating.")
            return

        # Use the full path directly
        new_folder = os.path.abspath(folder_input)

        # Ensure unique folder name if it already exists
        if os.path.exists(new_folder):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            new_folder = f"{new_folder}_{timestamp}"

        try:
            os.makedirs(new_folder, exist_ok=True)
            os.makedirs(os.path.join(new_folder, "plots"), exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create folder: {e}")
            return

        # Update config with new folder
        self.config.data["folder_location"] = new_folder
        self.folder_location_entry.delete(0, "end")
        self.folder_location_entry.insert(0, new_folder)

        # Use folder name for output and near field
        folder_name = os.path.basename(new_folder)
        output_name = f"{folder_name}.dat"
        nf_name = f"{folder_name}_nf.dat"

        self.config.data["output_file"] = output_name
        self.output_file_entry.delete(0, "end")
        self.output_file_entry.insert(0, output_name)

        self.config.data["near_field_file"] = nf_name
        self.near_field_file_entry.delete(0, "end")
        self.near_field_file_entry.insert(0, nf_name)

        self.config.data["separation"] = self.separation_entry.get().strip()
        self.config.data["geometry"] = self.geometry_var.get().strip()

        # Save config inside the new folder
        config_file = os.path.join(new_folder, "config.json")
        self.config.save_to_json(config_file)

        messagebox.showinfo(
            "New Simulation Folder",
            f"Created:\n{new_folder}\n\n"
            f"Output file set to {output_name}\n"
            f"Near-field file set to {nf_name}\n"
            f"Config saved as config.json"
        )


    def load_simulation_folder(self):
        """Load a previous simulation folder (and its config.json)."""
        current = self.folder_location_entry.get().strip()

        if current and os.path.exists(current):
            base_dir = os.path.dirname(current)
        else:
            base_dir = DEFAULT_FOLDER_LOCATION

        folder_selected = filedialog.askdirectory(
            title="Select Simulation Folder",
            initialdir=base_dir
        )
        if not folder_selected:
            return  # user cancelled

        config_file = os.path.join(folder_selected, "config.json")
        if not os.path.exists(config_file):
            messagebox.showwarning("Missing config.json",
                                f"No config.json found in {folder_selected}")
            return

        # Load config.json into memory
        if not self.config.load_from_json(config_file):
            messagebox.showerror("Error", "Failed to load config.json")
            return

        # Reuse existing logic
        self.load_previous_data(from_external_config=True)

        messagebox.showinfo("Loaded", f"Simulation loaded from:\n{folder_selected}")


    def open_simulation_folder(self):
        """Open windows explorer with the current folder"""
            # Open the current folder in the system file explorer
        folder_input = self.folder_location_entry.get().strip()
        if not folder_input:
            messagebox.showwarning(
                "Missing path", "Please enter a folder path in 'Folder Location' before opening.")
            return

        path_to_open = os.path.abspath(folder_input)
        if not os.path.exists(path_to_open):
            messagebox.showerror("Error", f"Path does not exist: {path_to_open}")
            return

        try:
            if os.name == 'nt':  # Windows
                os.startfile(path_to_open)
            elif os.name == 'posix':
                import subprocess
                subprocess.run(['xdg-open', path_to_open])
            else:
                messagebox.showerror("Unsupported OS", "Cannot open folder on this operating system.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")

    def load_previous_data(self, from_external_config=False):
        """
        Load simulation data either from last_config.json or from
        an already-loaded external config (via load_simulation_folder()).
        """
        if not from_external_config:
            config_file = os.path.join(current_dir, "last_config.json")
            if not self.config.load_from_json(config_file):
                return  # no saved config yet

        data = self.config.data

        # --- Restore main entries ---
        self.folder_location_entry.delete(0, "end")
        self.folder_location_entry.insert(0, data["folder_location"])

        self.output_file_entry.delete(0, "end")
        self.output_file_entry.insert(0, data["output_file"])

        self.num_spheres_entry.delete(0, "end")
        self.num_spheres_entry.insert(0, data["num_spheres"])

        self.position_entry.delete("1.0", "end")
        self.position_entry.insert("1.0", "\n".join(data["positions"]))

        self.incident_beta_entry.delete(0, "end")
        self.incident_beta_entry.insert(0, data["incident_beta"])

        self.incident_alpha_entry.delete(0, "end")
        self.incident_alpha_entry.insert(0, data["incident_alpha"])

        self.scattering_angle_entry.delete(0, "end")
        self.scattering_angle_entry.insert(0, data["scattering_angle"])

        self.length_scale_entry.delete(0, "end")
        self.length_scale_entry.insert(0, data["length_scale"])

        self.beam_type_var.set("Gaussian" if data["is_gaussian_beam"] else "Plane Wave")
        self.gaussian_constant_entry.delete(0, "end")
        self.gaussian_constant_entry.insert(0, data["gaussian_beam_constant"])

        self.near_field_var.set(data["near_field"])
        self.near_field_file_entry.delete(0, "end")
        self.near_field_file_entry.insert(0, data["near_field_file"])

        self.near_field_stepsize_auto_var.set(data.get("near_field_stepsize_auto", True))

        self.near_field_stepsize_entry.config(state="normal")
        self.near_field_stepsize_entry.delete(0, "end")
        self.near_field_stepsize_entry.insert(0, data.get("near_field_stepsize", ""))
        self.toggle_near_field_stepsize_mode()


        # --- Restore plotting settings ---
        self.plot_type_var.set(data.get("plot_type", "Poynting"))
        self.update_plot_options()
        for var, label in zip(self.plot_option_vars, self.plot_option_labels):
            var.set(label in data.get("plot_options", []))

        self.wavelength_entry.delete(0, "end")
        self.wavelength_entry.insert(0, data.get("wavelength", ""))

        self.radius_entry.delete(0, "end")
        self.radius_entry.insert(0, data.get("sphere_radius", ""))

        # Restore radius mode (equal / individual)
        radii_equal = data.get("radii_equal", True)
        self.radii_equal_var.set(radii_equal)
        # Rebuild UI first so the right widgets exist
        self._rebuild_radius_ui(preserve_values=False)
        if radii_equal:
            self.radius_entry.delete(0, "end")
            self.radius_entry.insert(0, data.get("sphere_radius", ""))
        else:
            saved_radii = data.get("sphere_radii_individual", [])
            for i, e in enumerate(self.individual_radius_entries):
                val = saved_radii[i] if i < len(saved_radii) else ""
                e.delete(0, "end")
                e.insert(0, val)

        self.material_var.set(data.get("material", "Custom"))

        self.custom_n_entry.delete(0, "end")
        self.custom_n_entry.insert(0, data.get("custom_n", ""))

        self.custom_k_entry.delete(0, "end")
        self.custom_k_entry.insert(0, data.get("custom_k", ""))

        self.separation_entry.delete(0, "end")
        self.separation_entry.insert(0, data.get("separation", ""))

        self.geometry_var.set(data.get("geometry", "(none)"))
        try:
            self.geometry_combo.set(self.geometry_var.get())
        except Exception:
            pass

        # --- Wavelength sweep ---
        wl = data.get("wavelength_sweep", {})
        self.sweep_var.set(wl.get("enabled", False))
        self.min_wavelength_entry.delete(0, "end")
        self.min_wavelength_entry.insert(0, wl.get("min", ""))
        self.max_wavelength_entry.delete(0, "end")
        self.max_wavelength_entry.insert(0, wl.get("max", ""))
        self.step_wavelength_entry.delete(0, "end")
        self.step_wavelength_entry.insert(0, wl.get("n", ""))

        # --- Radius sweep ---
        rs = data.get("radius_sweep", {})
        self.sweep_radius_var.set(rs.get("enabled", False))
        self.min_radius_entry.delete(0, "end")
        self.min_radius_entry.insert(0, rs.get("min", ""))
        self.max_radius_entry.delete(0, "end")
        self.max_radius_entry.insert(0, rs.get("max", ""))
        self.step_radius_entry.delete(0, "end")
        self.step_radius_entry.insert(0, rs.get("n", ""))

        if not from_external_config:
            self.load_write_status_label.config(text="Loading completed")


    def compute_near_field_step(self, coords, length_scale, side_scaled,
                                ppw=50,
                                nrad=25,
                                ngap=12,
                                max_points=2_000_000,
                                step_min=0.002,
                                step_max=0.15):
        """
        coords: lista de (x,y,z,r) en unidades físicas
        length_scale: k0 = 2π/λ
        side_scaled: lado del plano en unidades escaladas (k0·L)
        """

        if not coords:
            return 0.02

        # ---- Convertir a array ----
        arr = np.array(coords, dtype=float)

        # Escalar a coordenadas adimensionales k0·L
        arr[:, :4] *= length_scale

        xyz = arr[:, :3]
        r = arr[:, 3]

        rmin = np.min(r)

        # 1) criterio por longitud de onda (en k0·L, λ = 2π) points per wavelength
        step_wave = (2.0 * np.pi) / ppw

        # 2) criterio geométrico (radio mínimo)
        step_rad = rmin / nrad if rmin > 0 else step_wave

        # 3) criterio por gap mínimo
        n = len(arr)
        if n > 1:
            # Distancias centro-centro vectorizadas
            diff = xyz[:, None, :] - xyz[None, :, :]
            dist = np.linalg.norm(diff, axis=2)

            # Matriz de suma de radios
            rsum = r[:, None] + r[None, :]

            gap = dist - rsum

            # Ignorar diagonal y solapamientos (gap <= 0)
            mask = np.triu(np.ones_like(gap, dtype=bool), k=1)
            valid_gaps = gap[mask]
            valid_gaps = valid_gaps[valid_gaps > 0]

            if valid_gaps.size > 0:
                gap_min = np.min(valid_gaps)
                step_gap = gap_min / ngap
            else:
                step_gap = np.inf
        else:
            step_gap = np.inf

        # Paso candidato
        step = min(step_wave, step_rad, step_gap)
        step = max(step_min, min(step, step_max))

        # 4) limitar número total de puntos
        if side_scaled > 0:
            est_points = (side_scaled / step) ** 2
            if est_points > max_points:
                step = side_scaled / np.sqrt(max_points)
        # step = 0.01
        self.near_field_step = step

        entry_was_disabled = str(self.near_field_stepsize_entry.cget("state")) == "disabled"
        if entry_was_disabled:
            self.near_field_stepsize_entry.config(state="normal")

        self.near_field_stepsize_entry.delete(0, "end")
        self.near_field_stepsize_entry.insert(0, f"{step:.6f}d0")

        if entry_was_disabled:
            self.near_field_stepsize_entry.config(state="disabled")

        self.near_field_stepsize_label.config(text=f"Calculated: {step:.4f}")
        return float(step)


    def write_input_file(self):
        """Write simulation input parameters to mstm.inp (no backup)."""
        # Collect all data from entries and save to Config
        self.config.data["folder_location"] = self.folder_location_entry.get() or DEFAULT_FOLDER_LOCATION
        self.config.data["output_file"] = self.output_file_entry.get()
        self.config.data["num_spheres"] = self.num_spheres_entry.get()
        # Keep positions exactly as written by the user/app (no reformatting here)
        self.config.data["positions"] = [
            ln.strip()
            for ln in self.position_entry.get("1.0", "end-1c").splitlines()
            if ln.strip()
        ]
        self.config.data["incident_beta"] = self.incident_beta_entry.get()
        self.config.data["incident_alpha"] = self.incident_alpha_entry.get()
        self.config.data["scattering_angle"] = self.scattering_angle_entry.get()
        self.config.data["length_scale"] = self.length_scale_entry.get()
        self.config.data["gaussian_beam_constant"] = (
            self.gaussian_constant_entry.get() if self.beam_type_var.get() == "Gaussian" else False
        )
        self.config.data["near_field"] = self.near_field_var.get()
        self.config.data["near_field_file"] = (
            self.near_field_file_entry.get() if self.config.data["near_field"] else "f"
        )
        self.config.data["near_field_stepsize"] = self.near_field_stepsize_entry.get(
        ).strip()
        self.config.data["near_field_stepsize_auto"] = self.near_field_stepsize_auto_var.get()


        self.config.data["plot_type"] = self.plot_type_var.get()
        self.config.data["plot_options"] = [
            label for var, label in zip(self.plot_option_vars, self.plot_option_labels) if var.get()
        ]
        self.config.data["wavelength"] = self.wavelength_entry.get()
        self.config.data["sphere_radius"] = self.radius_entry.get()
        self.config.data["radii_equal"] = self.radii_equal_var.get()
        self.config.data["sphere_radii_individual"] = [
            e.get().strip() for e in self.individual_radius_entries
        ]
        self.config.data["material"] = self.material_var.get()
        self.config.data["custom_n"] = self.custom_n_entry.get().strip()
        self.config.data["custom_k"] = self.custom_k_entry.get().strip()
        self.config.data["separation"] = self.separation_entry.get().strip()
        self.config.data["geometry"] = self.geometry_var.get().strip()

        self.config.data["wavelength_sweep"] = {
            "enabled": self.sweep_var.get(),
            "min": self.min_wavelength_entry.get().strip(),
            "max": self.max_wavelength_entry.get().strip(),
            "n": self.step_wavelength_entry.get().strip()
        }

        self.config.data["radius_sweep"] = {
            "enabled": self.sweep_radius_var.get(),
            "min": self.min_radius_entry.get().strip(),
            "max": self.max_radius_entry.get().strip(),
            "n": self.step_radius_entry.get().strip()
        }

        folder_input_file = os.path.join(self.config.data["folder_location"], "mstm.inp")

        # Local helper: robust float for Fortran-style numbers (d/D → e)
        def to_float(s: str) -> float:
            return float((s or "").strip().replace("D", "e").replace("d", "e"))

        try:
            with open(folder_input_file, "w") as f:
                # Headers
                f.write("! mstm input file\n")

                # Folder location (comment)
                f.write("! folder_location\n")
                f.write(f'! {self.config.data["folder_location"]}\n')

                # Output file
                f.write("output_file\n")
                f.write(f'{self.config.data["output_file"]}\n')

                # Number of spheres
                f.write("number_spheres\n")
                f.write(f'{self.config.data["num_spheres"]}\n')


                # Sphere data (base block)
                if self.sweep_var.get():
                    print("Writing sweep sphere data")
                    # Use first wavelength as the main run
                    material = (self.material_var.get() or "Custom").strip()
                    print("Material for sweep:", material)
                    wl_list = self._iter_wavelengths()
                    xyzr_list = self._parse_positions_as_xyzr()

                    r_text_global = self.radius_entry.get().strip()
                    r_ref_um = float(r_text_global)

                    wl_first = wl_list[0]
                    if material and material != "Custom":
                        res = mstm.compute_parameters(r_ref_um, wl_first, material=material)
                    else:
                        n_real = float(self.custom_n_entry.get().strip())
                        n_imag = float(self.custom_k_entry.get().strip())
                        res = mstm.compute_parameters(
                        r_ref_um, wl_first, n_real=n_real, n_imag=n_imag)


                    ls = res["length_scale_factor"]
                    n = res["refractive_index"]
                    n_re, n_im = n.real, n.imag

                    f.write("sphere_data\n")
                    for (x, y, z, r_line) in xyzr_list:
                        f.write(f"{x},{y},{z},{r_line},({n_re:.10f}d0,{n_im:.10f}d0)\n")
                    f.write("end_of_sphere_data\n")
                    f.write("length_scale_factor\n")
                    f.write(f"{ls:.10f}d0\n")

                elif self.sweep_radius_var.get():
                    # ---- Radius sweep a λ fija ----
                    wl_rs       = float(self.wavelength_entry.get().strip())
                    material_rs = (self.material_var.get() or "Custom").strip()
                    radii_um    = self._iter_radii()
                    sep_txt_rs  = self.separation_entry.get().strip()
                    sep_um_rs   = float(sep_txt_rs) if sep_txt_rs else 0.0

                    if not radii_um:
                        raise ValueError(
                            "Radius sweep: define al menos 2 pasos con min < max.")

                    # λ fija → length_scale_factor y n son constantes para todos los runs.
                    # Se calcula una sola vez con el primer radio (r no afecta a ls ni a n).
                    if material_rs != "Custom":
                        res_rs = mstm.compute_parameters(
                            radii_um[0], wl_rs, material=material_rs)
                    else:
                        n_real_rs = float(self.custom_n_entry.get().strip())
                        n_imag_rs = float(self.custom_k_entry.get().strip())
                        res_rs = mstm.compute_parameters(
                            radii_um[0], wl_rs,
                            n_real=n_real_rs, n_imag=n_imag_rs)

                    ls_rs    = res_rs["length_scale_factor"]   # constante para todos los pasos
                    n_cx_rs  = res_rs["refractive_index"]      # constante para todos los pasos
                    n_re_rs  = n_cx_rs.real
                    n_im_rs  = n_cx_rs.imag

                    # Helper reutilizable: escribe sphere_data … end_of_sphere_data
                    # + length_scale_factor para un radio dado.
                    def _write_radius_block(fh, r_um):
                        centers = self._centers_for_geometry(r_um, sep_um_rs)
                        fh.write("sphere_data\n")
                        if centers:
                            # Geometría parametrizada: d = 2·r + sep se recalcula en cada paso
                            for (cx, cy, cz) in centers:
                                fh.write(
                                    f"{cx:.10f}d0,{cy:.10f}d0,{cz:.10f}d0,"
                                    f"{r_um:.10f}d0,"
                                    f"({n_re_rs:.10f}d0,{n_im_rs:.10f}d0)\n"
                                )
                        else:
                            # Sin geometría: reutilizar x,y,z del cuadro de posiciones,
                            # solo se sustituye el radio.
                            for (px, py, pz, _pr) in self._parse_positions_as_xyzr():
                                fh.write(
                                    f"{px},{py},{pz},"
                                    f"{r_um:.10f}d0,"
                                    f"({n_re_rs:.10f}d0,{n_im_rs:.10f}d0)\n"
                                )
                        fh.write("end_of_sphere_data\n")
                        fh.write("length_scale_factor\n")
                        fh.write(f"{ls_rs:.10f}d0\n")

                    # Primer run (bloque principal, sin new_run)
                    _write_radius_block(f, radii_um[0])


                else:
                    # Single run (no sweep)
                    print("Writing single run sphere data")
                    f.write("sphere_data\n")
                    for pos in self.config.data["positions"]:
                        f.write(f"{pos}\n")
                    f.write("end_of_sphere_data\n")
                    
                    f.write("length_scale_factor\n")
                    f.write(f"{self.config.data['length_scale']}\n")

                # Angles
                f.write("incident_beta_deg\n")
                f.write(f"{self.config.data['incident_beta']}\n")

                f.write("incident_alpha_deg\n")
                f.write(f"{self.config.data['incident_alpha']}\n")


                # Solver epsilon
                f.write("solution_epsilon\n")
                f.write("1.d-8\n")

                # Multipole order
                if int(self.multipole_order.get()):
                    f.write("max_t_matrix_order\n")
                    f.write(f"{self.multipole_order.get()}\n")
                    f.write("t_matrix_convergence_epsilon\n")
                    f.write("1.d-12\n")


                # Gaussian beam (optional)
                if self.beam_type_var.get() == "Gaussian":
                    f.write("gaussian_beam_constant\n")
                    f.write(f"{self.config.data['gaussian_beam_constant']}\n")
                    f.write("gaussian_beam_focal_point\n")
                    f.write("0.d0,0.d0,0.d0\n")

                # Always calculate scattering; near field optional
                f.write("calculate_scattering_matrix\n")
                f.write("t\n") if self.matrix.get() else f.write("f\n")

                f.write("scattering_map_increment\n")
                f.write(f"{self.config.data['scattering_angle']}\n")
                # f.write("calculate_near_field\n")
                # f.write("t\n" if self.config.data["near_field"] else "f\n")

                if self.config.data["near_field"] and not self.sweep_var.get() and not self.sweep_radius_var.get():
                    f.write("calculate_near_field\n")
                    f.write("t\n")

                    # Parse sphere centers/radii ONLY from the first 4 comma-separated values per line.
                    coords = []
                    for pos in self.config.data["positions"]:
                        # We only need x,y,z,r → first 4 CSV items; do NOT touch the refractive index part.
                        parts = [p.strip() for p in pos.split(",")]
                        if len(parts) < 4:
                            continue
                        try:
                            x, y, z, r = to_float(parts[0]), to_float(parts[1]), to_float(parts[2]), to_float(parts[3])
                        except ValueError:
                            continue
                        coords.append((x, y, z, r))

                    # Length scale as float (accepts d0)
                    length_scale = to_float(self.length_scale_entry.get())

                    xs = [x for x, _, _, _ in coords] or [0.0]
                    zs = [z for _, _, z, _ in coords] or [0.0]
                    rs = [r for _, _, _, r in coords] or [0.0]

                    margin = 2.0 * (max(rs) if rs else 0.0)

                    xmin, xmax = min(xs) - max(rs) - margin, max(xs) + max(rs) + margin
                    zmin, zmax = min(zs) - max(rs) - margin, max(zs) + max(rs) + margin

                    # center square box
                    xmid = 0.5 * (xmin + xmax)
                    zmid = 0.5 * (zmin + zmax)

                    side = max(xmax - xmin, zmax - zmin)
                    xmin, xmax = xmid - side / 2.0, xmid + side / 2.0
                    zmin, zmax = zmid - side / 2.0, zmid + side / 2.0

                    # scale into k0·length
                    xmin, xmax = length_scale * xmin, length_scale * xmax
                    zmin, zmax = length_scale * zmin, length_scale * zmax

                    f.write("near_field_minimum_border\n")
                    f.write(f"{xmin:.6f}d0,0.d0,{zmin:.6f}d0\n")

                    f.write("near_field_maximum_border\n")
                    f.write(f"{xmax:.6f}d0,0.d0,{zmax:.6f}d0\n")

                    # porque 'side' aún está en unidades físicas
                    side_scaled = length_scale * side


                    if self.near_field_stepsize_auto_var.get():
                        step = self.compute_near_field_step(
                            coords=coords,
                            length_scale=length_scale,
                            side_scaled=side_scaled,
                            ppw=50,
                            nrad=25,
                            ngap=12,
                            max_points=2_000_000,
                            step_min=0.002,
                            step_max=0.15
                        )
                    else:
                        manual_step_txt = self.near_field_stepsize_entry.get().strip()
                        if not manual_step_txt:
                            raise ValueError("Near-field manual step size is empty.")
                        step = to_float(manual_step_txt)
                        if step <= 0:
                            raise ValueError("Near-field manual step size must be positive.")
                        self.near_field_stepsize_label.config(text=f"Manual: {step:.8f}")


                    f.write("near_field_step_size\n")
                    f.write(f"{step:.6f}d0\n")

                    f.write("near_field_output_file\n")
                    f.write(f"{self.config.data['near_field_file']}\n")

                # ===== Append remaining wavelengths as extra runs (no extra end_of_options here) =====
                if self.sweep_var.get():
                    material = (self.material_var.get() or "Custom").strip()
                    wl_list = self._iter_wavelengths()
                    xyzr_list = self._parse_positions_as_xyzr()

                    r_text_global = self.radius_entry.get().strip()
                    r_ref_um = float(r_text_global)

                    for wl in wl_list[1:]:  # only the remaining wavelengths
                        if material and material != "Custom":
                            res = mstm.compute_parameters(r_ref_um, wl, material=material)
                        else:
                            n_real = float(self.custom_n_entry.get().strip())
                            n_imag = float(self.custom_k_entry.get().strip())
                            res = mstm.compute_parameters(r_ref_um, wl, n_real=n_real, n_imag=n_imag)

                        ls = res["length_scale_factor"]
                        n = res["refractive_index"]
                        n_re, n_im = n.real, n.imag

                        f.write("new_run\n")
                        f.write("sphere_data\n")
                        for (x, y, z, r_line) in xyzr_list:
                            f.write(f"{x},{y},{z},{r_line},({n_re:.10f}d0,{n_im:.10f}d0)\n")
                        f.write("end_of_sphere_data\n")
                        f.write("length_scale_factor\n")
                        f.write(f"{ls:.10f}d0\n")

                if self.sweep_radius_var.get():
                    # Runs adicionales (r[1], r[2], …) como bloques new_run
                    for r_um in radii_um[1:]:
                        f.write("new_run\n")
                        _write_radius_block(f, r_um)

                f.write("end_of_options\n")

            # Save current config to JSONs


            # Save to global and run folder
            config_file = os.path.join(current_dir, "last_config.json")
            self.config.save_to_json(config_file)

            run_config_file = os.path.join(self.config.data["folder_location"], "config.json")
            self.config.save_to_json(run_config_file)

            # self.save_canvas_as_png()
            self.load_write_status_label.config(
                text="Simulation input file written")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to write file: {e}")


    def run_simulation(self):
        """Start simulation with a modal spinner window."""

        self.load_write_status_label.config(text="Simulation input file written")
        self.status_label.config(text="Running simulation...")
        self.write_input_file()

        # --- Modal loading window ---
        self.spinner_win = tk.Toplevel(self.root)
        self.spinner_win.title("Running simulation")
        self.spinner_win.geometry("320x120")
        self.spinner_win.resizable(False, False)
        self.spinner_win.transient(self.root)
        self.spinner_win.grab_set()

        tk.Label(
            self.spinner_win,
            text="Simulation running...\nPlease wait.",
            font=("Arial", 11)
        ).pack(pady=(15, 10))

        self.progress = ttk.Progressbar(
            self.spinner_win,
            mode="indeterminate",
            length=250
        )
        self.progress.pack(pady=5)
        self.progress.start(12)  # smaller = faster animation

        # Optional: disable closing the spinner manually
        self.spinner_win.protocol("WM_DELETE_WINDOW", lambda: None)

        # Center it roughly over root
        self.spinner_win.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - 160
        y = self.root.winfo_rooty() + (self.root.winfo_height() // 2) - 60
        self.spinner_win.geometry(f"+{x}+{y}")

        # Run subprocess in background
        thread = threading.Thread(target=self._simulation_worker, daemon=True)
        thread.start()


    def _simulation_worker(self):
        """Background worker that runs the Fortran executable."""
        try:
            result = sb.run(
                "mstm.exe",
                cwd=self.config.data["folder_location"],
                stdout=sb.PIPE,
                stderr=sb.PIPE,
                text=True
            )
            self.root.after(0, lambda: self._simulation_finished(result))
        except Exception as e:
            self.root.after(0, lambda: self._simulation_failed(e))


    def _simulation_finished(self, result):
        """Called in the Tkinter thread when simulation ends."""
        self.progress.stop()
        self.spinner_win.destroy()

        self.status_label.config(text="Simulation completed")
        self.show_notification("Simulation completed", f"Result: {result.stdout}")


    def _simulation_failed(self, error):
        """Called in the Tkinter thread if simulation fails."""
        self.progress.stop()
        self.spinner_win.destroy()

        self.status_label.config(text="Simulation failed")
        self.show_notification("Simulation failed", str(error))


    def plot_scattering_matrix2(self):
        """Plot scattering matrix using external Python script."""
        python_plot_file = os.path.join(self.config.plot_location, "plot_scattering_matrix.py")
        self.write_input_file()


        scat_mat_file = os.path.join(
            self.config.data["folder_location"], 
            self.config.data["output_file"]
        )

        save_dir = self.config.data["folder_location"]  # <- folder for saving plots
        print("scat_mat_file =", scat_mat_file, " script =", python_plot_file)

        isS11 = self.S11_var.get()
        isDoP = self.dop_var.get()
        isDoLP = self.dolp_var.get()
        isDoCP = self.docp_var.get()

        isQExt = self.Qext_var.get()
        isQSca = self.Qsca_var.get()
        isQAbs = self.Qabs_var.get()
        isUnpolarized = self.unpol_var.get()
        isParallel = self.par_var.get()
        isPerpendicular = self.perp_var.get()

        if isS11 and isDoP and isDoLP and isDoCP:
            sb.Popen(["py", python_plot_file, scat_mat_file, "ALL", save_dir])
        elif isS11:
            sb.Popen(["py", python_plot_file, scat_mat_file, "S11", save_dir])
        elif isDoP:
            sb.Popen(["py", python_plot_file, scat_mat_file, "DoP", save_dir])
        elif isDoLP:
            sb.Popen(["py", python_plot_file, scat_mat_file, "DoLP", save_dir])
        elif isDoCP:
            sb.Popen(["py", python_plot_file, scat_mat_file, "DoCP", save_dir])

        if isQExt and isQSca and isQAbs:
            sb.Popen(["py", python_plot_file, scat_mat_file, "EFF", save_dir])
        elif isQExt:
            sb.Popen(["py", python_plot_file, scat_mat_file, "QExt", save_dir])
        elif isQSca:
            sb.Popen(["py", python_plot_file, scat_mat_file, "QSca", save_dir])
        elif isQAbs:
            sb.Popen(["py", python_plot_file, scat_mat_file, "QAbs", save_dir])
        

    def plot_scattering_matrix(self):
        """Plot scattering matrix and efficiencies using external script."""
        python_plot_file = os.path.join(self.config.plot_location, "plot_scattering_matrix.py")
        self.write_input_file()

        scat_mat_file = os.path.join(
            self.config.data["folder_location"],
            self.config.data["output_file"]
        )
        save_dir = self.config.data["folder_location"]
        print("scat_mat_file =", scat_mat_file, " script =", python_plot_file)

        # --- Collect selected options ---
        scat_selected = [k for k, v in self.scat_option_vars.items() if v.get()]
        pol_selected  = [k for k, v in self.pol_vars.items() if v.get()]
        q_selected    = [k for k, v in self.q_vars.items() if v.get()]
        print("Selected scat options:", scat_selected)
        # --- Scattering matrix plots ---
        if scat_selected:
            # If all are selected → use ALL
            if len(scat_selected) == len(self.scat_option_vars):
                mode = "DASHBOARD"
                sb.Popen(["py", python_plot_file, scat_mat_file, mode, save_dir])
                # mode = "S11"
                # sb.Popen(["py", python_plot_file, scat_mat_file, mode, save_dir])
            elif "DOP" in scat_selected and "DOLP" in scat_selected and "DOCP" in scat_selected:
                mode = "ALL"
                sb.Popen(["py", python_plot_file, scat_mat_file, mode, save_dir])
                for mode in scat_selected:
                    sb.Popen(["py", python_plot_file, scat_mat_file, mode, save_dir])
            else:
                for mode in scat_selected:
                    sb.Popen(["py", python_plot_file, scat_mat_file, mode, save_dir])

        # --- Efficiency plots ---
        if any(q_selected):
            for pol in pol_selected:
                if len(q_selected) == len(self.q_vars):
                    sb.Popen(["py", python_plot_file, scat_mat_file, "EFF", save_dir, "--pol", pol])
                else:
                    for qmode in q_selected:
                        sb.Popen(["py", python_plot_file, scat_mat_file, qmode, save_dir, "--pol", pol])


    def plot_near_field(self):
        """Plot near field using external Python script."""
        python_plot_file = os.path.join(self.config.plot_location, "plot_nearfield.py")
        self.write_input_file()

        near_field_file = os.path.join(
            self.config.data["folder_location"], 
            self.config.data["near_field_file"] or "nf.dat"
        )

        # Collect which checkbuttons are active
        selected_options = []
        for var, cb in zip(self.plot_option_vars, self.plot_option_labels):
            if var.get():
                selected_options.append(cb)

        if not selected_options:
            messagebox.showwarning("No plots selected", "Please select at least one plot option.")
            return

        save_dir = self.config.data["folder_location"]  # <- folder for saving plots
        length_scale = self.length_scale_entry.get()
        length_scale = length_scale.replace("d0", "").replace("D0", "")
        # Build the command → pass nearfieldplot type + selected components + save_dir
        # args = ["py", python_plot_file, near_field_file, self.plot_type_var.get()] + selected_options + [save_dir]
        args = ["py", python_plot_file,
                near_field_file,
                self.plot_type_var.get()] \
                + selected_options \
                + [length_scale, save_dir]
        sb.Popen(args)
        


    def plot_radius_sweep(self):
        """
        Llama al script plot_radius_sweep.py pasando el archivo de salida de
        MSTM y el config.json de la simulación actual, para que el script
        pueda recuperar los radios exactos del sweep.
        """
        # Ruta al script de plotting
        python_plot_file = os.path.join(
            self.config.plot_location, "plot_radius_sweep.py"
        )

        # Comprobar que el script existe
        if not os.path.isfile(python_plot_file):
            messagebox.showerror(
                "Script no encontrado",
                f"No se encuentra:\n{python_plot_file}\n\n"
                "Comprueba que 'plot_radius_sweep.py' está en la carpeta "
                "Plotting_codes y que la ruta en DEFAULT_PYTHON_PLOT_LOCATION "
                "es correcta."
            )
            return

        # Archivo de salida de MSTM
        folder = self.config.data.get("folder_location", "")
        out_file = self.config.data.get("output_file", "")
        if not folder or not out_file:
            messagebox.showwarning(
                "Carpeta o archivo no definidos",
                "Define la carpeta de simulación y el nombre del archivo de "
                "salida antes de hacer el plot."
            )
            return

        dat_file = os.path.join(folder, out_file)
        if not os.path.isfile(dat_file):
            messagebox.showwarning(
                "Archivo de salida no encontrado",
                f"No se encuentra:\n{dat_file}\n\n"
                "Ejecuta primero la simulación MSTM."
            )
            return

        # Guardar config.json en la carpeta de simulación para que el script
        # pueda leer los radios exactos del sweep
        config_json = os.path.join(folder, "config.json")
        try:
            self.config.save_to_json(config_json)
        except Exception as exc:
            messagebox.showwarning(
                "No se pudo guardar config.json",
                f"Los radios en el gráfico serán aproximados.\n({exc})"
            )
            config_json = None  # el script funcionará con índice de run

        # Lanzar el script en un proceso independiente
        cmd = ["py", python_plot_file, dat_file]
        if config_json:
            cmd.append(config_json)

        try:
            sb.Popen(cmd)
            self.plot_sweep_status.config(
                text="Abriendo plot...", fg="#357ABD"
            )
            # Limpiar el mensaje de estado tras 3 s
            self.root.after(
                3000,
                lambda: self.plot_sweep_status.config(text="", fg="gray")
            )
        except Exception as exc:
            self.plot_sweep_status.config(text="Error", fg="red")
            messagebox.showerror("Error al lanzar el script", str(exc))



    def plot_asymmetry(self):
        """Calcula y representa el parámetro de asimetría g."""
        python_plot_file = os.path.join(self.config.plot_location, "plot_asymmetry.py")

        if not os.path.isfile(python_plot_file):
            messagebox.showerror("Script no encontrado",
                                f"No se encuentra:\n{python_plot_file}")
            return

        folder  = self.config.data.get("folder_location", "")
        out_file = self.config.data.get("output_file", "")
        dat_file = os.path.join(folder, out_file)

        if not os.path.isfile(dat_file):
            messagebox.showwarning("Archivo no encontrado",
                                f"Ejecuta primero la simulación:\n{dat_file}")
            return

        config_json = os.path.join(folder, "config.json")
        try:
            self.config.save_to_json(config_json)
        except Exception:
            config_json = None

        lambda_um = self.wavelength_entry.get().strip()
        save_dir  = folder

        cmd = ["py", python_plot_file, dat_file,
            "--lambda_um", lambda_um,
            "--save_dir",  save_dir]
        if config_json:
            cmd += ["--config_json", config_json]

        sb.Popen(cmd)




    def show_notification(self, titled="Notification", message="Notification"):
        """Centered, scrollable notification up to 95% of screen height, text fits horizontally."""
        notification = tk.Toplevel(self.root)
        notification.title(titled)
        try:
            notification.iconbitmap(os.path.join(current_dir, "favicon.ico"))
        except Exception:
            pass
        notification.overrideredirect(False)

        # === Layout: Canvas + vertical scrollbar ===
        container = tk.Frame(notification)
        container.pack(expand=True, fill="both")

        canvas = tk.Canvas(container, highlightthickness=0, borderwidth=0)
        vbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas)

        # Put inner frame inside canvas
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=vbar.set)

        # Label – no wrap so it fits horizontally (window will widen up to 95% screen width)
        label = tk.Label(inner, text=message, padx=20, pady=20, anchor="w", justify="center")
        label.pack(fill="both", expand=True)

        canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")

        # === Measure exact content size ===
        notification.update_idletasks()
        content_w = inner.winfo_reqwidth()
        content_h = inner.winfo_reqheight()

        # === Screen limits (95%) ===
        screen_w = notification.winfo_screenwidth()
        screen_h = notification.winfo_screenheight()
        max_w = int(screen_w * 0.75)
        max_h = int(screen_h * 0.75)

        # Add a little room for the scrollbar if needed
        scrollbar_w = vbar.winfo_reqwidth() or 16

        # Window size: fit content but cap to 95% of screen
        window_w = min(content_w + scrollbar_w, max_w)
        window_h = min(content_h, max_h)

        # Update canvas viewport to the decided size
        canvas.configure(width=window_w, height=window_h)

        # Update scrollregion whenever inner changes
        def _on_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Keep the inner frame the same width as the canvas to avoid horizontal scrolling
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        inner.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", _on_configure)

        # Mouse wheel scrolling (Windows/Mac/Linux)
        def _wheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        def _wheel_linux(event):
            canvas.yview_scroll(1 if event.num == 5 else -1, "units")

        canvas.bind_all("<MouseWheel>", _wheel)        # Windows / macOS
        canvas.bind_all("<Button-4>", _wheel_linux)    # Linux
        canvas.bind_all("<Button-5>", _wheel_linux)

        # === Center on screen ===
        x = (screen_w // 2) - (window_w // 2)
        y = (screen_h // 2) - (window_h // 2) - 30
        notification.geometry(f"{window_w}x{window_h}+{x}+{y}")

        notification.focus_force()

# Run the application
root = tk.Tk()
app = MieTheoryApp(root)
root.mainloop()