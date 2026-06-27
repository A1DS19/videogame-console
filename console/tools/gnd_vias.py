#!/usr/bin/env python3
"""Robust GND stitcher for this JITX board.

The cap/IC GND lands are modeled as 0.01 mm POINT pads (JITX artifact), so the
ideal tie to the GND plane is a via placed *on the point* (via-in-pad). The
generic pcb-route stitch_gnd starts at a 0.8 mm offset and never tries on-pad, so
it misses these. This placer:

  1. For every GND SMD pad, places a GND through-via as close to the pad as
     possible (on-pad first, then a small offset + a connecting GND track),
     clearance-checked against different-net copper (copper clearance + hole
     clearance + via-to-via hole-to-hole).
  2. Lays a coarse plane-to-plane stitch grid to tie the F/B GND pours to the
     solid inner GND plane.

Through-vias span L1..L4, so a single via ties the pad's layer to the inner GND
plane (L2). Refills zones and reports the remaining unconnected count.
"""
import argparse
import math
import pcbnew

MM = 1_000_000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--via", type=float, default=0.56)
    ap.add_argument("--drill", type=float, default=0.30)
    ap.add_argument("--copper-clr", type=float, default=0.10)
    ap.add_argument("--hole-clr", type=float, default=0.255)
    ap.add_argument("--h2h", type=float, default=0.50)
    ap.add_argument("--track", type=float, default=0.25)
    ap.add_argument("--grid", type=float, default=4.0)
    ap.add_argument("--edge-inset", type=float, default=2.0)
    ap.add_argument("--edge-clear", type=float, default=0.35,
                    help="min via-to-board-edge / mounting-hole clearance (mm)")
    ap.add_argument("--phase", choices=["pads", "grid", "both"], default="both",
                    help="pads = per-GND-pad tie vias (run on the UNROUTED board); "
                         "grid = plane-to-plane stitch (run AFTER routing)")
    ap.add_argument("--on-pad-only", action="store_true",
                    help="place ONLY via-in-pad ties (offset 0, no connecting track) — "
                         "cheap obstacles for a pre-route pass that won't choke the router")
    ap.add_argument("--net", default="GND",
                    help="plane net to tie (default GND). A through-via on a net's pad "
                         "ties it to that net's plane. Grid phase is GND-only.")
    ap.add_argument("--only-refs", default="",
                    help="comma refs: restrict pad ties to these footprints "
                         "(e.g. tie only the unrouted V3V3 stragglers)")
    args = ap.parse_args()
    only_refs = {r.strip() for r in args.only_refs.split(",") if r.strip()}
    do_pads = args.phase in ("pads", "both")
    do_grid = args.phase in ("grid", "both") and args.net == "GND"

    b = pcbnew.LoadBoard(args.board)
    gnd = b.GetNetcodeFromNetname(args.net)
    if gnd < 0:
        raise SystemExit(f"no {args.net} net")

    via_r = args.via / 2 * MM
    drill_r = args.drill / 2 * MM
    cclr = args.copper_clr * MM
    hclr = args.hole_clr * MM
    h2h = args.h2h * MM
    trk_r = args.track / 2 * MM

    # Exact point-to-geometry obstacle model (the half-diagonal-circle model
    # grossly over-rejects long thin connector/ESD pads). Pads -> axis-aligned
    # rect from the effective-shape bbox (exact for axis-aligned pads, which the
    # connector/ESD GND lands are; mildly conservative for rotated pads, fine for
    # the small 0402/QFN ones). Tracks -> segment+halfwidth. Vias -> circle.
    # rects: (l,t,r,b,net,F,B)  segs: (ax,ay,bx,by,hw,net,F,B)  circs:(x,y,rad,net)
    # drills: (x,y,dr,net) for hole-to-hole.
    rects, segs, circs, drills = [], [], [], []

    for fp in b.GetFootprints():
        for p in fp.Pads():
            onF, onB = p.IsOnLayer(pcbnew.F_Cu), p.IsOnLayer(pcbnew.B_Cu)
            bb = p.GetEffectiveShape(pcbnew.B_Cu if onB else pcbnew.F_Cu).BBox()
            rects.append((bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom(),
                          p.GetNetCode(), onF, onB))
            dz = max(p.GetDrillSize().x, p.GetDrillSize().y)
            if dz > 0:
                c = p.GetPosition()
                drills.append((c.x, c.y, dz / 2, p.GetNetCode()))
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            c = t.GetPosition()
            drills.append((c.x, c.y, t.GetDrill() / 2, t.GetNetCode()))
            circs.append((c.x, c.y, t.GetWidth(pcbnew.F_Cu) / 2, t.GetNetCode()))
        elif t.Type() == pcbnew.PCB_TRACE_T:
            s, e = t.GetStart(), t.GetEnd()
            ly = t.GetLayer()
            segs.append((s.x, s.y, e.x, e.y, t.GetWidth() / 2, t.GetNetCode(),
                         ly == pcbnew.F_Cu, ly == pcbnew.B_Cu))

    # Edge.Cuts segments (board outline + the M3 mounting-hole cutouts): a via must
    # keep edge_clear from all of them, else copper_edge_clearance violations.
    edge_segs = []
    for d in b.GetDrawings():
        if d.IsOnLayer(pcbnew.Edge_Cuts) and d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            s, e = d.GetStart(), d.GetEnd()
            edge_segs.append((s.x, s.y, e.x, e.y))
    edge_keep = (args.edge_clear + args.via / 2) * MM

    placed = []  # (x,y) gnd vias
    cu_term = max(via_r + cclr, drill_r + hclr)  # via centre -> copper edge min

    def pt_rect(px, py, l, t, r, btm):
        dx = max(l - px, 0, px - r)
        dy = max(t - py, 0, py - btm)
        return math.hypot(dx, dy)

    def seg_pt(px, py, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay
        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)
        tt = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - (ax + tt * dx), py - (ay + tt * dy))

    def via_ok(x, y):
        for l, t, r, btm, net, onF, onB in rects:
            if net == gnd:
                continue
            if pt_rect(x, y, l, t, r, btm) < cu_term:
                return False
        for cx, cy, rad, net in circs:
            if net == gnd:
                continue
            d = math.hypot(x - cx, y - cy)
            if d < rad + max(via_r + cclr, drill_r + hclr):
                return False
        for ax, ay, bx, by, hw, net, onF, onB in segs:
            if net == gnd:
                continue
            if seg_pt(x, y, ax, ay, bx, by) < hw + cu_term:
                return False
        for cx, cy, dr, net in drills:  # hole-to-hole, every net
            d = math.hypot(x - cx, y - cy)
            if 1e-6 < d < drill_r + dr + h2h:
                return False
        for ax, ay, bx, by in edge_segs:  # board edge + mounting-hole keepout
            if seg_pt(x, y, ax, ay, bx, by) < edge_keep:
                return False
        return True

    def track_ok(ax, ay, bx, by, layer):
        # Fine-sample points along the (short) connecting track; reject if any
        # sample is too close to different-net copper on this layer, or to any
        # different-net drilled hole. Coarse sampling missed crossings -> shorts.
        onthis = (lambda f, bb: f) if layer == pcbnew.F_Cu else (lambda f, bb: bb)
        treach = trk_r + cclr
        n = max(2, int(math.hypot(bx - ax, by - ay) / (0.05 * MM)) + 1)
        pts = [(ax + i / n * (bx - ax), ay + i / n * (by - ay)) for i in range(n + 1)]
        for l, t, r, btm, net, onF, onB in rects:
            if net == gnd or not onthis(onF, onB):
                continue
            if any(pt_rect(px, py, l, t, r, btm) < treach for px, py in pts):
                return False
        for sx, sy, ex, ey, hw, net, onF, onB in segs:
            if net == gnd or not onthis(onF, onB):
                continue
            if any(seg_pt(px, py, sx, sy, ex, ey) < hw + treach for px, py in pts):
                return False
        for cx, cy, dr, net in drills:  # track copper -> different-net hole
            if net == gnd:
                continue
            if any(math.hypot(px - cx, py - cy) < dr + trk_r + hclr for px, py in pts):
                return False
        return True

    def add_via(x, y):
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
        v.SetWidth(int(args.via * MM))
        v.SetDrill(int(args.drill * MM))
        v.SetNetCode(gnd)
        b.Add(v)
        placed.append((x, y))
        drills.append((x, y, args.drill / 2 * MM, gnd))
        circs.append((x, y, via_r, gnd))

    def add_track(ax, ay, bx, by, layer):
        tr = pcbnew.PCB_TRACK(b)
        tr.SetStart(pcbnew.VECTOR2I(int(ax), int(ay)))
        tr.SetEnd(pcbnew.VECTOR2I(int(bx), int(by)))
        tr.SetWidth(int(args.track * MM))
        tr.SetLayer(layer)
        tr.SetNetCode(gnd)
        b.Add(tr)

    # (1) per GND SMD pad: via-in-pad first, then offsets with a track. Offset
    # search is biased to start radially OUTWARD from the board center (the inner
    # ring toward the MCU is where the escape vias live; the outer side is open).
    bbc = b.GetBoardEdgesBoundingBox().GetCenter()
    # GND vias already on the board (e.g. from a pre-route on-pad pass) so a later
    # mop-up pass doesn't double-tie an already-connected pad.
    existing_gnd_vias = [(t.GetPosition().x, t.GetPosition().y)
                         for t in b.GetTracks()
                         if t.Type() == pcbnew.PCB_VIA_T and t.GetNetCode() == gnd]
    taps, miss = 0, []
    offsets = [0.0] if args.on_pad_only else \
        [0.0, 0.5, 0.65, 0.8, 1.0, 1.25, 1.5, 1.8, 2.2, 2.6, 3.0]
    for fp in b.GetFootprints():
        if not do_pads:
            break
        if only_refs and fp.GetReference() not in only_refs:
            continue
        for p in fp.Pads():
            if p.GetNetCode() != gnd:
                continue
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue  # THT GND pads already span layers
            c = p.GetPosition()
            # already tied by a pre-route on-pad via touching this pad's copper?
            pbb = p.GetEffectiveShape(
                pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu).BBox()
            pr = math.hypot(pbb.GetWidth(), pbb.GetHeight()) / 2
            if any(math.hypot(c.x - vx, c.y - vy) < pr + via_r
                   for vx, vy in existing_gnd_vias):
                continue
            layer = pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu
            base = math.atan2(c.y - bbc.y, c.x - bbc.x)  # radially outward
            done = False

            # STRATEGY 0 — via directly on the pad's OWN copper (best: connects the
            # pad to L2 with no track/pour dependency). Long thin connector/ESD GND
            # pads have an open far end clear of neighbour pins; scan the pad copper
            # for a clear point and pick the one most clear of different-net copper.
            cand = []
            step = int(0.1 * MM)
            x0, x1 = pbb.GetLeft(), pbb.GetRight()
            y0, y1 = pbb.GetTop(), pbb.GetBottom()
            yy = y0
            while yy <= y1:
                xx = x0
                while xx <= x1:
                    pt = pcbnew.VECTOR2I(int(xx), int(yy))
                    if p.HitTest(pt, 0) and via_ok(xx, yy):
                        # score = distance to nearest different-net drilled hole
                        # (bigger = safer hole-to-hole); ties broken arbitrarily.
                        m = min((math.hypot(xx - cx, yy - cy)
                                 for cx, cy, dr, net in drills if net != gnd),
                                default=1e12)
                        cand.append((m, xx, yy))
                    xx += step
                yy += step
            if cand:
                _, vx, vy = max(cand)
                add_via(vx, vy)
                taps += 1
                done = True
            for off in offsets:
                if done:
                    break
                if off == 0.0:
                    if via_ok(c.x, c.y):
                        add_via(c.x, c.y)
                        taps += 1
                        done = True
                    continue
                # angles sweep outward-first: 0, +-30, +-60, ... around `base`
                order = [0]
                for k in range(1, 7):
                    order += [k * math.pi / 6, -k * math.pi / 6]
                for da in order:
                    ang = base + da
                    x, y = c.x + off * MM * math.cos(ang), c.y + off * MM * math.sin(ang)
                    if via_ok(x, y) and track_ok(c.x, c.y, x, y, layer):
                        add_via(x, y)
                        add_track(c.x, c.y, x, y, layer)
                        taps += 1
                        done = True
                        break
            if not done:
                miss.append(p.GetParentFootprint().GetReference())

    # (2) coarse plane stitch grid
    grid = 0
    if do_grid:
        bb = b.GetBoardEdgesBoundingBox()
        inset = int(args.edge_inset * MM)
        step = int(args.grid * MM)
        y = bb.GetTop() + inset
        while y <= bb.GetBottom() - inset:
            x = bb.GetLeft() + inset
            while x <= bb.GetRight() - inset:
                if via_ok(x, y):
                    add_via(x, y)
                    grid += 1
                x += step
            y += step

    # (3) island stitch: fill, then drop a via in every GND fill-polygon that has
    # no GND via yet, so isolated pour islands (incl. inner-plane fragments) tie to
    # the rest of the GND net. Re-fill afterwards. GND phase only.
    island = 0
    if do_grid:
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        gnd_via_pts = list(placed) + [
            (t.GetPosition().x, t.GetPosition().y) for t in b.GetTracks()
            if t.Type() == pcbnew.PCB_VIA_T and t.GetNetCode() == gnd]
        for z in b.Zones():
            if z.GetNetCode() != gnd:
                continue
            for ly in z.GetLayerSet().CuStack():
                poly = z.GetFilledPolysList(ly)
                for i in range(poly.OutlineCount()):
                    ps = pcbnew.SHAPE_POLY_SET()
                    ps.AddOutline(poly.Outline(i))
                    ob = ps.BBox()
                    # already has a GND via inside?
                    if any(ps.Contains(pcbnew.VECTOR2I(int(vx), int(vy)))
                           for vx, vy in gnd_via_pts
                           if ob.GetLeft() <= vx <= ob.GetRight()
                           and ob.GetTop() <= vy <= ob.GetBottom()):
                        continue
                    # find an interior point that takes a clean via
                    placed_here = False
                    gx = ob.GetLeft() + (ob.GetRight() - ob.GetLeft()) // 2
                    gy = ob.GetTop() + (ob.GetBottom() - ob.GetTop()) // 2
                    cands = [(gx, gy)]
                    stepx = max(1, (ob.GetRight() - ob.GetLeft()) // 6)
                    stepy = max(1, (ob.GetBottom() - ob.GetTop()) // 6)
                    yy = ob.GetTop()
                    while yy <= ob.GetBottom():
                        xx = ob.GetLeft()
                        while xx <= ob.GetRight():
                            cands.append((xx, yy))
                            xx += stepx
                        yy += stepy
                    for cx, cy in cands:
                        pt = pcbnew.VECTOR2I(int(cx), int(cy))
                        if ps.Contains(pt) and via_ok(cx, cy):
                            add_via(cx, cy)
                            gnd_via_pts.append((cx, cy))
                            island += 1
                            placed_here = True
                            break

    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(args.board, b)
    b.BuildConnectivity()
    m = f"  no-tap: {sorted(set(miss))}" if miss else ""
    print(f"GND vias: {taps} pad-taps + {grid} grid + {island} island; "
          f"unconnected now {b.GetConnectivity().GetUnconnectedCount(True)}{m}")


if __name__ == "__main__":
    main()
