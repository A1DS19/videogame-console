#!/usr/bin/env python3
"""Headless placement preview for the arcade controller.

Relocates the EXPORTED footprints (real courtyards/pads/nets) to a candidate
floorplan and runs the pcb-route placement gate (`check_placement.py`) on the
result — so a re-placement encoded in JITX `placement.py` can be validated
WITHOUT the GPU-gated JITX->KiCad re-export. Because placement is deterministic
(JITX puts each part exactly where `place()` says), this is a faithful preview.

Poses are in the JITX design frame (origin = board center, +y up), keyed by
KiCad ref: {ref: [dx_mm, dy_mm, rotate_deg]}. Rotation matches JITX `rotate=`.

The design-frame origin in KiCad mm is auto-derived from the board-edge bounding-box
center (JITX places the design with origin at the board center), so this works for any
exported board without a hardcoded constant. Override with --board if needed.
"""
import sys, json, argparse
import pcbnew

sys.path.insert(0, "/home/dev/projects/claude-configs/skills/pcb-route/scripts")
import check_placement as cp

# Default board = the arcade controller's exported/routing board (created at the
# post-export Phase-2 step). Override with --board.
BOARD = "/home/dev/projects/medi-pal/pcbs/arcade_controller_jitx/routing/arcade-controller.kicad_pcb"
MM = pcbnew.FromMM


def board_center_mm(board):
    """Design-frame origin = center of the board-edge bounding box, in KiCad mm."""
    bb = board.GetBoardEdgesBoundingBox()
    return pcbnew.ToMM(bb.GetCenter().x), pcbnew.ToMM(bb.GetCenter().y)


def apply_poses(board, poses, cx, cy):
    missing = set(poses)
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref not in poses:
            continue
        missing.discard(ref)
        dx, dy, rot = poses[ref]
        fp.SetPosition(pcbnew.VECTOR2I(int(MM(cx + dx)), int(MM(cy - dy))))
        fp.SetOrientationDegrees(rot)
    if missing:
        print(f"WARNING: poses for unknown refs: {sorted(missing)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--poses", required=True, help="JSON file {ref:[dx,dy,rot]}")
    ap.add_argument("--board", default=BOARD, help="exported .kicad_pcb to relocate")
    ap.add_argument("--edge-exempt", default="J1")
    ap.add_argument("--min-clearance", type=float, default=0.5)
    ap.add_argument("--edge-keepout", type=float, default=0.5)
    ap.add_argument("--decap-max", type=float, default=2.0)
    ap.add_argument("--decap-far", type=float, default=12.0)
    ap.add_argument("--xtal-max", type=float, default=5.0)
    args = ap.parse_args()

    poses = json.load(open(args.poses))
    b = pcbnew.LoadBoard(args.board)
    cx, cy = board_center_mm(b)
    apply_poses(b, poses, cx, cy)

    rm = {fp.GetReference(): fp for fp in b.GetFootprints()}
    exempt = {r.strip() for r in args.edge_exempt.split(",") if r.strip()}
    ov, tc, cross, boxes = cp.check_clearance(rm, args.min_clearance)
    edge = cp.check_edge(rm, boxes, b.GetBoardEdgesBoundingBox(), args.edge_keepout, exempt)
    decb, decf = cp.check_decoupling(rm, args.decap_max, args.decap_far)
    xt = cp.check_resonator(rm, args.xtal_max)
    silk = cp.check_silk_over_pad(rm)

    print(f"R118 overlaps (same side): {len(ov)}")
    for a, c in ov:
        print(f"  OVERLAP {a} <-> {c}")
    print(f"R119 too-close (<{args.min_clearance}): {len(tc)}")
    for a, c, g in sorted(tc, key=lambda x: x[2]):
        print(f"  CLOSE   {a} <-> {c}  gap={g:.3f}")
    print(f"R120 edge keepout: {len(edge)}")
    for r, m in sorted(edge, key=lambda x: x[1]):
        print(f"  EDGE    {r}  margin={m}")
    print(f"R14 decoupling too far: {len(decb)}")
    for cr, net, ir, d in sorted(decb, key=lambda x: -x[3]):
        print(f"  DECAP   {cr} ({net}) -> {ir}  dist={d}")
    print(f"R16 resonator too far: {len(xt)}")
    for xr, ir, d in xt:
        print(f"  XTAL    {xr} -> {ir}  dist={d}")

    block = len(ov) + len(tc) + len(edge) + len(decb) + len(xt)
    warn = len(cross) + len(decf) + len(silk)
    print(f"\n{'FAIL' if block else 'PASS'}: {block} blocking  [+{warn} warn: "
          f"{len(cross)} cross-layer, {len(decf)} far-cap, {len(silk)} silk]")
    sys.exit(1 if block else 0)


if __name__ == "__main__":
    main()
