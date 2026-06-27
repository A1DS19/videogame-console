# RP2350 Console — Build PLAN (task registry)

Tier: **complete-board**. Authoritative roadmap: `~/.claude/plans/2026-06-25_rp2350-console-board.md`.
Spec: `docs/specs/2026-06-25-rp2350-console-design.md` (frozen). Branch: `feat/rp2350-console-jitx`.
Build = `.venv/bin/jitx build <module.Design> --no-dependency-check` → `status: ok`. Runtime must be running.

Status legend: ☐ todo · ◐ in-progress · ☑ accept (build clean + reviewer-verified).

## Phase 0 — scaffold, sourcing, substrate
| # | Task | Status | Notes |
|---|---|---|---|
| 0.1 | Branch + scaffold + env | ☑ | venv (jitx 4.2.2), runtime up, `jitxlib.jlcpcb` (JLC04161H) verified. Reuse files pulled from arcade branch. |
| 0.2 | Source the BOM (Workflow, one agent/part class) — RoHS·stock·datasheet·alternates | ☑ | `docs/sourcing.md` + 12 datasheets. All LCSC'd: RP2350B C42415655, W25Q128JVSIQ C97521, X322512MSB4SI C9002, HDMI-001S C720616, TPD8S009 C471873, TLV62569 C141836, SMF5.0A C193402, PAM8302A C113367, B2B-PH-K-S C131337, L1 AOTA C42411119. Reused: B10B-XH-A C144400, SRV05-4A C20615829, USB-C C165948. **Open decisions ①–④ + corrections in sourcing.md.** |
| 0.3 | JLC04161H 4-layer substrate + 100 Ω diff | ☑ | `substrate.py` = `JLC04161H_7628()` (matches wireless); `SubstrateSmoke` builds `status: ok`. DRS_100 reserved for TMDS (Phase 3). |

## Phase 1 — component modeling (DB-probe first; TDD per component)
| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Reuse models: JstXH10, SRV05-4A (arcade), USB-C TYPEC31M12 (humidity) | ☑ | copied + 3D models (B10B-XH-A.stp, SRV05-4A.stp); all 3 test designs build `status: ok` |
| 1.2 | RP2350B QFN-80 ⚠️ top dead-board risk | ☑ | `rp2350b.py` QFN-80 generator (not in JITX DB), 81 ports, build ok, 3D attached. **Pin map ADVERSARIALLY VERIFIED CORRECT** (independent re-derivation vs datasheet Tables 1427-32: 0/80 mismatches; GPIO26-29=pads 27/28/36/37 not QFN-60-ADC; ADC=GPIO40-47; QSPI SD1/SD2 73↔74; GND=EP). ⚠️ Phase-4: confirm generator pad-1 orientation vs Fig 149. |
| 1.3 | HDMI Type-A connector + HDMI ESD array | ☑ | `hdmi_a.py` = DB Circuit wrapper (HDMI-001S, 23 ports, DB 3D); `tpd8s009.py` = 8-ch TMDS ESD (15 pins). ⚠️ TPD8S009 is **pure TMDS ESD — NO DDC/CEC/HPD** (those wire connector→MCU direct, matches spec). build ok |
| 1.4 | 3V3 buck + W25Q128 flash + 12 MHz crystal | ☑ | `tlv62569.py` SOT-23-5 (EN=1/GND=2/SW=3/VIN=4/FB=5; adjustable→FB divider; no PG pin); `w25q128jv.py` SOIC-8-208mil; `crystal_12mhz.py` 4-pad (XIN/XOUT/GND). build ok, 3D attached |
| 1.5 | PAM8302A amp + speaker connector (JST-PH 2-pin) | ☑ | `pam8302a.py` **MSOP-8** SOP gen (SD active-low; gain=2×(142k/Rin)); `jst_ph_2.py` PH 2.0mm 2-pin TH (SPK_P/SPK_N, drill 0.7mm). build ok, 3D attached |

