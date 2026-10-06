# Reproduction

## Postprocessing

Install the root requirements and run the standalone processor against combined baseline masks. The processor uses CPU libraries and does not require a GPU. The tested local environment used Python 3.14, NumPy 2.5.3, SciPy 1.18.1, NiBabel 5.4.2, and Matplotlib 3.11.2.

The source code is kept separate from upstream inference. The original inference repository is fetched at commit `7583213147e33daf2031cc0a3ad30faa516f4f64`.

## GPU baseline

Upload or paste `scripts/kaggle_baseline.py` into a Kaggle notebook with GPU acceleration and Internet enabled, then run all cells. The script creates an isolated Python 3.10 environment under temporary storage. It does not replace the notebook's Python runtime.

The recorded baseline used Python 3.10.22, PyTorch 2.2.2+cu121, MONAI 0.9.0, and a Tesla T4. It retained 96³ sliding windows, 75% overlap and 1.5 mm resampling. All 159 checkpoint entries loaded. The script places full-volume aggregation on CPU and sliding-window model execution on GPU.

Expected outputs are two baseline case directories, `baseline_predictions.zip`, `baseline_provenance.json`, and `baseline_verification.json`. The runner verifies shape, affine, label values, and all individual masks before packaging them.

Recorded input CT archive SHA256:

```text
936804a3f371061a13ca71f977396c0480e4e0983db2ad963464d7791104a330
```

Recorded baseline ZIP SHA256:

```text
ca4dbdab19a0a2cf3e25c0d8850f166e0e9ac12674d2243dde1a49465eea1856
```

Checkpoint and demo URLs are upstream-hosted resources. Access and licensing remain subject to their providers' terms. Dependency installation, runtime differences, and external downloads may affect reproduction. Numerical equality across other GPU/software environments has not been established.
