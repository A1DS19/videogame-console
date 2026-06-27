#!/usr/bin/env python3
"""Generate a complete {ref:[dx,dy,rot]} poses JSON (design frame) for headless
relocation. Reads every footprint's current pose from a reference board (the
routed board reflects the latest placement.py), then applies de-congestion
overrides that mirror placement.py exactly. Keeps placement.py the authority:
the OVERRIDES dict below is copied straight from placement.py.
"""
import json
import sys
import pcbnew

T = pcbnew.ToMM
REF_BOARD = sys.argv[1] if len(sys.argv) > 1 else "routing/rp2350-console-routed.kicad_pcb"
OUT = sys.argv[2] if len(sys.argv) > 2 else "routing/poses.json"

# Mirror of placement.py de-congested cap poses (design frame, +y up).
OVERRIDES = {
    # 8 IOVDD 100nF, radius 7.2
    "C6": (-6.55, 2.99, 245), "C7": (-6.74, -2.53, 291),
    "C8": (-3.43, -6.33, 332), "C9": (-0.89, -7.14, 353),
    "C10": (5.65, -4.47, 52), "C11": (7.19, -0.30, 88),
    "C12": (5.65, 4.47, 128), "C13": (-2.99, 6.55, 205),
    # specific-pin 100nF, spread
    "C14": (-0.3, 6.0, 0), "C15": (2.5, 6.0, 0), "C16": (8.2, 4.0, 125),
    # core 4.7uF + bulk 10uF, pushed out of the inner ring (R14-exempt)
    "C4": (-8.6, 0.3, 268), "C3": (3.0, 9.4, 0), "C5": (7.3, 8.6, 142),
    "C17": (-5.5, -9.5, 0), "C18": (3.6, -8.9, 0),
    "C19": (0.125, 11.4, 0),
}


def main():
    b = pcbnew.LoadBoard(REF_BOARD)
    bb = b.GetBoardEdgesBoundingBox()
    cx, cy = T(bb.GetCenter().x), T(bb.GetCenter().y)
    poses = {}
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        p = fp.GetPosition()
        dx = round(T(p.x) - cx, 4)
        dy = round(-(T(p.y) - cy), 4)
        rot = round(fp.GetOrientationDegrees(), 1)
        poses[ref] = [dx, dy, rot]
    for ref, (x, y, r) in OVERRIDES.items():
        if ref not in poses:
            print("WARN: override ref not on board:", ref)
        poses[ref] = [x, y, r]
    json.dump(poses, open(OUT, "w"), indent=1)
    print(f"wrote {len(poses)} poses -> {OUT}  ({len(OVERRIDES)} overridden)")


if __name__ == "__main__":
    main()
