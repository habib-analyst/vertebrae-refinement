# Recorded results

The experiment used two CT volumes from the upstream demo and the supplied vertebrae checkpoint. The pretrained model was used as supplied; no model training or fine-tuning was performed.

| Case | Original CT shape | Spacing, mm | Removed components | Reassigned components | Removed voxels | Reassigned voxels |
|---|---|---|---:|---:|---:|---:|
| BDMAP_00000006 | 512 × 512 × 391 | 0.78125 × 0.78125 × 2.5 | 3 | 0 | 480 | 0 |
| BDMAP_00000031 | 512 × 512 × 1394 | 0.9140625 × 0.9140625 × 0.7 | 4 | 7 | 711 | 187 |

In the first case, cervical-label islands appeared near a femur, approximately 590–625 mm from their corresponding main masks. In the second, distant wrong labels occurred on thoracic fragments and outside the main spine region. CT overlay inspection informed the conservative component-selection rule.

The output audit verified original CT shape and affine, valid labels, consistency between combined maps and all 24 binary masks per case, preservation of originally empty voxels, and agreement between recorded and actual changes. The two combined maps and 48 binary masks were checked locally. The stored records in `results/` contain the measured voxel counts and component changes.

Seven tests cover anisotropic spacing, diagonal connections, preservation of nearby and large fragments, unambiguous and ambiguous contact, empty input, invalid labels, idempotence on fixtures, output geometry, and consistency of binary masks. These are software checks, not measures of segmentation accuracy.

All seven tests passed locally on Windows with Python 3.14. The published verification utility also passed against both full-sized output volumes. Hosted GitHub Actions execution has not yet completed successfully. Additional local Python 3.11 and 3.12 checks were blocked by Windows Application Control before tests could execute; compatibility on those versions remains unverified.

There are no vertebra ground-truth masks for these cases. No Dice scores, benchmark ranking, statistical significance, or clinical benefit is reported. Boundary and nearby-label errors remain. The experiment has not established performance across other scans, acquisition protocols, or pathologies.
