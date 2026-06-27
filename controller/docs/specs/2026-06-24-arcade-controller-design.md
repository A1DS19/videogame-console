# Arcade Controller — Design Spec (Path B / JST-XH / JITX)

**Date:** 2026-06-24 · **Board:** `arcade_controller_jitx` · **Plan:** `~/.claude/plans/2026-06-24_223911-arcade-controller-pcb-build.md`

## Overview
A wired 8-button **tactile gamepad** PCB where **the board *is* the faceplate**. Eight 12×12 mm
through-hole tactile buttons (4-button D-pad + 4 action buttons) return **active-low** switch
signals over a keyed, detachable **JST-XH 1×10** tether (2–3 m shielded cable) to an out-of-repo
**3.3 V RP2040 "console"**. The board carries controller-end pull-ups, per-line series resistors,
and two 4-channel TVS arrays at the connector. It is **not** "fully passive" — that claim was
consciously dropped for ESD robustness.

The console interface is **frozen** in `docs/interface-contract.md` — the single source of truth
both repos cite.

## Block architecture & nets
- **Power:** `V3V3` arrives from the console on connector pin 10; feeds the 8 pull-ups + both TVS VCC pins.
  `GND` (pin 9) is the return + shield drain (single-point bonded at the console end).
- **8 button channels** `i = 0..7`, each:
  ```
  V3V3 ──[ Rpu_i 10k ]── BTNi_INT ──[ SWi ]── GND
  BTNi_INT ──[ Rs_i 220 ]── BTNi_OUT ──┬── J1 pin (i+1)
                                        └── TVS ch i ── GND   (clamp at the connector)
  ```
- **ESD:** two `SRV05-4A` 4-ch arrays (`D1` = BTN0..BTN3, `D2` = BTN4..BTN7) sit hard against `J1`.
  Each `VCC`→`V3V3`, `GND`→`GND` (fat low-inductance tie to the plane). Clamps each `BTNi_OUT` between
  GND and the 3.3 V rail at cable entry. (RCLAMP3328P 8-ch was the ideal part but isn't in the JITX
  parts DB — see `docs/sourcing.md`.)

## Components (see `docs/sourcing.md` for MPNs/LCSC)
| Ref | Qty | Part |
|---|---|---|
| SW1–SW8 | 8 | K2-1103DP-Q4SW-04 tactile button (12×12 THT, 4 pads / 2 terminals) |
| J1 | 1 | B10B-XH-A JST-XH 1×10 connector (ports BTN0..BTN7, GND, V3V3) |
| D1,D2 | 2 | SRV05-4A 4-ch TVS array (SOT-23-6; ports IO1..IO4, GND, VCC) |
| Rs0–Rs7 | 8 | 220 Ω 0603 series |
| Rpu0–Rpu7 | 8 | 10 kΩ 0603 pull-up |

## Electrical semantics
- Switch-to-GND, **pull-UP, active-low** (pressed = LOW). 10 k/220 divider asserts ≈71 mV (valid VIL).
- Debounce = **console firmware** (no RC on the controller).
- 3.3 V domain only; RP2040 **not** 5 V tolerant.

## Layout intent (placement.py)
- **Board = faceplate.** Top side carries **only the 8 THT buttons**, arranged as a gamepad:
  a 4-button D-pad (cross/diamond, left) and 4 action buttons (diamond, right).
- **Button center-to-center ≥ ~18 mm** so the Ø12.6 mm keycaps don't collide; D-pad cluster ↔ action
  cluster ≈ 60–80 mm. Board starts ~120 × 70 mm (≤150 mm wide); finalized at layout.
- **All SMD on the bottom** (the 16 resistors + TVS). TVS hard against J1; pull-ups/series-R near their button leads.
- **J1 on a board edge** (only externally-mated connector → edge, per the family-grouping rule).
  Vertical `B10B-XH-A` (cable exits back) or right-angle `S10B-XH-A` for a flush edge exit — decided at floorplan.
- **GND pour** on the bottom copper over the inset signal area; **4× M3 NPTH corner holes with keepouts** (R126 gate).
- Layout authority lives in the JITX source (`placement.py`), verified headless by the `pcb-route` `check_placement` gate.

## Test plan (Phase 3 bring-up)
1. **Bare board continuity:** each `J1` signal pin → GND on the matching button press; open on release.
2. **Adjacent-pin short test** across all 8 signal lines + power.
3. **Cable continuity/pinout** test vs this spec + the interface contract.
4. **Console loopback:** power 3V3 from the console, confirm all 8 read HIGH idle / LOW pressed with firmware debounce.
