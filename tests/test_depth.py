from carbonapp.depth import DEPTH_PROFILE, depth_metadata, validate_depth_profile


def test_depth_profile_covers_zero_to_two_hundred_cm():
    validate_depth_profile()
    assert DEPTH_PROFILE[0].top_cm == 0
    assert DEPTH_PROFILE[-1].bottom_cm == 200
    assert [item.code for item in DEPTH_PROFILE] == list("ABCDEFGHI")
    assert [item.thickness_cm for item in DEPTH_PROFILE] == [10, 10, 20, 20, 20, 20, 30, 30, 40]


def test_depth_metadata_contains_midpoints():
    metadata = depth_metadata()
    assert metadata[0]["midpoint_cm"] == 5
    assert metadata[-1]["midpoint_cm"] == 180
