#!/usr/bin/env bash
# Full headless route pipeline for the RP2350 console.
# 1) pre-place per-pad GND tie vias on the relocated UNROUTED board
# 2) Freerouting signal route (round-trip)
# 3) plane-to-plane GND grid stitch (post-route)
# 4) DRC report (no destructive trace-widening; board's track min is 0.09mm)
set -e
cd /home/dev/projects/medi-pal/pcbs/rp2350_console_jitx
PY=/usr/bin/python3
SK=/home/dev/.claude/skills/pcb-route/scripts
UNROUTED=routing/rp2350-console-unrouted.kicad_pcb
PRETIED=routing/rp2350-console-unrouted-gnd.kicad_pcb
ROUTED=routing/rp2350-console-routed.kicad_pcb
PASSES=${1:-60}
CLR=${2:-0.25}

# Clean route (no pre-placed GND obstacles — keeps the QFN escape routable). The
# routing clearance is bumped to CLR so via DRILLS satisfy the board's stricter
# hole_clearance (0.254) + hole_to_hole (0.4995) rules that Freerouting's
# copper-clearance model would otherwise miss.
EDGE=${3:-0.35}
$PY "$SK/specctra_route.py" --board "$UNROUTED" --out "$ROUTED" --passes "$PASSES" \
    --clearance "$CLR" --edge-clearance "$EDGE" 2>&1 \
    | grep -E "unrouted nets|routed ->|clearance "
cp "$ROUTED" routing/rp2350-console-routed-prestitch.kicad_pcb
# post-route: GND tie vias (via-on-pad + offset+B.Cu track) + plane stitch grid.
# --copper-clr must be >= the routed-board clearance (CLR) so stitch vias are
# DRC-clean; --edge-clear keeps them off the board edge + mounting holes.
$PY tools/gnd_vias.py --board "$ROUTED" --phase both --copper-clr 0.16 \
    2>/dev/null | grep "GND vias"
# tie any V3V3 stragglers Freerouting left to the V3V3 plane
$PY tools/gnd_vias.py --board "$ROUTED" --phase pads --net V3V3 --only-refs R3,L3 \
    --copper-clr 0.16 2>/dev/null | grep "GND vias" || true
# fix sub-spec VIAS only (min-trace 0.09 = board track min, so the legit 0.09mm
# QFN-escape traces are NEVER widened)
$PY "$SK/cleanup.py" --board "$ROUTED" --min-trace 0.09 --apply 2>/dev/null \
    | grep -E "sub-spec|vias fixed|traces fixed"
echo "--- DRC ---"
kicad-cli pcb drc --severity-error --format json -o /tmp/rp_drc.json "$ROUTED" >/dev/null 2>&1
$PY -c "
import json; from collections import Counter
d=json.load(open('/tmp/rp_drc.json'))
print('unconnected_items:',len(d['unconnected_items']))
for t,n in Counter(v['type'] for v in d['violations']).most_common(): print(f'  {n:4d} {t}')
"
