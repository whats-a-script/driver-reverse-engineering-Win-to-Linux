#!/usr/bin/env bash
# Read-only PCI BAR sweep for MT7927-class devices.
# Defaults to safe mode; optional /dev/mem peek requires --unsafe.
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bar_sweep.sh [--device <pci_id>] [--output <path>] [--unsafe]
  --device   PCI identifier (e.g., 0000:01:00.0). Defaults to first Mediatek wireless device found.
  --output   Path to write JSON log (created if missing). Defaults to stdout only.
  --unsafe   Enable /dev/mem read-only peek of BAR regions (first 256 bytes). Off by default.

Actions (read-only):
  1) lspci -nn scan to locate Mediatek MT79xx/MT7927 devices
  2) Parse BAR regions from `lspci -vv`
  3) Optional /dev/mem read of each BAR when --unsafe is used

No writes are performed. Use sudo for --unsafe /dev/mem access.
USAGE
}

DEVICE=""
OUTPUT=""
UNSAFE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --device) DEVICE="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --unsafe) UNSAFE=1; shift 1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

if ! command -v lspci >/dev/null 2>&1; then
  echo "lspci not found" >&2
  exit 1
fi

timestamp() { date -Iseconds; }

find_device() {
  lspci -nn | grep -Ei "mediatek|mt79" | head -n1 | awk '{print $1}'
}

if [[ -z "$DEVICE" ]]; then
  DEVICE=$(find_device || true)
fi

RAW=""
if [[ -n "$DEVICE" ]]; then
  RAW=$(lspci -s "$DEVICE" -vv 2>/dev/null || true)
fi

parse_bars() {
  python - <<'PY'
import json, re, sys
raw=sys.stdin.read()
bars=[]
for line in raw.splitlines():
    m=re.search(r'Region\s+(\d+):\s+Memory at ([0-9a-fA-F]+).*\[size=([0-9a-fA-Fx]+)\]', line)
    if m:
        bars.append({"bar": int(m.group(1)), "base": f"0x{m.group(2)}", "size": m.group(3)})
json.dump(bars, sys.stdout)
PY
}

BAR_JSON=$(printf "%s" "$RAW" | parse_bars)

PREVIEWS="{}"
if [[ $UNSAFE -eq 1 && -n "$DEVICE" ]]; then
  PREVIEWS=$(python - <<PY
import json, subprocess
bars=json.loads('''$BAR_JSON''')
out={}
for entry in bars:
    base=int(entry["base"],16)
    try:
        data=subprocess.check_output(["sudo","dd","if=/dev/mem","bs=1","count=64",f"skip={base}"], stderr=subprocess.DEVNULL)
        out[f"bar_{entry['bar']}_preview"]=data.hex()
    except Exception:
        out[f"bar_{entry['bar']}_preview"]="unavailable"
print(json.dumps(out))
PY
)
fi

LOG_JSON=$(python - <<PY
import json
from datetime import datetime
log={
    "timestamp": datetime.utcnow().isoformat()+"Z",
    "device": """$DEVICE""",
    "unsafe": bool($UNSAFE),
    "bars": json.loads('''$BAR_JSON'''),
    "previews": json.loads('''$PREVIEWS'''),
}
print(json.dumps(log, indent=2))
PY
)

if [[ -n "$OUTPUT" ]]; then
  echo "$LOG_JSON" > "$OUTPUT"
fi

echo "$LOG_JSON"
