import os

import matplotlib.pyplot as plt
import numpy as np

from equations import compute_eigenvalues_by_ensemble, unfold_eigenvalues, calculate_level_spacings, create_goe_matrix, wigner_surmise_goe, wigner_surmise_gue, create_gue_matrix, create_gse_matrix, wigner_surmise_gse, semicircular_density, \
    generate_spectral_density_data


def ensure_images_directory():
    path = './images'
    os.makedirs(path, exist_ok=True)
    return path


def normalize_spacings(spacings):
    return spacings / np.mean(spacings), np.mean(spacings)


def process_matrix_batch(generator_func, size, batch_size):
    return [generator_func(size) for _ in range(batch_size)]


def analyze_spacing_distribution(matrices, ensemble_type=None):
    spacings = []

    for matrix in matrices:
        eigenvalues = compute_eigenvalues_by_ensemble(matrix, ensemble_type)
        unfolded = unfold_eigenvalues(eigenvalues)
        spacings.extend(calculate_level_spacings(unfolded))

    spacings = np.asarray(spacings)
    norm, mean = normalize_spacings(spacings)
    return dict(raw_spacings=spacings, normalized_spacings=norm, mean_spacing=mean)


def get_ensemble_properties(ensemble_type):
    return {
        'GOE': dict(beta=1, generator=create_goe_matrix, wigner_func=wigner_surmise_goe, color='blue', formula=r'$P_1(s)=\frac{\pi}{2}s\,e^{-\pi s^{2}/4}$'),
        'GUE': dict(beta=2, generator=create_gue_matrix, wigner_func=wigner_surmise_gue, color='red', formula=r'$P_2(s)=\frac{32}{\pi^{2}}s^{2}e^{-4s^{2}/\pi}$'),
        'GSE': dict(beta=4, generator=create_gse_matrix, wigner_func=wigner_surmise_gse, color='green', formula=r'$P_4(s)=A_4 s^{4}e^{-64s^{2}/9\pi}$')
    }[ensemble_type]


def plot_comparison(ax, data, theory_x, theory_y, color, title, xlabel, ylabel, xlim, cfg):
    ax.hist(data, bins=cfg['bins'], density=True, alpha=0.7, color=color, edgecolor='black', linewidth=0.5)
    ax.plot(theory_x, theory_y, 'k-', linewidth=3)
    ax.set(title=title, xlabel=xlabel, ylabel=ylabel, xlim=xlim)
    ax.grid(alpha=0.3)


