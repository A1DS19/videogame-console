# RP2350 Console — ARCHITECTURE

Big-picture reference for sub-agents. Authority for *decisions* is `docs/specs/2026-06-25-rp2350-console-design.md`.
**Selected parts + LCSC + open decisions ①–④ live in `docs/sourcing.md`** (the BOM source of truth).

## Sourcing corrections (fold into modeling)
- **PAM8302A = MSOP-8** (not SOT-23-5): pins IN+, IN−, SD, GND, VDD, OUT+, OUT−. Gain = 2×(142kΩ/Rin).
- **HDMI TMDS ESD covers 8 lines** → 1× TPD8S009DSMR (8-ch inline) or 2× TPD4E02B04 (4-ch). Not one 4-ch part.
- **Core SMPS (RPi Pico-2 exact):** VREG_VIN ← 3V3 → internal buck → VREG_LX → **L1 (Abracon AOTA-B201610S3R3, 3.3µH 0806, POLARIZED — model the dot)** → DVDD 1.1V; C6/C7/C9 = 3×4.7µF 0402; **R3 33Ω** + C9 = VREG_AVDD RC filter.
- **Flash = W25Q128JV (3.3V)** — the look-alike JW (1.8V) shares the footprint and will NOT work.

## Power tree
```
USB-C VBUS (5V) ──┬─► 3V3 regulator (buck ≥1A pref) ──► V3V3 rail
                  │      └─► RP2350 IOVDD/ADC/USB rails, QSPI flash, both controller 3V3 feeds, HDMI DDC pull-ups
                  ├─► PAM8302A audio amp  (VDD = 5V, NOT 3V3; ~0.5A peak into 8Ω)
                  ├─► HDMI +5V (pin18) via ferrite/current-limit
                  └─► VBUS TVS/ESD
RP2350 core: internal SMPS → external core inductor + caps (Pico 2 power section), core rail decoupling.
```
- **Three nets:** `VBUS` (5V), `V3V3` (3.3V), `GND`.
- **On 5V:** PAM8302A, HDMI +5V pin. **On 3V3:** everything else.
- Each controller port: pin10 = 3V3 fed via a per-port ferrite + local bulk cap.

## RP2350B pin/GPIO budget (48 GPIO; ~30 used)
| Function | Count | Notes |
|---|---|---|
| HSTX video (4 TMDS pairs) | 8 | **fixed HSTX pins** — D0/D1/D2/CLK ± |
| 2× controller (8 BTN each) | 16 | a fixed 8-GPIO block per port, active-low in (internal pull-ups as backstop) |
| Audio | 2 | PWM out (1) + amp SD/enable (1) |
| DDC I2C | 2 | SCL/SDA + pull-ups (optional EDID) |
| HPD | 1 | hotplug via divider (optional) |
| Status LED | 1 | + series R |
Plus: XIN/XOUT (12 MHz xtal), QSPI (flash + BOOTSEL strap on QSPI_CS), RUN reset, USB DP/DM, power rails, GND/EP.

## Interface map (signal chains)
- **Video:** RP2350 HSTX → series R → HDMI ESD array → HDMI Type-A (D0±/D1±/D2±/CLK±). 100 Ω diff, length-matched, short.
- **Controllers (×2):** JST-XH 1×10 (B10B-XH-A) → console ESD (2× SRV05-4A/port) → RP2350 GPIO. Contract pins: 1–8 BTN0..7 (active-low), 9 GND, 10 3V3-out.
- **Audio:** RP2350 PWM → RC LPF (~20–30 kHz) → AC-couple → PAM8302A IN+ → speaker conn (JST-PH 2-pin, 8 Ω).
- **USB:** USB-C → CC 5.1k×2, D+/D− → RP2350 native USB (UF2). VBUS → power tree.
- **Flash:** W25Q128 (16 MB) on QSPI.

## Frozen controller contract (must match `arcade_controller_jitx`)
10-pin JST-XH: `1..8 = BTN0..BTN7` (active-low), `9 = GND`, `10 = 3V3`. 3.3 V domain. Console supplies 3V3, reads 8 active-low lines per port. Console-side ESD = SRV05-4A (matches controller-end). This is the contract the gamepad PCB already ships against — do not change pin roles.

## Module hierarchy (planned)
```
rp2350_console_jitx/
├── substrate.py            # JLC04161H 4-layer + 100Ω diff routing structure
├── components/
│   ├── jst_xh_10.py        # reuse (arcade)         srv05_4a.py  # reuse (arcade)
│   ├── usbc.py             # reuse (humidity TYPEC31M12)
│   ├── rp2350b.py          # ⚠️ QFN-80, top risk
│   ├── hdmi_typea.py  hdmi_esd.py
│   ├── regulator.py  flash_w25q.py  crystal_12mhz.py
│   └── pam8302a.py  speaker_conn.py
├── main.py                 # power+core / video / controllers / audio (split by concern)
└── placement.py            # floorplan + GND planes + stitching
```

## Top risks (carry into every relevant task)
1. **HDMI SI** — DRC won't catch it; 100 Ω controlled-Z + short matched TMDS + solid GND ref + ESD at connector.
2. **RP2350B QFN-80 pin map** — the dead-board risk; DB-probe first, reviewer-verify every pin vs datasheet. RP2350A (QFN-60) fallback if B unavailable (drops EDID/hotplug/expansion).
3. **HSTX→connector topology** — confirm series-R + ESD vs the Pimoroni Pico DV / Adafruit RP2350-HDMI reference before Task 2.2.
4. **RP2350 core SMPS** L/C — follow the Pico 2 power section exactly.
