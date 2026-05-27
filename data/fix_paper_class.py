#!/usr/bin/env python3
"""
Fix Paper -> Paper_Cardboard and rebuild splits so paper/cartons are trained.
"""

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.etl_service import ETLService

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
ALIASES = {"Paper": "Paper_Cardboard", "Cardboard": "Paper_Cardboard"}


def move_all_images(src: Path, dest: Path) -> int:
    if not src.exists():
        return 0
    dest.mkdir(parents=True, exist_ok=True)
    moved = 0
    for img in src.rglob("*"):
        if not img.is_file() or img.suffix.lower() not in IMAGE_EXTS:
            continue
        target = dest / img.name
        if target.exists():
            target = dest / f"{moved}_{img.name}"
        shutil.move(str(img), str(target))
        moved += 1
    return moved


def rename_in(root: Path) -> int:
    total = 0
    for alias, canonical in ALIASES.items():
        src = root / alias
        if not src.exists():
            continue
        dest = root / canonical
        n = move_all_images(src, dest)
        total += n
        if src.exists():
            shutil.rmtree(src, ignore_errors=True)
        print(f"  {root.name}/{alias} -> {canonical}: {n} images")
    return total


def count_images(folder: Path) -> int:
    if not folder.exists():
        return 0
    return sum(1 for f in folder.rglob("*") if f.is_file() and f.suffix.lower() in IMAGE_EXTS)


def main():
    project = Path(__file__).parent.parent
    organized = project / "data" / "processed" / "organized"
    processed = project / "data" / "processed"
    raw_rw = project / "data" / "raw" / "RealWaste"

    if not organized.exists() and raw_rw.exists():
        print("Organized data missing — running ETL...")
        import subprocess
        subprocess.check_call([sys.executable, str(project / "data" / "etl.py")])

    if not organized.exists():
        print("ERROR: No data. Place RealWaste in data/raw and run: python data/etl.py")
        sys.exit(1)

    print("Fixing paper folder names...")
    rename_in(organized)

    n_org = count_images(organized / "Paper_Cardboard")
    print(f"Organized Paper_Cardboard: {n_org} images")

    if n_org == 0:
        print("WARNING: No paper images in organized. Re-run: python data/etl.py")
        sys.exit(1)

    splits = processed / "splits"
    if splits.exists():
        shutil.rmtree(splits)

    print("Rebuilding train/val/test splits...")
    stats = ETLService.split_dataset(str(organized), str(processed))
    n_train = stats.get("train", {}).get("Paper_Cardboard", 0)
    print(f"Train Paper_Cardboard: {n_train} images")

    if n_train == 0:
        sys.exit(1)

    print("\nOK! Ab model train karo (zaroori):")
    print("  python data/finetune_model.py --epochs 15")


if __name__ == "__main__":
    main()
