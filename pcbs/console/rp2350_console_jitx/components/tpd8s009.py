"""
Texas Instruments TPD8S009DSMR — 8-channel TVS/ESD protection array for
DisplayPort/HDMI/DVI TMDS lines.  LCSC C471873.

Package: DSM (R-PDSO-N15), 15-pin SON, body 6.50 x 2.50 mm
  (datasheet "Package Information" table, p.1: SON(15), 2.50 x 6.50 mm body).

Pinout — datasheet p.3, "Figure 4-1. DSM Package 15-Pin SON Top View" +
"Pin Functions" table:
  Pin  1  D0+   ESD port   (TMDS data 0, +)
  Pin  2  GND   ground
  Pin  3  D0-   ESD port   (TMDS data 0, -)
  Pin  4  D1+   ESD port   (TMDS data 1, +)
  Pin  5  GND   ground
  Pin  6  D1-   ESD port   (TMDS data 1, -)
  Pin  7  D2+   ESD port   (TMDS data 2, +)
  Pin  8  GND   ground
  Pin  9  D2-   ESD port   (TMDS data 2, -)
  Pin 10  D3+   ESD port   (TMDS data 3/clock, +)
  Pin 11  GND   ground
  Pin 12  D3-   ESD port   (TMDS data 3/clock, -)
  Pin 13  VCC   I/O supply
  Pin 14  N.C.  not internally connected
  Pin 15  VCC   I/O supply

Each ESD channel is a single SHUNT node (steering diodes clamp the line to
GND/VCC per the "Simplified Internal Schematic", p.1) — it is NOT a series
pass-through; the "Easy Straight-Through Routing Package" feature is a layout
convenience (pins arranged so the TMDS pairs route straight past with short
stubs), not separate connector-side/MCU-side terminals.

Landpattern — datasheet p.16 "LAND PATTERN" (drawing 4210120/A) + p.15
"MECHANICAL DATA" (DSM R-PDSO-N15, 4208854/A):
  Row A (pins 1-12): one long edge, pitch 0.50 mm, span 5.50 mm.
  Row B (pins 13-15): opposite long edge, pitch 1.50 mm, span 3.00 mm.
  Recommended copper land: 0.30 mm (across) x 1.45 mm (along), non-solder-mask
  defined (0.06 mm mask relief all around), stencil aperture 0.25 x 1.40 mm.
  Row-to-row land centre-to-centre = 3.30 mm overall - 1.45 mm land = 1.85 mm
  => each row centred at Y = +-0.925 mm.
Pad centres cross-checked against the JITX parts-DB landpattern for
TPD8S009DSMR (build --no-dependency-check probe) — identical poses.
No exposed/thermal pad (lead-frame SON, terminals on two opposing edges only).

3D model: manufacturer STEP from the JITX parts DB (resolved via
Part(mpn="TPD8S009DSMR")), vendored to models/TPD8S009DSMR.stp.
"""

import jitx
from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Circle, Polyline, Text
from jitxlib.symbols.box import BoxSymbol, Column, PinGroup, Row


# ======================================================================
# Pad — single SMD land shared by all 15 terminals (datasheet p.16)
# ======================================================================


class _Land(Pad):
    """SMD land 0.30 (across) x 1.45 mm (along), NSMD + stencil aperture."""

    shape = rectangle(0.30, 1.45)
    soldermask = Soldermask(rectangle(0.42, 1.57))  # +0.06 mm relief all around
    paste = Paste(rectangle(0.25, 1.40))  # datasheet stencil aperture


# ======================================================================
# Landpattern (module scope — JITX prohibits subclassing inside __init__)
# ======================================================================


