# RP2350 console — finishing the route in KiCad GUI (v2, post-validation-fixes)

The **corrected** netlist (81 parts: +27 Ω USB Rs, +1 kΩ XOSC/BOOTSEL Rs, +2 DVDD caps,
L1 polarity dot→DVDD) was re-exported, the 6 new parts placed (gate-clean), then
auto-routed (Freerouting @ 0.2 mm) + GND/V3V3 stitched. Working board:
**`routing/rp2350-console-v2-stitched.kicad_pcb`**.

State: **all signal nets routed** (TMDS / QSPI / USB / GPIO / power) · DRC =
**19 unconnected + 1 clearance + 2 benign annular**. Every unconnected is a
**GND/V3V3 plane-tie** on a boxed-in pad — no signal is open. This needs the KiCad
**interactive push-and-shove** router (Route ▸ Interactive Router, Mode: Shove).

## Connectivity (19 ratsnest — all GND/V3V3 ties)
1. **HDMI/ESD GND fanout (5):** `D2` (TPD8S009) ×4 + `D3` (SRV05) ×1 GND pads —
   0.30 mm pads flanked by TMDS at 0.5 mm; a 0.56 mm via won't fit on them. Route a
   thin GND trace from each to a nearby GND via, **or** reflow the F.Cu GND pour so it
   reaches them (it fragments where the TMDS fan out).
2. **Boxed-in GND ties (11):** caps wedged in dense clusters (incl. the MCU EP `U3`,
   `C29` the new DVDD cap, `C4/C6/C7/C8/C14`) — drop one GND via each, or a thin tie
   to the adjacent plane.
3. **Boxed-in V3V3 ties (3):** `C13/C15` + one rail pad — one via each to the L3 V3V3
   plane.
   *(Tip: `tools/gnd_vias.py --phase pads --net <GND|V3V3> --copper-clr 0.2 --only-refs <ref>`
   can retry a single pad after you open space; the ones above are the residue it
   couldn't fit at 0.2 mm clearance.)*

## DRC violations (1 + 2 benign)
4. **1 clearance** — a stitch via < 0.2 mm from a trace; drag the via ~0.1 mm off it.
5. **2 annular_width on `J1`** — benign: the USB-C `TYPE-C-31-M-12` shield THT pads have
   a 0.005 mm ring baked into the footprint. Don't fix; allowlist at DRC
   (`drc.py --allow annular_width:J1`).

## TMDS 100 Ω diff-tune (SI-critical — do this too)
6. The 4 TMDS pairs are routed as default single-ended traces (JITX's `DRS_100` does
   **not** export). Re-route them as **diff pairs, short + length-matched, 100 Ω**
   (HDMI is hard against the MCU's left edge, so they're short). Set a KiCad
   diff-pair netclass of **0.1722 mm width / 0.15 mm gap** (the exact DRS_100 values
   for 100 Ω on this 7628 stackup over the L2 GND plane) and route with the
   differential-pair tool. Validate HDMI on a real TV at bring-up.

## L1 inductor orientation (one visual check)
7. The netlist now has the polarity dot/P1 → DVDD (RPi Fig 25). Confirm the **physical
   rotation** faces the dot **away** from the MCU vs datasheet Fig 23 in the 3D view;
   nudge `l_core`'s rotation if the silkscreen dot faces the wrong way.

## Then hand it back
Save → tell me, and I'll: `drc.py` (confirm 0 unconnected + only the allowlisted J1
annular) → `fab.py` + **`check_bom.py --fix`** (gerbers/drill/CPL/STEP + a JLCPCB BOM
with real packages + LCSC) → commit the final routed board + fab package, promoting
`rp2350-console-v2-stitched` to the canonical `rp2350-console-routed.kicad_pcb`.

Bases if you'd rather re-route a region from scratch:
`routing/rp2350-console-v2-unrouted.kicad_pcb` (placed, planes-only, gate-clean).
