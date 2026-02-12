#!/usr/bin/env python3
"""
Controlled MMIO read script for MT7927-class devices.

Default mode is read-only and file-based: given a sysfs resource file or a
pre-collected mmapable path, it emits a JSON dump of selected offsets.

Usage:
  python mmio_dump.py --resource /sys/bus/pci/devices/0000:01:00.0/resource0 \\
                      --offsets 0x0,0x10,0x14 --width 4 --count 4

Flags:
  --unsafe       Allow /dev/mem mapping (read-only) when --phys-base is used.
  --resource     Path to PCI resource (preferred, read-only).
  --phys-base    Physical base address (hex) for /dev/mem mapping (requires --unsafe).
  --offsets      Comma-separated hex offsets to read (default: 0x0).
  --width        Access width in bytes (1,2,4) default 4.
  --count        Number of sequential reads per offset (default: 1).
  --output       Optional JSON output path.

No writes are performed. Use --unsafe deliberately; the default uses only safe
resources that the kernel exposes read-only.
"""

from __future__ import annotations

import argparse
import json
import mmap
import os
import sys
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Read-only MMIO dump for MT7927")
    p.add_argument("--resource", help="PCI resource file (preferred, read-only)")
    p.add_argument("--phys-base", help="Physical base address for /dev/mem mapping (hex)")
    p.add_argument("--unsafe", action="store_true", help="Permit /dev/mem mapping (read-only)")
    p.add_argument("--offsets", default="0x0", help="Comma-separated hex offsets")
    p.add_argument("--width", type=int, default=4, choices=(1, 2, 4), help="Access width in bytes")
    p.add_argument("--count", type=int, default=1, help="Sequential reads per offset")
    p.add_argument("--output", help="Write JSON to file")
    return p.parse_args()


def read_resource(path: Path, offsets, width: int, count: int):
    results = []
    with path.open("rb") as f:
        for off in offsets:
            f.seek(off)
            for i in range(count):
                data = f.read(width)
                results.append({"offset": hex(off + i * width), "value": data.hex()})
    return results


def read_dev_mem(phys_base: int, offsets, width: int, count: int):
    devmem = Path("/dev/mem")
    if not devmem.exists():
        raise FileNotFoundError("/dev/mem not available")
    results = []
    with devmem.open("rb") as f:
        # map a conservative 4KB window
        mm = mmap.mmap(f.fileno(), length=0x1000, offset=phys_base, access=mmap.ACCESS_READ)
        for off in offsets:
            for i in range(count):
                start = off + i * width
                mm.seek(start)
                data = mm.read(width)
                results.append({"offset": hex(start), "value": data.hex()})
        mm.close()
    return results


def main():
    args = parse_args()
    offsets = [int(x, 16) for x in args.offsets.split(",") if x]

    if args.phys_base and not args.unsafe:
        sys.exit("--unsafe required for /dev/mem mapping")

    records = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "resource": args.resource,
        "phys_base": args.phys_base,
        "unsafe": bool(args.unsafe),
        "width": args.width,
        "count": args.count,
        "reads": [],
    }

    try:
        if args.resource:
            records["reads"] = read_resource(Path(args.resource), offsets, args.width, args.count)
        elif args.phys_base:
            records["reads"] = read_dev_mem(int(args.phys_base, 16), offsets, args.width, args.count)
        else:
            sys.exit("Specify --resource (preferred) or --phys-base with --unsafe")
    except Exception as exc:  # noqa: BLE001
        records["error"] = str(exc)

    out_json = json.dumps(records, indent=2)
    if args.output:
        Path(args.output).write_text(out_json)
    print(out_json)


if __name__ == "__main__":
    main()
