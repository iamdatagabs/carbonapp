import numpy as np
import pandas as pd
import pytest
from carbonapp.preprocessing import MSCTransformer, SNVTransformer, SavitzkyGolayTransformer
from carbonapp.preprocessing_comparison import nested_preprocessing_comparison

def synthetic_frame(n_groups=12, repeats=2, n_features=12):
    rng = np.random.default_rng(19)
    rows = []
    for group in range(n_groups):
        latent = rng.normal(size=n_features)
        for repeat in range(repeats):
            spectrum = (0.04 + np.linspace(0, 0.01, n_features) + latent*0.001)*(1+0.08*group)
            row = {"Indice": len(rows), "Amostra": group//3,
                "Profundidade": "A" if repeat == 0 else "B", "Sample Number": f"S{group}",
                "TOC": float(8+2*latent[0]-latent[1]+rng.normal(0, 0.05)),
                "N": float(0.5+latent[0]*0.1)}
            row.update({f"r{1100+2*i}": float(spectrum[i]) for i in range(n_features)})
            rows.append(row)
    return pd.DataFrame(rows)

def test_snv_centers_and_scales_each_spectrum():
    x = np.array([[1.,2.,3.,4.],[4.,6.,8.,10.]])
    out = SNVTransformer().fit_transform(x)
    assert np.allclose(out.mean(axis=1), 0)
    assert np.allclose(out.std(axis=1, ddof=1), 1)

def test_msc_reference_is_learned_from_fit_rows():
    x = np.array([[1.,2.,3.,4.],[2.,4.,6.,8.],[3.,6.,9.,12.]])
    transformer = MSCTransformer().fit(x[:2])
    assert np.allclose(transformer.reference_, x[:2].mean(axis=0))
    assert np.isfinite(transformer.transform(x[2:])).all()

def test_savgol_derivative_is_finite_and_scaled_by_nm():
    x = np.tile(np.linspace(0, 1, 12), (3,1))
    out = SavitzkyGolayTransformer(window_length=7, polyorder=2, deriv=1).fit_transform(x)
    assert np.isfinite(out).all()
    assert np.allclose(out[:,3:-3], 1/11/2, atol=1e-6)

def test_nested_comparison_produces_oof_and_fold_baseline():
    result = nested_preprocessing_comparison(synthetic_frame(), outer_splits=3, inner_splits=2,
        preprocessing_methods=("raw","snv"), models=("bayesian_ridge","elastic_net"), k=6)
    assert set(result["preprocessing"]) == {"raw","snv"}
    assert len(result["preprocessing"]["raw"]["predictions"]) == 24
    assert len(result["preprocessing"]["snv"]["folds"]) == 3
    assert np.isfinite(result["fold_specific_mean_baseline"]["metrics"]["rmse"])

def test_invalid_savgol_window_rejected():
    with pytest.raises(ValueError, match="odd"):
        SavitzkyGolayTransformer(window_length=6).fit(np.ones((3,12)))
