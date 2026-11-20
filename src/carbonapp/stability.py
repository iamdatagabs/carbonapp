"""Repeated grouped-resampling stability of within-depth NIR band selection."""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.model_selection import GroupShuffleSplit
from .data import spectral_columns, validate_dataset

def within_depth_feature_selection_stability(frame, target="TOC", group_column="Amostra", n_resamples=100, test_size=0.25, k=40, random_state=42):
    """Select bands after training-only depth centering in repeated group splits."""
    validate_dataset(frame)
    if target not in ("TOC","N"): raise ValueError("target must be TOC or N")
    if group_column not in frame: raise ValueError(f"Missing group column: {group_column}")
    if n_resamples < 2: raise ValueError("n_resamples must be >= 2")
    if not 0 < test_size < 1: raise ValueError("test_size must be between 0 and 1")
    if k < 1: raise ValueError("k must be >= 1")
    bands=spectral_columns(frame)
    keys=[group_column,"Profundidade"]
    if group_column=="Sample Number": keys.insert(1,"Amostra")
    data=frame.groupby(keys,as_index=False,sort=False).agg({**{b:"mean" for b in bands},target:"mean"})
    groups=data[group_column].to_numpy()
    if pd.Series(groups).nunique()<4: raise ValueError("At least 4 independent groups are required")
    x=data[bands].astype(float).to_numpy(); y=data[target].astype(float).to_numpy()
    depth=data["Profundidade"].astype(str).to_numpy()
    splitter=GroupShuffleSplit(n_splits=n_resamples,test_size=test_size,random_state=random_state)
    counts=np.zeros(len(bands),dtype=int); ranks_total=np.zeros(len(bands),dtype=float)
    for train_idx,_ in splitter.split(x,y,groups):
        xt=x[train_idx].copy(); yt=y[train_idx].copy(); dt=depth[train_idx]
        for layer in np.unique(dt):
            mask=dt==layer; xt[mask]-=xt[mask].mean(axis=0); yt[mask]-=yt[mask].mean()
        selector=SelectKBest(f_regression,k=min(k,len(bands))).fit(xt,yt)
        counts+=selector.get_support().astype(int)
        scores=np.nan_to_num(selector.scores_,nan=0.0,posinf=0.0,neginf=0.0)
        order=np.argsort(-scores,kind="stable"); ranks=np.empty(len(bands)); ranks[order]=np.arange(1,len(bands)+1)
        ranks_total+=ranks
    out=pd.DataFrame({"band":bands,"wavelength_nm":[int(b[1:]) for b in bands],"selected_resamples":counts,"selection_frequency":counts/n_resamples,"mean_rank":ranks_total/n_resamples,"n_resamples":n_resamples,"group_column":group_column,"target":target})
    return out.sort_values(["selection_frequency","mean_rank","wavelength_nm"],ascending=[False,True,True]).reset_index(drop=True)