## Phase 2 — circuit wiring (`main.py`, split by concern)
| # | Task | Status | Notes |
|---|---|---|---|
| 2.1 | Power tree + RP2350 core + flash + clock | ☑ | `main.py` ConsoleCircuit. USB-C (VBUS=B4A9/A4B9, CC 5.1k×2, D±=A6+B6/A7+B7 reversible→USB), **SMF5.0A K→VBUS/A→GND** (correct reverse-bias), buck (VIN/EN←VBUS, SW→2.2µH→V3V3, FB div→VFB 0.6V → 51.7k/11.5k), **core SMPS Pico-2-exact** (VREG_LX→L1.P1dot→DVDD=DVDD[0..2]+VREG_FB, C6/C7/C9, R3 33Ω), IOVDD×8+USB_OTP+QSPI_IO decoupled, flash QSPI, xtal+2×30pF, BOOTSEL/RUN/LED. build ok |
| 2.2 | HDMI / HSTX video chain | ☑ | 4 TMDS pairs GPIO12-19 → 0Ω series (placeholder) → TPD8S009 shunt → HDMI; shields/pin17/tabs→GND; +5V←VBUS via ferrite; DDC GPIO26/27 +4.7k pull-ups; HPD div→GPIO28; CEC/UTILITY NC. build ok |
| 2.3 | 2 controller ports + console ESD | ☑ | loop P1(GPIO0-7)/P2(GPIO8-11,20-23); JstXH10; pin9 GND, pin10 V3V3 via per-port ferrite+10µF bulk; 2× SRV05-4A/port; each BTN = GPIO+conn+ESD. build ok |
| 2.4 | PWM audio → PAM8302A → 8 Ω speaker | ☑ | GPIO24→RC LPF(3.3k/2.2nF ~22kHz)→1µF AC-couple→Rin(0Ω,~24dB)→amp IN+; SD←GPIO25 +100k PU (default-on); VDD←VBUS+1µF/10µF; BTL OUT→speaker. build ok |

## Phase 3 — constraints, placement, planes
| # | Task | Status | Notes |
|---|---|---|---|
| 3.1 | TMDS differential constraints (100 Ω, length-matched) | ☑ | DiffPair `>>` topos + ConstrainDiffPair (DRS_100, GND-ref, skew ~0, insertion-loss cap) under ReferencePlanes. **Restructured: top-level Design + SI constraints moved to `designs/console.py`** (grep convention); build target now `rp2350_console_jitx.designs.console.ConsoleBoard`; .gitignore anchored `/designs/` so source designs/ tracked. `f12bc4a` |
| 3.2 | Floorplan + GND planes + stitching | ☑ | `placement.py` (Opus; Fable 5 was unavailable). **72×66mm**, MCU central; HDMI+TPD8S009 LEFT edge → TMDS short+straight; USB-C+buck TOP; 2 JST-XH+ESD RIGHT (P1/P2); xtal/audio/speaker/buttons BOTTOM; **pin-anchored decoupling on Side.Bottom under pads**; pours GND=L1/L2/L4, V3V3=L3; 4× M3 NPTH (outline cutouts). Stitching vias = Phase 4 (KiCad). Refine placement at export. |
| 3.3 | Build clean (placement gate deferred to post-export) | ☑ | build `status: ok`; `--dump` 75 parts, 0 same-side overlaps (courtyard validator), connectors on edges, decaps bottom. check_placement.py gate = post-export (Phase 4). |

## Phase 4 — export → route → DRC → fab (`pcb-route`, GPU/human-gated)
| # | Task | Status | Notes |
|---|---|---|---|
| 4.x | Export (GPU/human) → check_placement → route (TMDS hand-tune) → DRC → fab | ☐ | stops for human export; then pcb-route + check_bom |

## Global gates (every task)
RoHS hard gate · plentiful stock · datasheet → `docs/datasheets/<MPN>.pdf` · compare alternates · **3D model on every part** · grep gates (`scripts/grep_gates.sh`) clean · reviewer-verified pin maps on every modeled IC.
