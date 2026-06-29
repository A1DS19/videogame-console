# RP2350 console — finishing the route in KiCad GUI

The board is **~95% routed** (`routing/rp2350-console-routed.kicad_pcb`): root QFN-80
congestion fixed, DRC down to **15 unconnected + 5 hole_to_hole + 2 benign annular**.
The residual genuinely needs the KiCad **interactive push-and-shove router** (Route ▸
Interactive Router, Mode: Shove) — it's the dense HDMI/ESD GND fanout between the TMDS
pins, which an autorouter can't do cleanly. Open the board in KiCad and:

## Connectivity (15 ratsnest)
1. **HDMI/ESD GND pins (6):** `J2` pads 17/8/5 and `D2` (TPD8S009) pads p2/p5/p8 — 0.30 mm
   GND pads flanked by TMDS at 0.5 mm; a 0.56 mm via won't fit on them. Route a thin GND
   trace from each to a nearby GND via, **or** reflow the F.Cu GND pour so it reaches them
   (the pour fragments where the TMDS fan out).
2. **Tight single GND/V3V3 ties (3):** `R19` GND, `C4` GND, `U3` pad p62 (a QFN GND pin
   wedged between the 0.4 mm-pitch VREG pads) — drop one via each.
3. **2 GND zone islands** (F.Cu + B.Cu): Edit ▸ Fill All Zones, then drop one stitch via in
   each island to tie it to the plane.
4. **2 orphan route stubs** (V3V3 on B.Cu ~0.6 mm, GND on F.Cu ~1.8 mm): just delete them
   (dangling, harmless).

## DRC violations (7)
5. **5 hole_to_hole** via pairs at 0.41–0.49 mm (need 0.4995): `D1_P/D1_N`, `V3V3/GPIO23`,
   `D2_P/V3V3`, and 2× `V3V3/V3V3` — drag one via of each pair ~0.1 mm apart.
6. **2 annular_width on J1** — benign: the USB-C `TYPE-C-31-M-12` shield THT pads 17/18 have a
   0.005 mm ring baked into the footprint. Don't fix; allowlist at DRC:
   `drc.py --board routing/rp2350-console-routed.kicad_pcb --allow annular_width:J1`.

## TMDS 100 Ω diff-tune (SI-critical — do this too)
7. The 4 TMDS pairs routed as default single-ended traces. Re-route them as **diff pairs,
   short + length-matched, 100 Ω** (HDMI is left-edge hard against the MCU, so they're short).
   The JITX source already declares the 100 Ω `DRS_100` constraint; set a matching KiCad
   netclass/diff-pair (0.1722 mm width / 0.15 mm gap — the exact DRS_100 values for 100 Ω on this 7628 stackup over the L2 GND plane)
   and route with the differential-pair tool. Validate HDMI on a real TV at bring-up.

## Then hand it back
Save → tell me, and I'll: `drc.py` (confirm 0 unconnected + only the allowlisted J1 annular)
→ `fab.py` + **`check_bom.py --fix`** (gerbers/drill/CPL/STEP + a JLCPCB-uploadable BOM with
real packages + LCSC). Then commit the final routed board + fab package.

Tip: `routing/rp2350-console-unrouted.kicad_pcb` is the clean de-congested base if you'd rather
re-autoroute a region from scratch.
