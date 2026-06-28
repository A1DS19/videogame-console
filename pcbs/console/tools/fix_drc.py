#!/usr/bin/env python3
"""Headless DRC closer for hole_to_hole + clearance violations.

Drives off kicad-cli's DRC JSON (items carry uuid + pos). For each violation it
moves the MORE-MOVABLE item of the pair (a via, or a track bend-vertex) to a
nearby spot that clears every rule, dragging coincident track endpoints so the
net stays connected. Pads are never moved. Re-runs DRC and iterates.

Rules enforced for a moved via / track:
  copper clearance  >= CLR   (copper edge to different-net copper edge)
  hole clearance    >= HCLR  (drill edge to different-net copper edge)
  hole-to-hole      >= H2H   (drill edge to ANY other drill edge)
  edge clearance    >= EDGE  (copper edge to board edge / mounting holes)
"""
import argparse
import json
import math
import subprocess
import tempfile

import pcbnew

MM = 1_000_000
CLR = 0.15 * MM
HCLR = 0.254 * MM
H2H = 0.4995 * MM
EDGE = 0.30 * MM
MARG = 0.02 * MM  # extra margin so we land safely past the limit


def run_drc(path):
    out = tempfile.mktemp(suffix=".json")
    subprocess.run(["kicad-cli", "pcb", "drc", "--severity-error", "--format",
                    "json", "-o", out, path], check=True, capture_output=True)
    return json.load(open(out))


