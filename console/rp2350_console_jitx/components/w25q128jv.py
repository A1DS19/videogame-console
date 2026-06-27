"""
Winbond W25Q128JVSIQ — 128 Mbit (16 MB) 3.3 V QSPI/SPI NOR flash, SOIC-8 208-mil.

LCSC: C97521. Package Code S = 8-pin SOIC 208-mil (wide body), 2.7–3.6 V "JV".
(NOT the 1.8 V "JW" look-alike — see docs/sourcing.md.)

Pinout (datasheet p.5 §3.1 / §3.3, Figure 1a "8-pin SOIC 208-mil", Top View):
  Pin 1: /CS              Chip Select Input
  Pin 2: DO (IO1)         Data Output / Data I/O 1
  Pin 3: /WP (IO2)        Write Protect / Data I/O 2
  Pin 4: GND              Ground
  Pin 5: DI (IO0)         Data Input / Data I/O 0
  Pin 6: CLK              Serial Clock Input
  Pin 7: /HOLD or /RESET (IO3)   Hold/Reset / Data I/O 3
  Pin 8: VCC             Power Supply

SOIC 208-mil mechanical (datasheet p.67 §10.1, Package Code S; min/max in mm):
  A  (overall height): 1.75 – 2.16
  b  (lead width):     0.35 – 0.48
  D  (body length):    5.18 – 5.38   (along the pin rows)
  E1 (body width):     5.13 – 5.33   (molded body, between the lead rows)
  e  (pitch):          1.27 BSC
  H  (lead span):      7.70 – 8.10   (lead tip-to-tip across the rows)
  L  (lead foot):      0.50 – 0.80
"""

import jitx
from jitx import PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.toleranced import Toleranced
from jitxlib.landpatterns.generators.soic import SOIC
from jitxlib.landpatterns.leads import LeadProfile, SMDLead
from jitxlib.landpatterns.leads.protrusions import BigGullWingLeads
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.symbols.box import BoxSymbol, Column, PinGroup, Row


class W25Q128JV(jitx.Component):
    """Winbond W25Q128JVSIQ 128 Mbit QSPI NOR flash, SOIC-8 208-mil."""

    mpn = "W25Q128JVSIQ"
    manufacturer = "Winbond Electronics"
    lcsc = "C97521"
    reference_designator_prefix = "U"
    datasheet = (
        "https://www.winbond.com/resource-files/w25q128jv%20revj%2003272018%20plus.pdf"
    )

    # Ports — one per physical pin, named per datasheet §3.3 (pin 1..8).
    # Quad-SPI I/O lines carry both their legacy SPI name and the IOx alias.
    CS = Port()  # pin 1 — /CS chip select (active low)
    IO1_DO = Port()  # pin 2 — DO / IO1
    IO2_WP = Port()  # pin 3 — /WP / IO2 (active-low write protect)
    GND = Port()  # pin 4 — ground
    IO0_DI = Port()  # pin 5 — DI / IO0
    CLK = Port()  # pin 6 — serial clock
    IO3_HOLD = Port()  # pin 7 — /HOLD or /RESET / IO3
    VCC = Port()  # pin 8 — power supply

    # SOIC-8 208-mil landpattern — wide body. Dimensions from datasheet p.67
    # §10.1 (Package Code S). NOT .narrow() and NOT the generic .wide() helper
    # (which forces a 7.5 mm body); E1 here is ~5.23 mm, so set dims explicitly.
    landpattern = (
        SOIC(num_leads=8)
        .lead_profile(
            LeadProfile(
                pitch=1.27,
                span=Toleranced.min_max(7.70, 8.10),  # H
                type=SMDLead(
                    length=Toleranced.min_max(0.50, 0.80),  # L
                    width=Toleranced.min_max(0.35, 0.48),  # b
                    lead_type=BigGullWingLeads,
                ),
            )
        )
        .package_body(
            RectanglePackage(
                length=Toleranced.min_max(5.18, 5.38),  # D
                width=Toleranced.min_max(5.13, 5.33),  # E1
                height=Toleranced.min_max(1.75, 2.16),  # A
            )
        )
    )

    # BoxSymbol: SPI/QSPI signals on the left; power split top/bottom.
    symbol = BoxSymbol(
        rows=Row(
            left=PinGroup(CS, CLK, IO0_DI, IO1_DO, IO2_WP, IO3_HOLD),
        ),
        columns=Column(
            up=PinGroup(VCC),
            down=PinGroup(GND),
        ),
    )

    # 3D model: the exact W25Q128JVSIQ (LCSC C97521) STEP resolved from the JITX
    # parts DB (Part(mpn=...) → 3d-models/jitx-64d18a78b789d8dc4b82e2c6.stp),
    # copied into the committed models/ dir. Generator landpatterns carry no DB
    # 3D automatically, so attach it here to complete the board STEP export.
    # Resolves relative to this file: components/ -> project_root/models/.
    # (HUMAN: confirm seating in the 3D view after export and adjust if needed.)
    model3ds = [Model3D("../../models/W25Q128JVSIQ.stp")]

    # Explicit PadMapping — standard SOIC linear numbering p[1..8] matches the
    # datasheet pin numbers (p.5 §3.3): pin 1 = /CS, around to pin 8 = VCC.
    def __init__(self) -> None:
        lp = self.landpattern
        self.mappings = [
            PadMapping(
                {
                    self.CS: [lp.p[1]],
                    self.IO1_DO: [lp.p[2]],
                    self.IO2_WP: [lp.p[3]],
                    self.GND: [lp.p[4]],
                    self.IO0_DI: [lp.p[5]],
                    self.CLK: [lp.p[6]],
                    self.IO3_HOLD: [lp.p[7]],
                    self.VCC: [lp.p[8]],
                }
            )
        ]


Device: type[W25Q128JV] = W25Q128JV