def visualize_analysis(results, ensemble_type, cfg):
    props = get_ensemble_properties(ensemble_type)
    s_th = np.linspace(0, 5, cfg['linspace'])
    x_th = np.linspace(-3, 3, cfg['linspace'])

    spacing = analyze_spacing_distribution(results['matrices'], ensemble_type)

    figure, axes = plt.subplots(1, 2, figsize=(12, 5))
    figure.suptitle(f'{ensemble_type} Random-Matrix Analysis (Beta={props["beta"]})', fontweight='bold')

    plot_comparison(axes[0], spacing['normalized_spacings'], s_th, props['wigner_func'](s_th),
                    props['color'], f'{ensemble_type}: {props["formula"]}',
                    r'Normalised spacing $s/\langle s\rangle$', 'P(s)', (0, 5), cfg)

    plot_comparison(axes[1], results['eigenvalues'], x_th, semicircular_density(x_th), props['color'],
                    r'Wigner semicircle $\rho(x)=\frac{1}{2\pi}\sqrt{4-x^{2}}$', r'$\lambda$',
                    r'$\rho(\lambda)$', (-3, 3), cfg)

    axes[1].text(0.02, 0.98, f'mean = {results["eigenvalues"].mean():.3f}\nσ² = {results["eigenvalues"].var():.3f}',
                 transform=axes[1].transAxes, va='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    plt.tight_layout()
    return figure, spacing


def visualize_spectral_density_evolution(cfg):
    print('\nAnalyzing Spectral Densities of Ensembles.')
    sizes = cfg['spectral_matrix_sizes']
    num_samples = cfg['num_samples']
    ensembles = cfg['ensembles']
    bins = cfg['bins']

    columns = 3
    rows = (len(sizes) + columns - 1) // columns

    figure, axes = plt.subplots(rows, columns, figsize=(15, 5 * rows))
    axes = np.atleast_2d(axes).reshape(rows, columns)
    figure.suptitle('Spectral Density Across Symmetric Matrix Sizes', fontsize=18, fontweight='bold')

    for ensemble in ensembles:
        props = get_ensemble_properties(ensemble)
        data = generate_spectral_density_data(ensemble, sizes, num_samples)

        for index, matrix_size in enumerate(sizes):
            r, c = divmod(index, columns)
            ax = axes[r, c]
            eigenvalues = data[matrix_size]
            eig_min, eig_max = eigenvalues.min(), eigenvalues.max()
            hist_range = (min(-3, eig_min), max(3, eig_max))
            histogram, edges = np.histogram(eigenvalues, bins=bins, density=True, range=hist_range)
            centres = 0.5 * (edges[:-1] + edges[1:])
            ax.plot(centres, histogram, color=props['color'], lw=2, alpha=0.8, label=ensemble)
            ax.fill_between(centres, 0, histogram, color=props['color'], alpha=0.25)
            ax.set(xlim=(-3, 3), ylim=(0, 0.6), title=f'Matrix Size = {matrix_size}')
            ax.grid(alpha=0.3)

            if index == 0:
                ax.legend(fontsize=9)
            if r == rows - 1:
                ax.set_xlabel('λ')
            if c == 0:
                ax.set_ylabel('ρ(λ)')

    for k in range(len(sizes), rows * columns):
        r, c = divmod(k, columns)
        figure.delaxes(axes[r, c])

    plt.tight_layout()
    return figure


def execute_ensemble_analysis(ensemble_type, cfg, images_dir):
    ensemble_names = {
        'GOE': 'Gaussian Orthogonal Ensemble',
        'GUE': 'Gaussian Unitary Ensemble',
        'GSE': 'Gaussian Symplectic Ensemble',
    }
    print(f'\nAnalyzing {ensemble_names.get(ensemble_type, ensemble_type)}...')
    gen = get_ensemble_properties(ensemble_type)['generator']
    matrix_size = cfg['matrix_size']
    batch_size = cfg['batch_size']
    num_samples = cfg['num_samples']

    matrices, eigenvals = [], []
    batches = num_samples // batch_size

    for i in range(batches):
        batch = process_matrix_batch(gen, matrix_size, batch_size)
        matrices.extend(batch)

        for matrix in batch:
            eigenvals.extend(compute_eigenvalues_by_ensemble(matrix, ensemble_type))

        del batch

    analysis = dict(matrices=matrices, eigenvalues=np.asarray(eigenvals))
    figure, spacing = visualize_analysis(analysis, ensemble_type, cfg)
    save_analysis_plot(figure, ensemble_type, images_dir)
    display_statistical_results(eigenvals, spacing)
    plt.close(figure)
    del matrices
    del analysis


def save_analysis_plot(figure, ensemble_type, images_dir):
    filename = os.path.join(images_dir, f'{ensemble_type}_RMT.png')
    figure.savefig(filename, bbox_inches='tight')
    plt.show()
    print(f'  Saved figure to {filename}')


def display_statistical_results(eigenvalues, spacing):
    mean, variance = np.mean(eigenvalues), np.var(eigenvalues)
    print(f"  Mean Eigenvalue: {mean:.6f} (expected ≈ 0)")
    print(f"  Eigenvalue Variance: {variance:.6f} (expected ≈ 1)")
    print(f"  Mean Level Spacing: {spacing['mean_spacing']:.6f}")
    print(f"  Total Eigenvalues: {len(eigenvalues)}")
    print(f"  Semicircular Convergence: {(1 - abs(variance - 1)) * 100:.1f}%")


def run_ensemble_analysis(cfg, images_dir):
    for ens in cfg['ensembles']:
        execute_ensemble_analysis(ens, cfg, images_dir)


def run_spectral_evolution_analysis(cfg, images_dir):
    figure = visualize_spectral_density_evolution(cfg)
    filename = os.path.join(images_dir, 'Spectral_Density_Evolution.png')
    figure.savefig(filename, bbox_inches='tight')
    plt.show()
    print(f'  Saved figure to {filename}')
