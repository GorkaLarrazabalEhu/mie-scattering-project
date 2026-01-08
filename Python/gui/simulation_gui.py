import tkinter as tk
from tkinter import messagebox
import os
import subprocess as sb

default_folder_location = "C:\\Gorka\\UNI\\TFG\\code\\Simulaciones"
def load_previous_data():
    file = (folder_location_entry.get() or default_folder_location) +"\\mstm.inp"
    print(file)
    if os.path.isfile(file):
        try:
            with open(file, "r") as f:
                lines = f.readlines()
            
            # Parse the file data
            data = {}
            line_iter = iter(lines)
            i = 0
            for line in line_iter:
                line = line.strip()
                print(f"i = {i}, line: {line}")
                i=i+1
                if "folder_location" in line:
                    data["folder_location"] = next(line_iter).replace("!","").strip()
                elif "output_file" == line:
                    data["output_file"] = next(line_iter).strip()
                    print(data["output_file"])
                elif "number_spheres" in line:
                    data["number_spheres"] = next(line_iter).strip()
                elif "incident_beta_deg" in line:
                    data["incident_beta_deg"] = next(line_iter).strip()
                elif "incident_alpha_deg" in line:
                    data["incident_alpha_deg"] = next(line_iter).strip()
                elif "length_scale_factor" in line:
                    data["length_scale_factor"] = next(line_iter).strip()
                elif "gaussian_beam_constant" in line:
                    data["gaussian_beam_constant"] = next(line_iter).strip()
                elif "calculate_near_field" in line:
                    data["calculate_near_field"] = next(line_iter).strip()
                elif "near_field_output_file" in line:
                    data["near_field_output_file"] = next(line_iter).strip()
                elif "sphere_data" in line:
                    sphere_data = []
                    for line in line_iter:
                        if "end_of_sphere_data" in line:
                            break
                        sphere_data.append(line.strip())
                    data["sphere_data"] = sphere_data

            # Populate fields with previous data, ensuring editable state
            folder_location_entry.config(state="normal")
            folder_location_entry.delete(0, "end")
            folder_location_entry.insert(0, data.get("folder_location", ""))

            output_file_entry.config(state="normal")
            output_file_entry.delete(0, "end")
            output_file_entry.insert(0, data.get("output_file", ""))

            num_spheres_entry.config(state="normal")
            num_spheres_entry.delete(0, "end")
            num_spheres_entry.insert(0, data.get("number_spheres", ""))

            incident_beta_entry.config(state="normal")
            incident_beta_entry.delete(0, "end")
            incident_beta_entry.insert(0, data.get("incident_beta_deg", "45.d0"))

            incident_alpha_entry.config(state="normal")
            incident_alpha_entry.delete(0, "end")
            incident_alpha_entry.insert(0, data.get("incident_alpha_deg", "0.d0"))

            length_scale_entry.config(state="normal")
            length_scale_entry.delete(0, "end")
            length_scale_entry.insert(0, data.get("length_scale_factor", "1.d0"))

            gaussian_constant_entry.config(state="normal")
            gaussian_constant_entry.delete(0, "end")
            gaussian_constant_entry.insert(0, data.get("gaussian_beam_constant", "0.1d0"))

            position_entry.config(state="normal")
            position_entry.delete("1.0", "end")
            position_entry.insert("1.0", "\n".join(data.get("sphere_data", [])))

            near_field_var.set(data["calculate_near_field"] == "t")
            near_field_file_entry.config(state="normal")
            near_field_file_entry.delete(0, "end")
            print(data.get("near_field_output_file"))
            near_field_file_entry.insert(0, data.get("near_field_output_file", ""))
            
            # messagebox.showinfo("Load Previous Data", "Previous data loaded from mstm.inp.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load previous data: {e}")


def write_input_file():
    folder_location = folder_location_entry.get() or default_folder_location
    output_file = output_file_entry.get()
    num_spheres = num_spheres_entry.get()
    positions = position_entry.get("1.0", "end").splitlines()  # Each line is a sphere's position data
    incident_beta = incident_beta_entry.get()
    incident_alpha = incident_alpha_entry.get()
    length_scale = length_scale_entry.get()
    gaussian_constant = gaussian_constant_entry.get() if beam_type_var.get() == "Gaussian" else None
    near_field = near_field_var.get()
    near_field_file = near_field_file_entry.get() if near_field else "f"  # False if near field not calculated
    beam_type = beam_type_var.get()
    folder_input_file = f"{folder_location}\\mstm.inp"
    print(folder_input_file)

    # Write inputs to mstm.inp file
    try:
        with open(f"{folder_input_file}", "w") as f:
            f.write("! mstm input file\n")
            f.write("! folder_location\n")
            f.write(f"! {folder_location}\n")
            f.write("output_file\n")
            f.write(f"{output_file}\n")
            f.write("number_spheres\n")
            f.write(f"{num_spheres}\n")
            f.write("sphere_data\n")
            for pos in positions:
                f.write(f"{pos}\n")

            f.write("end_of_sphere_data\n")
            f.write("incident_beta_deg\n")
            f.write(f"{incident_beta}\n")  # User-defined value
            f.write("incident_alpha_deg\n")
            f.write(f"{incident_alpha}\n")  # User-defined value
            f.write("length_scale_factor\n")
            f.write(f"{length_scale}\n")  # User-defined value
            f.write("solution_epsilon\n")
            f.write("1.d-8\n")

            # Include Gaussian beam parameters if Gaussian is selected
            if beam_type == "Gaussian":
                f.write("gaussian_beam_constant\n")
                f.write(f"{gaussian_constant}\n")
                f.write("gaussian_beam_focal_point\n")
                f.write("0.d0,0.d0,0.d0\n")

            f.write("calculate_scattering_matrix\n")
            f.write("t\n")  # Always calculated
            f.write("calculate_near_field\n")
            f.write("t\n" if near_field else "f\n")

            if near_field:
                f.write("near_field_minimum_border\n")
                f.write("-20.d0,0.d0,-20.d0\n")
                f.write("near_field_maximum_border\n")
                f.write("20.d0,0.d0,20.d0\n")
                f.write("near_field_step_size\n")
                f.write("0.1d0\n")
                f.write("near_field_output_file\n")
                f.write(f"{near_field_file}\n")

            f.write("end_of_options\n")

        messagebox.showinfo("Simulation input file written", "Simulation input file written.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to write to file: {e}")

