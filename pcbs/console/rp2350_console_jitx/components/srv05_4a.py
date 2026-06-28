"""
R+O (Zhuhai Hongjiacheng) SRV05-4A - 4-Channel TVS/ESD Protection Array

Uni-directional 5V ultra-small-capacitance ESD suppressor, SOT-23-6L.
LCSC: C20615829.

Pinout (datasheet page 1, Function Diagram — pin numbering is SOT-23-6 standard):
  Pin 1: IO1   (I/O line, left-column top)
  Pin 2: GND   (ground / TVS cathode reference, left-column mid)
  Pin 3: IO2   (I/O line, left-column bottom)
  Pin 4: IO3   (I/O line, right-column bottom)
  Pin 5: VCC   (steering-diode upper rail, right-column mid)
  Pin 6: IO4   (I/O line, right-column top)

SOT23-6L mechanical (datasheet page 1, same package as USBLC6 reference):
  D  (body length): 2.70–3.10 mm
  E  (lead span):   2.60–3.00 mm
  E1 (body width):  1.50–1.80 mm
  e  (pitch):       0.95 mm nominal
  b  (lead width):  0.30–0.50 mm
  L  (lead length): 0.30–0.60 mm
  A  (height):      1.00–1.30 mm
"""

import jitx
from jitx import PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.toleranced import Toleranced
from jitxlib.landpatterns.generators.sot import SOT23_6, SOTLeadProfile
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.symbols.box import BoxSymbol, Column, PinGroup, Row


class Srv05_4A(jitx.Component):
    """4-channel uni-directional TVS/ESD protection array, SOT-23-6."""

    mpn = "SRV05-4A"
    manufacturer = "Zhuhai Hongjiacheng Technology Co., Ltd"
    lcsc = "C20615829"
    reference_designator_prefix = "D"
    datasheet = "https://www.lcsc.com/datasheet/lcsc_datasheet_2402181546_Zhuhai-Hongjiacheng-Technology-SRV05-4A_C20615829.pdf"

    # Ports — one per physical pin, named per datasheet Function Diagram.
    IO1 = Port()  # pin 1 — protected I/O line
    GND = Port()  # pin 2 — ground (TVS cathode-side reference)
    IO2 = Port()  # pin 3 — protected I/O line
    IO3 = Port()  # pin 4 — protected I/O line
    VCC = Port()  # pin 5 — steering-diode upper rail
    IO4 = Port()  # pin 6 — protected I/O line

    # SOT-23-6 landpattern — dimensions from datasheet page 1 mechanical drawing,
    # identical package to USBLC6 reference part (same lead span, body dimensions).
    landpattern = (
        SOT23_6()
        .lead_profile(
            SOTLeadProfile(
                span=Toleranced.min_max(2.6, 3.0),
            )
        )
        .package_body(
            RectanglePackage(
                width=Toleranced.min_max(1.5, 1.8),
                length=Toleranced.min_max(2.7, 3.1),
                height=Toleranced.min_max(1.0, 1.3),
            )
        )
    )

    # BoxSymbol: I/O lines on the left; GND down, VCC up on the columns.
    symbol = BoxSymbol(
        rows=Row(
            left=PinGroup(IO1, IO2, IO3, IO4),
        ),
        columns=Column(
            up=PinGroup(VCC),
            down=PinGroup(GND),
        ),
    )

    # 3D model: the exact SRV05-4A (LCSC C20615829) STEP from the JITX parts DB,
    # downloaded to models/. Attaching it here makes the board STEP export complete
    # (custom/generator landpatterns get no DB 3D automatically — see docs/sourcing.md).
    # Resolves relative to this file: components/ -> project_root/models/.
    # Origin-centered manufacturer model; offset/rotation left at the DB default
    # (HUMAN: visually confirm seating in the 3D view after export and adjust if needed).
    model3ds = [Model3D("../../models/SRV05-4A.stp")]

    # Explicit PadMapping — SOT23_6 pad numbering:
    #   left column top→bottom:  p[1], p[2], p[3]
    #   right column top→bottom: p[6], p[5], p[4]
    def __init__(self) -> None:
        lp = self.landpattern
        self.mappings = [
            PadMapping(
                {
                    self.IO1: [lp.p[1]],
                    self.GND: [lp.p[2]],
                    self.IO2: [lp.p[3]],
                    self.IO3: [lp.p[4]],
                    self.VCC: [lp.p[5]],
                    self.IO4: [lp.p[6]],
                }
            )
        ]


Device: type[Srv05_4A] = Srv05_4A
