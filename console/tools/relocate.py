#!/usr/bin/env python3
"""Relocate footprints in a fresh unrouted board to a {ref:[dx,dy,rot]} JSON.
Design frame origin = board-edge-bbox center. Preserves layer/flip; sets pos+rot.
Usage: relocate.py <src.kicad_pcb> <poses.json> <out.kicad_pcb>
"""
import json
import sys
import pcbnew

src, poses_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
MM = pcbnew.FromMM
poses = json.load(open(poses_path))
b = pcbnew.LoadBoard(src)
bb = b.GetBoardEdgesBoundingBox()
cx, cy = pcbnew.ToMM(bb.GetCenter().x), pcbnew.ToMM(bb.GetCenter().y)
miss = set(poses)
for fp in b.GetFootprints():
    r = fp.GetReference()
    if r not in poses:
        print("NOT IN POSES:", r)
        continue
    miss.discard(r)
    dx, dy, rot = poses[r]
    fp.SetPosition(pcbnew.VECTOR2I(int(MM(cx + dx)), int(MM(cy - dy))))
    fp.SetOrientationDegrees(rot)
if miss:
    print("poses with no fp:", sorted(miss))
b.Save(out)
print("relocated ->", out)
