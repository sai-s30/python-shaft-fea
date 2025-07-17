import tkinter as tk
from tkinter import ttk, messagebox
from solver.fea_solver import solve_fea
import pyvista as pv
import os
import numpy as np


class FEAShaftGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Shaft FEA Simulator")
        self.geometry("450x600") # Increased height again to accommodate new input

        self.load_types = {
            "axial": ["Axial Load (N)"],
            "bending": ["Bending Load (N)"], # This will be the magnitude of the force for bending
            "torsion": ["Torsion Load (Nm)"],
            "axial+bending": ["Axial Load (N)", "Bending Load (N)"],
            "axial+torsion": ["Axial Load (N)", "Torsion Load (Nm)"],
            "bending+torsion": ["Bending Load (N)", "Torsion Load (N)"], # Changed Nm to N for consistency with bending load type
            "axial+bending+torsion": ["Axial Load (N)", "Bending Load (N)", "Torsion Load (N)"] # Changed Nm to N
        }

        self.create_widgets()

    def create_widgets(self):
        padding = {'padx': 10, 'pady': 5}

        ttk.Label(self, text="Shaft Length (m):").grid(row=0, column=0, sticky='w', **padding)
        self.length_var = tk.StringVar(value="1.0")
        ttk.Entry(self, textvariable=self.length_var).grid(row=0, column=1, **padding)

        ttk.Label(self, text="Shaft Radius (m):").grid(row=1, column=0, sticky='w', **padding)
        self.radius_var = tk.StringVar(value="0.1")
        ttk.Entry(self, textvariable=self.radius_var).grid(row=1, column=1, **padding)

        ttk.Label(self, text="Young's Modulus E (Pa):").grid(row=2, column=0, sticky='w', **padding)
        self.E_var = tk.StringVar(value="2e11")
        ttk.Entry(self, textvariable=self.E_var).grid(row=2, column=1, **padding)

        ttk.Label(self, text="Poisson's Ratio ν:").grid(row=3, column=0, sticky='w', **padding)
        self.nu_var = tk.StringVar(value="0.3")
        ttk.Entry(self, textvariable=self.nu_var).grid(row=3, column=1, **padding)

        # New: Mesh Element Size input
        ttk.Label(self, text="Mesh Element Size (m):").grid(row=4, column=0, sticky='w', **padding)
        # Default to a value that's reasonable, e.g., radius / 5 or 0.02
        self.element_size_var = tk.StringVar(value="0.02")
        ttk.Entry(self, textvariable=self.element_size_var).grid(row=4, column=1, **padding)


        ttk.Label(self, text="Load Type:").grid(row=5, column=0, sticky='w', **padding) # Row changed
        self.load_type_var = tk.StringVar()
        load_options = list(self.load_types.keys())
        self.load_type_combo = ttk.Combobox(self, textvariable=self.load_type_var, values=load_options, state="readonly")
        self.load_type_combo.current(0)
        self.load_type_combo.grid(row=5, column=1, **padding) # Row changed
        self.load_type_combo.bind("<<ComboboxSelected>>", self.update_load_inputs)

        self.load_inputs_frame = ttk.Frame(self)
        self.load_inputs_frame.grid(row=6, column=0, columnspan=2, sticky='w', **padding) # Row changed

        self.load_input_vars = {}
        # New: Variables for bending load position
        self.bending_x_var = tk.StringVar(value="0.0")
        self.bending_y_var = tk.StringVar(value="0.0")

        self.update_load_inputs() # Initialize load inputs frame

        self.run_button = ttk.Button(self, text="Run FEA", command=self.run_fea)
        self.run_button.grid(row=7, column=0, columnspan=2, pady=10) # Row changed

        self.visualize_button = ttk.Button(self, text="Visualize Results", command=self.visualize_results, state="disabled")
        self.visualize_button.grid(row=8, column=0, columnspan=2, pady=5) # Row changed

        self.animate_button = ttk.Button(self, text="Play Animation", command=self.play_animation, state="disabled")
        self.animate_button.grid(row=9, column=0, columnspan=2, pady=5) # Row changed

        self.status_label = ttk.Label(self, text="")
        self.status_label.grid(row=10, column=0, columnspan=2) # Row changed

    def update_load_inputs(self, event=None):
        for widget in self.load_inputs_frame.winfo_children():
            widget.destroy()
        self.load_input_vars.clear()

        selected_load = self.load_type_var.get()
        labels = self.load_types.get(selected_load, [])

        current_row = 0
        for i, label in enumerate(labels):
            ttk.Label(self.load_inputs_frame, text=label).grid(row=current_row, column=0, sticky='w', padx=10, pady=2)
            var = tk.StringVar(value="1000.0")
            entry = ttk.Entry(self.load_inputs_frame, textvariable=var, width=15)
            entry.grid(row=current_row, column=1, padx=10, pady=2)
            self.load_input_vars[label] = var
            current_row += 1

            # Add bending load position inputs if 'bending' is in the selected load type
            if "bending" in selected_load:
                if label == "Bending Load (N)": # Attach position inputs to the Bending Load field
                    ttk.Label(self.load_inputs_frame, text="Bending X-pos (m):").grid(row=current_row, column=0, sticky='w', padx=10, pady=2)
                    ttk.Entry(self.load_inputs_frame, textvariable=self.bending_x_var, width=15).grid(row=current_row, column=1, padx=10, pady=2)
                    current_row += 1

                    ttk.Label(self.load_inputs_frame, text="Bending Y-pos (m):").grid(row=current_row, column=0, sticky='w', padx=10, pady=2)
                    ttk.Entry(self.load_inputs_frame, textvariable=self.bending_y_var, width=15).grid(row=current_row, column=1, padx=10, pady=2)
                    current_row += 1


    def run_fea(self):
        try:
            params = {
                "length": float(self.length_var.get()),
                "radius": float(self.radius_var.get()),
                "E": float(self.E_var.get()),
                "nu": float(self.nu_var.get()),
                "element_size": float(self.element_size_var.get()), # New: Get element size
                "load_type": self.load_type_var.get(),
                "load_value": {} # Initialize as dict
            }

            load_val = {"axial": 0.0, "bending": 0.0, "torsion": 0.0}
            for label, var in self.load_input_vars.items():
                val = float(var.get())
                if "Axial" in label:
                    load_val["axial"] = val
                elif "Bending" in label:
                    load_val["bending"] = val
                elif "Torsion" in label:
                    load_val["torsion"] = val

            params["load_value"] = load_val

            # Add bending position to params if bending load is selected
            if "bending" in params["load_type"]:
                params["bending_pos"] = {
                    "x": float(self.bending_x_var.get()),
                    "y": float(self.bending_y_var.get())
                }
            else:
                params["bending_pos"] = {"x": 0.0, "y": 0.0} # Default if no bending load

        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values.")
            return

        self.status_label.config(text="Running FEA... please wait.")
        self.update()

        try:
            solve_fea(params)
        except Exception as e:
            messagebox.showerror("Error", f"FEA simulation failed:\n{str(e)}")
            self.status_label.config(text="Simulation failed.")
            self.visualize_button.config(state="disabled")
            self.animate_button.config(state="disabled")
            return

        self.status_label.config(text="FEA completed successfully.")
        self.visualize_button.config(state="normal")
        self.animate_button.config(state="normal")
        messagebox.showinfo("Success", "FEA completed successfully!\nYou can now visualize and animate the results.")

    def visualize_results(self):
        vtk_path = "output/deformed_shaft.vtk"
        if not os.path.exists(vtk_path):
            messagebox.showerror("File Not Found", f"VTK file not found at {vtk_path}. Run FEA first.")
            return

        mesh = pv.read(vtk_path)

        displacement = mesh.point_data.get("Displacement")
        if displacement is None:
            messagebox.showerror("Data Error", "Displacement data not found in VTK file.")
            return

        deformed_points = mesh.points + displacement
        deformed_mesh = mesh.copy()
        deformed_mesh.points = deformed_points

        plotter = pv.Plotter()
        plotter.add_mesh(deformed_mesh, scalars="Von_Mises", show_edges=True, cmap="jet")
        plotter.add_scalar_bar(title="Von Mises Stress")
        plotter.show()

    def play_animation(self):
        vtk_path = "output/deformed_shaft.vtk"
        if not os.path.exists(vtk_path):
            messagebox.showerror("File Not Found", f"VTK file not found at {vtk_path}. Run FEA first.")
            return

        mesh = pv.read(vtk_path)
        displacement = mesh.point_data.get("Displacement")
        von_mises_final = mesh.point_data.get("Von_Mises")

        if displacement is None or von_mises_final is None:
            messagebox.showerror("Data Error", "Displacement or Von Mises data missing in VTK file.")
            return

        n_steps = 1000
        points_initial = mesh.points
        von_mises_final = np.array(von_mises_final)

        min_vm_overall = 0
        max_vm_overall = von_mises_final.max() if von_mises_final.size > 0 else 1.0 # Handle case where max_vm might be 0

        plotter = pv.Plotter()

        # Create an initial mesh that we will continually update
        # This mesh will hold the current state of points and scalars
        current_display_mesh = mesh.copy()
        current_display_mesh.points = points_initial
        current_display_mesh.point_data["Von_Mises"] = np.zeros_like(von_mises_final)

        mesh_actor = plotter.add_mesh(current_display_mesh, scalars="Von_Mises", show_edges=True, cmap="jet",
                                      clim=[min_vm_overall, max_vm_overall])
        plotter.add_scalar_bar(title="Von Mises Stress")

        def update_frame(value):
            t_idx = int(value)
            t = t_idx / (n_steps - 1) if n_steps > 1 else 0.0 # Handle n_steps=1 case

            # Calculate interpolated points and stress for the current time step 't'
            current_points = points_initial + t * displacement
            current_von_mises = t * von_mises_final

            # Directly update the points and active scalars of the mesh that the actor is displaying
            # We get the underlying PyVista DataSet from the actor's mapper
            current_mesh_data = mesh_actor.mapper.GetInput()
            current_mesh_data.points = current_points
            current_mesh_data.point_data["Von_Mises"] = current_von_mises
            current_mesh_data.Modified() # Inform VTK that the data has changed

            # This line might not be strictly necessary if scalars are updated via point_data,
            # but it ensures the active scalars array used for coloring is explicitly set.
            mesh_actor.active_scalars = current_von_mises

            # Tell the mapper to update its internal representation
            mesh_actor.mapper.Modified()
            plotter.render()


        plotter.add_slider_widget(callback=update_frame,
                                  rng=[0, n_steps - 1],
                                  value=0,
                                  title='Deformation Step',
                                  pointa=(.025, .1),
                                  pointb=(.225, .1),
                                  style='modern')

        plotter.show()


if __name__ == "__main__":
    app = FEAShaftGUI()
    app.mainloop()
