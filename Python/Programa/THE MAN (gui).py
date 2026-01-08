import tkinter as tk
from tkinter import messagebox
import os
import subprocess as sb


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
            "gaussian_beam_constant": "0.1d0",
            "is_gaussian_beam": False,
            "near_field": False,
            "near_field_file": "",
            "nearfieldplot": ""
        }
        # self.beam_type = "Plane Wave" # creo que no hace falta


class MieTheoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mie Theory Simulation")
        root.iconbitmap(os.path.join(current_dir, "favicon.ico"))

        # Initialize Config object to store parameters
        self.config = Config()

        # Build the GUI
        self.build_gui()
        self.load_previous_data()

    
    def build_gui(self):
        """Create all UI components and layout with frames + grid."""

        # ===== File Options =====
        frame_files = tk.LabelFrame(self.root, text="File Options", padx=5, pady=5)
        frame_files.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_files, text="Folder Location").grid(row=0, column=0, sticky="w")
        self.folder_location_entry = tk.Entry(frame_files, width=50)
        self.folder_location_entry.insert(0, DEFAULT_FOLDER_LOCATION)
        self.folder_location_entry.grid(row=0, column=1, sticky="ew")

        tk.Label(frame_files, text="Output File Name").grid(row=1, column=0, sticky="w")
        self.output_file_entry = tk.Entry(frame_files, width=30)
        self.output_file_entry.grid(row=1, column=1, sticky="ew")

        tk.Label(frame_files, text="Number of Spheres").grid(row=2, column=0, sticky="w")
        self.num_spheres_entry = tk.Entry(frame_files, width=10)
        self.num_spheres_entry.grid(row=2, column=1, sticky="w")

        tk.Label(frame_files, text="Spheres Position (x, y, z, r, n)").grid(row=3, column=0, sticky="nw")
        self.position_entry = tk.Text(frame_files, height=4, width=50)
        self.position_entry.grid(row=3, column=1, sticky="ew")

        # ===== Incident Parameters =====
        frame_incident = tk.LabelFrame(self.root, text="Incident Parameters", padx=5, pady=5)
        frame_incident.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_incident, text="Incident Beta (deg)").grid(row=0, column=0, sticky="w")
        self.incident_beta_entry = tk.Entry(frame_incident, width=10)
        self.incident_beta_entry.insert(0, self.config.data["incident_beta"])
        self.incident_beta_entry.grid(row=0, column=1, padx=5)

        tk.Label(frame_incident, text="Incident Alpha (deg)").grid(row=0, column=2, sticky="w")
        self.incident_alpha_entry = tk.Entry(frame_incident, width=10)
        self.incident_alpha_entry.insert(0, self.config.data["incident_alpha"])
        self.incident_alpha_entry.grid(row=0, column=3, padx=5)

        tk.Label(frame_incident, text="Length Scale Factor").grid(row=1, column=0, sticky="w")
        self.length_scale_entry = tk.Entry(frame_incident, width=10)
        self.length_scale_entry.insert(0, self.config.data["length_scale"])
        self.length_scale_entry.grid(row=1, column=1, padx=5)

        # ===== Beam Options =====
        frame_beam = tk.LabelFrame(self.root, text="Beam Options", padx=5, pady=5)
        frame_beam.pack(fill="x", padx=10, pady=5)

        self.beam_type_var = tk.StringVar(value="Plane Wave")
        tk.Label(frame_beam, text="Beam Type").grid(row=0, column=0, sticky="w")
        tk.Radiobutton(frame_beam, text="Plane Wave", variable=self.beam_type_var,
                       value="Plane Wave").grid(row=0, column=1, sticky="w")
        tk.Radiobutton(frame_beam, text="Gaussian", variable=self.beam_type_var,
                       value="Gaussian").grid(row=0, column=2, sticky="w")

        tk.Label(frame_beam, text="Gaussian Beam Constant").grid(row=1, column=0, sticky="w")
        self.gaussian_constant_entry = tk.Entry(frame_beam, width=10)
        self.gaussian_constant_entry.insert(0, self.config.data["gaussian_beam_constant"])
        self.gaussian_constant_entry.grid(row=1, column=1, padx=5, sticky="w")

        # ===== Near Field =====
        frame_near = tk.LabelFrame(self.root, text="Near Field", padx=5, pady=5)
        frame_near.pack(fill="x", padx=10, pady=5)

        self.near_field_var = tk.BooleanVar()
        tk.Checkbutton(frame_near, text="Near Field Calculation",
                       variable=self.near_field_var).grid(row=0, column=0, sticky="w")

        tk.Label(frame_near, text="Near Field Output File").grid(row=1, column=0, sticky="w")
        self.near_field_file_entry = tk.Entry(frame_near, width=30)
        self.near_field_file_entry.grid(row=1, column=1, sticky="ew")

        # tk.Label(frame_near, text="Near Field Plot").grid(row=2, column=0, sticky="w")
        # self.nearfieldplot = tk.StringVar(value="Poynting Vector")
        # tk.Radiobutton(frame_near, text="Electric Field",
        #                variable=self.nearfieldplot, value="Electric Field").grid(row=2, column=1, sticky="w")
        # tk.Radiobutton(frame_near, text="Poynting Vector",
        #                variable=self.nearfieldplot, value="Poynting Vector").grid(row=2, column=2, sticky="w")

        # ===== Controls =====
        frame_buttons = tk.Frame(self.root)
        frame_buttons.pack(pady=10)

        tk.Button(frame_buttons, text="Write mstm.inp", command=self.write_input_file).grid(row=0, column=0, padx=5)
        self.load_write_status_label = tk.Label(frame_buttons, text="Loading")
        self.load_write_status_label.grid(row=0, column=1, padx=5)

        tk.Button(frame_buttons, text="Execute mstm.exe", command=self.run_simulation).grid(row=1, column=0, padx=5, pady=5)
        self.status_label = tk.Label(frame_buttons, text="Ready")
        self.status_label.grid(row=1, column=1, padx=5)

        tk.Button(frame_buttons, text="Plot Scattering Matrix",
                  command=self.plot_scattering_matrix).grid(row=2, column=0, padx=5, pady=5)
        # tk.Button(frame_buttons, text="Plot Near Field",
        #           command=self.plot_near_field).grid(row=2, column=1, padx=5, pady=5)
        
        # ===== Plot Options =====
        frame_plot = tk.LabelFrame(self.root, text="Plot Options", padx=5, pady=5)
        frame_plot.pack(fill="x", padx=10, pady=5)

        # Radio buttons for plot type
        self.plot_type_var = tk.StringVar(value="Poynting")
        tk.Radiobutton(frame_plot, text="Electric Field", variable=self.plot_type_var,
                       value="Electric", command=self.update_plot_options).grid(row=0, column=0, sticky="w")
        tk.Radiobutton(frame_plot, text="Magnetic Field", variable=self.plot_type_var,
                       value="Magnetic", command=self.update_plot_options).grid(row=0, column=1, sticky="w")
        tk.Radiobutton(frame_plot, text="Poynting Vector", variable=self.plot_type_var,
                       value="Poynting", command=self.update_plot_options).grid(row=0, column=2, sticky="w")

        # Frame that will hold the dynamic checkbuttons
        self.frame_plot_options = tk.Frame(frame_plot)
        self.frame_plot_options.grid(row=1, column=0, columnspan=3, pady=5)

        # Button to select/deselect all
        self.select_all_button = tk.Button(frame_plot, text="Select All",
                                           command=self.toggle_select_all)
        self.select_all_button.grid(row=2, column=0, pady=5, sticky="w")

        # Keep references to checkbutton variables
        self.plot_option_vars = []
        self.update_plot_options()  # initialize
        

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
            for i, comp in enumerate(["Sx", "Sy", "Sz"]):
                var = tk.BooleanVar()
                cb = tk.Checkbutton(self.frame_plot_options, text=comp, variable=var)
                cb.grid(row=0, column=i, padx=5, pady=2, sticky="w")
                self.plot_option_vars.append(var)
                self.plot_option_labels.append(comp)


        # Add "Plot Near Field" button here
        tk.Button(self.frame_plot_options, text="Plot Near Field", command=self.plot_near_field).grid(
            row=5, column=1, pady=5, sticky="e"
        )

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

    def load_previous_data(self):
        """Load previous simulation data from mstm.inp."""
        file = os.path.join(self.folder_location_entry.get()
                            or DEFAULT_FOLDER_LOCATION, "mstm.inp")
        if os.path.isfile(file):
            try:
                with open(file, "r") as f:
                    lines = f.readlines()

                # Parse the file data
                # data = {}
                line_iter = iter(lines)
                i = 0
                for line in line_iter:
                    line = line.strip()
                    if "folder_location" in line:
                        self.config.data["folder_location"] = next(
                            line_iter).replace("!", "").strip()
                    elif "output_file" == line:
                        self.config.data["output_file"] = next(
                            line_iter).strip()
                        print(self.config.data["output_file"])
                    elif "number_spheres" in line:
                        self.config.data["number_spheres"] = next(
                            line_iter).strip()
                    elif "incident_beta_deg" in line:
                        self.config.data["incident_beta_deg"] = next(
                            line_iter).strip()
                    elif "incident_alpha_deg" in line:
                        self.config.data["incident_alpha_deg"] = next(
                            line_iter).strip()
                    elif "length_scale_factor" in line:
                        self.config.data["length_scale_factor"] = next(
                            line_iter).strip()
                    elif "gaussian_beam_constant" in line:
                        self.config.data["is_gaussian_beam"] = True
                        self.config.data["gaussian_beam_constant"] = next(
                            line_iter).strip()
                    elif "calculate_near_field" in line:
                        self.config.data["calculate_near_field"] = next(
                            line_iter).strip()
                    elif "near_field_output_file" in line:
                        self.config.data["near_field_output_file"] = next(
                            line_iter).strip()
                    elif "sphere_data" in line:
                        sphere_data = []
                        for line in line_iter:
                            if "end_of_sphere_data" in line:
                                break
                            sphere_data.append(line.strip())
                        self.config.data["sphere_data"] = sphere_data

                if self.config.data["is_gaussian_beam"]:
                    self.beam_type_var.set("Gaussian")

                # Populate fields with previous data, ensuring editable state
                self.folder_location_entry.config(state="normal")
                self.folder_location_entry.delete(0, "end")
                self.folder_location_entry.insert(
                    0, self.config.data.get("folder_location", ""))

                self.output_file_entry.config(state="normal")
                self.output_file_entry.delete(0, "end")
                self.output_file_entry.insert(
                    0, self.config.data.get("output_file", ""))

                self.num_spheres_entry.config(state="normal")
                self.num_spheres_entry.delete(0, "end")
                self.num_spheres_entry.insert(
                    0, self.config.data.get("number_spheres", ""))

                self.incident_beta_entry.config(state="normal")
                self.incident_beta_entry.delete(0, "end")
                self.incident_beta_entry.insert(
                    0, self.config.data.get("incident_beta_deg", "0.d0"))

                self.incident_alpha_entry.config(state="normal")
                self.incident_alpha_entry.delete(0, "end")
                self.incident_alpha_entry.insert(
                    0, self.config.data.get("incident_alpha_deg", "0.d0"))

                self.length_scale_entry.config(state="normal")
                self.length_scale_entry.delete(0, "end")
                self.length_scale_entry.insert(
                    0, self.config.data.get("length_scale_factor", "1.d0"))

                self.gaussian_constant_entry.config(state="normal")
                self.gaussian_constant_entry.delete(0, "end")
                self.gaussian_constant_entry.insert(
                    0, self.config.data.get("gaussian_beam_constant"))

                self.position_entry.config(state="normal")
                self.position_entry.delete("1.0", "end")
                self.position_entry.insert("1.0", "\n".join(
                    self.config.data.get("sphere_data", [])))

                self.near_field_var.set(
                    self.config.data["calculate_near_field"] == "t")
                self.near_field_file_entry.config(state="normal")
                self.near_field_file_entry.delete(0, "end")
                self.near_field_file_entry.insert(
                    0, self.config.data.get("near_field_output_file", ""))

                # messagebox.showinfo("Load Previous Data", "Previous data loaded from mstm.inp.")
                self.load_write_status_label.config(text="Loading completed")
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to load previous data: {e}")

    def write_input_file(self):
        """Write simulation input parameters to mstm.inp."""
        # Collect all data from entries and save to Config
        self.config.data["folder_location"] = self.folder_location_entry.get(
        ) or DEFAULT_FOLDER_LOCATION
        self.config.data["output_file"] = self.output_file_entry.get()
        self.config.data["num_spheres"] = self.num_spheres_entry.get()
        self.config.data["positions"] = self.position_entry.get(
            "1.0", "end").splitlines()
        self.config.data["incident_beta"] = self.incident_beta_entry.get()
        self.config.data["incident_alpha"] = self.incident_alpha_entry.get()
        self.config.data["length_scale"] = self.length_scale_entry.get()
        self.config.data["gaussian_beam_constant"] = self.gaussian_constant_entry.get(
        ) if self.beam_type_var.get() == "Gaussian" else False
        self.config.data["near_field"] = self.near_field_var.get()
        self.config.data["near_field_file"] = self.near_field_file_entry.get(
        ) if self.config.data["near_field"] else "f"

        folder_input_file = os.path.join(
            self.config.data["folder_location"], "mstm.inp")
        print(folder_input_file)

        try:
            with open(folder_input_file, "w") as f:
                # Write the parameters from self.config to file

                f.write("! mstm input file\n")
                f.write("! folder_location\n")
                f.write(f'! {self.config.data["folder_location"]}\n')
                f.write("output_file\n")
                f.write(f'{self.config.data["output_file"]}\n')
                f.write("number_spheres\n")
                f.write(f'{self.config.data["num_spheres"]}\n')
                f.write("sphere_data\n")
                for pos in self.config.data["positions"]:
                    f.write(f"{pos}\n")
                f.write("end_of_sphere_data\n")
                f.write("incident_beta_deg\n")
                # User-defined value
                f.write(f"{self.config.data['incident_beta']}\n")
                f.write("incident_alpha_deg\n")
                # User-defined value
                f.write(f"{self.config.data['incident_alpha']}\n")
                f.write("length_scale_factor\n")
                # User-defined value
                f.write(f"{self.config.data['length_scale']}\n")
                f.write("solution_epsilon\n")
                f.write("1.d-8\n")

                # Include Gaussian beam parameters if Gaussian is selected
                if self.beam_type_var.get() == "Gaussian":
                    f.write("gaussian_beam_constant\n")
                    f.write(f"{self.config.data['gaussian_beam_constant']}\n")
                    f.write("gaussian_beam_focal_point\n")
                    f.write("0.d0,0.d0,0.d0\n")

                f.write("calculate_scattering_matrix\n")
                f.write("t\n")  # Always calculated
                f.write("calculate_near_field\n")
                f.write("t\n" if self.config.data["near_field"] else "f\n")

                if self.config.data["near_field"]:
                    f.write("near_field_minimum_border\n")
                    f.write("-20.d0,0.d0,-20.d0\n")
                    f.write("near_field_maximum_border\n")
                    f.write("20.d0,0.d0,20.d0\n")
                    f.write("near_field_step_size\n")
                    f.write("0.1d0\n")
                    f.write("near_field_output_file\n")
                    f.write(f"{self.config.data['near_field_file']}\n")

                f.write("end_of_options\n")

            # messagebox.showinfo("Simulation input file written", "Simulation input file written.")
            # self.show_notification("", "Simulation input file written.")
            self.load_write_status_label.config(
                text="Simulation input file written")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to write file: {e}")

    def run_simulation(self):
        """Run the Fortran executable."""

        # Update the status label to show that the simulation is starting
        self.status_label.config(text="Running simulation...")
        self.root.update_idletasks()  # Ensure the GUI updates immediately

        self.write_input_file()
        result = sb.run(
            "mstm.exe", cwd=self.config.data["folder_location"], stdout=sb.PIPE, stderr=sb.PIPE, text=True)
        # C:\\Users\\txuel\\UNI\\TFG Fisika\\code\\Fortran\\Programa\\

        # Update the status label to show that the simulation is completed
        self.status_label.config(text="Simulation completed")
        self.show_notification("Simulation completed",
                               f"Result: {result.stdout}")
        # messagebox.showinfo("Simulation completed", f"Result: {result.stdout}")

    def plot_scattering_matrix(self):
        """Plot scattering matrix using external Python script."""
        python_plot_file = self.config.plot_location+"\\plot_scattering_matrix.py"
        self.write_input_file()
        scat_mat_file = os.path.join(
            self.config.data["folder_location"], self.config.data["output_file"])
        print("scat_mat_file = ", scat_mat_file, " ", python_plot_file)
        sb.Popen(["py", python_plot_file, scat_mat_file])

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

        # Build the command → pass nearfieldplot type + selected components
        args = ["py", python_plot_file, near_field_file, self.plot_type_var.get()] + selected_options
        sb.Popen(args)

    def show_notification(self, titled="Notification", message="Notification"):
        """Display a non-blocking notification."""
        notification = tk.Toplevel(self.root)
        notification.title(titled)
        notification.iconbitmap(os.path.join(current_dir, "favicon.ico"))

        notification.geometry("250x100")  # Initial size and position
        notification.overrideredirect(False)  # Remove window borders

        label = tk.Label(notification, text=message, padx=10, pady=10)
        label.pack(expand=True, fill='both')  # Expand to fill the space

        # Update the size of the notification window to fit the label content
        notification.update_idletasks()  # Update the window to calculate the size
        notification.geometry(f"{notification.winfo_reqwidth()}x{notification.winfo_reqheight()}") # Set the window size to fit the content
        notification.focus_force()


# Run the application
root = tk.Tk()
app = MieTheoryApp(root)
root.mainloop()