def seg_pt(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _ccw(ax, ay, bx, by, cx, cy):
    return (cy - ay) * (bx - ax) > (by - ay) * (cx - ax)


def seg_seg(a, b, c, d):
    """Min distance between segments a-b and c-d. 0 if they cross (else the
    endpoint-to-segment minimum) — endpoint-only misses an X crossing → short."""
    if (_ccw(*a, *c, *d) != _ccw(*b, *c, *d)) and \
       (_ccw(*a, *b, *c) != _ccw(*a, *b, *d)):
        return 0.0
    return min(seg_pt(*a, *c, *d), seg_pt(*b, *c, *d),
              seg_pt(*c, *a, *b), seg_pt(*d, *a, *b))


class Geom:
    """Obstacle snapshot, with a set of excluded uuids (the items being moved)."""

    def __init__(self, board, exclude):
        self.rects, self.segs, self.circs, self.drills, self.edges = [], [], [], [], []
        for fp in board.GetFootprints():
            for p in fp.Pads():
                bb = p.GetEffectiveShape(
                    pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu).BBox()
                self.rects.append((bb.GetLeft(), bb.GetTop(), bb.GetRight(),
                                   bb.GetBottom(), p.GetNetCode(),
                                   p.IsOnLayer(pcbnew.F_Cu), p.IsOnLayer(pcbnew.B_Cu)))
                dz = max(p.GetDrillSize().x, p.GetDrillSize().y)
                if dz > 0:
                    c = p.GetPosition()
                    self.drills.append((c.x, c.y, dz / 2, p.GetNetCode()))
        for t in board.GetTracks():
            if t.m_Uuid.AsString() in exclude:
                continue
            if t.Type() == pcbnew.PCB_VIA_T:
                c = t.GetPosition()
                self.drills.append((c.x, c.y, t.GetDrill() / 2, t.GetNetCode()))
                self.circs.append((c.x, c.y, t.GetWidth(pcbnew.F_Cu) / 2,
                                   t.GetNetCode()))
            else:
                s, e = t.GetStart(), t.GetEnd()
                self.segs.append((s.x, s.y, e.x, e.y, t.GetWidth() / 2,
                                  t.GetNetCode(), t.GetLayer()))
        for d in board.GetDrawings():
            if d.IsOnLayer(pcbnew.Edge_Cuts) and d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                s, e = d.GetStart(), d.GetEnd()
                self.edges.append((s.x, s.y, e.x, e.y))

    def via_ok(self, x, y, drill_r, via_r, net):
        cu = max(via_r + CLR, drill_r + HCLR) + MARG
        for l, t, r, b, n, _, _ in self.rects:
            if n == net:
                continue
            dx = max(l - x, 0, x - r)
            dy = max(t - y, 0, y - b)
            if math.hypot(dx, dy) < cu:
                return False
        for cx, cy, rad, n in self.circs:
            if n == net:
                continue
            if math.hypot(x - cx, y - cy) < rad + cu:
                return False
        for ax, ay, bx, by, hw, n, _ in self.segs:
            if n == net:
                continue
            if seg_pt(x, y, ax, ay, bx, by) < hw + cu:
                return False
        for cx, cy, dr, n in self.drills:
            # hole-to-hole applies to EVERY drill regardless of net; the via being
            # moved is already excluded from Geom, so there is no "self" to skip —
            # a candidate landing on another drill (d≈0) MUST fail.
            if math.hypot(x - cx, y - cy) < drill_r + dr + H2H + MARG:
                return False
        for ax, ay, bx, by in self.edges:
            if seg_pt(x, y, ax, ay, bx, by) < via_r + EDGE + MARG:
                return False
        return True

    def track_ok(self, ax, ay, bx, by, hw, net, layer):
        onF, onB = layer == pcbnew.F_Cu, layer == pcbnew.B_Cu
        for l, t, r, b, n, pf, pb in self.rects:
            if n == net or not (pf if onF else pb):
                continue
            # rect-to-seg distance via corner + endpoint sampling
            for px, py in ((l, t), (r, t), (l, b), (r, b)):
                if seg_pt(px, py, ax, ay, bx, by) < hw + CLR + MARG:
                    return False
            cx2 = min(max((ax + bx) / 2, l), r)
            cy2 = min(max((ay + by) / 2, t), b)
            if seg_pt(cx2, cy2, ax, ay, bx, by) < hw + CLR + MARG:
                return False
        for sx, sy, ex, ey, shw, n, sl in self.segs:
            if n == net or sl != layer:
                continue
            if seg_seg((ax, ay), (bx, by), (sx, sy), (ex, ey)) < hw + shw + CLR + MARG:
                return False
        for cx, cy, rad, n in self.circs:
            if n == net:
                continue
            if seg_pt(cx, cy, ax, ay, bx, by) < rad + hw + CLR + MARG:
                return False
        for cx, cy, dr, n in self.drills:
            if n == net:
                continue
            if seg_pt(cx, cy, ax, ay, bx, by) < dr + hw + HCLR + MARG:
                return False
        for ex0, ey0, ex1, ey1 in self.edges:
            if seg_seg((ax, ay), (bx, by), (ex0, ey0), (ex1, ey1)) < hw + EDGE + MARG:
                return False
        return True


def coincident_tracks(board, pos, net):
    """Tracks with an endpoint exactly at pos (same net) — they move with the via."""
    out = []
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T or t.GetNetCode() != net:
            continue
        if t.GetStart() == pos:
            out.append((t, "start"))
        elif t.GetEnd() == pos:
            out.append((t, "end"))
    return out


def try_move(board, via, conflict_xy):
    """Search for a clear new position for `via`, biased away from conflict_xy.
    Moves the via + its coincident track ends. Returns True if moved."""
    pos = via.GetPosition()
    net = via.GetNetCode()
    drill_r = via.GetDrill() / 2
    via_r = via.GetWidth(pcbnew.F_Cu) / 2
    moved = coincident_tracks(board, pos, net)
    exclude = {via.m_Uuid.AsString()} | {t.m_Uuid.AsString() for t, _ in moved}
    g = Geom(board, exclude)

    base = math.atan2(pos.y - conflict_xy[1], pos.x - conflict_xy[0])
    for step in [s * 0.05 * MM for s in range(2, 41)]:  # 0.1 .. 2.0 mm
        angs = [base] + [base + k * math.pi / 12 * s
                         for k in range(1, 13) for s in (1, -1)]
        for a in angs:
            nx = int(pos.x + step * math.cos(a))
            ny = int(pos.y + step * math.sin(a))
            if not g.via_ok(nx, ny, drill_r, via_r, net):
                continue
            ok = True
            for t, end in moved:
                other = t.GetEnd() if end == "start" else t.GetStart()
                if not g.track_ok(other.x, other.y, nx, ny, t.GetWidth() / 2,
                                  net, t.GetLayer()):
                    ok = False
                    break
            if not ok:
                continue
            via.SetPosition(pcbnew.VECTOR2I(nx, ny))
            for t, end in moved:
                if end == "start":
                    t.SetStart(pcbnew.VECTOR2I(nx, ny))
                else:
                    t.SetEnd(pcbnew.VECTOR2I(nx, ny))
            return True
    return False


def _anchored(board, v):
    """True if a pad center or via sits exactly at point v (a real terminal)."""
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetPosition() == v:
                return True
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T and t.GetPosition() == v:
            return True
    return False


def move_vertex(board, track, conflict_xy):
    """Move a FREE bend vertex of `track` (the endpoint nearest conflict_xy that has
    no pad/via on it) away from conflict_xy to a clear spot, dragging every coincident
    same-net track end. Returns True if moved."""
    net = track.GetNetCode()
    cands = sorted([track.GetStart(), track.GetEnd()],
                   key=lambda p: math.hypot(p.x - conflict_xy[0], p.y - conflict_xy[1]))
    for v in cands:
        if _anchored(board, v):
            continue
        comoved = []
        for t in board.GetTracks():
            if t.Type() == pcbnew.PCB_VIA_T or t.GetNetCode() != net:
                continue
            if t.GetStart() == v:
                comoved.append((t, "start"))
            elif t.GetEnd() == v:
                comoved.append((t, "end"))
        exclude = {t.m_Uuid.AsString() for t, _ in comoved}
        g = Geom(board, exclude)
        base = math.atan2(v.y - conflict_xy[1], v.x - conflict_xy[0])
        for step in [s * 0.05 * MM for s in range(2, 31)]:  # 0.1 .. 1.5 mm
            for a in [base] + [base + k * math.pi / 12 * s
                               for k in range(1, 10) for s in (1, -1)]:
                nx = int(v.x + step * math.cos(a))
                ny = int(v.y + step * math.sin(a))
                ok = True
                for t, end in comoved:
                    other = t.GetEnd() if end == "start" else t.GetStart()
                    if not g.track_ok(other.x, other.y, nx, ny, t.GetWidth() / 2,
                                      net, t.GetLayer()):
                        ok = False
                        break
                if not ok:
                    continue
                nv = pcbnew.VECTOR2I(nx, ny)
                for t, end in comoved:
                    if end == "start":
                        t.SetStart(nv)
                    else:
                        t.SetEnd(nv)
                return True
    return False


def find_item(board, uuid):
    for t in board.GetTracks():
        if t.m_Uuid.AsString() == uuid:
            return t
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.m_Uuid.AsString() == uuid:
                return p
    return None


def movability(item):
    """Higher = prefer to move. Pads never move; plane-net tracks/vias move first."""
    if isinstance(item, pcbnew.PAD):
        return -1
    plane = item.GetNetname() in ("GND", "V3V3")
    is_via = item.Type() == pcbnew.PCB_VIA_T
    return (3 if plane else 1) + (1 if not is_via else 0)  # tracks slightly over vias


def fix_violation(board, viol):
    items = [(find_item(board, it["uuid"]),
              (pcbnew.FromMM(it["pos"]["x"]), pcbnew.FromMM(it["pos"]["y"])))
             for it in viol.get("items", [])]
    items = [(o, p) for o, p in items if o is not None]
    if len(items) < 2:
        return False
    items.sort(key=lambda op: movability(op[0]), reverse=True)
    for obj, _ in items:
        if isinstance(obj, pcbnew.PAD):
            continue
        other_xy = next(p for o, p in items if o is not obj)
        if obj.Type() == pcbnew.PCB_VIA_T:
            if try_move(board, obj, other_xy):
                return True
        else:
            if move_vertex(board, obj, other_xy):
                return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--board", required=True)
    ap.add_argument("--types", default="hole_to_hole,clearance")
    ap.add_argument("--passes", type=int, default=6)
    # Fab minima (defaults = JLCPCB). Set --clearance to the value the board was
    # ROUTED at so a moved item lands DRC-clean.
    ap.add_argument("--clearance", type=float, default=0.15, help="copper clearance mm")
    ap.add_argument("--hole-clr", type=float, default=0.254, help="drill→copper mm")
    ap.add_argument("--h2h", type=float, default=0.4995, help="drill→drill mm")
    ap.add_argument("--edge-clear", type=float, default=0.30, help="copper→edge mm")
    args = ap.parse_args()
    types = {t.strip() for t in args.types.split(",")}
    global CLR, HCLR, H2H, EDGE
    CLR, HCLR = args.clearance * MM, args.hole_clr * MM
    H2H, EDGE = args.h2h * MM, args.edge_clear * MM

    for it in range(1, args.passes + 1):
        b = pcbnew.LoadBoard(args.board)
        rpt = run_drc(args.board)
        viols = [v for v in rpt["violations"] if v["type"] in types]
        if not viols:
            print(f"pass {it}: 0 target violations — done")
            break
        fixed = 0
        for v in viols:
            if fix_violation(b, v):
                fixed += 1
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        b.Save(args.board)
        print(f"pass {it}: {len(viols)} target viol -> fixed {fixed}")
        if fixed == 0:
            print("  no further automatic fixes possible")
            break

    rpt = run_drc(args.board)
    from collections import Counter
    c = Counter(v["type"] for v in rpt["violations"])
    print("final:", dict(c), " unconnected:", len(rpt.get("unconnected_items", [])))


if __name__ == "__main__":
    main()

