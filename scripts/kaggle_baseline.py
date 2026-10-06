"""Run pinned SuPreM vertebrae inference on Kaggle and verify baseline masks."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time
import urllib.request
import zipfile

REVISION = "7583213147e33daf2031cc0a3ad30faa516f4f64"
work = Path("/kaggle/working")
temp = Path("/kaggle/temp/vertebrae_refinement")
temp.mkdir(parents=True, exist_ok=True)
work.mkdir(parents=True, exist_ok=True)
repo = temp / "SuPreM"
predictions = work / "AbdomenAtlasDemoPredictBaseline"
started = time.time()
os.environ['MPLBACKEND'] = 'Agg'

def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)

def download(url, path):
    if not path.exists():
        print("Downloading", url, flush=True)
        urllib.request.urlretrieve(url, path)
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

run([sys.executable, "-m", "pip", "install", "--quiet", "uv"])
environment = temp / "env"
run(["uv", "venv", "--python", "3.10", str(environment)])
python = str(environment / "bin" / "python")
run(["uv", "pip", "install", "--python", python, "torch==2.2.2",
     "--index-url", "https://download.pytorch.org/whl/cu121"])
run(["uv", "pip", "install", "--python", python, "numpy==1.26.4",
     "monai==0.9.0", "nibabel", "scipy", "einops", "connected-components-3d",
     "fastremap", "h5py", "pandas", "matplotlib", "tqdm", "opencv-python-headless<4.12"])
if not repo.exists():
    run(["git", "clone", "https://github.com/MrGiovanni/SuPreM.git", str(repo)])
run(["git", "checkout", REVISION], cwd=repo)
archive = temp / "AbdomenAtlasDemo.tar.gz"
checkpoint = temp / "swin_unetr_totalsegmentator_vertebrae.pth"
hashes = {
    "ct_archive": download("https://www.cs.jhu.edu/~zongwei/dataset/AbdomenAtlasDemo.tar.gz", archive),
    "checkpoint": download("https://www.cs.jhu.edu/~zongwei/model/swin_unetr_totalsegmentator_vertebrae.pth", checkpoint),
}
if not (temp / "AbdomenAtlasDemo").exists():
    with tarfile.open(archive) as bundle:
        bundle.extractall(temp, filter="data")
ct_root = temp / "AbdomenAtlasDemo"
cases = sorted(p.parent.name for p in ct_root.glob("*/ct.nii.gz"))
assert cases, "No CT cases found"
print("CT cases:", cases, flush=True)

# A fresh process uses the installed NumPy version. Keep upstream source unchanged.
bootstrap = '''
import gc, runpy, torch
from model.SwinUNETR_target import SwinUNETR
assert torch.cuda.is_available(), "Kaggle GPU must be enabled"
print("GPU:", torch.cuda.get_device_name(0), "torch:", torch.__version__, flush=True)
original_load = torch.load
def trusted_load(*args, **kwargs):
    kwargs.setdefault("weights_only", False)
    return original_load(*args, **kwargs)
torch.load = trusted_load
model = SwinUNETR(img_size=(96,96,96), in_channels=1, out_channels=25, feature_size=48)
state = torch.load(CHECKPOINT, map_location="cpu")["net"]
state = {".".join(key.split(".")[1:]): value for key, value in state.items()}
model.load_state_dict(state, strict=True)
print("Checkpoint: every parameter loaded", flush=True)
del model, state
gc.collect()
runpy.run_path("inference.py", run_name="__main__")
'''.replace("CHECKPOINT", repr(str(checkpoint)))
run([python, "-u", "-c", bootstrap, "--save_dir", str(predictions),
     "--checkpoint", str(checkpoint), "--data_root_path", str(ct_root),
     "--customize", "--device", "cpu"], cwd=repo / "direct_inference")

verification = '''
import json, pathlib, nibabel as nib, numpy as np
rows = []
names = ["L5","L4","L3","L2","L1"] + [f"T{i}" for i in range(12,0,-1)] + [f"C{i}" for i in range(7,0,-1)]
for case in CASES:
    ct = nib.load(str(CT_ROOT / case / "ct.nii.gz"))
    labels = nib.load(str(PRED / case / "combined_labels.nii.gz"))
    assert labels.shape == ct.shape, (case, "shape mismatch")
    assert np.allclose(labels.affine, ct.affine), (case, "affine mismatch")
    data = np.asarray(labels.dataobj)
    assert set(np.unique(data)).issubset(set(range(25))), (case, "invalid labels")
    counts = {}
    for label, name in enumerate(names, 1):
        mask = nib.load(str(PRED / case / "segmentations" / f"vertebrae_{name}.nii.gz"))
        assert mask.shape == ct.shape and np.allclose(mask.affine, ct.affine)
        binary = np.asarray(mask.dataobj)
        assert np.array_equal(binary, data == label), (case, name, "inconsistent mask")
        counts[name] = int(np.count_nonzero(binary))
    rows.append({"case":case, "shape":list(ct.shape), "voxel_counts":counts})
OUTPUT.write_text(json.dumps(rows, indent=2))
print("Verified CT geometry and 24 individual masks for every case", flush=True)
'''
verification = ("from pathlib import Path\nCT_ROOT=Path(" + repr(str(ct_root)) + ")\nPRED=Path(" + repr(str(predictions)) + ")\nOUTPUT=Path(" + repr(str(work / "baseline_verification.json")) + ")\nCASES=" + repr(cases) + "\n" + verification)
run([python, "-u", "-c", verification])
with zipfile.ZipFile(work / "baseline_predictions.zip", "w", zipfile.ZIP_DEFLATED) as bundle:
    for path in predictions.rglob("*.nii.gz"):
        bundle.write(path, path.relative_to(work))
(work / "baseline_provenance.json").write_text(json.dumps({
    "revision": REVISION, "sha256": hashes, "cases": cases,
    "elapsed_seconds": time.time() - started,
    "status": "baseline inference only; refinement and visual review still required",
}, indent=2))
print("BASELINE COMPLETE. Refinement is still required.", flush=True)
