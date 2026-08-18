import pytest

from scripts.validate_3d_navigability import affine_map_to_prefab_local_xz


@pytest.fixture
def synthetic_mapping():
    return {
        "map_bounds_min_x": 10.0,
        "map_bounds_min_y": -20.0,
        "map_bounds_size_x": 40.0,
        "map_bounds_size_y": 80.0,
        "terrain_size_x": 100.0,
        "terrain_size_z": 200.0,
        "terrain_prefab_local_x": -3.0,
        "terrain_prefab_local_z": 7.0,
    }


def test_affine_mapping_maps_source_bounds_to_terrain_extents(synthetic_mapping):
    assert affine_map_to_prefab_local_xz(synthetic_mapping, 10.0, -20.0) == (-3.0, 7.0)
    assert affine_map_to_prefab_local_xz(synthetic_mapping, 50.0, 60.0) == (97.0, 207.0)


def test_affine_mapping_preserves_fractional_position(synthetic_mapping):
    assert affine_map_to_prefab_local_xz(synthetic_mapping, 20.0, 40.0) == pytest.approx(
        (22.0, 157.0)
    )
