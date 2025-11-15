#!/usr/bin/env python3
import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Select photos based on darktable ratings stored in XMP sidecars.\n"
            "Scans the current directory for *.xmp files."
        )
    )
    parser.add_argument(
        "ratings",
        help=(
            "Comma-separated list of ratings and/or ranges, e.g. "
            "'1,3,5' or '1-3,5'.  Use 'r' for removed / -1."
        ),
    )
    parser.add_argument(
        "-f",
        "--file",
        dest="file_pattern",
        help="Optional regex to match the photo filename (e.g. '^20250411-' or 'jpg').",
    )
    return parser.parse_args()


def parse_ratings(spec: str):
    """
    Parse a rating spec like:
        '1,3,5' or '1-3,5' or '0-5'
    into a set of integers.
    """
    ratings = set()

    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue

        if "-" in part:
            # range like 1-3
            try:
                start_str, end_str = part.split("-", 1)
                start = int(start_str.strip())
                end = int(end_str.strip())
            except ValueError:
                print(f"Invalid rating range: {part!r}", file=sys.stderr)
                sys.exit(1)

            if start > end:
                start, end = end, start

            for r in range(start, end + 1):
                ratings.add(r)
        else:
            # single rating like '3'
            if part == "r":
                ratings.add(-1)
            else:
                try:
                    ratings.add(int(part))
                except ValueError:
                    print(f"Invalid rating value: {part!r}", file=sys.stderr)
                    sys.exit(1)

    if not ratings:
        print("No valid ratings provided.", file=sys.stderr)
        sys.exit(1)

    return ratings


def get_rating_from_xmp(xmp_path: Path):
    """
    Try to extract the rating from a darktable XMP file.
    Returns an int rating or None if not found / parse error.
    """
    try:
        tree = ET.parse(xmp_path)
        root = tree.getroot()
    except ET.ParseError:
        return None

    # 1. Try as an attribute, e.g. xmp:Rating="3"
    for elem in root.iter():
        for key, value in elem.attrib.items():
            if (
                key.endswith("}Rating")
                or key.endswith(":Rating")
                or key == "xmp:Rating"
                or key == "Rating"
            ):
                try:
                    return int(value)
                except ValueError:
                    pass

    # 2. Try as a child element, e.g. <xmp:Rating>3</xmp:Rating>
    for elem in root.iter():
        tag = elem.tag
        if (
            tag.endswith("}Rating")
            or tag.endswith(":Rating")
            or tag == "xmp:Rating"
            or tag == "Rating"
        ):
            if elem.text:
                text = elem.text.strip()
                if text:
                    try:
                        return int(text)
                    except ValueError:
                        pass

    return None


def main():
    args = parse_args()
    wanted_ratings = parse_ratings(args.ratings)

    file_pattern = None
    if args.file_pattern:
        try:
            file_pattern = re.compile(args.file_pattern)
        except re.error as e:
            print(f"Invalid regex for --file: {e}", file=sys.stderr)
            sys.exit(1)

    cwd = Path(os.getcwd())

    for xmp_path in cwd.glob("*.xmp"):
        # Derive the corresponding photo filename first,
        # e.g. 20250411-111016-3393.raf.xmp -> 20250411-111016-3393.raf
        photo_path = xmp_path.with_suffix("")
        photo_name = photo_path.name

        # If a filename pattern is specified, skip early if it doesn't match
        if file_pattern and not file_pattern.search(photo_name):
            continue

        rating = get_rating_from_xmp(xmp_path)
        if rating is None or rating not in wanted_ratings:
            continue

        # Print the matched photo path (not the xmp)
        print(photo_path.as_posix())


if __name__ == "__main__":
    main()
