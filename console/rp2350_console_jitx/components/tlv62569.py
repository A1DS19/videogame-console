"""
Texas Instruments TLV62569DBVR — 2.5–5.5 V, 2 A synchronous step-down (buck)

Single-output adjustable buck converter, SOT-23-5 (DBV) package.
LCSC: C141836.

Pinout — datasheet "5 Pin Configuration and Functions", Pin Functions table
(SLVSDG1C, p.3, SOT23-5 / DBV column):
  Pin 1: EN   — enable logic input (high = on; do not float)
  Pin 2: GND  — ground
  Pin 3: SW   — switch node (connect output-filter inductor)
  Pin 4: VIN  — power supply input
  Pin 5: FB   — feedback (external resistor divider)
(NOTE: the common "1=SW…" SOT-23 buck mnemonic is WRONG for this part — the TI
table above is authoritative and was cross-confirmed by the JITX parts-DB part.)

DBV0005A (SOT-23-5) mechanical — datasheet PACKAGE OUTLINE drawing (p.21):
  E  (lead span):   2.60–3.00 mm
  E1 (body width):  1.45–1.75 mm
  D  (body length): 2.75–3.05 mm
  e  (pitch):       0.95 mm  (2X 0.95)
  b  (lead width):  0.30–0.50 mm  (5X)
  L  (lead length): 0.30–0.60 mm  (TYP)
  A  (height):      0.90–1.45 mm  (1.45 mm max)
"""

import jitx
from jitx import PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.toleranced import Toleranced
from jitxlib.landpatterns.generators.sot import SOT23_5, SOTLead, SOTLeadProfile
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.symbols.box import BoxSymbol, Column, PinGroup, Row


class Tlv62569(jitx.Component):
    """TI TLV62569 2 A synchronous buck regulator, SOT-23-5 (DBV)."""

    mpn = "TLV62569DBVR"
    manufacturer = "Texas Instruments"
    lcsc = "C141836"
    reference_designator_prefix = "U"
    datasheet = "https://www.ti.com/lit/ds/symlink/tlv62569.pdf"

    # Ports — one per physical pin, named per datasheet Pin Functions table.
    EN = Port()  # pin 1 — enable logic input
    GND = Port()  # pin 2 — ground
    SW = Port()  # pin 3 — switch node
    VIN = Port()  # pin 4 — supply input
    FB = Port()  # pin 5 — feedback

    # SOT-23-5 (DBV0005A) landpattern — dimensions from datasheet PACKAGE
    # OUTLINE drawing (p.21). Lead span E, body D/E1, pitch e, lead b/L.
    landpattern = (
        SOT23_5()
        .lead_profile(
            SOTLeadProfile(
                span=Toleranced.min_max(2.6, 3.0),
                pitch=0.95,
                type=SOTLead(
                    length=Toleranced.min_max(0.30, 0.60),
                    width=Toleranced.min_max(0.30, 0.50),
                ),
            )
        )
        .package_body(
            RectanglePackage(
                width=Toleranced.min_max(1.45, 1.75),
                length=Toleranced.min_max(2.75, 3.05),
                height=Toleranced.min_max(0.90, 1.45),
            )
        )
    )

    # BoxSymbol: inputs (VIN, EN) on the left, switch/feedback on the right,
    # ground down.
    symbol = BoxSymbol(
        rows=Row(
            left=PinGroup(VIN, EN),
            right=PinGroup(SW, FB),
        ),
        columns=Column(
            down=PinGroup(GND),
        ),
    )

    # 3D model: the exact TLV62569DBVR (LCSC C141836) STEP from the JITX parts
    # DB, copied to models/ so the board STEP export is complete (generator
    # landpatterns get no DB 3D automatically — see components/srv05_4a.py).
    # Resolves relative to this file: components/ -> project_root/models/.
    # Origin-centered manufacturer model; offset/rotation at the DB default
    # (HUMAN: confirm seating in the 3D view after export and adjust if needed).
    model3ds = [Model3D("../../models/TLV62569DBVR.stp")]

    # Explicit PadMapping — SOT23_5 linear pad numbering p[1]..p[5], per the
    # datasheet Pin Functions table (verified against the JITX-DB part mapping).
    def __init__(self) -> None:
        lp = self.landpattern
        self.mappings = [
            PadMapping(
                {
                    self.EN: [lp.p[1]],
                    self.GND: [lp.p[2]],
                    self.SW: [lp.p[3]],
                    self.VIN: [lp.p[4]],
                    self.FB: [lp.p[5]],
                }
            )
        ]


Device: type[Tlv62569] = Tlv62569
