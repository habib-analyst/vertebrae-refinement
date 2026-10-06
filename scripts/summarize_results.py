"""Export numerical summaries and a chart from postprocessing reports."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    rows = []
    for path in sorted(args.predictions.glob("*/postprocessing_report.json")):
        report = json.loads(path.read_text())
        # Publish numerical changes without CT images or spatial coordinates.
        for change in report["components_changed"]:
            change.pop("centroid_ras_mm", None)
        assert sum(c["removed_voxels"] for c in report["components_changed"]) == report["removed_voxels"]
        assert sum(c["relabelled_voxels"] for c in report["components_changed"]) == report["relabelled_voxels"]
        rows.append(report)
    if not rows:
        parser.error("No postprocessing reports found")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "changes.json").write_text(json.dumps(rows, indent=2) + "\n")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    x = list(range(len(rows)))
    for ax, unit in zip(axes, ("voxels", "components")):
        if unit == "voxels":
            removed = [r["removed_voxels"] for r in rows]
            reassigned = [r["relabelled_voxels"] for r in rows]
        else:
            removed = [sum(c["target_label"] == 0 for c in r["components_changed"]) for r in rows]
            reassigned = [sum(c["target_label"] != 0 for c in r["components_changed"]) for r in rows]
        bars1 = ax.bar([v - .19 for v in x], removed, .36, label="Removed", color="#2563a6")
        bars2 = ax.bar([v + .19 for v in x], reassigned, .36, label="Reassigned", color="#c7792a")
        ax.bar_label(bars1, padding=4)
        ax.bar_label(bars2, padding=4)
        ax.set_xticks(x, [r["case"].replace("BDMAP_", "Case ") for r in rows])
        ax.set_ylabel("Number of " + unit)
        ax.set_title("Changed " + unit)
        ax.set_ylim(0, max(removed + reassigned) * 1.22)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=.15)
        ax.set_axisbelow(True)
    axes[0].legend(frameon=False)
    fig.suptitle("Vertebrae Refinement • measured changes", fontsize=17, fontweight="bold")
    fig.text(.5, .025, "Two CT volumes; segmentation accuracy was not measured.", ha="center", color="#52525b")
    fig.tight_layout(rect=(0, .065, 1, .92))
    fig.savefig(args.output / "measured_changes.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
