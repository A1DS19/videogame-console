# RP2350 Console — Sourcing (BOM)

Phase 0 Task 0.2. Live JLCPCB/LCSC data sourced 2026-06-27 (one research agent per part class).
Gates applied per part: **RoHS** (hard), **plentiful stock + JLCPCB-assemblable** (LCSC C-number
recorded for DB-probe), **≥2 alternates compared**, **datasheet → `docs/datasheets/<MPN>.pdf`**.
Stock is volatile (esp. the RP2350 family) — **re-confirm before fab**.

Library: **Basic/Preferred** = free assembly; **Extended** = one-time ~$3/part setup fee (no MOQ).

## Selected BOM

| Ref(s) | Role | MPN | LCSC | Package | Lib | Qty | ~$ea | Datasheet |
|---|---|---|---|---|---|---|---|---|
| U1 | MCU | **RP2350B** | C42415655 | QFN-80-EP 10×10, 0.4mm | Ext | 1 | 1.25 | RP2350.pdf |
| U2 | QSPI flash 16MB (3.3V **JV**) | **W25Q128JVSIQ** | C97521 | SOIC-8-208mil | **Basic** | 1 | 1.97 | W25Q128JVSIQ.pdf |
| Y1 | 12 MHz crystal (CL=20pF) | **X322512MSB4SI** | C9002 | SMD3225-4P | **Basic** | 1 | 0.07 | X322512MSB4SI.pdf |
| C(xtal) | Crystal load caps 30pF C0G | 0603CG300J500NT | C1658 | 0603 | **Basic** | 2 | ~0 | (generic) |
| J(hdmi) | HDMI Type-A recept., SMD R/A | **HDMI-001S** | C720616 | HDMI-A 19P SMD R/A | Ext | 1 | 0.27 | HDMI-001S.pdf |
| D(hdmi) | TMDS ESD (see decision ①) | **TPD8S009DSMR** | C471873 | SON-15 | Ext | 1 | 1.31 | TPD8S009DSMR.pdf |
| U3 | 5V→3.3V buck (see ②) | **TLV62569DBVR** | C141836 | SOT-23-5 | Ext | 1 | 0.07 | TLV62569.pdf |
| D(vbus) | VBUS 5V TVS (unidir.) | **SMF5.0A** | C2759874 | SOD-123FL | Ext | 1 | 0.03 | SMF5.0A.pdf |
| U4 | Mono Class-D amp (⚠️ **MSOP-8**) | **PAM8302AASCR** | C113367 | **MSOP-8** | Ext | 1 | 0.21 | PAM8302AASCR.pdf |
| J(spk) | Speaker conn JST-PH 2-pin THT | **B2B-PH-K-S(LF)(SN)** | C131337 | PH 2.0mm 1×2 TH | Ext | 1 | 0.03 | B2B-PH-K-S.pdf |
| L1 | Core SMPS inductor 3.3µH (polarized) | **AOTA-B201610S3R3-101-T** | C42411119 | 0806 (2016M) | Ext | 1 | 0.27 | AOTA-…pdf |
| C6/C7/C9 | Core SMPS caps 4.7µF 0402 X5R | CL05A475MP5NRNC | C23733 | 0402 | **Basic** | 3 | ~0 | CL05A475…pdf |
| R3 | AVDD RC-filter 33Ω 0402 | (Basic 33R 0402) | TBD@model | 0402 | Basic | 1 | ~0 | — |
| J1/J2 | Controller ports JST-XH 1×10 (reuse) | **B10B-XH-A(LF)(SN)** | C144400 | XH 2.5mm 1×10 TH | Ext | 2 | 0.13 | (reused) |
| D1–D4 | Controller ESD (reuse, 2/port) | **SRV05-4A** | C20615829 | SOT-23-6 | **Preferred** | 4 | 0.03 | (reused) |
| J(usb) | USB-C recept. (reuse) | **TYPE-C-31-M-12** | C165948 | USB-C 16P SMD R/A | Ext | 1 | 0.13 | (reused) |

