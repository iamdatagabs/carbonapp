import numpy as np
import pandas as pd
import pytest
from carbonapp.stability import within_depth_feature_selection_stability

def make_frame(n_groups=20,n_bands=8):
    rng=np.random.default_rng(7); rows=[]
    for group in range(n_groups):
        latent=rng.normal()
        for depth,offset in (("A",5),("B",0),("C",-4)):
            row={"Indice":len(rows),"Amostra":group//2,"Profundidade":depth,"Sample Number":f"S{group}","TOC":float(10+offset+2*latent),"N":float(.5+.1*latent)}
            row.update({f"r{1100+2*i}":float((latent if i==0 else rng.normal())+rng.normal(0,.03)) for i in range(n_bands)})
            rows.append(row)
    return pd.DataFrame(rows)

def test_stability_reports_frequency():
    out=within_depth_feature_selection_stability(make_frame(),n_resamples=12,k=3)
    assert len(out)==8 and out.selection_frequency.between(0,1).all()
    assert out.selected_resamples.max()<=12 and set(out.group_column)=={"Amostra"}

def test_invalid_resample_count():
    with pytest.raises(ValueError,match="n_resamples"):
        within_depth_feature_selection_stability(make_frame(),n_resamples=1)
