"""Remove or relabel small vertebra components far from their main component.

Dependencies: numpy, scipy, nibabel. Run:
python postprocessing_vertebrae.py --input BASELINE --output AbdomenAtlasDemoPredict

Use the largest 26-connected component as the reference for each label. Select
secondary components no larger than 10% of that reference and over 50 mm away.
Relabel a selected component if it touches one retained label whose reference
component is within 20 mm; otherwise set it to background. Leave other voxels
unchanged. This does not fix missing bone, boundaries, or vertebral numbering.
"""
import argparse
import json
from pathlib import Path

import nibabel as nib
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

NAMES = ['L5', 'L4', 'L3', 'L2', 'L1'] + [f'T{i}' for i in range(12, 0, -1)] + [f'C{i}' for i in range(7, 0, -1)]


def refine_volume(data, affine, max_gap_mm=50.0, max_fraction=0.1):
    if data.ndim != 3 or not np.isin(data, np.arange(25)).all():
        raise ValueError('Expected a 3D integer label volume with values 0 through 24')
    if max_gap_mm <= 0 or not 0 < max_fraction < 1:
        raise ValueError('Gap must be positive and fraction must lie between 0 and 1')
    refined = data.astype(np.uint8, copy=True)
    changes = []
    anchors = {}
    candidates = []
    for label, region in enumerate(ndimage.find_objects(refined, max_label=24), 1):
        if region is None:
            continue
        components, count = ndimage.label(refined[region] == label, np.ones((3, 3, 3)))
        sizes = np.bincount(components.ravel())[1:]
        largest = int(np.argmax(sizes)) + 1
        origin = np.array([part.start for part in region])
        anchor = np.argwhere(components == largest) + origin
        tree = cKDTree(nib.affines.apply_affine(affine, anchor))
        anchors[label] = tree
        for component, size in enumerate(sizes, 1):
            if component == largest or size > max_fraction * sizes[largest - 1]:
                continue
            points = np.argwhere(components == component) + origin
            world = nib.affines.apply_affine(affine, points)
            distance = float(tree.query(world)[0].min())
            if distance > max_gap_mm:
                refined[tuple(points.T)] = 0
                candidates.append((label, points, world, distance))
    # Remove all candidate islands before checking contact with retained labels.
    # Apply relabeling after all contact decisions to avoid order-dependent results.
    decisions = []
    for label, points, world, distance in candidates:
        lower = np.maximum(points.min(axis=0) - 1, 0)
        upper = np.minimum(points.max(axis=0) + 2, data.shape)
        region = tuple(slice(a, b) for a, b in zip(lower, upper))
        local = np.zeros(tuple(upper - lower), dtype=bool)
        local[tuple((points - lower).T)] = True
        contact = ndimage.binary_dilation(local, structure=np.ones((3, 3, 3))) & ~local
        neighbors = np.unique(refined[region][contact])
        plausible = [int(other) for other in neighbors if other not in (0, label)
                     and anchors[int(other)].query(world)[0].min() <= 20.0]
        target = plausible[0] if len(plausible) == 1 else 0
        decisions.append((points, target))
        changes.append({'label': label, 'name': NAMES[label - 1],
                        'target_label': target, 'changed_voxels': len(points),
                        'removed_voxels': len(points) if target == 0 else 0,
                        'relabelled_voxels': len(points) if target else 0,
                        'gap_mm': distance, 'centroid_ras_mm': world.mean(axis=0).tolist()})
    for points, target in decisions:
        refined[tuple(points.T)] = target
    return refined, changes


def process_case(source, destination, max_gap_mm=50.0, max_fraction=0.1):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError('Use a separate output directory to preserve the baseline')
    image = nib.load(source / 'combined_labels.nii.gz')
    data = np.asarray(image.dataobj)
    refined, changes = refine_volume(data, image.affine, max_gap_mm, max_fraction)
    (destination / 'segmentations').mkdir(parents=True, exist_ok=True)

    def save(values, path):
        result = nib.Nifti1Image(values.astype(np.uint8), image.affine, image.header.copy())
        result.set_qform(image.get_qform(), int(image.header['qform_code']))
        result.set_sform(image.get_sform(), int(image.header['sform_code']))
        nib.save(result, path)

    save(refined, destination / 'combined_labels.nii.gz')
    for label, name in enumerate(NAMES, 1):
        save(refined == label, destination / 'segmentations' / f'vertebrae_{name}.nii.gz')
    report = {'case': source.name, 'shape': list(image.shape),
              'parameters': {'max_gap_mm': max_gap_mm, 'max_fraction': max_fraction},
              'removed_voxels': int(sum(row['removed_voxels'] for row in changes)),
              'relabelled_voxels': int(sum(row['relabelled_voxels'] for row in changes)),
              'removed_volume_mm3': float(sum(row['removed_voxels'] for row in changes) * abs(np.linalg.det(image.affine[:3, :3]))),
              'components_changed': changes}
    (destination / 'postprocessing_report.json').write_text(json.dumps(report, indent=2))
    print(source.name, 'removed', report['removed_voxels'], 'and relabelled', report['relabelled_voxels'], 'voxels in', len(changes), 'remote components', flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-gap-mm', type=float, default=50.0)
    parser.add_argument('--max-fraction', type=float, default=0.1)
    args = parser.parse_args()
    cases = sorted(args.input.glob('*/combined_labels.nii.gz'))
    if not cases:
        parser.error('No case directories containing combined_labels.nii.gz found')
    for path in cases:
        process_case(path.parent, args.output / path.parent.name, args.max_gap_mm, args.max_fraction)
