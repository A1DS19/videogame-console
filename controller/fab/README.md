# Arcade controller — JLCPCB fab package

Generated from `routing/arcade-controller-routed.kicad_pcb` (Specctra/Freerouting route → DRC-clean → fab).
**DRC: 0 violations / 0 unconnected** (kicad-cli, zones filled, ratsnest truth).

## Order settings (JLCPCB)
- **Layers:** 2 · **Size:** 120 × 70 mm · **Thickness:** 1.6 mm · FR-4, HASL or ENIG.
- Min track 0.25 mm, min clearance 0.2 mm, via Ø0.6 / drill 0.3 mm (annular 0.15 mm), edge clearance 0.3 mm — all standard 2-layer.
- 4× M3 NPTH (Ø3.2) corner mounting holes with copper keepouts.

## Files
| File | Use |
|---|---|
| `arcade-controller-gerbers.zip` | Gerbers + Excellon drill — upload this |
| `arcade-controller-cpl.csv` | Pick-and-place (27 parts: 8 SW **top**, 16 R + 2 TVS + J1 **bottom**) |
| `arcade-controller-bom.csv` | BOM with LCSC codes (from `docs/sourcing.md`) |
| `arcade-controller.step` | Board-only STEP (fab) |
| `arcade-controller-3d.step` | Full STEP with component models (enclosure CAD) |

## Assembly notes
- **Two-sided assembly:** tactile switches (THT) on **top** = the faceplate the user presses; SMD passives, 2× TVS,
  and the JST-XH connector on the **bottom** = the back. Confirm side assignment in the CPL when ordering PCBA.
- **GND** is a solid pour on **both** layers (top is a near-solid plane). Connectivity is carried by the top plane +
  PTH pads; the two SMD TVS GND pads (`D1.p2`, `D2.p2`, B.Cu-only) tie up to the top plane via a **GND via at the pad**
  (via-in-pad). JLCPCB tents these by default — acceptable for a GND/ESD reference; request resin-plug only if desired.
- **Resistors:** R1–R8 = 10 kΩ pull-ups, R9–R16 = 220 Ω series (active-low: V3V3–[10k]–INT–[switch]–GND, INT–[220]–OUT–[TVS]–J1).
- **Off-board (NOT on this BOM):** the cable tether (XHP-10 housing + SXH-001T crimps + shielded 10-cond cable,
  drain bonded single-point at the console end). See `docs/interface-contract.md` and `docs/sourcing.md`.
