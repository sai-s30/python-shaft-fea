import numpy as np

def get_elasticity_matrix(E, nu):
    factor = E / ((1 + nu) * (1 - 2 * nu))
    D = factor * np.array([
        [1 - nu, nu, nu, 0, 0, 0],
        [nu, 1 - nu, nu, 0, 0, 0],
        [nu, nu, 1 - nu, 0, 0, 0],
        [0, 0, 0, (1 - 2*nu)/2, 0, 0],
        [0, 0, 0, 0, (1 - 2*nu)/2, 0],
        [0, 0, 0, 0, 0, (1 - 2*nu)/2],
    ])
    return D
