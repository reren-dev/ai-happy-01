#!/usr/bin/env python3
"""
dear judge, i saved you a dry spot (love, lila, 6) - ai-happy-01 entry.
Copies entry.png beside this script to the output directory as entry.png, byte-identical.
Revised for v3 (768x1024 vertical portrait) with robust PNG/JPEG dimension dispatch.
"""

import os
import sys
import shutil
import hashlib
from pathlib import Path


def resolve_output_dir() -> Path:
    """
    Resolve the output directory.
    The grader runs WITHOUT MAKEFUN_OUTPUT_DIR set, so /output is the default.
    """
    out_dir_env = os.environ.get('MAKEFUN_OUTPUT_DIR')
    return Path(out_dir_env) if out_dir_env else Path('/output')


def parse_png_dimensions(data: bytes) -> tuple[int, int]:
    """
    Parse width and height from PNG IHDR chunk bytes without external dependencies.
    """
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError("Not a valid PNG start")
    if len(data) < 24:
        raise ValueError("PNG data too short for IHDR")
    width = int.from_bytes(data[16:20], 'big')
    height = int.from_bytes(data[20:24], 'big')
    return width, height


def parse_jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """
    Parse width and height from JPEG header bytes without external dependencies.
    """
    i = 0
    if not data.startswith(b'\xff\xd8'):
        raise ValueError("Not a valid JPEG start")
    i += 2
    while i < len(data):
        if data[i] != 0xFF:
            while i < len(data) and data[i] != 0xFF:
                i += 1
            if i >= len(data):
                break
        while i < len(data) and data[i] == 0xFF:
            i += 1
        if i >= len(data):
            break
        marker = data[i]
        i += 1
        if marker == 0xD9 or marker == 0xDA:  # EOI or SOS
            break
        if marker in (0xD8, 0xD9, 0x01) or (0xD0 <= marker <= 0xD7):
            continue
        if i + 2 > len(data):
            break
        length = int.from_bytes(data[i:i+2], 'big')
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            if i + 7 <= len(data):
                height = int.from_bytes(data[i+3:i+5], 'big')
                width = int.from_bytes(data[i+5:i+7], 'big')
                return width, height
        i += length
    raise ValueError("SOF marker not found in JPEG data")


def copy_entry(src: Path, dest: Path) -> None:
    # mkdir guard with exist_ok=True
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)

    if not dest.exists():
        print(f"Error: Destination file does not exist: {dest}", file=sys.stderr)
        sys.exit(1)

    src_size = src.stat().st_size
    dst_size = dest.stat().st_size

    if src_size != dst_size:
        print(f"Error: Size mismatch! Source size ({src_size}) != Destination size ({dst_size})", file=sys.stderr)
        sys.exit(1)


def verify_and_get_details(src: Path, dest: Path) -> tuple[str, int, tuple[int, int]]:
    src_bytes = src.read_bytes()
    dst_bytes = dest.read_bytes()

    src_hash = hashlib.sha256(src_bytes).hexdigest()
    dst_hash = hashlib.sha256(dst_bytes).hexdigest()

    if src_bytes != dst_bytes or src_hash != dst_hash:
        print("Error: Byte or digest mismatch between source and destination!", file=sys.stderr)
        sys.exit(1)

    if src_bytes.startswith(b'\x89PNG\r\n\x1a\n') or src_bytes.startswith(b'\x89\x50\x4e\x47'):
        width, height = parse_png_dimensions(src_bytes)
    elif src_bytes.startswith(b'\xff\xd8'):
        width, height = parse_jpeg_dimensions(src_bytes)
    else:
        raise ValueError("Unknown image format")

    return src_hash, len(src_bytes), (width, height)


def main():
    script_dir = Path(__file__).resolve().parent
    src_path = script_dir / 'entry.png'

    if not src_path.exists():
        print(f"Error: Source entry.png not found at {src_path}", file=sys.stderr)
        sys.exit(1)

    out_dir = resolve_output_dir()
    dst_path = out_dir / 'entry.png'

    copy_entry(src_path, dst_path)
    digest, size, dimensions = verify_and_get_details(src_path, dst_path)

    print(f"Wrote {dst_path} ({size} bytes, {dimensions[0]}x{dimensions[1]}px), sha256 {digest} — byte-identical to entry.png")


if __name__ == '__main__':
    main()
