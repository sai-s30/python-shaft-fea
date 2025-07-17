import numpy as np

def assemble_global_stiffness(points, cells, D):
    """
    Assemble global stiffness matrix for tetrahedral mesh.
    """
    num_nodes = len(points)
    K = np.zeros((num_nodes * 3, num_nodes * 3))

    for tet in cells:
        node_ids = tet
        coords = points[node_ids]
        ke = compute_element_stiffness(coords, D)

        for i_local, i_global in enumerate(node_ids):
            for j_local, j_global in enumerate(node_ids):
                K[i_global*3:i_global*3+3, j_global*3:j_global*3+3] += ke[i_local*3:i_local*3+3, j_local*3:j_local*3+3]

    return K


def compute_element_stiffness(coords, D):
    """
    Compute element stiffness matrix for a tetrahedral element.
    """
    # Construct the 4x4 matrix for shape function derivatives
    A = np.ones((4, 4))
    A[:, 1:] = coords
    detA = np.linalg.det(A)
    volume = abs(detA) / 6.0

    if volume < 1e-12:
        return np.zeros((12, 12))  # Skip degenerate elements

    B = np.zeros((6, 12))  # Strain-displacement matrix

    # Invert A once, reuse for all nodes
    invA = np.linalg.inv(A)

    for i in range(4):
        # Gradient of shape function i is the ith column of invA, excluding first row
        grad_N = invA[1:, i]  # shape (3,)

        B[:, i*3:i*3+3] = np.array([
            [grad_N[0], 0, 0],
            [0, grad_N[1], 0],
            [0, 0, grad_N[2]],
            [grad_N[1], grad_N[0], 0],
            [0, grad_N[2], grad_N[1]],
            [grad_N[2], 0, grad_N[0]],
        ])

    ke = volume * (B.T @ D @ B)
    return ke


def apply_boundary_conditions(K, F, fixed_dofs):
    """
    Apply boundary conditions by reducing the global system.
    Returns reduced K, reduced F, and free DOFs.
    """
    total_dofs = K.shape[0]
    all_dofs = np.arange(total_dofs)
    free_dofs = np.setdiff1d(all_dofs, fixed_dofs)

    K_reduced = K[np.ix_(free_dofs, free_dofs)]
    F_reduced = F[free_dofs]

    return K_reduced, F_reduced, free_dofs


def compute_von_mises_stress(points, cells, U, D):
    """
    Compute von Mises stress averaged at each node.
    """
    stress = np.zeros(len(points))
    counts = np.zeros(len(points))

    for tet in cells:
        node_ids = tet
        coords = points[node_ids]
        u_e = np.hstack([U[i*3:i*3+3] for i in node_ids])

        A = np.ones((4, 4))
        A[:, 1:] = coords
        detA = np.linalg.det(A)
        volume = abs(detA) / 6.0

        if volume < 1e-12:
            continue

        invA = np.linalg.inv(A)

        B = np.zeros((6, 12))
        for i in range(4):
            grad_N = invA[1:, i]

            B[:, i*3:i*3+3] = np.array([
                [grad_N[0], 0, 0],
                [0, grad_N[1], 0],
                [0, 0, grad_N[2]],
                [grad_N[1], grad_N[0], 0],
                [0, grad_N[2], grad_N[1]],
                [grad_N[2], 0, grad_N[0]],
            ])

        strain = B @ u_e
        sigma = D @ strain

        von_mises = np.sqrt(
            0.5 * ((sigma[0] - sigma[1])**2 + (sigma[1] - sigma[2])**2 + (sigma[2] - sigma[0])**2)
            + 3 * (sigma[3]**2 + sigma[4]**2 + sigma[5]**2)
        )

        for idx in node_ids:
            stress[idx] += von_mises
            counts[idx] += 1

    # Average von Mises stress per node
    stress[counts > 0] /= counts[counts > 0]
    return stress