def run_simulation():
    result = sb.run("mstm.exe",  cwd=folder_location_entry.get() ,stdout=sb.PIPE, stderr=sb.PIPE, text=True)
    # Print standard output and standard error
    print("Output:\n", result.stdout)
    print("Errors:\n", result.stderr)
    
    messagebox.showinfo("Simulation run completed", f"Result: {result.stdout}")

def plot_scattering_matrix():
    python_plot_file_location = "C:\\Gorka\\UNI\\TFG\\code\\Python\\Plotting_codes\\plot_scattering_matrix.py"
    scat_mat_file = (folder_location_entry.get() or default_folder_location) +"\\"+ output_file_entry.get()
    sb.Popen(["py", python_plot_file_location, scat_mat_file])

def plot_near_field():
    python_plot_file_location = "C:\\Gorka\\UNI\\TFG\\code\\Python\\Plotting_codes\\plot_nearfield.py"
    nf_default = "nf_fig.dat"
    nearfield_file = (folder_location_entry.get() or default_folder_location) + "\\"+(near_field_file_entry.get() or nf_default)
    print(nearfield_file)
    sb.Popen(["py", python_plot_file_location, nearfield_file])

# Create the main window
root = tk.Tk()
root.title("Mie Theory Simulation")

# Folder Location
tk.Label(root, text="Folder Location").pack()
folder_location_entry = tk.Entry(root)
folder_location_entry.insert(0, f"{default_folder_location}")  
folder_location_entry.pack()

# Output File Name
tk.Label(root, text="Output File Name").pack()
output_file_entry = tk.Entry(root)
output_file_entry.pack()

# Number of Spheres
tk.Label(root, text="Number of Spheres").pack()
num_spheres_entry = tk.Entry(root)
num_spheres_entry.pack()

# Spheres Position
tk.Label(root, text="Spheres Position (x, y, z, radius) and Refractive Index (re, im)").pack()
position_entry = tk.Text(root, height=4)  # Multi-line input for each sphere
position_entry.pack()

# Incident Angles
tk.Label(root, text="Incident Beta (deg)").pack()
incident_beta_entry = tk.Entry(root)
incident_beta_entry.insert(0, "45.d0")  # Default value
incident_beta_entry.pack()

tk.Label(root, text="Incident Alpha (deg)").pack()
incident_alpha_entry = tk.Entry(root)
incident_alpha_entry.insert(0, "0.d0")  # Default value
incident_alpha_entry.pack()

# Length Scale Factor
tk.Label(root, text="Length Scale Factor").pack()
length_scale_entry = tk.Entry(root)
length_scale_entry.insert(0, "1.d0")  # Default value
length_scale_entry.pack()

# Near Field Calculation
near_field_var = tk.BooleanVar()
tk.Checkbutton(root, text="Near Field Calculation", variable=near_field_var).pack()

# Near field Output File
tk.Label(root, text="Near Field Output File Name").pack()
near_field_file_entry = tk.Entry(root)
near_field_file_entry.pack()


# Beam Type
beam_type_var = tk.StringVar(value="Gaussian")
tk.Label(root, text="Beam Type").pack()
tk.Radiobutton(root, text="Plane Wave", variable=beam_type_var, value="Plane Wave").pack()
tk.Radiobutton(root, text="Gaussian", variable=beam_type_var, value="Gaussian").pack()

# Gaussian Beam Constant (only if Gaussian is selected)
tk.Label(root, text="Gaussian Beam Constant").pack()
gaussian_constant_entry = tk.Entry(root)
gaussian_constant_entry.insert(0, "0.1d0")  # Default value
gaussian_constant_entry.pack()

# Run Button
run_button = tk.Button(root, text="Write mstm.inp", command=write_input_file)
run_button.pack()

run_button = tk.Button(root, text="Execute mstm.exe", command = run_simulation)
run_button.pack()

Scattering_matrix_plot_button = tk.Button(root, text="Plot Scattering Matrix", command=plot_scattering_matrix)
Scattering_matrix_plot_button.pack()

near_field_plot_button = tk.Button(root, text="Plot Near Field", command = plot_near_field)
near_field_plot_button.pack()

# Load previous data from mstm.inp if available
load_previous_data()

root.mainloop()
