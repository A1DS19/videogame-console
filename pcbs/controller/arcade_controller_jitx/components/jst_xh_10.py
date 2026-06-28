"""
JST B10B-XH-A(LF)(SN) — 10-circuit XH series vertical through-hole board connector

2.5 mm pitch, single-row, 10-pin top-entry wire-to-board header (LCSC C144400).
PCB post: 0.64 mm square brass, tin-plated.
Drill: φ0.9 mm (9-circuits-or-more, datasheet p.2 fig "9 circuits or more").
Lead length below PCB: ~3.4 mm (datasheet p.5, header top-entry side-view).

Port→pin mapping (frozen by docs/interface-contract.md):
  BTN0–BTN7 → pins 1–8  (button signal returns, active-low)
  GND        → pin 9
  V3V3       → pin 10   (3.3 V supply from console)
"""

import jitx
from jitx import PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.toleranced import Toleranced
from jitxlib.landpatterns.generators.header import Header
from jitxlib.landpatterns.leads import THLead
from jitxlib.symbols.box import BoxSymbol, PinGroup, Row


class JstXH10(jitx.Component):
    """JST XH 10-pin 2.5 mm single-row vertical THT board connector."""

    mpn = "B10B-XH-A(LF)(SN)"
    manufacturer = "JST"
    reference_designator_prefix = "J"
    datasheet = "https://www.jst.com/wp-content/uploads/2021/01/eXH.pdf"

    # 8 button signal lines (pins 1–8)
    BTN0 = Port()
    BTN1 = Port()
    BTN2 = Port()
    BTN3 = Port()
    BTN4 = Port()
    BTN5 = Port()
    BTN6 = Port()
    BTN7 = Port()

    # Power / ground (pins 9–10)
    GND = Port()
    V3V3 = Port()

    # Symbol: button signals on left, power on right
    symbol = BoxSymbol(
        rows=Row(
            left=PinGroup(BTN0, BTN1, BTN2, BTN3, BTN4, BTN5, BTN6, BTN7),
            right=PinGroup(GND, V3V3),
        ),
    )

    # 3D model: the exact B10B-XH-A JST-XH 1x10 (LCSC C144400) STEP from the JITX
    # parts DB, downloaded to models/. The Header-generator landpattern carries no
    # DB 3D automatically, so attach it here to complete the board STEP export.
    # Resolves relative to this file: components/ -> project_root/models/.
    # Origin-centered manufacturer model; offset/rotation at the DB default
    # (HUMAN: confirm seating in the 3D view after export and adjust if needed).
    model3ds = [Model3D("../../models/B10B-XH-A.stp")]

    def __init__(self) -> None:
        # XH series PCB post: 0.64 mm square (datasheet p.5 header drawing).
        # Drill: φ0.9 mm for ≥9 circuits top-entry type (datasheet p.2).
        # Lead length below PCB: 3.4 mm nominal (datasheet p.5 side view).
        self.landpattern = Header(
            num_leads=10,
            num_rows=1,
            lead=THLead(
                length=Toleranced(3.4, 0.3),
                width=Toleranced(0.64, 0.05),
            ),
            pitch=2.5,
        )

        lp = self.landpattern
        # Single-row linear numbering: lp.p[1] … lp.p[10]
        # Order per interface-contract.md: BTN0–BTN7, GND, V3V3
        self.mappings = [
            PadMapping(
                {
                    self.BTN0: [lp.p[1]],
                    self.BTN1: [lp.p[2]],
                    self.BTN2: [lp.p[3]],
                    self.BTN3: [lp.p[4]],
                    self.BTN4: [lp.p[5]],
                    self.BTN5: [lp.p[6]],
                    self.BTN6: [lp.p[7]],
                    self.BTN7: [lp.p[8]],
                    self.GND:  [lp.p[9]],
                    self.V3V3: [lp.p[10]],
                }
            )
        ]


Device: type[JstXH10] = JstXH10
