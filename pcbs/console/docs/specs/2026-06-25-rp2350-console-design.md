# RP2350 Game Console — Board Design Spec

**Date:** 2026-06-25 · **Status:** brainstormed, pending user review → writing-plans
**Project (to be created):** `pcbs/rp2350_console_jitx/` · **Authoring:** JITX · **Route/fab:** `pcb-route`

## Scope

This spec covers the **PCB only**. The **firmware** (boot menu, DVI video driver, PWM audio, controller
reading, the games themselves) is a **separate sub-project** with its own spec, built after the board.
The two meet at: (a) the RP2350 pin assignment frozen here, and (b) the controller interface contract
(reused verbatim from `pcbs/arcade_controller_jitx/docs/interface-contract.md`).

## Goal

A bare-metal **RP2350 game console** that renders retro-class graphics to a TV/monitor over **HDMI**
(DVI signalling via the RP2350 HSTX peripheral), plays a **menu of built-in games** from flash, reads
**two** of the 8-button gamepad controllers over their frozen JST-XH contract, and outputs sound via a
an **onboard 8 Ω speaker driven by a Class-D amp**. USB-C powered + programmed.

## Decisions (resolved during brainstorming)
- **MCU:** RP2350**B** (QFN-80, 48 GPIO) — headroom for 2 controllers + HDMI + EDID/hotplug + audio + expansion.
- **Video:** DVI-over-HDMI via **HSTX** (RP2350's high-speed serial TX, purpose-built for this). HDMI Type-A out.
- **Software model:** **multi-game menu**, games baked into flash (no SD card).
- **Audio:** **PWM → RC filter → mono Class-D amp (PAM8302A) → onboard 8 Ω speaker** (2-pin connector).
  HDMI audio is *not* attempted (impractical to bit-bang).
- **Controllers:** **two** ports, each the exact frozen contract from `arcade_controller_jitx`.
- **Board:** **4-layer JLC04161H** (controlled-impedance 100 Ω TMDS diff pairs over a solid ground plane).

## Block architecture

```
            USB-C (5V + UF2 prog)
               │
        ┌──────┴───────┐   12 MHz xtal
   5V ─►│ 3V3 regulator │      │
        └──────┬───────┘   ┌──┴───────────────┐      HSTX 4 diff pairs      ┌─────────────┐
         3V3 ──┼──────────►│     RP2350B       ├──[series R]──[HDMI ESD]──►│ HDMI Type-A │──► TV
               │           │  (QFN-80)         │   (3×TMDS data + 1 clk)   └─────────────┘
               ├──QSPI────►│  + core L (SMPS)  │       +5V (pin18) ◄── 5V (ferrite/limit)
        16MB flash         │                   │       DDC I2C / HPD ◄──► GPIO (EDID/hotplug, optional)
               │           │                   │
               │           │   PWM ──[RC LPF]──► Class-D amp (PAM8302A, 5V) ──► 8 Ω speaker (2-pin conn)
               │           │                   │
      ┌────────┴───────┐   │   16 GPIO in ◄── [console-side ESD] ◄── P1 JST-XH (B10B-XH-A)
      │ BOOTSEL + RUN  │   │                ◄── [console-side ESD] ◄── P2 JST-XH (B10B-XH-A)
      └────────────────┘   │   3V3 + GND feed each port (per contract pins 9/10)
                           └───────────────────┘   status LED
```

## Subsystems

### 1. MCU + boot
- **RP2350B** (QFN-80). 12 MHz crystal on XIN/XOUT + load caps. Internal core SMPS → needs the external
  **core inductor + caps** per the RP2350 reference (Pico 2 power section); IOVDD/ADC/USB rails at 3.3 V,
  full decoupling.
- **Flash:** external **QSPI 16 MB** (e.g. W25Q128) on the dedicated QSPI pins — holds firmware + all game assets.
- **Boot/reset:** **BOOTSEL** button (QSPI_CS strap → UF2 bootloader) + **RUN** reset button.
- **Pin budget (48 GPIO):** HSTX video 8 (fixed pins) · 2×8 controllers 16 · mono audio PWM 1 + amp enable 1 ·
  status LED 1 · DDC I2C 2 · HPD 1 ≈ **30 used**, comfortable headroom for expansion.

### 2. Video — HDMI (DVI)
- RP2350 **HSTX** drives 4 TMDS differential pairs (D0±, D1±, D2±, CLK±) into an **HDMI Type-A receptacle**.
- **Series resistors** on the TMDS lines + a dedicated **HDMI ESD/TVS array** on all 4 pairs (the connector is
  exposed; ESD is mandatory). Follow the Pimoroni Pico DV / Adafruit RP2350-HDMI reference topology.
- HDMI **+5 V (pin 18)** sourced from board 5 V through a ferrite/current-limit. **DDC (SCL/SDA)** → RP2350 I2C
  with pull-ups (optional EDID read); **HPD (pin 19)** → a GPIO via divider (optional hotplug); **CEC** unconnected.
- **Target mode:** 640×480 @ 60 Hz (25.2 MHz pixel clock — the universally-accepted DVI base mode), 320×240
  framebuffer pixel-doubled, retro-class color. (Firmware concern; listed for context.)

### 3. Controller ports (×2)
- 2× **B10B-XH-A** (JST-XH 1×10) — identical to the controller's connector, **frozen contract**:
  pins 1–8 = BTN0..BTN7 (active-low in), pin 9 = GND, pin 10 = 3.3 V out (each port fed from the 3.3 V rail
  via a ferrite + local bulk cap; the controller's pull-ups draw ≈µA–mA).
- **Console-side ESD:** the 16 incoming lines arrive over 2–3 m cables → protect at the console too. Reuse the
  **SRV05-4A** pattern: **4× SRV05-4A** (2 per port), VCC → 3.3 V, GND → GND. (Series-R optional; the controller
  already has 220 Ω in-line.)
- Firmware enables RP2350 internal pull-ups as a backstop; the contract's controller-end pull-ups are primary.

### 4. Audio
- **Mono.** One RP2350 **PWM** output → **RC low-pass filter** (reconstruct analog, corner ~20–30 kHz) →
  AC-coupling cap → **PAM8302A mono filterless Class-D amplifier** → **2-pin speaker connector** (JST-PH 2.0,
  `B2B-PH-K`) for an **8 Ω speaker**.
- PAM8302A: single **5 V** supply (from USB VBUS), gain set by an input resistor (start ~24 dB), **SD/enable
  pin → a GPIO** (firmware mute / power-save), local bulk cap; filterless Class-D output (add ferrite beads on
  the outputs if EMI needs it). ~1.25 W into 8 Ω is plenty for a console.
- Stereo alternative (not chosen): PAM8403 + 2 speakers. Singular speaker/amp per the requirement → mono.

### 5. Power + USB
- **USB-C** receptacle: 5 V VBUS (power), CC1/CC2 5.1 kΩ sink resistors, D+/D− → RP2350 native USB (UF2 + HID later).
- **5 V → 3.3 V** regulator sized for RP2350 (overclocked HSTX) + flash + 2 controllers + HDMI +5 V load
  (~0.5–1 A headroom). Buck preferred (efficiency) or a stout LDO. ESD/TVS on VBUS.
- HDMI +5 V (pin 18) tapped from VBUS through a ferrite/limit.
- **Audio amp (PAM8302A) runs off 5 V VBUS** (not 3.3 V) — peak ~0.5 A into 8 Ω at full volume; budget VBUS +
  the USB-C source accordingly, with a local bulk cap at the amp.

### 6. Layout / signal integrity (4-layer JLC04161H)
- Stackup: **L1 signal / L2 GND / L3 power(+GND) / L4 signal** (JLC04161H). TMDS pairs routed on **L1 over the
  L2 GND plane**, **100 Ω differential** (JITX `jitxlib.jlcpcb` JLC04161H + its 100 Ω differential routing
  structure), intra-pair length-matched, kept short (HDMI connector near the RP2350).
- **HDMI, USB-C, both controller ports, and the speaker connector on board edges** (external mates — per the family-
  grouping rule: external connectors go on the perimeter). Each connector's **ESD array hard against it**.
- Solid GND plane + **GND stitching vias** (the wireless-board technique). RP2350 decoupling pin-anchored;
  flash + crystal tight to the MCU.
- 4× **M3 NPTH** mounting holes with keepouts.

## Reuse
- **Interface contract + JST-XH connector + SRV05-4A** model carry over from `arcade_controller_jitx`.
- **JLC04161H 4-layer substrate + 100 Ω diff routing + GND stitcher + pcb-route** flow carry over from
  `wireless_lighting_jitx`.

## Toolchain
- **JITX**: `jitx-substrate-modeler` (JLC04161H + 100 Ω differential routing structure),
  `jitx-interconnect-constraints` (TMDS pair + length-match constraints), `jitx-component-modeler`
  (RP2350B QFN-80, HDMI Type-A, USB-C, flash, PAM8302A amp, speaker connector, regulator, HDMI-ESD),
  `jitx-circuit-builder`.
- **Route/fab:** `pcb-route` (Specctra/Freerouting round-trip, DRC, JLCPCB fab) — **needs a GPU/human export**
  like the controller (headless export is blank).
- **3D models on every part** (standing rule — DB parts carry them; hand-modeled parts get one attached).

## Risks / open items
- **HDMI SI** — the highest-risk area. Mitigated by 100 Ω controlled impedance, short matched TMDS, solid GND
  reference, ESD at the connector. Validate against a real TV at bring-up; DRC won't catch SI.
- **RP2350B footprint/availability** — QFN-80; confirm JLCPCB stock + model the footprint carefully (pin map is
  the dead-board risk, like every IC). RP2350A (QFN-60) is the fallback if B is unavailable (drops EDID/hotplug/expansion).
- **HSTX-direct-to-connector** drive — confirm the series-R + ESD topology against the Pimoroni/Adafruit RP2350
  HDMI reference before committing.
- **RP2350 core SMPS inductor** — follow the Pico 2 reference power section exactly.
- **Firmware** (separate spec) is substantial: DVI timing on HSTX, the menu, PWM audio, 2-controller input, games.

## Test plan (board bring-up)
1. **Power:** 3.3 V + RP2350 core rail good; no shorts; current sane.
2. **USB:** enumerates as RP2350 UF2 bootloader (BOOTSEL).
3. **Video:** flash a DVI test-pattern firmware → image on a TV/monitor (the real HDMI SI check).
4. **Controllers:** plug both gamepads → all 16 buttons read correctly per the contract.
5. **Audio:** PWM tone → amp → 8 Ω speaker (verify amp enable + no oscillation).

## Out of scope (this spec)
- **Firmware** (own spec): boot menu, HSTX DVI driver, PWM audio engine, 2-controller input, the games.
- Enclosure / 2-player ergonomics.
- HDMI audio, CEC, HDCP.
