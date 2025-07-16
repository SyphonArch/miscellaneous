#!/usr/bin/env python3
"""
Batch-fill missing creation dates for images/videos.

Phases:
1. Scan and report statistics.
2. Dry run: preview files that would be modified.
3. On confirmation, write timestamps extracted from filenames.

Requires: exiftool (on PATH), tqdm (Python package)
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
from tqdm import tqdm

# ---- CONFIGURATION ----
IMAGE_EXT = {".jpg", ".jpeg", ".heic", ".heif", ".png"}
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".avi", ".hevc"}

DATE_TAGS = [
    "DateTimeOriginal",
    "CreateDate",
    "MediaCreateDate",
    "TrackCreateDate",
    "QuickTime:CreateDate",
]

def extract_timestamp_from_name(name: str) -> str | None:
    dt = None

    # YYYYMMDD_HHMMSS or YYYYMMDD-HHMMSS
    m = re.search(r"(\d{4})(\d{2})(\d{2})[_-](\d{2})(\d{2})(\d{2})", name)
    if m:
        y, mth, d, H, M, S = map(int, m.groups())
        try:
            dt = datetime(y, mth, d, H, M, S)
        except ValueError:
            return None

    # YYYY_MM_DD HH_MM or similar (space separator, HH_MM format)
    elif m := re.search(r"(\d{4})[_-](\d{2})[_-](\d{2})[ _](\d{2})[_-](\d{2})", name):
        y, mth, d, H, M = map(int, m.groups())
        try:
            dt = datetime(y, mth, d, H, M, 0)
        except ValueError:
            return None

    # YYYY-MM-DD HH.MM.SS
    elif m := re.search(r"(\d{4})-(\d{2})-(\d{2})[ ](\d{2})\.(\d{2})\.(\d{2})", name):
        y, mth, d, H, M, S = map(int, m.groups())
        try:
            dt = datetime(y, mth, d, H, M, S)
        except ValueError:
            return None

    # YYYYMMDDHHMMSS
    elif m := re.search(r"(?<!\d)(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(?!\d)", name):
        y, mth, d, H, M, S = map(int, m.groups())
        try:
            dt = datetime(y, mth, d, H, M, S)
        except ValueError:
            return None

    # Standalone YYYYMMDD
    elif m := re.search(r"(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)", name):
        y, mth, d = map(int, m.groups())
        try:
            dt = datetime(y, mth, d, 12, 0, 0)
        except ValueError:
            return None

    # 13-digit Unix timestamp (milliseconds)
    elif m := re.search(r"(?<!\d)(\d{13})(?!\d)", name):
        try:
            ts = int(m.group(1)) // 1000
            dt = datetime.utcfromtimestamp(ts)
        except Exception:
            return None

    if dt and 1995 <= dt.year <= 2026:
        return dt.strftime("%Y:%m:%d %H:%M:%S")
    return None


def metadata_present(path: Path) -> bool:
    try:
        res = subprocess.run(
            ["exiftool", "-json", "-n", *[f"-{t}" for t in DATE_TAGS], str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        info = json.loads(res.stdout or "[]")[0] if res.stdout else {}
        for tag in DATE_TAGS:
            val = info.get(tag)
            if isinstance(val, str):
                try:
                    dt = datetime.strptime(val, "%Y:%m:%d %H:%M:%S")
                    if 1995 <= dt.year <= 2026:
                        return True
                except ValueError:
                    continue
        return False
    except Exception:
        return False


def write_date(path: Path, dt: str) -> None:
    subprocess.run(
        ["exiftool", f"-AllDates={dt}", "-overwrite_original", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def scan_folder(root: Path) -> dict:
    stats = {
        "photo": Counter(),
        "video": Counter(),
    }
    print(f"🔍 Scanning folder: {root}")

    missing_files: dict[str, list[tuple[Path, str]]] = defaultdict(list)
    unfixable_files: list[tuple[str, Path]] = []

    media_files = [
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXT.union(VIDEO_EXT)
    ]

    print(f"📂 Scanning {len(media_files)} media files...")
    for p in tqdm(media_files, desc="Scanning", unit="file"):
        ext = p.suffix.lower()
        cls = "photo" if ext in IMAGE_EXT else "video"

        stats[cls]["total"] += 1

        if metadata_present(p):
            stats[cls]["with_date"] += 1
        else:
            stats[cls]["no_date"] += 1
            ts = extract_timestamp_from_name(p.name)
            if ts:
                stats[cls]["name_has_date"] += 1
                missing_files[cls].append((p, ts))
            else:
                unfixable_files.append((cls, p))

    return {
        "stats": stats,
        "missing_files": missing_files,
        "unfixable_files": unfixable_files,
    }


def pct(part: int, total: int) -> str:
    return f"{(part / total * 100):5.1f}%" if total else " 0.0%"


def print_report(stats: dict[str, Counter]) -> None:
    for cls in ("photo", "video"):
        s = stats[cls]
        total = s["total"]
        without_fix = s["no_date"] - s["name_has_date"]
        print(f"\n--- {cls.upper()}S ---")
        print(f"Total files             : {total}")
        print(f"With metadata           : {s['with_date']}  ({pct(s['with_date'], total)})")
        print(f"Without metadata        : {s['no_date']}  ({pct(s['no_date'], total)})")
        print(f"  └─ filename has date  : {s['name_has_date']}  ({pct(s['name_has_date'], total)})")
        print(f"  └─ cannot be corrected: {without_fix}  ({pct(without_fix, total)})")
    print("\n📊 Statistics complete. No changes have been made yet.")


def dry_run_preview(missing_files: dict[str, list[tuple[Path, str]]], unfixable_files: list[tuple[str, Path]]):
    total_fixable = sum(len(v) for v in missing_files.values())

    if not total_fixable and not unfixable_files:
        print("\n✅ No files need updating.")
        return

    if unfixable_files:
        print(f"\n🚫 {len(unfixable_files)} files cannot be corrected (no metadata and no date in filename):")
        for cls, path in unfixable_files:
            print(f"[{cls}] {path}")

    if total_fixable:
        print(f"\n🧪 Dry run: {total_fixable} files would be updated:")
        for cls in ("photo", "video"):
            for path, dt in missing_files[cls]:
                print(f"[{cls}] {path} → {dt}")


def write_phase(missing_files: dict[str, list[tuple[Path, str]]]):
    all_to_fix = [(cls, path, dt) for cls, files in missing_files.items() for (path, dt) in files]
    print(f"\n✍️ Writing metadata to {len(all_to_fix)} files...\n")
    for cls, path, dt in tqdm(all_to_fix, desc="Writing", unit="file"):
        write_date(path, dt)
    print("\n✅ Completed writing metadata.")


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: adddate.py /path/to/media_root")

    root = Path(sys.argv[1]).expanduser()
    if not root.is_dir():
        sys.exit("❌ Provided path is not a directory.")

    results = scan_folder(root)
    print_report(results["stats"])
    dry_run_preview(results["missing_files"], results["unfixable_files"])

    proceed = input("\nDo you want to proceed and write the above dates? [y/N] ").lower().strip()
    if proceed != "y":
        print("❎ Aborted. No files were modified.")
        return

    write_phase(results["missing_files"])


if __name__ == "__main__":
    main()
