"""Fold-safe preprocessing transformers for NIR spectra."""
import numpy as np
from scipy.signal import savgol_filter
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_array, check_is_fitted

class SNVTransformer(BaseEstimator, TransformerMixin):
    """Standard normal variate correction, independently per spectrum."""
    def fit(self, X, y=None):
        check_array(X, dtype=float)
        return self
    def transform(self, X):
        x = check_array(X, dtype=float, copy=True)
        sd = x.std(axis=1, ddof=1, keepdims=True)
        sd[sd < 1e-12] = 1.0
        return (x - x.mean(axis=1, keepdims=True)) / sd

class MSCTransformer(BaseEstimator, TransformerMixin):
    """MSC against a mean reference spectrum learned from training rows only."""
    def fit(self, X, y=None):
        x = check_array(X, dtype=float)
        self.reference_ = x.mean(axis=0)
        self.centered_reference_ = self.reference_ - self.reference_.mean()
        self.reference_ss_ = float(self.centered_reference_ @ self.centered_reference_)
        if self.reference_ss_ < 1e-12:
            raise ValueError("MSC reference spectrum has near-zero variance")
        return self
    def transform(self, X):
        check_is_fitted(self, "reference_")
        x = check_array(X, dtype=float, copy=True)
        out = np.empty_like(x)
        ref = self.reference_
        rc = self.centered_reference_
        for i, row in enumerate(x):
            slope = float((row-row.mean()) @ rc / self.reference_ss_)
            if abs(slope) < 1e-12:
                raise ValueError("MSC encountered a near-zero fitted slope")
            intercept = float(row.mean() - slope * ref.mean())
            out[i] = (row-intercept) / slope
        return out

class SavitzkyGolayTransformer(BaseEstimator, TransformerMixin):
    """Savitzky-Golay smoothing or derivative applied row-wise."""
    def __init__(self, window_length=9, polyorder=2, deriv=0, delta=2.0):
        self.window_length, self.polyorder = window_length, polyorder
        self.deriv, self.delta = deriv, delta
    def fit(self, X, y=None):
        x = check_array(X, dtype=float)
        if self.window_length % 2 != 1:
            raise ValueError("window_length must be odd")
        if self.window_length > x.shape[1] or self.polyorder >= self.window_length:
            raise ValueError("Invalid Savitzky-Golay window or polynomial order")
        if not 0 <= self.deriv <= self.polyorder or self.delta <= 0:
            raise ValueError("Invalid derivative order or wavelength spacing")
        return self
    def transform(self, X):
        x = check_array(X, dtype=float)
        return savgol_filter(x, self.window_length, self.polyorder, deriv=self.deriv,
                             delta=self.delta, axis=1, mode="interp")

def build_preprocessor(name):
    if name == "raw":
        from sklearn.preprocessing import FunctionTransformer
        return FunctionTransformer(validate=True)
    if name == "snv":
        return SNVTransformer()
    if name == "msc":
        return MSCTransformer()
    if name == "savgol_smooth":
        return SavitzkyGolayTransformer(deriv=0)
    if name == "savgol_first_derivative":
        return SavitzkyGolayTransformer(deriv=1)
    raise ValueError(f"Unsupported preprocessing strategy: {name}")
