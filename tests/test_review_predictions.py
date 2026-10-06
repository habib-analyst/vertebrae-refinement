import numpy as np
from review_predictions import component_summary


def test_components_report_physical_volumes_and_world_centroid():
    data = np.zeros((10, 10, 10), dtype=np.uint8)
    data[1:4, 2:5, 3:6] = 1
    data[8, 8, 8] = 1
    affine = np.diag([-2., 3., -4., 1.])
    affine[:3, 3] = [20., 30., 40.]
    row = component_summary(data, affine)[0]
    assert row['label'] == 1
    assert row['component_voxels'] == [27, 1]
    assert np.isclose(row['voxel_volume_mm3'], 24)
    assert np.allclose(row['largest_centroid_ras_mm'], [16., 39., 24.])


def test_empty_volume_has_no_components():
    assert component_summary(np.zeros((3, 3, 3)), np.eye(4)) == []
