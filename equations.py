import numpy as np


def sample_gaussian_real(scale, size=None):
    return np.random.default_rng().normal(0, scale, size)


def sample_gaussian_complex(scale, size=None):
    half = scale / np.sqrt(2)
    rng = np.random.default_rng()
    return rng.normal(0, half, size) + 1j * rng.normal(0, half, size)


def create_goe_matrix(size):
    sigma_off = 1 / np.sqrt(size)
    sigma_diag = np.sqrt(2) * sigma_off
    matrix = np.zeros((size, size))
    upper = np.triu_indices(size, k=1)
    matrix[upper] = sample_gaussian_real(sigma_off, len(upper[0]))
    matrix += matrix.T
    np.fill_diagonal(matrix, sample_gaussian_real(sigma_diag, size))
    return matrix


def create_gue_matrix(size):
    sigma = 1 / np.sqrt(size)
    matrix = np.zeros((size, size), dtype=np.complex128)
    upper = np.triu_indices(size, k=1)
    matrix[upper] = sample_gaussian_complex(sigma, len(upper[0]))
    matrix += np.conj(matrix.T)
    np.fill_diagonal(matrix, sample_gaussian_real(sigma, size))
    return matrix


def create_gse_matrix(size):
    sigma_off = 1 / np.sqrt(2 * size)
    sigma_diag = np.sqrt(2) * sigma_off  # = 1/sqrt(size)

    # A: complex Hermitian
    A = np.zeros((size, size), dtype=np.complex128)
    upper = np.triu_indices(size, k=1)
    A[upper] = sample_gaussian_complex(sigma_off, len(upper[0]))
    A += np.conj(A.T)
    np.fill_diagonal(A, sample_gaussian_real(sigma_diag, size))

    # B: complex anti-Hermitian (B† = -B), diagonal zero
    B = np.zeros((size, size), dtype=np.complex128)
    B[upper] = sample_gaussian_complex(sigma_off, len(upper[0]))
    B = B - np.conj(B.T)
    np.fill_diagonal(B, 0.0 + 0.0j)

    upper_block = np.hstack((A, B))
    lower_block = np.hstack((-np.conj(B), np.conj(A)))
    H = np.vstack((upper_block, lower_block))

    return H


def compute_eigenvalues_by_ensemble(matrix, ensemble_type=None):
    eigenvalues = np.linalg.eigvalsh(matrix)
    # For GSE matrices, eigenvalues come in degenerate pairs due to Kramers degeneracy
    if ensemble_type == 'GSE':
        eigenvalues = np.sort(eigenvalues)[::2]
    return eigenvalues


def calculate_level_spacings(eigenvalues):
    eigenvalues_sorted = np.sort(eigenvalues)
    spacings = np.diff(eigenvalues_sorted)
    return spacings[spacings > 1e-12]


def semicircular_density(x):
    density = np.zeros_like(x, dtype=float)
    support_mask = np.abs(x) <= 2
    density[support_mask] = np.sqrt(4.0 - x[support_mask] ** 2) / (2.0 * np.pi)
    return density


def semicircular_cumulative(x):
    cdf = np.zeros_like(x, dtype=float)
    cdf[x >= 2] = 1
    cdf[x <= -2] = 0
    support_mask = np.abs(x) <= 2
    x_support = x[support_mask]
    cdf[support_mask] = (0.5 + (np.arcsin(x_support / 2) + x_support * np.sqrt(4 - x_support ** 2) / 4) / np.pi)
    return cdf


def unfold_eigenvalues(eigenvalues):
    size = len(eigenvalues)
    return size * semicircular_cumulative(eigenvalues)


def wigner_surmise_goe(spacing):
    return 0.5 * np.pi * spacing * np.exp(-0.25 * np.pi * spacing ** 2)


def wigner_surmise_gue(spacing):
    return (32 / np.pi ** 2) * spacing ** 2 * np.exp(-4 * spacing ** 2 / np.pi)


def wigner_surmise_gse(spacing):
    A4 = 2 ** 18 / (3 ** 6 * np.pi ** 3)
    return A4 * spacing ** 4 * np.exp(-64 * spacing ** 2 / (9 * np.pi))


def generate_spectral_density_data(ensemble_type, matrix_sizes, num_samples):
    generate_ensembles = {
        'GOE': create_goe_matrix,
        'GUE': create_gue_matrix,
        'GSE': create_gse_matrix,
    }
    generate_matrix = generate_ensembles[ensemble_type]

    density_data = {}
    for size in matrix_sizes:
        eigen_values = [
            compute_eigenvalues_by_ensemble(generate_matrix(size), ensemble_type)
            for _ in range(num_samples)
        ]
        density_data[size] = np.concatenate(eigen_values)

    return density_data
