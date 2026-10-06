import nibabel as nib
import numpy as np
import pytest
from postprocessing_vertebrae import refine_volume, process_case, NAMES


def test_removes_small_distant_island_but_preserves_nearby_fragment():
    data = np.zeros((40, 12, 12), dtype=np.uint8)
    data[2:7, 2:7, 2:7] = 24
    data[9, 3, 3] = 24
    data[30:32, 3, 3] = 24
    refined, changes = refine_volume(data, np.diag([-3, 1, 1, 1]))
    assert refined[9, 3, 3] == 24
    assert not refined[30:32, 3, 3].any()
    assert np.count_nonzero(refined == 24) == 126
    assert changes[0]['removed_voxels'] == 2
    assert np.array_equal(data[30:32, 3, 3], [24, 24])


def test_large_fragments_and_diagonal_connections_are_preserved():
    data = np.zeros((40, 12, 12), dtype=np.uint8)
    data[1:4, 1:4, 1:4] = 1
    data[4, 4, 4] = 1
    data[30:33, 1:4, 1:4] = 1
    refined, changes = refine_volume(data, np.eye(4))
    assert np.array_equal(refined, data)
    assert changes == []


def test_remote_wrong_label_is_reassigned_only_with_unambiguous_contact():
    data = np.zeros((80, 12, 12), dtype=np.uint8)
    data[1:5, 2:6, 2:6] = 18
    data[65:69, 2:6, 2:6] = 9
    data[69, 3:5, 3:5] = 18
    refined, changes = refine_volume(data, np.eye(4))
    assert np.all(refined[69, 3:5, 3:5] == 9)
    assert np.count_nonzero(refined) == np.count_nonzero(data)
    assert changes[0]['target_label'] == 9
    assert np.array_equal(refine_volume(refined, np.eye(4))[0], refined)
    data[70:74, 2:6, 2:6] = 10
    ambiguous, _ = refine_volume(data, np.eye(4))
    assert not ambiguous[69, 3:5, 3:5].any()


def test_physical_gap_changes_with_spacing_and_empty_is_valid():
    data = np.zeros((25, 5, 5), dtype=np.uint8)
    data[1:4, 1:4, 1:4] = 2
    data[15, 2, 2] = 2
    fine, _ = refine_volume(data, np.diag([0.5, 1, 1, 1]), max_gap_mm=10)
    coarse, _ = refine_volume(data, np.eye(4), max_gap_mm=10)
    assert fine[15, 2, 2] == 2
    assert coarse[15, 2, 2] == 0
    empty = np.zeros((3, 3, 3), dtype=np.uint8)
    assert np.array_equal(refine_volume(empty, np.eye(4))[0], empty)
    assert np.array_equal(refine_volume(coarse, np.eye(4), max_gap_mm=10)[0], coarse)
    with pytest.raises(ValueError):
        refine_volume(np.full((3, 3, 3), 25), np.eye(4))


def test_saved_geometry_and_individual_masks_are_consistent(tmp_path):
    source = tmp_path / 'source'
    destination = tmp_path / 'destination'
    source.mkdir()
    data = np.zeros((40, 8, 8), dtype=np.uint8)
    data[1:4, 1:4, 1:4] = 5
    data[30, 2, 2] = 5
    affine = np.array([[-2, 0, 0, 80], [0, 1.2, 0, -20], [0, 0, 2.5, 10], [0, 0, 0, 1]])
    image = nib.Nifti1Image(data, affine)
    image.set_qform(affine, 1)
    image.set_sform(affine, 2)
    nib.save(image, source / 'combined_labels.nii.gz')
    process_case(source, destination)
    result = nib.load(destination / 'combined_labels.nii.gz')
    values = np.asarray(result.dataobj)
    assert result.shape == data.shape and np.allclose(result.affine, affine)
    assert result.header['qform_code'] == 1 and result.header['sform_code'] == 2
    for label, name in enumerate(NAMES, 1):
        mask = nib.load(destination / 'segmentations' / f'vertebrae_{name}.nii.gz')
        assert np.allclose(mask.affine, affine)
        assert np.array_equal(np.asarray(mask.dataobj), values == label)
