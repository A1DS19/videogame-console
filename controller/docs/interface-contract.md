# Arcade Controller ⇄ Console — Interface Contract (FROZEN v1)

> **This file is the single source of truth for the controller↔console electrical/logical
> interface.** The console firmware/board lives in a **separate repo** and MUST cite this file.
> Any change here is a breaking change that requires a coordinated update on both sides.
> The original draft's pull-down bug existed precisely because the two sides drifted — this
> contract exists to stop that.

## Connector

- **Board side (controller):** JST-XH `B10B-XH-A(LF)(SN)` — 1×10, 2.5 mm pitch, vertical THT (LCSC C144400).
- **Cable side:** `XHP-10` housing (C144408) + `SXH-001T-P0.6` crimp contacts (C140573), round shielded 10-conductor cable, 2–3 m.
- **Keying:** **mechanical** — the XH housing polarizing boss + friction-latch ramp. No conductor is spent on keying, which is why pin 10 carries 3V3 (below).

## Pin map (FROZEN)

| XH pin | Net    | Dir (controller→console) | Function |
|-------:|--------|--------------------------|----------|
| 1 | `BTN0` | out (open-drain-ish, active-low) | D-pad **Up** |
| 2 | `BTN1` | out | D-pad **Down** |
| 3 | `BTN2` | out | D-pad **Left** |
| 4 | `BTN3` | out | D-pad **Right** |
| 5 | `BTN4` | out | Action **A** |
| 6 | `BTN5` | out | Action **B** |
| 7 | `BTN6` | out | Action **X** |
| 8 | `BTN7` | out | Action **Y** |
| 9 | `GND`  | —  | Ground return + cable-shield drain |
| 10 | `V3V3` | in (console→controller) | 3.3 V supply for the controller-end pull-ups; absence = no controller (implicit tether-detect) |

## Electrical semantics

- **Polarity:** **active-LOW.** A pressed button reads **LOW**; released reads **HIGH**.
- **Per-line topology (controller side):**
  `V3V3 —[10 kΩ pull-up]— NODE —[switch]— GND`, and `NODE —[220 Ω series]— PINₙ`.
  - Idle: console GPIO sees ~3.3 V through 10 kΩ+220 Ω → **HIGH**.
  - Pressed: NODE pulled to GND → console GPIO sees ~71 mV (10 k/220 divider) → **valid LOW**.
- **Pull location:** **controller-end**, referenced to the console-supplied 3V3 on pin 10. (The console does **not** also need to pull these lines, but enabling its internal pull-ups is harmless and adds redundancy.)
- **Power domain:** **3.3 V. The console MUST NOT drive 5 V onto these lines — the RP2040 is NOT 5 V tolerant.** The console supplies a clean 3.3 V (≤ a few mA) on pin 10.
- **ESD:** two 4-channel TVS arrays (SRV05-4A) on the controller clamp each signal between GND and the 3V3 rail **at the connector** (cable entry). The console may add its own, but is not required to.

## Debounce

- **Owned by the console firmware.** No hardware RC on the controller.
- Recommended: N-consecutive-sample or a 5–20 ms time-constant debounce per channel.

## Shield / grounding

- Round shielded cable; the braid/foil **drain is bonded single-point at the CONSOLE end only** (chassis/console GND). The controller end **floats** the drain — avoids a ground loop over the 2–3 m run.
- `GND` (pin 9) is the signal return for all 8 lines.

## Suggested RP2040 GPIO mapping (console side — non-binding, document yours here)

| Net | Suggested RP2040 GPIO |
|-----|-----------------------|
| BTN0..BTN7 | any 8 free GPIOs; configure as inputs, debounce in firmware |
| V3V3 | a 3.3 V supply pin (low current) |
| GND  | GND |

> The GPIO numbers are the **console repo's** decision — record the real mapping here once chosen, so both repos share one authority.
