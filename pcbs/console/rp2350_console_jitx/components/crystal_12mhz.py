"""
YXC X322512MSB4SI — 12 MHz SMD crystal unit (YSX321SL series), 4-pad SMD3225-4P.

3.20 x 2.50 x 0.70 mm, AT-fundamental, CL = 20 pF, +/-10 ppm. LCSC C9002.
This is the RP2350 reference clock (XOSC drives 20 pF with 2x ~30 pF load caps).

Pinout (datasheet p.1 "Top View Crystal Connection" + LCSC C9002 pinout):
  Pad 1: XIN  / OSC1  (crystal terminal — bottom-left)
  Pad 2: GND         (case ground — bottom-right)
  Pad 3: XOUT / OSC2  (crystal terminal — top-right)
  Pad 4: GND         (case ground — top-left)
The two DIAGONAL pads (1 & 3) are the active crystal terminals; pads 2 & 4 are
case/shield ground (same net) — confirmed by the datasheet diagram (crystal symbol
drawn diagonally between #1 and #3, "GND" labels on #4 and #2).

Land pattern (datasheet p.1 "Top View Suggested Layout", cross-checked 1:1 against
the EasyEDA/LCSC C9002 footprint "CRYSTAL-SMD_4P-L3.2-W2.5-BL"):
  pad size : 1.40 (X) x 1.20 (Y) mm
  pad span : 0.8 mm gap (X) / 0.5 mm gap (Y) -> centers at (+/-1.10, +/-0.85) mm
Body (datasheet p.1 Dimensions): 3.20 x 2.50 x 0.70 mm.
"""

import jitx
from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Circle, Text
from jitxlib.symbols.box import BoxSymbol, Column, PinGroup, Row


# ======================================================================
# Landpattern (module scope — JITX prohibits subclassing inside __init__)
# ======================================================================


class _CrystalPad(Pad):
    """SMD pad, 1.40 x 1.20 mm (datasheet recommended land pattern)."""

    shape = rectangle(1.4, 1.2)
    soldermask = Soldermask(rectangle(1.4, 1.2))
    paste = Paste(rectangle(1.4, 1.2))


class _X322512Landpattern(Landpattern):
    """
    4-pad SMD3225 crystal land pattern (datasheet "Top View Suggested Layout").

    Pad centers placed in the JITX frame (Y up) — these are the EasyEDA C9002
    pad positions with Y negated (KiCad Y-down -> JITX Y-up). The pad-number ->
    position assignment matches the datasheet "Top View Crystal Connection":
      #1 bottom-left, #2 bottom-right, #3 top-right, #4 top-left.
    """

    name = "easyeda2kicad:CRYSTAL-SMD_4P-L3.2-W2.5-BL"

    p = {
        1: _CrystalPad().at(-1.10, -0.85),  # XIN  / OSC1 (bottom-left)
        2: _CrystalPad().at(1.10, -0.85),  # GND        (bottom-right)
        3: _CrystalPad().at(1.10, 0.85),  # XOUT / OSC2 (top-right)
        4: _CrystalPad().at(-1.10, 0.85),  # GND        (top-left)
    }

    reference_designator = Silkscreen(Text(">REF", 1, Anchor.W).at((0, 2.0)))
    value_label = Custom(Text(">VALUE", 1, Anchor.W).at((0, -2.0)), name="Fab")

    # Pin-1 (XIN) marker: small silk dot just outside the bottom-left corner.
    silkscreen = [Silkscreen(Circle(radius=0.15).at((-2.1, -0.85)))]

    # Courtyard covers the pad span (+/-1.8 X, +/-1.45 Y) + the pin-1 dot.
    courtyard = Courtyard(rectangle(4.6, 3.2))


# ======================================================================
# Component
# ======================================================================


class Crystal12MHz(jitx.Component):
    """YXC X322512MSB4SI 12 MHz SMD3225-4P crystal (CL = 20 pF)."""

    mpn = "X322512MSB4SI"
    manufacturer = "YXC"
    lcsc = "C9002"
    reference_designator_prefix = "Y"
    datasheet = "https://datasheet.lcsc.com/datasheet/pdf/a84bd8d530dd46e4b0f6d0ee59d8a89c.pdf?productCode=C9002"

    # Ports — one functional name per electrical net.
    XIN = Port()  # pad 1 (OSC1) — crystal terminal to RP2350 XIN
    XOUT = Port()  # pad 3 (OSC2) — crystal terminal to RP2350 XOUT
    GND = Port()  # pads 2 & 4 — case/shield ground (single net)

    landpattern = _X322512Landpattern()

    # Symbol: crystal terminals on the sides, case ground down.
    symbol = BoxSymbol(
        rows=Row(
            left=PinGroup(XIN),
            right=PinGroup(XOUT),
        ),
        columns=Column(
            down=PinGroup(GND),
        ),
    )

    # 3D model: the C9002 STEP fetched from EasyEDA/LCSC (easyeda2kicad --full),
    # saved to models/. The model is centered at the footprint origin (KiCad model
    # offset 0/0/0), so the default attach seats it correctly. Custom landpatterns
    # carry no DB 3D automatically, so it is attached here for a complete board STEP.
    # Resolves relative to this file: components/ -> project_root/models/.
    # (HUMAN: confirm seating in the 3D view after export and adjust if needed.)
    model3ds = [Model3D("../../models/X322512MSB4SI.stp")]

    def __init__(self) -> None:
        lp = self.landpattern
        # Pad map per datasheet pinout: XIN=p1, XOUT=p3, GND=p2 & p4 (same net).
        self.mappings = [
            PadMapping(
                {
                    self.XIN: [lp.p[1]],
                    self.XOUT: [lp.p[3]],
                    self.GND: [lp.p[2], lp.p[4]],
                }
            )
        ]


Device: type[Crystal12MHz] = Crystal12MHz
