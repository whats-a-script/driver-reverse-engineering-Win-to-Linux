#!/usr/bin/env python3
"""
Read-only DMA descriptor pattern probe for MT7927.

Default mode scans a provided binary capture (e.g., /proc/kcore slice or
fpga/logic-analyzer dump) for likely DMA descriptors. No writes occur.

Usage:
  python dma_probe.py --input capture.bin --stride 16 --pattern 7927 --output report.json

Optional live scan:
  python dma_probe.py --devmem 0x40000000 --length 0x10000 --unsafe
This uses /dev/mem read-only and requires root plus --unsafe.
"""

from __future__ import annotations

import argparse
import json
import mmap
from datetime import datetime
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="MT7927 DMA descriptor probe (read-only)")
    p.add_argument("--input", help="Path to memory dump or capture file")
    p.add_argument("--pattern", default="7927", help="Hex pattern to look for (default: 7927)")
    p.add_argument("--stride", type=int, default=16, help="Stride to sample when scanning input")
    p.add_argument("--limit", type=int, default=256, help="Max matches to record")
    p.add_argument("--devmem", help="Physical base for /dev/mem scan (hex)")
    p.add_argument("--length", type=lambda x: int(x, 0), default=0x1000, help="Length to map from /dev/mem")
    p.add_argument("--unsafe", action="store_true", help="Permit /dev/mem read-only mapping")
    p.add_argument("--output", help="Write JSON findings to file")
    return p.parse_args()


def scan_bytes(data: bytes, pattern: bytes, stride: int, limit: int):
    hits = []
    plen = len(pattern)
    for idx in range(0, len(data) - plen, stride):
        if data[idx : idx + plen] == pattern:
            hits.append(idx)
            if len(hits) >= limit:
                break
    return hits


def main():
    args = parse_args()
    if args.devmem and not args.unsafe:
        raise SystemExit("--unsafe required for /dev/mem scanning")
    if not args.input and not args.devmem:
        raise SystemExit("Provide --input file or --devmem address")

    pattern = bytes.fromhex(args.pattern)
    hits = []
    source = None

    if args.input:
        blob = Path(args.input).read_bytes()
        hits = scan_bytes(blob, pattern, args.stride, args.limit)
        source = args.input
    elif args.devmem:
        import os

        devmem = Path("/dev/mem")
        if not devmem.exists():
            raise SystemExit("/dev/mem not available")
        base = int(args.devmem, 16)
        with devmem.open("rb") as f:
            mm = mmap.mmap(f.fileno(), length=args.length, offset=base, access=mmap.ACCESS_READ)
            data = mm[:]
            hits = scan_bytes(data, pattern, args.stride, args.limit)
            mm.close()
        source = f"/dev/mem@0x{base:x}+0x{args.length:x}"

    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": source,
        "unsafe": bool(args.unsafe),
        "pattern_hex": args.pattern,
        "stride": args.stride,
        "limit": args.limit,
        "hits": hits,
    }

    out = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(out)
    print(out)


if __name__ == "__main__":
    main()
