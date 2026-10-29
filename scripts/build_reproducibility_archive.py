"""Create the compact archive requested for repository/DOI deposition."""

from pathlib import Path
import argparse
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "team16_reproducibility_archive.zip"

DIRECTORIES = [
    ROOT / "configs",
    ROOT / "src",
    ROOT / "tests",
    ROOT / "dashboard",
    ROOT / "scripts",
    ROOT / ".streamlit",
    ROOT / "reports" / "metrics",
    ROOT / "reports" / "figures",
]

FILES = [
    ROOT / "README.md",
    ROOT / "REPRODUCIBILITY.md",
    ROOT / "CITATION.cff",
    ROOT / ".zenodo.json",
    ROOT / "requirements.txt",
    ROOT / "requirements-dashboard.txt",
    ROOT / "requirements-lock.txt",
    ROOT / "DASHBOARD_SETUP.md",
    ROOT / "FINAL_CORRECTIONS_UPDATE.md",
    ROOT / "TeamNo_16_23BCT0029_FINAL_CORRECTIONS.docx",
    ROOT / "TeamNo_16_23BCT0029_MINOR_CORRECTIONS_FINAL.docx",
    ROOT / "pytest.ini",
    ROOT / "PROGRESS.md",
    ROOT / "reports" / "data_quality_report.md",
    ROOT / "reports" / "FINAL_PROJECT_REPORT.md",
    ROOT / "data" / "processed" / "integrated_cell_dataset.parquet",
    ROOT / "data" / "processed" / "lagged_cell_dataset.parquet",
    ROOT / "data" / "processed" / "absa_deduplicated_split.parquet",
    ROOT / "data" / "processed" / "heldout_priority_queue.parquet",
]


def should_include(path: Path) -> bool:
    return (path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
            and path.name != "secrets.toml")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    included = set()
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=7) as archive:
        for directory in DIRECTORIES:
            if not directory.exists():
                continue
            for path in directory.rglob("*"):
                if should_include(path):
                    archive.write(path, path.relative_to(ROOT).as_posix())
                    included.add(path.resolve())
        for path in FILES:
            if should_include(path) and path.resolve() not in included:
                archive.write(path, path.relative_to(ROOT).as_posix())

    size_mb = output.stat().st_size / (1024 * 1024)
    print(f"Wrote {output} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()

