"""Render CT overlays and report segmentation components; no accuracy claims."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from scipy import ndimage


def component_summary(data, affine):
    rows = []
    voxel_volume = float(abs(np.linalg.det(affine[:3, :3])))
    regions = ndimage.find_objects(data.astype(np.uint8), max_label=24)
    for label, region in enumerate(regions, 1):
        if region is None:
            continue
        components, count = ndimage.label(data[region] == label)
        sizes = np.bincount(components.ravel())[1:]
        largest = int(np.argmax(sizes)) + 1
        centroid = np.asarray(ndimage.center_of_mass(components == largest))
        centroid += [part.start for part in region]
        rows.append({
            'label': label, 'component_count': int(count),
            'component_voxels': sorted(map(int, sizes), reverse=True),
            'voxel_volume_mm3': voxel_volume,
            'largest_centroid_ras_mm': nib.affines.apply_affine(affine, centroid).tolist(),
        })
    return rows


def review_case(ct_path, label_path, output):
    ct_img = nib.load(ct_path)
    label_img = nib.load(label_path)
    if ct_img.shape != label_img.shape or not np.allclose(ct_img.affine, label_img.affine):
        raise ValueError('CT and segmentation geometry differ')
    labels = np.asarray(label_img.dataobj)
    if not set(np.unique(labels)).issubset(set(range(25))):
        raise ValueError('Unexpected vertebra label values')
    rows = component_summary(labels, label_img.affine)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'components.json').write_text(json.dumps(rows, indent=2))
    ct_img = nib.as_closest_canonical(ct_img)
    label_img = nib.as_closest_canonical(label_img)
    ct = np.asarray(ct_img.dataobj)
    labels = np.asarray(label_img.dataobj)
    spacing = ct_img.header.get_zooms()[:3]
    if rows:
        world_centers = np.array([row['largest_centroid_ras_mm'] for row in rows])
        center = np.median(nib.affines.apply_affine(np.linalg.inv(ct_img.affine), world_centers), axis=0)
    else:
        center = np.array(ct.shape) / 2
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    for axis in range(2):
        for column, offset_mm in enumerate([-10, 0, 10]):
            index = int(np.clip(round(center[axis] + offset_mm / spacing[axis]), 0, ct.shape[axis] - 1))
            image_slice = np.take(ct, index, axis=axis).T
            label_slice = np.take(labels, index, axis=axis).T
            remaining = [dimension for dimension in range(3) if dimension != axis]
            aspect = spacing[remaining[1]] / spacing[remaining[0]]
            panel = axes[axis, column]
            panel.imshow(image_slice, cmap='gray', vmin=-200, vmax=700, origin='lower', aspect=aspect)
            panel.imshow(np.ma.masked_equal(label_slice, 0), cmap='turbo', vmin=1, vmax=24,
                         alpha=0.45, interpolation='nearest', origin='lower', aspect=aspect)
            panel.set_title(f'{"Sagittal" if axis == 0 else "Coronal"}, {offset_mm:+d} mm')
            panel.axis('off')
    fig.suptitle(f'{ct_path.parent.name}: CT with vertebra labels (review only)')
    fig.tight_layout()
    fig.savefig(output / 'overlays.png', dpi=180)
    plt.close(fig)
    print(ct_path.parent.name, [(r['label'], r['component_voxels'][:4]) for r in rows])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ct-root', type=Path, required=True)
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for label_path in sorted(args.predictions.glob('*/combined_labels.nii.gz')):
        case = label_path.parent.name
        review_case(args.ct_root / case / 'ct.nii.gz', label_path, args.output / case)
