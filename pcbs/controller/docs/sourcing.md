# arcade_controller_jitx — sourcing (verified against JLCPCB/LCSC catalog 2026-06-24)

All parts live-sourced via the JLCPCB DB (kicad-mcp `search_jlcpcb_parts`/`get_jlcpcb_part`) and
cross-checked on LCSC. Criteria per `pcb-route` → Component sourcing: **RoHS (hard gate)** ·
plentiful stock · compared alternates · 0603 passives · datasheet saved to `docs/datasheets/<MPN>.pdf`.

| Ref | Function | MPN | LCSC | Pkg | Lib | Stock | RoHS | DS |
|---|---|---|---|---|---|---|---|---|
| SW1–SW8 | Tactile button (12×12 THT, gamepad) | K2-1103DP-Q4SW-04 | C136701 | 12×12 THT 4-pin, H=12 mm | Extended | 23,059 | ✓ | ✓ |
| J1 | Board connector (10-cond keyed tether) | B10B-XH-A(LF)(SN) | C144400 | JST-XH 2.5 mm 1×10 vert THT | Extended | 13,814 | ✓ | ✓ |
| D1,D2 | TVS/ESD array, 4-ch ×2 (rail-clamp) | SRV05-4A | C20615829 | SOT-23-6 | **Preferred** | 44,549 | ✓ | ✓ |
| Rs0–Rs7 | Series-R 220 Ω (ESD/EOS limit, 8 lines) | CR0603-JW-221ELF | C1851952 | 0603 ±5% 100 mW | Extended | 195 k | ✓ | ✓ |
| Rpu0–Rpu7 | Pull-up 10 kΩ (8 lines) | 0603WAF1002T5E | C25804 | 0603 ±1% 100 mW | **Basic** | 22.3 M | ✓ | ✓ |

> **220 Ω MPN pinned for a 3D model (build artifact, 2026-06-25):** the unpinned 220 Ω
> optimizer pick (`0603WAF2200T5E`/C22962) resolved to a JITX-DB part with **no 3D model**, so
> its footprint exported without a STEP (19 of 27 footprints were model-less). It is now pinned
> in `main.py` to **Bourns `CR0603-JW-221ELF`** — the same `CR0603-JW` series as the 10 kΩ
> pull-ups, which carries the shared 0603 DB STEP (`jitx_model_3d_id 64d1a938b789d8dc4b8658b6`).
> Value/size unchanged (220 Ω, 0603). If a Basic-library 220 Ω is preferred for cost, `0603WAF2200T5E`
> remains valid electrically — but verify it gains a 3D model in the export before reverting.

**Per-board board-side BOM ≈ $0.69** (8 switches @ $0.057, J1 @ $0.134, 2× SRV05-4A @ $0.029, 16× 0603 R @ ~$0.001).
One-time JLCPCB Extended feeder fees ≈ $6 (switch + connector; the SRV05-4A is **Preferred** = no fee).

> **TVS choice (resolved at build):** the technically-ideal part was **RCLAMP3328P** (8-ch, 3.3 V standoff,
> DFN3810-9) — but it is **NOT in the JITX `jitxlib-parts` DB** (a curated subset), so it would require a
> hand-imported leadless 0.4 mm-pitch footprint for a marginal benefit. The plan's documented fallback,
> **2× SRV05-4A** (SOT-23-6, 4-ch each), resolves cleanly from the JITX DB, is **JLC Preferred** (no feeder
> fee, 44.5k stock), and is the lower-risk choice. Trade-off: SRV05 is **5 V standoff** (not 3.3 V) — fine for
> switch-to-GND active-low lines; its VCC pin is tied to the board's `V3V3` rail so it clamps each I/O between
> GND and 3.3 V. Both RCLAMP3328P and TPD8E003 datasheets remain in `docs/datasheets/` for reference.

