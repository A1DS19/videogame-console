"""
JST B2B-PH-K-S(LF)(SN) — 2-circuit PH series vertical (top-entry) through-hole
board connector. Speaker output port (J) for the mono PAM8302A amp.

2.0 mm pitch, single-row, 2-pin top-entry wire-to-board header (LCSC C131337).
Post: copper alloy, tin-plated (datasheet p.3 "Header (Through-hole type)").
Recommended PCB drill: φ0.7 +0.1/0 mm (datasheet p.1, "PC board layout … Top
entry type", labelled φ0.7).
Pitch: 2.0 mm ±0.05 (datasheet p.1 layout "2±0.05"; p.3 table B2B-PH-K-S A=2.0).
Post length below PCB: ~3.4 mm (datasheet p.3 "Top entry type <2 circuits>"
side view, dimension "(3.4)").

Port→pin mapping (frozen by the speaker-port contract):
  SPK_P → pin 1  (No. 1 circuit, datasheet "Mark of No. 1 circuit") — amp OUT+
  SPK_N → pin 2  — amp OUT-

DB-probe note: Part(mpn="B2B-PH-K-S(LF)(SN)") resolves in the JITX parts DB with
the correct 2.0 mm-pitch TH footprint, a symbol, and a manufacturer 3D model, but
its drilled hole is φ0.9 mm — oversized vs the datasheet's φ0.7 +0.1/0 mm (0.7-0.8
mm). This component therefore models the landpattern from the datasheet (Header
generator + datasheet-faithful 0.7 mm drill) and re-uses only the DB 3D model
(models/B2B-PH-K-S.stp). See needs_orchestrator_review.
"""

import jitx
from jitx import PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.toleranced import Toleranced
from jitxlib.landpatterns.generators.header import Header
from jitxlib.landpatterns.leads import THLead
from jitxlib.landpatterns.pads import THPadConfig
from jitxlib.symbols.box import BoxSymbol, PinGroup, Row


class JstPH2(jitx.Component):
    """JST PH 2-pin 2.0 mm single-row vertical (top-entry) THT board connector."""

    mpn = "B2B-PH-K-S(LF)(SN)"
    manufacturer = "JST"
    lcsc = "C131337"
    reference_designator_prefix = "J"
    datasheet = "https://www.jst.com/wp-content/uploads/2021/01/ePH.pdf"

    # One port per physical pin (datasheet "Mark of No. 1 circuit" = pin 1).
    SPK_P = Port()  # pin 1 — speaker + (amp OUT+)
    SPK_N = Port()  # pin 2 — speaker - (amp OUT-)

    # Simple 2-pin connector symbol.
    symbol = BoxSymbol(
        rows=Row(left=PinGroup(SPK_P, SPK_N)),
    )

    # 3D model: the exact B2B-PH-K-S (LCSC C131337) STEP from the JITX parts DB,
    # copied to models/. The Header-generator landpattern carries no DB 3D
    # automatically, so attach it here to complete the board STEP export.
    # Resolves relative to this file: components/ -> project_root/models/.
    # The DB model is origin-aligned to the DB landpattern, whose pads differ
    # slightly from this generator's symmetric pad placement
    # (HUMAN: confirm seating in the 3D view after export and nudge if needed).
    model3ds = [Model3D("../../models/B2B-PH-K-S.stp")]

    def __init__(self) -> None:
        # PH series, 2-circuit, top-entry THT — dims from the datasheet:
        #   pitch = 2.0 mm        (p.1 layout "2±0.05"; p.3 table A=2.0)
        #   drill = φ0.7 mm       (p.1 "PC board layout … Top entry type", φ0.7)
        #   post length below PCB = 3.4 mm (p.3 "<2 circuits>" side view "(3.4)")
        #
        # The datasheet specifies the recommended PCB hole (φ0.7) directly, not a
        # post cross-section. The default IPC pad config inflates the hole well
        # beyond the lead, so override with a THPadConfig whose cutout = the
        # datasheet hole (the lead/template circle, 0.7 mm) and copper = that +
        # 0.5 mm -> a 1.2 mm annular pad (0.25 mm annular ring).
        self.landpattern = Header(
            num_leads=2,
            num_rows=1,
            lead=THLead(
                length=Toleranced(3.4, 0.3),
                width=Toleranced(0.7, 0.05),
            ),
            pitch=2.0,
        ).pad_config(THPadConfig(copper=0.5))

        lp = self.landpattern
        # Single-row linear numbering: lp.p[1] = No. 1 circuit, lp.p[2].
        self.mappings = [
            PadMapping(
                {
                    self.SPK_P: [lp.p[1]],
                    self.SPK_N: [lp.p[2]],
                }
            )
        ]


Device: type[JstPH2] = JstPH2