Plus board-level passives (sourced at modeling time, all Basic 0603/0402): RP2350 per-pin decoupling
(100nF ×~10 + 4.7µF on far DVDD), buck external L (~2.2µH) + in/out caps (10µF/22µF) + FB divider (2×R),
USB-C CC 5.1k ×2, TMDS series R ×8, audio RC LPF (R+C) + AC-couple cap + gain R (Rin; gain = 2×(142k/Rin)),
per-port 3V3 ferrite + bulk cap ×2, status LED + series R, DDC pull-ups ×2, HPD divider.

## Cost roll-up (rough, 1-off)
Actives + connectors ≈ **$6.3/board**; board-level passives ≈ **$0.3/board** → **~$6.6/board** in parts.
Plus a **one-time ~$30** JLCPCB Extended-part setup (≈10 Extended parts × ~$3): RP2350B, HDMI conn, HDMI
ESD, buck, VBUS TVS, PAM8302A, speaker conn, B10B-XH-A, USB-C, core inductor. (Flash/crystal/caps = Basic,
SRV05-4A = Preferred → free.) Drops sharply at volume (most actives ~½ price @1k).

## Open decisions (surface at the Phase-0 check-in)
**① HDMI TMDS ESD — single vs dual.** Default chosen: **1× TPD8S009DSMR** (8-ch, sits *inline* behind the
connector → cleanest TMDS routing, one part). Cheaper/deeper-stock alt: **2× TPD4E02B04DQAR** (C106794,
0.25pF/ch, ~$0.29ea, USON-10) — lower cap + lower cost but two parts and ~$6 more one-time setup. Pick at modeling.

**② Flash strategy — 16MB external vs 2MB integrated.** Spec chose **RP2350B + W25Q128 (16MB)**. Alternative
**RP2354B** (C39843328, same QFN-80, **2MB flash stacked inside** → removes U2 + QSPI routing, ~$1.55, ~453 stk).
Only viable if all games fit in 2MB. Recommendation: **stay 16MB external** per spec unless you want the simpler board.

**③ Crystal — Basic 20pF vs Pico-2-exact.** Default **X322512MSB4SI** (Basic, CL=20pF, 2×30pF caps). De-risk
alt = **ABM8-272-T3** (C20625731, the *exact* Pico 2 crystal, CL=10pF + 2×15pF C1644, Extended). Basic is fine
(RP2350 XOSC drives 20pF); pick the Abracon only if you want byte-identical Pico-2 startup behavior.

**④ Regulator — buck vs LDO.** Default **buck TLV62569DBVR** (efficient, cool; needs ext L + FB divider + caps).
LDO fallback **AMS1117-3.3** (C6186, Basic/free) burns ~1.7W @1A → hot; not recommended for an always-on console.

## Corrections this sourcing forced (vs spec/plan)
- **PAM8302A is MSOP-8, not SOT-23-5** (Diodes ships only MSOP-8/SO-8/U-DFN). Model as MSOP-8 (IN+, IN−, SD, GND, VDD, OUT+, OUT−). ARCHITECTURE/PLAN updated.
- **HDMI ESD must cover 8 TMDS lines** → 1× 8-ch (TPD8S009) or 2× 4-ch (TPD4E02B04); not a single 4-ch part.
- **Core SMPS = the exact RPi Pico-2 parts**: L1 Abracon AOTA-B201610S3R3-101-T (3.3µH 0806 **polarized** — model the polarity dot), C6/C7/C9 3×4.7µF 0402, **R3 33Ω** AVDD RC filter. VREG_VIN ← 3V3, DVDD = 1.1V core.
- **Flash must be the 3.3V "JV"** variant — the look-alike W25Q128**JW** (1.8V) shares the footprint and will not work.

## Component-modeling notes (Phase 1 DB-probe targets)
DB-probe `Part(mpn=...)` with these LCSC: C42415655, C97521, C9002, C720616, C471873, C141836, C2759874,
C113367, C131337, C42411119, C23733, C144400, C20615829, C165948. Reviewer-verify every IC pin map vs the
saved datasheet (RP2350B QFN-80 is the dead-board risk — datasheet §1.2.1.2). 3D model required on every part.
SMF5.0A is mpn-resolved (no pinned LCSC), so the fab BOM ships the as-built reel **C2759874** — a
JEDEC-equivalent SMF5.0A/SOD-123FL; any RoHS SMF5.0A in SOD-123FL is acceptable.
