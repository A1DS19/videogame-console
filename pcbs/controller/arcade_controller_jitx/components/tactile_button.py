"""
Korean Hroparts Elec K2-1103DP-Q4SW-04 — 12x12 mm through-hole tactile switch.

The arcade-controller gamepad button. Instantiated 8x by the wiring task; each
press connects port A to port B (a simple SPST momentary switch).

LCSC: C136701.
Datasheet: docs/datasheets/K2-1103DP-Q4SW-04_C136701.pdf (page 1: PCB Layout
"Pattern side" + Circuit Diagram).

Geometry (datasheet page 1, "PCB Layout (Pattern side)"):
  - Body 12.0 x 12.0 mm; round actuator Ø6.7 mm centered; H-code "Q" => H = 12 mm.
  - 4 plated through-holes, drill Ø1.30 mm, on a NON-SQUARE grid:
      12.50 mm apart in X (two columns), 5.00 mm apart in Y (two rows).
    Hole centers (origin at body center, mm):
      (-6.25, +2.50)  (-6.25, -2.50)   LEFT  column  -> port A
      (+6.25, +2.50)  (+6.25, -2.50)   RIGHT column  -> port B
  The non-square pitch is why the single-pitch Header generator can't model this;
  the four pads are placed explicitly in a custom Landpattern below.

Electrical pairing (datasheet page 1, "Circuit Diagram") — CRITICAL:
  The two holes in the SAME column are internally common (one switch terminal).
  Pressing the button bridges the LEFT column to the RIGHT column. Therefore:
    port A = both LEFT pads,  port B = both RIGHT pads.
  Tying a left pad and a right pad to the same port would short the switch
  permanently closed (= dead). Hence the explicit two-pads-per-port PadMapping.
"""

import jitx
from jitx import PadMapping
from jitx.anchor import Anchor
from jitx.feature import Courtyard, Silkscreen
from jitx.landpattern import Landpattern
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Circle, Text
from jitxlib.landpatterns.pads import THPad
from jitxlib.symbols.box import BoxSymbol, PinGroup, Row

# Through-hole pad geometry (datasheet page 1).
_DRILL_DIA = 1.30  # plated hole Ø, datasheet "4-Ø1.30"
_PAD_DIA = 1.90  # copper land Ø = drill + ~0.3 mm annular ring per side

# Hole-center grid (origin at body center).
_X = 6.25  # half of the 12.50 mm column spacing
_Y = 2.50  # half of the 5.00 mm row spacing
_BODY = 12.0  # 12 x 12 mm body for the silkscreen / courtyard outline


class _ButtonPad(THPad):
    """Round plated through-hole pad: Ø1.90 mm copper, Ø1.30 mm drill.

    THPad auto-generates soldermask openings on BOTH sides (the copper expanded
    by the design soldermask registration), which is required for a solderable
    through-hole terminal.
    """

    def __init__(self) -> None:
        super().__init__(
            copper=Circle(diameter=_PAD_DIA),
            cutout=Circle(diameter=_DRILL_DIA),
        )


class _TactileButtonLandpattern(Landpattern):
    """Four explicitly-placed THT pads on the 12.50 x 5.00 mm grid.

    Pad numbering (matches the PadMapping below):
      p[1] = (-6.25, +2.50)  LEFT-top      -> A
      p[2] = (-6.25, -2.50)  LEFT-bottom   -> A
      p[3] = (+6.25, +2.50)  RIGHT-top     -> B
      p[4] = (+6.25, -2.50)  RIGHT-bottom  -> B
    """

    p = {
        1: _ButtonPad().at(-_X, _Y),
        2: _ButtonPad().at(-_X, -_Y),
        3: _ButtonPad().at(_X, _Y),
        4: _ButtonPad().at(_X, -_Y),
    }

    # 12 x 12 mm body outline + reference designator.
    silkscreen = Silkscreen(rectangle(_BODY, _BODY))
    courtyard = Courtyard(rectangle(_BODY, _BODY))
    ref_text = Silkscreen(Text(">REF", 1.0, Anchor.C).at(0.0, _BODY / 2 + 1.0))

    # 3D model: the exact K2-1103DP-Q4SW-04 12x12 THT tactile switch (LCSC C136701)
    # STEP from the JITX parts DB, downloaded to models/. This custom landpattern has
    # no DB 3D, so attach the model here to complete the board STEP export.
    # Resolves relative to this file: components/ -> project_root/models/.
    # Origin-centered manufacturer model; offset/rotation at the DB default
    # (HUMAN: confirm seating in the 3D view after export and adjust if needed).
    model3ds = [Model3D("../../models/K2-1103DP-Q4SW-04.stp")]


class TactileButton(jitx.Component):
    """K2-1103DP-Q4SW-04 12x12 mm THT tactile push switch (SPST momentary).

    Two terminals: A and B. Each terminal is a pair of common through-holes
    (same column). Pressing the actuator connects A to B.
    """

    mpn = "K2-1103DP-Q4SW-04"
    manufacturer = "Korean Hroparts Elec"
    lcsc = "C136701"
    reference_designator_prefix = "SW"
    datasheet = "https://www.lcsc.com/product-detail/Tactile-Switches_Korean-Hroparts-Elec-K2-1103DP-Q4SW-04_C136701.html"

    # Two switch terminals (each is a same-column pair of common pads).
    A = Port()
    B = Port()

    landpattern = _TactileButtonLandpattern()

    # Simple two-terminal switch symbol: A on the left, B on the right.
    symbol = BoxSymbol(
        rows=Row(
            left=PinGroup(A),
            right=PinGroup(B),
        ),
    )

    def __init__(self) -> None:
        lp = self.landpattern
        # CRITICAL pairing (datasheet "Circuit Diagram"): same-column pads are
        # internally common. A = both LEFT pads (p1, p2); B = both RIGHT pads
        # (p3, p4). Each port maps to TWO pads.
        self.mappings = [
            PadMapping(
                {
                    self.A: [lp.p[1], lp.p[2]],
                    self.B: [lp.p[3], lp.p[4]],
                }
            )
        ]


Device: type[TactileButton] = TactileButton
