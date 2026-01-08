import tkinter as tk
from tkinter import messagebox
import os
import subprocess as sb

# Constants
DEFAULT_FOLDER_LOCATION = "C:\\Gorka\\UNI\\TFG\\code\\Simulaciones"
current_dir = os.path.dirname(os.path.abspath(__file__))
class Config:
    """Store simulation configuration parameters."""
    def __init__(self):
        self.folder_location = DEFAULT_FOLDER_LOCATION
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
            "near_field_file": ""
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
        """Create all UI components and layout."""
        # Folder Location
        tk.Label(self.root, text="Folder Location").pack()
        self.folder_location_entry = self.create_entry(DEFAULT_FOLDER_LOCATION)
        
        # Output File Name
        tk.Label(self.root, text="Output File Name").pack()
        self.output_file_entry = self.create_entry()
        
        # Number of Spheres
        tk.Label(self.root, text="Number of Spheres").pack()
        self.num_spheres_entry = self.create_entry()
        
        # Spheres Position
        tk.Label(self.root, text="Spheres Position (x, y, z, radius) and Refractive Index (re, im)").pack()
        self.position_entry = tk.Text(self.root, height=4)
        self.position_entry.pack()
        
        # Incident Angles
        self.incident_beta_entry = self.create_label_entry("Incident Beta (deg)", self.config.data["incident_beta"])
        self.incident_alpha_entry = self.create_label_entry("Incident Alpha (deg)", self.config.data["incident_alpha"])
        
        # Length Scale Factor
        self.length_scale_entry = self.create_label_entry("Length Scale Factor", self.config.data["length_scale"])
        
        # Near Field Calculation
        self.near_field_var = tk.BooleanVar()
        tk.Checkbutton(self.root, text="Near Field Calculation", variable=self.near_field_var).pack()
        
        # Near Field Output File
        self.near_field_file_entry = self.create_label_entry("Near Field Output File Name")
        
        # Beam Type
        self.beam_type_var = tk.StringVar(value="Plane Wave")
        tk.Label(self.root, text="Beam Type").pack()
        tk.Radiobutton(self.root, text="Plane Wave", variable=self.beam_type_var, value="Plane Wave").pack()
        tk.Radiobutton(self.root, text="Gaussian", variable=self.beam_type_var, value="Gaussian").pack()
        
        # Gaussian Beam Constant
        self.gaussian_constant_entry = self.create_label_entry("Gaussian Beam Constant", self.config.data["gaussian_beam_constant"])
        
        # Buttons
        self.create_button("Write mstm.inp", self.write_input_file)
        self.load_write_status_label = tk.Label(self.root, text="Loading")
        self.load_write_status_label.pack()
        self.create_button("Execute mstm.exe", self.run_simulation)
        self.status_label = tk.Label(self.root, text="Ready")
        self.status_label.pack()
        self.create_button("Plot Scattering Matrix", self.plot_scattering_matrix)
        self.create_button("Plot Near Field", self.plot_near_field)
        
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
        file = os.path.join(self.folder_location_entry.get() or DEFAULT_FOLDER_LOCATION, "mstm.inp")
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
                        self.config.data["folder_location"] = next(line_iter).replace("!","").strip()
                    elif "output_file" == line:
                        self.config.data["output_file"] = next(line_iter).strip()
                        print(self.config.data["output_file"])
                    elif "number_spheres" in line:
                        self.config.data["number_spheres"] = next(line_iter).strip()
                    elif "incident_beta_deg" in line:
                        self.config.data["incident_beta_deg"] = next(line_iter).strip()
                    elif "incident_alpha_deg" in line:
                        self.config.data["incident_alpha_deg"] = next(line_iter).strip()
                    elif "length_scale_factor" in line:
                        self.config.data["length_scale_factor"] = next(line_iter).strip()
                    elif "gaussian_beam_constant" in line:
                        self.config.data["is_gaussian_beam"] = True
                        self.config.data["gaussian_beam_constant"] = next(line_iter).strip()
                    elif "calculate_near_field" in line:
                        self.config.data["calculate_near_field"] = next(line_iter).strip()
                    elif "near_field_output_file" in line:
                        self.config.data["near_field_output_file"] = next(line_iter).strip()
                    elif "sphere_data" in line:
                        sphere_data = []
                        for line in line_iter:
                            if "end_of_sphere_data" in line:
                                break
                            sphere_data.append(line.strip())
                        self.config.data["sphere_data"] = sphere_data
                
                if  self.config.data["is_gaussian_beam"]:
                    self.beam_type_var.set("Gaussian")
                    
                    
                # Populate fields with previous data, ensuring editable state
                self.folder_location_entry.config(state="normal")
                self.folder_location_entry.delete(0, "end")
                self.folder_location_entry.insert(0, self.config.data.get("folder_location", ""))

                self.output_file_entry.config(state="normal")
                self.output_file_entry.delete(0, "end")
                self.output_file_entry.insert(0, self.config.data.get("output_file", ""))

                self.num_spheres_entry.config(state="normal")
                self.num_spheres_entry.delete(0, "end")
                self.num_spheres_entry.insert(0, self.config.data.get("number_spheres", ""))

                self.incident_beta_entry.config(state="normal")
                self.incident_beta_entry.delete(0, "end")
                self.incident_beta_entry.insert(0, self.config.data.get("incident_beta_deg", "0.d0"))

                self.incident_alpha_entry.config(state="normal")
                self.incident_alpha_entry.delete(0, "end")
                self.incident_alpha_entry.insert(0, self.config.data.get("incident_alpha_deg", "0.d0"))

                self.length_scale_entry.config(state="normal")
                self.length_scale_entry.delete(0, "end")
                self.length_scale_entry.insert(0, self.config.data.get("length_scale_factor", "1.d0"))

                self.gaussian_constant_entry.config(state="normal")
                self.gaussian_constant_entry.delete(0, "end")
                self.gaussian_constant_entry.insert(0, self.config.data.get("gaussian_beam_constant"))

                self.position_entry.config(state="normal")
                self.position_entry.delete("1.0", "end")
                self.position_entry.insert("1.0", "\n".join(self.config.data.get("sphere_data", [])))

                self.near_field_var.set(self.config.data["calculate_near_field"] == "t")
                self.near_field_file_entry.config(state="normal")
                self.near_field_file_entry.delete(0, "end")
                self.near_field_file_entry.insert(0, self.config.data.get("near_field_output_file", ""))
                
                # messagebox.showinfo("Load Previous Data", "Previous data loaded from mstm.inp.")
                self.load_write_status_label.config(text = "Loading completed")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load previous data: {e}")

        
    def write_input_file(self):
        """Write simulation input parameters to mstm.inp."""
        # Collect all data from entries and save to Config
        self.config.data["folder_location"] = self.folder_location_entry.get() or DEFAULT_FOLDER_LOCATION
        self.config.data["output_file"] = self.output_file_entry.get()
        self.config.data["num_spheres"] = self.num_spheres_entry.get()
        self.config.data["positions"] = self.position_entry.get("1.0", "end").splitlines()
        self.config.data["incident_beta"] = self.incident_beta_entry.get()
        self.config.data["incident_alpha"] = self.incident_alpha_entry.get()
        self.config.data["length_scale"] = self.length_scale_entry.get()
        self.config.data["gaussian_beam_constant"] = self.gaussian_constant_entry.get() if self.beam_type_var.get() == "Gaussian" else False
        self.config.data["near_field"] = self.near_field_var.get()
        self.config.data["near_field_file"] = self.near_field_file_entry.get() if self.config.data["near_field"] else "f"
        
        folder_input_file = os.path.join(self.config.data["folder_location"], "mstm.inp")
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
                f.write(f"{self.config.data['incident_beta']}\n")  # User-defined value
                f.write("incident_alpha_deg\n")
                f.write(f"{self.config.data['incident_alpha']}\n")  # User-defined value
                f.write("length_scale_factor\n")
                f.write(f"{self.config.data['length_scale']}\n")  # User-defined value
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
            self.load_write_status_label.config(text = "Simulation input file written")



        except Exception as e:
            messagebox.showerror("Error", f"Failed to write file: {e}")

    def run_simulation(self):
        """Run the Fortran executable."""

        # Update the status label to show that the simulation is starting
        self.status_label.config(text="Running simulation...")
        self.root.update_idletasks()  # Ensure the GUI updates immediately

        self.write_input_file()
        result = sb.run("mstm.exe", cwd=self.config.data["folder_location"], stdout=sb.PIPE, stderr=sb.PIPE, text=True)


        # Update the status label to show that the simulation is completed
        self.status_label.config(text="Simulation completed")
        self.show_notification("Simulation completed", f"Result: {result.stdout}")
        # messagebox.showinfo("Simulation completed", f"Result: {result.stdout}")

    def plot_scattering_matrix(self):
        """Plot scattering matrix using external Python script."""
        python_plot_file = "C:\\Gorka\\UNI\\TFG\\code\\Python\\Plotting_codes\\plot_scattering_matrix.py"
        self.write_input_file()
        scat_mat_file = os.path.join(self.config.data["folder_location"], self.config.data["output_file"])
        sb.Popen(["py", python_plot_file, scat_mat_file])
        
    def plot_near_field(self):
        """Plot near field using external Python script."""
        python_plot_file = "C:\\Gorka\\UNI\\TFG\\code\\Python\\Plotting_codes\\plot_nearfield.py"
        self.write_input_file()
        near_field_file = os.path.join(self.config.data["folder_location"], self.config.data["near_field_file"] or "nf.dat")
        sb.Popen(["py", python_plot_file, near_field_file])
    
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
        notification.geometry(f"{notification.winfo_reqwidth()}x{notification.winfo_reqheight()}")  # Set the window size to fit the content
        notification.focus_force()

        
# Run the application
root = tk.Tk()
app = MieTheoryApp(root)
root.mainloop()
