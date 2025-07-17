import os
import subprocess

def generate_shaft_mesh(length=1.0, radius=0.05, element_size=None, mesh_file="output/shaft.vtk"): # Added element_size parameter
    # If element_size is not provided, use default calculation based on radius
    if element_size is None:
        cl_min = radius / 3
        cl_max = radius / 2
    else:
        # Use the provided element_size for both min and max for simplicity,
        # or you could derive min/max from it (e.g., element_size / 2, element_size)
        cl_min = element_size
        cl_max = element_size * 1.5 # Allow some variation if desired, or just use element_size for both

    geo_code = f"""
SetFactory("OpenCASCADE");
Cylinder(1) = {{0, 0, 0, 0, 0, {length}, {radius}}};
Mesh.CharacteristicLengthMin = {cl_min};
Mesh.CharacteristicLengthMax = {cl_max};
Mesh 3;
"""
    os.makedirs("output", exist_ok=True)
    geo_file = "output/shaft.geo"
    with open(geo_file, "w") as f:
        f.write(geo_code)

    subprocess.run(["gmsh", geo_file, "-3", "-format", "vtk", "-o", mesh_file], check=True)
    print(f"[✓] Mesh generated at {mesh_file}")
    return mesh_file
