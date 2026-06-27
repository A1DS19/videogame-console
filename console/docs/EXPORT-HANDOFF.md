# RP2350 Console — Phase 4 export hand-off

Phases 0–3 (the full JITX design) are DONE and committed on `feat/rp2350-console-jitx`.
The board builds `status: ok`. **Phase 4 (export → route → DRC → fab) is GPU/human-gated** — the
JITX→KiCad export needs a GPU (headless export is blank), exactly like the arcade controller.

## What you do (the GPU export)
1. Make sure the runtime is up (from `pcbs/rp2350_console_jitx/`):
   `.venv/bin/jitx runtime status` → if not running, `.venv/bin/jitx runtime start --background`
2. Open the board viewer / export:
   `.venv/bin/jitx ui open --board --design rp2350_console_jitx.designs.console.ConsoleBoard`
   then **Export** `RP2350Console` / `ConsoleBoard` to KiCad.
3. Copy the exported `.kicad_pcb` (+ the generated `.pretty/` footprint lib) into `routing/`.
4. Tell me it's exported — I take it from there.

**Build target:** `rp2350_console_jitx.designs.console.ConsoleBoard`
(the netlist is `main.py:ConsoleCircuit`; the top-level Design + TMDS SI constraints are in
`designs/console.py`; placement + pours are `placement.py`.)

## What I do after the export (pcb-route)
1. **`check_placement.py`** gate on the export (`--edge-exempt` the 5 edge connectors: HDMI,
   USB-C, both JST-XH, speaker) — fix any same-side overlaps / edge / decoupling-distance flags
   by iterating `placement.py` (re-export) or in the GUI. (This is the gate that couldn't run
   headless.)
2. **Netclass-to-spec + route:** normalize netclasses, then Freerouting (Specctra round-trip).
   **TMDS pairs:** confirm the DRS_100 100 Ω diff routing took; route/hand-tune the 4 pairs
   **short + length-matched** in the KiCad GUI (the SI-critical nets); then GND-stitch
   (`tools/stitch_gnd.py` from pcb-route — the stitching vias are intentionally NOT in source).
3. **DRC:** `drc.py` → 0 unconnected; allowlist only benign edge/keepout items.
4. **Fab:** `fab.py` → gerbers + drill + CPL + STEP + BOM. **Use the new `check_bom` gate**:
   `check_bom.py --fix --jitx-bom <jitx bom> --parts-db parts-db/ --manual <manual.csv> -o
   fab/...-bom-jlcpcb.csv` so the BOM ships with real packages + LCSC codes (avoids the pendant
   suspension). The 2 DB-unindexed parts that may need a `manual-parts.csv` line: none expected
   (all 24 LCSC codes resolved at sourcing) — but re-confirm RP2350B/AOTA resolve in the fab BOM.

## Review notes carried from Phase 3 (check at export, not blockers)
- **Pad-1 orientation:** confirm the QFN-80 generator's pad-1 vs RP2350 datasheet Figure 149
  (the one residual from the pin-map verification — a generator convention, not a map error).
- **Core inductor (L1) orientation:** `l_core` dot/P1 → VREG_LX (switch node) faces the MCU; sanity-check vs the Pico-2 reference in the 3D/layout view.
- **Bottom-side decap rotations:** power pad faces the served pin; eyeball in the 3D view.
- **TMDS series Rs = 0 Ω placeholders** (8×) — HSTX routes direct; you may DNP them.
- **Board 72×66 mm** is the JITX floorplan size — finalize against any enclosure constraint.
- **HDMI SI** is the top real risk — DRC won't catch it; validate on a real TV at bring-up.

## Decisions locked (Phase 0–2)
RP2350B + 16 MB external flash (W25Q128JV) · 1× TPD8S009 HDMI ESD · Basic 20 pF crystal · TLV62569
buck · amp default-ON · no SWD header this rev · GPIO budget per ARCHITECTURE.md.
Firmware (boot menu, HSTX DVI driver, PWM audio, 2-controller input, games) = **separate plan**.
