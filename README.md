# vertebrae-refinement

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)] [![GitHub stars](https://img.shields.io/github/stars/habib-analyst/vertebrae-refinement.svg)]

**Physical-distance postprocessing for vertebra segmentation masks: identify small components far from their assigned vertebra, then remove them or reassign them to a supported neighboring label.**

The contribution is the postprocessing and verification workflow — baseline predictions come from an existing SuPreM/SwinUNETR model; the repo is explicit about what the heuristic fixes and what it leaves behind.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt

# refine a baseline mask set: each case dir must contain combined_labels.nii.gz
# (labels 0-24; 0 = background, 1-24 = L5 to C1)
python postprocessing_vertebrae.py --input predictions_baseline --output predictions_refined
```

Output per case: refined `combined_labels.nii.gz`, a `postprocessing_report.json` recording every change, and all 24 binary vertebra masks.

To verify refined outputs against CTs, baseline masks, and change reports:

```bash
python -m scripts.verify_predictions --ct-root ct_volumes --baseline predictions_baseline \
  --predictions predictions_refined --output results/verification.json
```

## Measured results

Measured on two CT volumes (no reference annotations available, so these are verified change counts — **not** accuracy scores).

| Case | Components changed | Voxels removed | Voxels reassigned |
|---|---|---:|---:|
| BDMAP_00000006 | 3 | 480 | 0 |
| BDMAP_00000031 | 11 | 711 | 187 |
| **Total** | **14** | **1,191** | **187** |

Verification: both output volumes retained the original CT shape and affine; all 48 individual binary masks matched their combined label maps; no background voxels were converted to foreground. Machine-readable record: `results/verification.json`.

| Tests | 7/7 local green (`python -m pytest tests -q`) |

## How it works

1. Find the largest 26-connected component for each vertebra label.
2. Select a secondary component only if it contains at most 10% as many voxels and lies more than 50 mm from the main component.
3. Measure distances in world coordinates using the full NIfTI affine.
4. Reassign the component only if it touches exactly one plausible retained label whose main component is within 20 mm — otherwise remove it.
5. Contact decisions are made before relabeling, avoiding dependence on label processing order.

## Limitations (stated upfront)

- No Dice/sensitivity measured: no vertebra reference annotations were available for these cases.
- The method leaves boundary errors, missing bone, and nearby wrong labels unresolved — see [vertebrae-learned-cleanup](https://github.com/habib-analyst/vertebrae-learned-cleanup), which closes this loop with a measured +22.9pp Dice gain.
- CT scans, model weights, and prediction archives are not in this repo and must be obtained under their applicable terms.

## Sources and license

Baseline model and inference: [SuPreM](https://github.com/MrGiovanni/SuPreM). Demo source: [AbdomenAtlas](https://github.com/MrGiovanni/AbdomenAtlas). Original code here is MIT licensed; upstream code, checkpoints, and datasets keep their own licenses — see `THIRD_PARTY.md`.

---
Built by [Habib Ur Rehman](https://github.com/habib-analyst) · ML/AI Engineer & healthcare-AI researcher ·
[LinkedIn](https://www.linkedin.com/in/hur-dev) · [habib.top](https://habib.top)
