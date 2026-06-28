"""
Abracon AOTA-B201610S3R3-101-T — 3.3 uH mini molded power inductor (0806 / 2016 metric).

The RP2350 core-SMPS inductor (VREG_LX -> L -> DVDD 1.1 V), the exact part
Abracon lists as "Approved for use with Raspberry Pi's RP235x" (datasheet p.1).
LCSC C42411119. 2-pad SMD, POLARIZED (white-ink polarity dot).

Datasheet: docs/datasheets/AOTA-B201610S3R3-101-T.pdf (Abracon Rev A, 9/13/2024).

Electrical (datasheet p.1, Electrical Specifications table):
  L = 3.3 uH @ 1 MHz/1.0 V, tolerance M (+-20 %)
  DCR 115 mOhm typ / 140 mOhm max, Isat 2.8 A typ, Irms 2.3 A typ, SRF >= 21 MHz.

Mechanical (datasheet p.4, Mechanical Specifications, dims Inch[mm]):
  Body:  2.00 +-0.20 (W, terminal axis) x 1.60 +-0.20 (L) x 1.00 MAX (H) mm.
  Terminal (bottom) width: 0.60 +-0.20 mm.
  Recommended Land Pattern: two pads, each 1.00 mm wide x 1.60 mm tall,
  separated by a 1.00 mm gap -> pad centers 2.00 mm apart (0.039 [1.00] dims).

Polarity (datasheet p.4, "Marking (White Ink polarity dot)" figure):
  The white-ink dot marks the "+" terminal (current I_amps enters at the dotted
  side, exits the "-" side). Modeled here as P1 = dotted "+" terminal, with a
  silkscreen polarity dot placed next to the P1 pad so placement honors winding
  orientation (the RP2350 power section is orientation-sensitive).
"""

import jitx
from jitx import PadMapping, SymbolMapping
from jitx.anchor import Anchor
from jitx.model3d import Model3D
from jitx.feature import Courtyard, Custom, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.shapes.primitive import Circle, Polyline, Text
from jitxlib.symbols.inductor import InductorSymbol


# Recommended-land-pattern pad: 1.00 mm (x) x 1.60 mm (y) SMD (datasheet p.4).
class _IndPad(Pad):
    """SMD terminal pad, 1.00 x 1.60 mm (datasheet p.4 recommended land pattern)."""

    shape = rectangle(1.0, 1.6)
    soldermask = Soldermask(rectangle(1.0, 1.6))
    paste = Paste(rectangle(1.0, 1.6))


class _AotaB201610Landpattern(Landpattern):
    """
    2-pad land pattern for the AOTA-B201610 (2016-metric molded inductor).

    Pads centered at x = +-1.00 mm (1.00 mm pad + 1.00 mm gap -> 2.00 mm pitch),
    each 1.00 x 1.60 mm. p[1] is the polarity-dot "+" terminal (right side,
    matching the datasheet TOP VIEW where the dot sits at the top-right).
    """

    name = "L_AOTA-B201610S3R3_2016"

    p = {
        1: _IndPad().at(1.0, 0.0),  # P1: polarity-dot "+" terminal (right)
        2: _IndPad().at(-1.0, 0.0),  # P2: "-" terminal (left)
    }

    # White-ink polarity dot beside P1 (datasheet p.4 marking figure).
    polarity_dot = Silkscreen(Circle(radius=0.18).at(1.0, 1.35))

    # Body-extent silk on the long (L = 1.60 mm) edges, clear of the 1.60 mm pads.
    silkscreen = [
        Silkscreen(Polyline(0.12, [(-1.0, 1.0), (1.0, 1.0)])),
        Silkscreen(Polyline(0.12, [(-1.0, -1.0), (1.0, -1.0)])),
    ]

    reference_designator = Silkscreen(Text(">REF", 0.6, Anchor.C).at((0.0, 2.1)))
    value_label = Custom(Text(">VALUE", 0.6, Anchor.C).at((0.0, -2.1)), name="Fab")

    # Courtyard envelopes the 3.00 mm land span + body tolerance (2.20 x 1.80 max).
    courtyard = Courtyard(rectangle(3.5, 2.3))


class AotaB201610S3R3(jitx.Component):
    """Abracon AOTA-B201610S3R3-101-T 3.3 uH polarized power inductor (0806/2016)."""

    mpn = "AOTA-B201610S3R3-101-T"
    manufacturer = "Abracon LLC"
    lcsc = "C42411119"
    reference_designator_prefix = "L"
    datasheet = "https://abracon.com/Magnetics/power/AOTA-B201610S3R3.pdf"
    model3ds = [Model3D("../../models/AOTA-B201610S3R3-101-T.stp")]  # EasyEDA STEP for LCSC C42411119

    # Two terminals. P1 = dotted "+" terminal; P2 = "-" terminal (datasheet p.4).
    P1 = Port()
    P2 = Port()

    landpattern = _AotaB201610Landpattern()
    symbol = InductorSymbol(pitch=4.0)

    cmappings = [
        SymbolMapping({P1: symbol.p[1], P2: symbol.p[2]}),
        PadMapping({P1: landpattern.p[1], P2: landpattern.p[2]}),
    ]


Device: type[AotaB201610S3R3] = AotaB201610S3R3
