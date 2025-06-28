#!/usr/bin/env python3
"""Rename image files based on EXIF time and orientation.

This module exposes :func:`rename_files` which accepts a list of image paths and
returns the names of the newly created files.  When run directly it mimics the
behaviour of the original ``pic-new`` perl script.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Sequence


def read_exif_datetime(path: Path) -> datetime | None:
    """Return the EXIF creation time of *path* if available."""
    try:
        result = subprocess.run(
            ["exiftags", "-i", "-s:", str(path)],
            text=True,
            capture_output=True,
            check=True,
        )
    except Exception:
        return None
    prefix = "Image Created:"
    for line in result.stdout.splitlines():
        if line.startswith(prefix):
            date_str = line[len(prefix) :].strip()
            return parse_exif_time(date_str)
    return None


def parse_exif_time(date_str):
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def check_orientation(path: Path) -> bool:
    """Return ``True`` if ``jhead`` reports an Orientation field."""
    try:
        result = subprocess.run(
            ["jhead", str(path)],
            text=True,
            capture_output=True,
            check=True,
        )
    except Exception:
        return False
    return any("Orientation" in line for line in result.stdout.splitlines())


def do_move(
    src: Path, dest: Path, backup: Path, rotate: bool, dryrun: bool
) -> None:
    """Move ``src`` to ``dest`` optionally rotating the image."""
    if not rotate:
        cmd = ["mv", "-i", str(src), str(dest)]
        if dryrun:
            print(" ".join(cmd))
        else:
            subprocess.run(cmd, check=True)
        return

    cmd_backup = ["mv", "-i", str(src), str(backup)]
    cmd_transform = ["exiftran", "-a", str(backup), "-o", str(dest)]
    if dryrun:
        print(" ".join(cmd_backup))
        print(" ".join(cmd_transform))
        print(f"rm {backup}")
        return

    print(f"{src} ==> {dest} ...")
    if dest.exists() or backup.exists():
        print("    File already exists, skipping!")
        return
    subprocess.run(cmd_backup, check=True)
    subprocess.run(cmd_transform, check=True)
    backup.unlink()


def rename_xmp(src: Path, dest: Path, dryrun: bool) -> List[str]:
    """Rename the sidecar XMP for *src* if present."""
    xmp_src = src.with_name(src.name + ".xmp")
    if not xmp_src.exists():
        return []
    xmp_dest = dest.with_name(dest.name + ".xmp")
    do_move(xmp_src, xmp_dest, Path("/"), rotate=False, dryrun=dryrun)
    return [str(xmp_dest)]


def rename_files(
    files: Sequence[str],
    offset_hours: float = 0.0,
    dryrun: bool = False,
    no_rotate: bool = False,
) -> List[str]:
    """Rename ``files`` returning the new filenames."""
    tz_offset = timedelta(hours=offset_hours)
    created: List[str] = []
    for src_name in files:
        src = Path(src_name)
        # Sequence number derived from the file name only, not full path
        seq = re.sub(r"[^0-9]", "", src.stem)

        dt = read_exif_datetime(src)
        if dt is None:
            print("No EXIF creation date.")
            dt = datetime.fromtimestamp(src.stat().st_mtime)

        mtime = dt + tz_offset
        if (
            mtime - datetime(1970, 1, 1)
        ).total_seconds() < 3600 * 24 * 365 * 15:
            print(
                "EXIF data isn't believable ({}).  Using file date.".format(
                    int((mtime - datetime(1970, 1, 1)).total_seconds())
                )
            )
            mtime = datetime.fromtimestamp(src.stat().st_mtime) + tz_offset

        base = f"{mtime:%Y%m%d-%H%M%S}-{seq}"
        dest = src.with_name(base).with_suffix(".jpg")
        backup = dest.with_name(dest.name + f".orig-{int(time.time())}")

        orientation = check_orientation(src)
        do_move(
            src,
            dest,
            backup,
            rotate=not (no_rotate or not orientation),
            dryrun=dryrun,
        )
        created.append(str(dest))
        created += rename_xmp(src, dest, dryrun)

        canon_base = src.with_suffix("")
        canon_raw = canon_base.with_suffix(".CR2")
        if canon_raw.exists():
            linux_raw = dest.with_suffix(".cr2")
            do_move(
                canon_raw, linux_raw, Path("/"), rotate=False, dryrun=dryrun
            )
            created.append(str(linux_raw))
            created += rename_xmp(canon_raw, linux_raw, dryrun)

        fuji_raw = canon_base.with_suffix(".RAF")
        if fuji_raw.exists():
            linux_raw = dest.with_suffix(".raf")
            do_move(
                fuji_raw, linux_raw, Path("/"), rotate=False, dryrun=dryrun
            )
            created.append(str(linux_raw))
            created += rename_xmp(fuji_raw, linux_raw, dryrun)

    return created


def main():
    parser = argparse.ArgumentParser(
        description="Rename and rotate images using EXIF info."
    )
    parser.add_argument(
        "--time", type=float, default=0.0, help="Offset time in hours"
    )
    parser.add_argument(
        "--nr",
        dest="no_rotate",
        action="store_true",
        help="Don't rotate images",
    )
    parser.add_argument(
        "--dryrun", action="store_true", help="Just print what would be done"
    )
    parser.add_argument("images", nargs="+", help="Images to process")
    args = parser.parse_args()

    new_files = rename_files(
        args.images,
        offset_hours=args.time,
        dryrun=args.dryrun,
        no_rotate=args.no_rotate,
    )
    for name in new_files:
        print(name)


if __name__ == "__main__":
    main()
