# Method and assumptions

The input is a combined NIfTI label map, not model probabilities. Each positive label represents one vertebra. The largest 26-connected component provides a spatial reference for that label; it is assumed to contain the main prediction for that vertebra.

## Component selection

A secondary component becomes a candidate when both conditions hold:

- its voxel count is at most 10% of the main component's count;
- its minimum distance to any main-component voxel center exceeds 50 mm.

Voxel coordinates are transformed with the full affine before a nearest-neighbor query. This handles anisotropic spacing, axis flips, rotation, and shear without treating voxel indices as physical distances. The distance is between voxel centers rather than continuous voxel surfaces.

The 10% and 50 mm thresholds are conservative choices made after inspecting two cases. They were not optimized on a labeled validation set. The ratio preserves large disconnected fragments, and the gap protects nearby fragments. Neither condition guarantees that a selected component is an error.

## Removal and relabeling

All candidate islands are temporarily removed. A one-voxel 26-connected neighborhood identifies contact with retained labels. A neighboring label is plausible only when its main component is within 20 mm of the candidate. With exactly one plausible label, the candidate is reassigned to it. With zero or multiple plausible labels, it remains background.

All decisions use the same retained-label volume and are applied afterward. No region growing, morphological filling, or changes to originally empty voxels occur.

## Output contract

The processor writes the combined map and regenerates all 24 binary masks from it. It copies the input affine, qform/sform matrices and codes, and writes uint8 masks. Every corrected component has a source label, target label, voxel count, physical gap, and world-coordinate centroid in the JSON report.

The input and output case directories must differ. The baseline remains available for comparison.

The separate overlay review utility uses 6-connected components for descriptive summaries. Its component counts differ from the 26-connected components used by the refinement algorithm and change reports.

## Failure cases

- A large false-positive component can become the spatial reference.
- Large remote false positives remain because of the size safeguard.
- A genuine disconnected bone fragment can be removed.
- Ambiguous removal can create missing bone.
- Touching an incorrect neighboring prediction can produce an incorrect reassignment.
- Nearby wrong labels, partial volumes, anatomical variation, numbering errors, and missing vertebrae are not resolved.

The processor is a research heuristic. The two-case result record is not clinical validation.
