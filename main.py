from utils import ensure_images_directory, run_ensemble_analysis, run_spectral_evolution_analysis


def config():
    return {
        'matrix_size': 32,
        'num_samples': 50000,
        'batch_size': 512,
        'ensembles': ['GOE', 'GUE', 'GSE'],
        'spectral_matrix_sizes': [1, 2, 4, 8, 16, 32],
        'bins': 128,
        'linspace': 2500,
    }


def main():
    cfg = config()
    images_dir = ensure_images_directory()

    run_ensemble_analysis(cfg, images_dir)
    run_spectral_evolution_analysis(cfg, images_dir)


if __name__ == '__main__':
    main()
