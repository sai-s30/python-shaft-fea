import meshio
import numpy as np
import os

from solver.material import get_elasticity_matrix
from solver.fea_math import assemble_global_stiffness, apply_boundary_conditions, compute_von_mises_stress
from mesh.generate_mesh import generate_shaft_mesh # Ensure this import is correct

def solve_fea(params):
    length = params["length"]
    radius = params["radius"]
    E = params["E"]
    nu = params["nu"]
    element_size = params["element_size"] # New: Get element size
    load_type = params["load_type"]
    load_value = params["load_value"]  # Dict with keys: 'axial', 'bending', 'torsion'
    bending_pos = params.get("bending_pos", {"x": 0.0, "y": 0.0})

    # Pass element_size to the mesh generation function
    mesh_file = generate_shaft_mesh(length=length, radius=radius, element_size=element_size)

    print("[✓] Reading mesh...")
    mesh = meshio.read(mesh_file)
    points = mesh.points
    cells = mesh.cells_dict["tetra"]
    num_nodes = len(points)

    print(f"[✓] Mesh: {num_nodes} nodes, {len(cells)} tetra elements")

    D = get_elasticity_matrix(E, nu)

    print("[✓] Assembling global stiffness matrix...")
    K = assemble_global_stiffness(points, cells, D)
    total_dofs = num_nodes * 3

    F = np.zeros(total_dofs)

    # Find nodes on top face (z = max z)
    z_max = np.max(points[:, 2])
    load_node_indices = [i for i, (_, _, z) in enumerate(points) if np.isclose(z, z_max, atol=1e-6)]

    # Apply loads dynamically based on load_type and load_value dict
    for part in load_type.split("+"):
        part = part.strip().lower()
        if part == "axial" and load_value.get("axial", 0) != 0:
            for i in load_node_indices:
                F[i*3 + 2] += load_value["axial"] / len(load_node_indices)
        elif part == "bending" and load_value.get("bending", 0) != 0:
            # Apply bending load at the specified position
            bending_force = load_value["bending"]
            target_x, target_y = bending_pos["x"], bending_pos["y"]

            top_node_coords = points[load_node_indices, :2]

            distances = np.linalg.norm(top_node_coords - np.array([target_x, target_y]), axis=1)

            if len(distances) > 0:
                closest_node_local_idx = np.argmin(distances)
                closest_node_global_idx = load_node_indices[closest_node_local_idx]

                F[closest_node_global_idx * 3 + 1] += bending_force
                print(f"[✓] Applied bending load of {bending_force} N at node {closest_node_global_idx} (approx x={points[closest_node_global_idx,0]:.3f}, y={points[closest_node_global_idx,1]:.3f})")
            else:
                print("[!] Warning: No nodes found on the top face to apply bending load.")

        elif part == "torsion" and load_value.get("torsion", 0) != 0:
            for i in load_node_indices:
                x, y, _ = points[i]
                F[i*3 + 0] += -y * load_value["torsion"]
                F[i*3 + 1] += x * load_value["torsion"]
        else:
            if part not in ["axial", "bending", "torsion"]:
                raise ValueError(f"Invalid load component '{part}' in load_type '{load_type}'")

    # Fix nodes at bottom (z = min z)
    fixed_dofs = []
    z_min = np.min(points[:, 2])
    for i, (_, _, z) in enumerate(points):
        if np.isclose(z, z_min, atol=1e-6):
            fixed_dofs.extend([i*3, i*3 + 1, i*3 + 2])

    print("[✓] Applying boundary conditions...")
    K_reduced, F_reduced, free_dofs = apply_boundary_conditions(K, F, fixed_dofs)

    print(f"System size before BC: {total_dofs} DOFs")
    print(f"System size after BC: {K_reduced.shape[0]} DOFs")

    print("[✓] Solving system...")
    U_reduced = np.linalg.solve(K_reduced, F_reduced)

    U = np.zeros(total_dofs)
    U[free_dofs] = U_reduced

    print("[✓] Computing von Mises stress...")
    stress = compute_von_mises_stress(points, cells, U, D)

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    deformed_points = points + U.reshape((-1, 3))

    meshio.write(
        os.path.join(output_dir, "deformed_shaft.vtk"),
        meshio.Mesh(points=deformed_points, cells={"tetra": cells},
                    point_data={"Displacement": U.reshape((-1, 3)), "Von_Mises": stress}),
    )

    print("[✓] FEA completed and results saved to output/deformed_shaft.vtk")
