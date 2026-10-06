"""Check CT geometry, binary masks, and actual changes against audit reports."""
import argparse
import json
from pathlib import Path

import nibabel as nib
import numpy as np
from postprocessing_vertebrae import NAMES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ct-root', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    paths = sorted(args.predictions.glob('*/combined_labels.nii.gz'))
    if not paths:
        parser.error('No combined label maps found')
    rows = []
    for path in paths:
        case = path.parent.name
        ct = nib.load(args.ct_root / case / 'ct.nii.gz')
        image = nib.load(path)
        baseline = nib.load(args.baseline / case / path.name)
        assert image.shape == baseline.shape == ct.shape, (case, 'shape')
        assert np.allclose(image.affine, ct.affine) and np.allclose(image.affine, baseline.affine), (case, 'affine')
        values = np.asarray(image.dataobj)
        original = np.asarray(baseline.dataobj)
        assert np.isin(values, np.arange(25)).all(), (case, 'label values')
        assert not np.any((original == 0) & (values != 0)), (case, 'background additions')
        counts = {}
        for label, name in enumerate(NAMES, 1):
            mask = nib.load(path.parent / 'segmentations' / f'vertebrae_{name}.nii.gz')
            assert mask.shape == ct.shape and np.allclose(mask.affine, ct.affine), (case, name, 'geometry')
            binary = np.asarray(mask.dataobj)
            assert np.array_equal(binary, values == label), (case, name, 'mask consistency')
            counts[name] = int(np.count_nonzero(binary))
        report = json.loads((path.parent / 'postprocessing_report.json').read_text())
        removed = int(np.count_nonzero((values == 0) & (original != 0)))
        relabelled = int(np.count_nonzero((values != original) & (values != 0)))
        assert removed == report['removed_voxels'], (case, 'removed count')
        assert relabelled == report['relabelled_voxels'], (case, 'relabelled count')
        # Multiple components may have the same source and target: compare their total.
        pairs = {}
        for change in report['components_changed']:
            pair = (change['label'], change['target_label'])
            pairs[pair] = pairs.get(pair, 0) + change['changed_voxels']
        audited = np.zeros(values.shape, dtype=bool)
        for (source, target), expected in pairs.items():
            affected = (original == source) & (values != original) & (values == target)
            assert np.count_nonzero(affected) == expected, (case, source, target, 'change count')
            audited |= affected
        assert np.array_equal(audited, values != original), (case, 'unreported changes')
        rows.append({'case': case, 'shape': list(image.shape), 'removed_voxels': removed,
                     'relabelled_voxels': relabelled, 'all_24_masks_consistent': True,
                     'voxel_counts': counts})
        print(case, 'verified', flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, indent=2) + '\n')


if __name__ == '__main__':
    main()
