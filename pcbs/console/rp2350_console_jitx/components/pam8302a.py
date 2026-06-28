"""
Diodes PAM8302AASCR — 2.5 W filterless Class-D mono audio amplifier, MSOP-8.

LCSC C113367. Drives the console's 8 Ω speaker (via a JST-PH port).

Pinout (datasheet DS41333 Rev.6 page 1, "Pin Assignments" MSOP-8 Top View) —
verified against the JITX parts-DB pin_properties for C113367:
  Pin 1: SD    (shutdown, ACTIVE-LOW: logic-low = amp off; overbar /SD)
  Pin 2: NC    (no internal connection)
  Pin 3: IN+   (non-inverting audio input)        -> port INP
  Pin 4: IN-   (inverting audio input)            -> port INN
  Pin 5: VO+   (bridge-tied speaker output +)     -> port OUTP
  Pin 6: VDD   (2.0-5.5 V supply)
  Pin 7: GND   (ground)
  Pin 8: VO-   (bridge-tied speaker output -)     -> port OUTN

MSOP-8 mechanical (datasheet page 10, "Package Outline Dimensions", all mm):
  D  (body length):     2.90-3.10
  E1 (body width):      2.90-3.10
  E  (lead span):       4.70-5.10
  e  (pitch):           0.65
  L  (lead foot length):0.40-0.80
  b  (lead width):      0.22-0.38
  A  (overall height):  max 1.10  (A2 body 0.75-0.95)

Closed-loop gain is set externally (datasheet page 7): GV = 20*log(150k/(10k+Rin)),
i.e. ~2x(142k/Rin) per the BOM note. The differential output is filterless and must
NOT be AC-coupled or ground-referenced; route VO+/VO- straight to the speaker.
"""

import jitx
from jitx import PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.toleranced import Toleranced
from jitxlib.landpatterns.generators.sop import SOP, SOPLead
from jitxlib.landpatterns.leads import LeadProfile
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.symbols.box import BoxSymbol, Column, PinGroup, Row


class PAM8302A(jitx.Component):
    """2.5 W Class-D mono audio amplifier, MSOP-8 (Diodes PAM8302AASCR)."""

    mpn = "PAM8302AASCR"
    manufacturer = "Diodes Incorporated"
    lcsc = "C113367"
    reference_designator_prefix = "U"
    datasheet = "https://www.diodes.com/assets/Datasheets/PAM8302A.pdf"

    # Ports — one per physical pin, named per datasheet page-1 Pin Assignments.
    SD = Port()  # pin 1 — shutdown, active-low (low = amp off)
    NC = Port()  # pin 2 — no connection
    INP = Port()  # pin 3 — IN+ non-inverting input
    INN = Port()  # pin 4 — IN- inverting input
    OUTP = Port()  # pin 5 — VO+ speaker output (+)
    VDD = Port()  # pin 6 — supply 2.0-5.5 V
    GND = Port()  # pin 7 — ground
    OUTN = Port()  # pin 8 — VO- speaker output (-)

    # MSOP-8 landpattern via the SOP generator (gull-wing, 0.65 mm pitch).
    # Dimensions are the datasheet page-10 mechanical drawing (see module docstring).
    landpattern = (
        SOP(num_leads=8)
        .lead_profile(
            LeadProfile(
                span=Toleranced.min_max(4.70, 5.10),  # E — lead tip-to-tip
                pitch=0.65,  # e
                type=SOPLead(
                    length=Toleranced.min_max(0.40, 0.80),  # L — foot length
                    width=Toleranced.min_max(0.22, 0.38),  # b — lead width
                ),
            )
        )
        .package_body(
            RectanglePackage(
                width=Toleranced.min_max(2.90, 3.10),  # E1 — body width
                length=Toleranced.min_max(2.90, 3.10),  # D — body length
                height=Toleranced.min_max(0.86, 1.10),  # A2..A
            )
        )
    )

    # BoxSymbol: inputs + shutdown on the left, speaker outputs on the right,
    # VDD up / GND down — mirrors the datasheet pin directions.
    symbol = BoxSymbol(
        rows=Row(
            left=PinGroup(SD, NC, INP, INN),
            right=PinGroup(OUTP, OUTN),
        ),
        columns=Column(
            up=PinGroup(VDD),
            down=PinGroup(GND),
        ),
    )

    # 3D model: the exact PAM8302AASCR (LCSC C113367) STEP from the JITX parts DB,
    # auto-downloaded to 3d-models/ during the DB probe and copied to models/ with a
    # clean name. The generator landpattern carries no DB 3D automatically, so attach
    # it here to complete the board STEP export. Resolves relative to this file:
    # components/ -> project_root/models/.
    # The DB tags this model "unknown transformation coordinates - please validate
    # before use" (HUMAN: confirm seating in the 3D view after export; adjust
    # offset/rotation if it does not sit flat on the MSOP-8 footprint).
    model3ds = [Model3D("../../models/PAM8302AASCR.stp")]

    # Explicit PadMapping — SOP LinearNumbering pads p[1]..p[8] map to the
    # datasheet pin numbers (left col 1-4 top->bottom, right col 5-8 bottom->top).
    def __init__(self) -> None:
        lp = self.landpattern
        self.mappings = [
            PadMapping(
                {
                    self.SD: [lp.p[1]],
                    self.NC: [lp.p[2]],
                    self.INP: [lp.p[3]],
                    self.INN: [lp.p[4]],
                    self.OUTP: [lp.p[5]],
                    self.VDD: [lp.p[6]],
                    self.GND: [lp.p[7]],
                    self.OUTN: [lp.p[8]],
                }
            )
        ]


Device: type[PAM8302A] = PAM8302A