class _Tpd8s009Landpattern(Landpattern):
    """
    R-PDSO-N15 (DSM) land pattern, top (PCB) view.

    Row A (Y = +0.925): pins 1-12 left-to-right at X = +2.75 .. -2.75, 0.50 pitch.
    Row B (Y = -0.925): pins 13/14/15 at X = -1.50 / 0.00 / +1.50, 1.50 pitch.
    Pin 1 (D0+) sits at the +X end of row A (top view).
    """

    name = "TI:R-PDSO-N15_TPD8S009DSM"

    # Row A — pins 1..12 at Y = +0.925, X stepping -0.50 from +2.75.
    # Row B — pins 13..15 at Y = -0.925.
    p = {
        1: _Land().at(2.75, 0.925),
        2: _Land().at(2.25, 0.925),
        3: _Land().at(1.75, 0.925),
        4: _Land().at(1.25, 0.925),
        5: _Land().at(0.75, 0.925),
        6: _Land().at(0.25, 0.925),
        7: _Land().at(-0.25, 0.925),
        8: _Land().at(-0.75, 0.925),
        9: _Land().at(-1.25, 0.925),
        10: _Land().at(-1.75, 0.925),
        11: _Land().at(-2.25, 0.925),
        12: _Land().at(-2.75, 0.925),
        13: _Land().at(-1.50, -0.925),
        14: _Land().at(0.00, -0.925),
        15: _Land().at(1.50, -0.925),
    }

    # Silkscreen: short body-edge lines (clear of the lands) + pin-1 dot.
    # Body 6.60 x 2.60 mm => half-extents X = 3.30, Y = 1.30 (datasheet p.15).
    silkscreen = [
        Silkscreen(Polyline(0.12, [(3.30, -1.30), (3.30, 1.30)])),
        Silkscreen(Polyline(0.12, [(-3.30, -1.30), (-3.30, 1.30)])),
        Silkscreen(Circle(radius=0.15).at((3.20, 1.80))),  # pin-1 marker
    ]
    reference_designator = Silkscreen(Text(">REF", 0.8, Anchor.C).at((0.0, 2.35)))
    value_label = Custom(Text(">VALUE", 0.8, Anchor.C).at((0.0, -2.35)), name="Fab")

    # Courtyard covers the lands (Y +-1.65) and body (X +-3.30) + ~0.25 mm.
    courtyard = Courtyard(rectangle(7.10, 3.80))


# ======================================================================
# Component
# ======================================================================


class Tpd8s009(jitx.Component):
    """TI TPD8S009 8-channel HDMI/DisplayPort TMDS ESD protection array, SON-15."""

    mpn = "TPD8S009DSMR"
    manufacturer = "Texas Instruments"
    lcsc = "C471873"
    reference_designator_prefix = "D"
    datasheet = "https://www.ti.com/lit/ds/symlink/tpd8s009.pdf"

    # 8 high-speed ESD channels = the 4 TMDS differential pairs (pins 1,3,4,6,7,9,10,12)
    D0_P = Port()  # pin 1
    D0_N = Port()  # pin 3
    D1_P = Port()  # pin 4
    D1_N = Port()  # pin 6
    D2_P = Port()  # pin 7
    D2_N = Port()  # pin 9
    D3_P = Port()  # pin 10
    D3_N = Port()  # pin 12

    # Ground returns — pins 2, 5, 8, 11
    GND = [Port() for _ in range(4)]

    # I/O supply rail — pins 13, 15
    VCC = [Port() for _ in range(2)]

    # Not internally connected — pin 14
    NC = Port()

    landpattern = _Tpd8s009Landpattern()

    # Manufacturer STEP (JITX parts DB), vendored to models/.
    # Resolves relative to this file: components/ -> project_root/models/.
    # Origin-centred DB model (position/rotation = 0); HUMAN: confirm seating
    # in the 3D view after export and adjust if needed.
    model3ds = [Model3D("../../models/TPD8S009DSMR.stp")]

    def __init__(self) -> None:
        # Symbol: TMDS channels on the left (pair-ordered), VCC/NC right, GND down.
        self.symbol = BoxSymbol(
            rows=Row(
                left=PinGroup(
                    self.D0_P,
                    self.D0_N,
                    self.D1_P,
                    self.D1_N,
                    self.D2_P,
                    self.D2_N,
                    self.D3_P,
                    self.D3_N,
                ),
                right=PinGroup(*self.VCC, self.NC),
            ),
            columns=Column(
                down=PinGroup(*self.GND),
            ),
        )

        # Port -> pad number per datasheet "Pin Functions" table (p.3).
        lp = self.landpattern
        self.mappings = [
            PadMapping(
                {
                    self.D0_P: lp.p[1],
                    self.GND[0]: lp.p[2],
                    self.D0_N: lp.p[3],
                    self.D1_P: lp.p[4],
                    self.GND[1]: lp.p[5],
                    self.D1_N: lp.p[6],
                    self.D2_P: lp.p[7],
                    self.GND[2]: lp.p[8],
                    self.D2_N: lp.p[9],
                    self.D3_P: lp.p[10],
                    self.GND[3]: lp.p[11],
                    self.D3_N: lp.p[12],
                    self.VCC[0]: lp.p[13],
                    self.NC: lp.p[14],
                    self.VCC[1]: lp.p[15],
                }
            )
        ]


Device: type[Tpd8s009] = Tpd8s009