## Off-board (hand-assembled cable tether — NOT on the JLCPCB P&P BOM)
| Function | MPN | LCSC | Notes |
|---|---|---|---|
| Cable housing | XHP-10 | C144408 | 1×10 JST-XH crimp housing |
| Cable crimps | SXH-001T-P0.6 | C140573 | 22–28 AWG, 10 needed |
| Cable | round shielded 10-conductor, 2–3 m | — | Mouser/Belden/Alpha; drain bonded single-point at console end |
| (optional) Keycap ×8 | SHOU HAN A24 | C49451761 | ⚠️ thin stock (~400/color), **hand-pressed** — order from LCSC, NOT JLC-assembled |

## 3D models (board STEP completeness — medi-pal standing rule)
Every footprint must carry a `(model …)` ref so the board STEP export is complete. DB-resolved
passives inherit their STEP from the JITX parts DB automatically; the 3 hand-modeled components
do not, so the exact-MPN STEP is pulled from the JITX DB and committed under `models/`, then attached
in source via `jitx.model3d.Model3D` (relative path `../../models/<MPN>.stp`):

| Ref | Component | STEP file (committed) | JITX DB model id | Attached in |
|---|---|---|---|---|
| J1 | JST-XH B10B-XH-A (C144400) | `models/B10B-XH-A.stp` | `64d1a40db789d8dc4b85c2b4` | `components/jst_xh_10.py` (Component) |
| D1,D2 | SRV05-4A (C20615829) | `models/SRV05-4A.stp` | `64d1415db789d8dc4b7a40f3` | `components/srv05_4a.py` (Component) |
| SW1–SW8 | K2-1103DP-Q4SW-04 (C136701) | `models/K2-1103DP-Q4SW-04.stp` | `64d1510eb789d8dc4b7c1658` | `components/tactile_button.py` (Landpattern) |

Offsets/rotations are left at the DB default `(0,0,0)`/`(1,1,1)`. The DB flagged these STEPs with
"unknown transformation coordinates — validate before use", so **after the GPU export, visually check
each part's seating in the 3D view** and adjust `Model3D(position=…, rotation=…)` if a part floats or
is mis-oriented. The 220 Ω + 10 kΩ resistors get their 3D from the DB part (see the resistor note above).

## Mounting
4× **M3 NPTH Ø3.2** corner holes **with keepouts** (note only, not a BOM line; `pcb-route` `check_placement` R126 gate enforces the keepout).

## Notes / alternates considered
- **TVS (D1) is the thinnest-stock line (2,710).** If live stock has dropped at build time, fall back to **2× SRV05-4A** (C20615829, JLC **Preferred** = no feeder fee, 44.5k stock, SOT-23-6, 4-ch each). Trade-off: SRV05 is **5 V standoff** (not 3.3 V) — still fine for switch-to-GND lines, marginally less optimal on a strict 3.3 V rail. The exact-named TI **TPD8E003** (C2867469) was **rejected** — only ~49 in stock + Extended.
- **No JLC Basic tact-switch or connector exists** — the Basic library is essentially R/C/discretes. Switch + connector + TVS are unavoidably Extended. Use ONE switch MPN board-wide to pay the switch feeder fee once.
- **Switch force/feel:** K2-1103DP is **2.5 N** (firm, positive — heavier than a typical 1.6 N tact). Lighter option: ALPS `SKHCBEA010` (C139752, 1.3 N) but pricier + square actuator (no cheap round cap). Shorter actuator variant `K2-1103DP-G4SW-04` (C136707, H=7 mm) if 12 mm stands too proud — same 12×12 footprint, thinner stock (552).
- **Resistors:** both 220 Ω + 10 kΩ are UNI-ROYAL 0603WAF Basic (no feeder fee, M+ stock). Series 220 Ω chosen mid-window (100–470 Ω acceptable); 100 Ω (C22775) / 330 Ω (C23138) are in-family Basic alternates if edge-rate vs ESD-limiting needs tuning.

## Dogfood / sourcing findings (this build)
- JLCPCB DB free-text search is brittle on multi-word/decimal queries — query by series prefix (e.g. `RCLAMP`, `K2-1103`) or `get_jlcpcb_part` by known LCSC code.
- Real datasheet PDFs live on `wmsc.lcsc.com`/`datasheet.lcsc.com`; `www.lcsc.com/datasheet/*.pdf` serves **HTML stubs** — validate `file` type.
- All 15 datasheets (incl. alternates) saved to `docs/datasheets/`.
