import numpy as np
import pandas as pd
import pytest

from carbonapp.profile import build_profile_3d_payload, build_profile_summary, build_vertical_profile


def profile_frame():
    rows = []
    for point in (1, 2):
        for depth, value in zip("ABCDEFGHI", range(1, 10)):
            for repeat in (1, 2):
                rows.append({
                    "Indice": len(rows), "Amostra": point, "Profundidade": depth,
                    "Sample Number": f"P{point}-{depth}",
                    "TOC": float(value + point), "N": float(value / 10),
                    "r1100": float(value), "r1102": float(value + 0.1),
                })
    return pd.DataFrame(rows)


def test_vertical_profile_preserves_real_layer_thicknesses_and_missingness():
    frame = profile_frame()
    frame = frame[~((frame.Amostra == 1) & (frame.Profundidade == "D"))]
    result = build_vertical_profile(frame, 1)
    assert [(x["top_cm"], x["bottom_cm"]) for x in result["layers"]] == [
        (0,10),(10,20),(20,40),(40,60),(60,80),(80,100),(100,130),(130,160),(160,200)
    ]
    assert result["layers"][3]["value"] is None


def test_summary_weights_sampling_points_equally():
    result = build_profile_summary(profile_frame())
    assert result.loc[result.code == "A", "n_points"].iloc[0] == 2
    assert result.loc[result.code == "A", "mean"].iloc[0] == 2.5


def test_3d_payload_uses_categorical_points_and_negative_depth():
    result = build_profile_3d_payload(profile_frame())
    assert result["point_ids"] == ["1", "2"]
    assert min(result["z"]) < 0
    assert "not geographic" in result["spatial_warning"]


def test_unknown_point_raises():
    with pytest.raises(KeyError):
        build_vertical_profile(profile_frame(), 999)


def test_profile_rejects_conflicting_reference_values_within_sample_number():
    frame = profile_frame()
    frame.loc[1, "TOC"] += 1
    with pytest.raises(ValueError, match="invariant"):
        build_profile_summary(frame)


def test_profile_rejects_sample_number_reused_across_layers():
    frame = profile_frame()
    frame.loc[frame.index[-1], "Sample Number"] = frame.loc[0, "Sample Number"]
    with pytest.raises(ValueError, match="multiple sampling points or depth layers"):
        build_profile_summary(frame)
