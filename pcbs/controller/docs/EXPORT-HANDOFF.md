# Arcade Controller — Phase 2/3 resume guide (post-export)

> **✅ Phase 2 DONE (2026-06-26):** exported → staged to `routing/` → 3D models filled (27/27) → refdes
> de-clipped → 4× M3 NPTH + keepouts → Freerouting (46/50 nets) → **solid F.Cu GND plane + 2 TVS-pad GND vias**
> to close the bottom-pour islands → **DRC 0/0/0** → fab package in `fab/` (gerbers+drill+CPL+BOM-with-LCSC+STEP).
> Canonical board = `routing/arcade-controller-routed.kicad_pcb`. **⏯️ ONLY Phase 3 (cable + bring-up) remains.**

Phases 0–1 are **done** (branch `feat/arcade-controller-jitx`): the board is electrically
complete, builds headless (`jitx build … status: ok`), placement authored + pose-verified.
Everything below needs the **GPU-gated JITX→KiCad export** first, so it is deferred to a
session with a display (or `jitx ui`).

Design: `arcade_controller_jitx.main.ArcadeController` · Build env: project `.venv/bin/jitx`
(JITX 4.2.0). Runtime: `.venv/bin/jitx runtime start --background` (already installed,
`--target ubuntu` on Fedora). Build helper: `… build <design> --no-dependency-check` (prefix
`yes |` if a stable-design instance-swap prompt blocks a headless build).

## Phase 2 — export → gate → route → DRC → fab (use the `pcb-route` skill)

1. **Export (GPU/human):** open the project in `jitx ui` / VSCode and export
   `ArcadeController` to KiCad. Produces `designs/arcade_controller_jitx.main.ArcadeController/kicad/*.kicad_pcb`.
   Copy it to `routing/arcade-controller.kicad_pcb`.

2. **Placement gate:** run the `pcb-route` gate on the export (placement is already baked in):
   `python3 /home/dev/projects/claude-configs/skills/pcb-route/scripts/check_placement.py routing/arcade-controller.kicad_pcb --edge-exempt J1`
   (run with the **system** python that has `pcbnew`). To iterate placement without re-exporting:
   edit `placement.py`, re-dump poses, and run `tools/preview_placement.py --poses <poses.json>`
   (already adapted: auto-centers, `--edge-exempt J1`). Expect 0 blocking (no crystal/decoupling
   checks apply here — only overlap/too-close/edge).

3. **Mounting holes:** add 4× **M3 NPTH (Ø3.2)** in the board corners **with keepouts** (deferred
   from JITX — they are mechanical/net-less). The R126 keepout gate validates them here.

4. **Netclass-to-spec + route:** JITX export writes a degenerate netclass via-dia → normalize
   to JLCPCB 2-layer spec first (the `pcb-route` `specctra_route.py` does this), then Freerouting
   via the Specctra round-trip. This board is trivial (8 THT switches, 1 connector, SMD on the
   bottom, GND pour) — expect ~100% auto-route; finish any straggler in KiCad GUI.

5. **DRC:** `pcb-route` `drc.py` → expect 0 unconnected; allowlist only benign edge/keepout items.

6. **Fab:** `pcb-route` `fab.py` → gerbers + drill + CPL + STEP. **BOM:** the JITX export has no
   MPN, so build the JLCPCB BOM from `docs/sourcing.md` (real LCSC codes) — not from the export.

## Phase 3 — cable + bring-up (hand-assembled, off-PCB)
- Crimp `XHP-10` + `SXH-001T` onto 2–3 m round shielded 10-cond cable per `docs/interface-contract.md`;
  drain bonded **single-point at the console end only**.
- Bring-up test plan: see `docs/specs/2026-06-24-arcade-controller-design.md` §Test plan
  (continuity per button → GND on press; adjacent-pin short test; cable pinout; console loopback).

## Open layout decisions for Phase 2
- **Connector exit:** vertical `B10B-XH-A` (cable exits the back, current model) vs right-angle
  `S10B-XH-A` (C157991) for a flush edge exit — decide against the enclosure.
- **Board size:** started 120×70 mm; tighten once cluster spacing + keycap clearance is dimensioned.
- **Keycaps:** optional `SHOU HAN A24` (C49451761), hand-pressed, ordered from LCSC (not JLC-assembled).
