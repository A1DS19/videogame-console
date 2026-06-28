"""
Korean Hroparts Elec TYPE-C-31-M-12 — USB-C 2.0 16-pin SMD receptacle.

LCSC: C165948
Footprint source: EasyEDA/LCSC via parts2jitx-lcsc C165948 --footprint
  → parts2jitx-kicad kicad_footprints/C165948.kicad_mod --class-name TYPEC31M12
  (non-standard mixed SMD+THT footprint; KiCad import required)

Pin naming follows the USB-C 2.0 spec + connector pinout from parts2jitx-lcsc --pinout.
The four EH (mounting shell) pads are structural — named EH[0..3].
The two unnamed circle TH pads are shell strain-relief points — named SHELL[0..1].
"""

import jitx
from jitx import PadMapping
from jitx.feature import Courtyard, Custom, Cutout, Paste, Silkscreen, Soldermask
from jitx.landpattern import Landpattern, Pad
from jitx.net import Port
from jitx.shapes.composites import capsule, rectangle
from jitx.shapes.primitive import Arc, ArcPolyline, Circle, Polyline, Text
from jitx.anchor import Anchor
from jitxlib.symbols.box import BoxSymbol, PinGroup, Row


# ======================================================================
# Pad shape definitions (converted from KiCad footprint via parts2jitx)
# ======================================================================


class _SignalPad(Pad):
    """SMD signal pad (0.3 x 1.3 mm) — USB-C 2.0 data/CC/SBU pins."""

    shape = rectangle(0.3, 1.3)
    soldermask = Soldermask(rectangle(0.3, 1.3))
    paste = Paste(rectangle(0.3, 1.3))


class _PowerPadWide(Pad):
    """SMD power pad (0.6 x 1.3002 mm) — GND/VBUS outer merged pads."""

    shape = rectangle(0.6, 1.3002)
    soldermask = Soldermask(rectangle(0.6, 1.3002))
    paste = Paste(rectangle(0.6, 1.3002))


class _PowerPadNarrow(Pad):
    """SMD power pad (0.6 x 1.3 mm) — GND/VBUS inner merged pads."""

    shape = rectangle(0.6, 1.3)
    soldermask = Soldermask(rectangle(0.6, 1.3))
    paste = Paste(rectangle(0.6, 1.3))


class _ShellPadA(Pad):
    """Through-hole shell/mounting pad, oval 1.2×1.8 mm, drill 0.8×1.4 mm."""

    shape = capsule(1.2, 1.8)
    cutout = Cutout(capsule(0.8, 1.4))


class _ShellPadB(Pad):
    """Through-hole shell/mounting pad, oval 1.2×2.0 mm, drill 0.8×1.6 mm."""

    shape = capsule(1.2, 2.0)
    cutout = Cutout(capsule(0.8, 1.6))


class _StrainReliefPad(Pad):
    """Through-hole strain-relief/shell circle, 0.75 mm diameter (no net)."""

    shape = Circle(radius=0.375)
    cutout = Cutout(Circle(radius=0.375))


# ======================================================================
# Landpattern (module scope — JITX prohibits subclassing inside __init__)
# ======================================================================


class _TYPEC31M12Landpattern(Landpattern):
    """
    Landpattern for TYPE-C-31-M-12 derived from the EasyEDA footprint.

    Pad positions are KiCad-origin with Y-axis flipped to JITX frame
    (KiCad Y+ = down → JITX Y+ = up, so all KiCad Y coords are negated).

    p dict keys correspond to the logical pad index used in PadMapping;
    the ordering matches parts2jitx-kicad output (pad names from KiCad).
    """

    name = "easyeda2kicad:USB-C_SMD-TYPE-C-31-M-12_1"

    # Each pad is declared only in the p dict to avoid the "encountered
    # multiple times" error that occurs when a pad is both a named class
    # attribute AND inside the dict.
    p = {
        1: _SignalPad().at(-1.75, 2.47),  # B8 / SBU2
        2: _SignalPad().at(-1.25, 2.47),  # A5 / CC1
        3: _SignalPad().at(-0.75, 2.47),  # B7 / DN2
        4: _SignalPad().at(-0.25, 2.47),  # A6 / DP1
        5: _SignalPad().at(0.25, 2.47),  # A7 / DN1
        6: _SignalPad().at(0.75, 2.47),  # B6 / DP2
        7: _SignalPad().at(1.25, 2.47),  # A8 / SBU1
        8: _SignalPad().at(1.75, 2.47),  # B5 / CC2
        9: _PowerPadWide().at(-3.2, 2.47),  # A1B12 / GND left
        10: _PowerPadNarrow().at(3.2, 2.47),  # B1A12 / GND right
        11: _PowerPadNarrow().at(2.4, 2.47),  # B4A9 / VBUS right
        12: _PowerPadNarrow().at(-2.4, 2.47),  # A4B9 / VBUS left
        13: _ShellPadA().at(4.33, -2.47),  # EH KiCad pad "2"
        14: _ShellPadB().at(4.33, 1.71),  # EH KiCad pad "1"
        15: _ShellPadB().at(-4.33, 1.71),  # EH KiCad pad "4"
        16: _ShellPadA().at(-4.33, -2.47),  # EH KiCad pad "3"
        17: _StrainReliefPad().at(-2.9, 1.21),  # SHELL[0]
        18: _StrainReliefPad().at(2.9, 1.21),  # SHELL[1]
    }

    reference_designator = Silkscreen(Text(">REF", 1, Anchor.W).at((0, 6.474)))
    value_label = Custom(Text(">VALUE", 1, Anchor.W).at((0, -6.474)), name="Fab")
    silkscreen = [
        Silkscreen(Polyline(0.25, [(-4.47, -1.38), (-4.47, 0.49)])),
        Silkscreen(Polyline(0.25, [(4.47, -5.09), (-4.47, -5.09)])),
        Silkscreen(Polyline(0.25, [(-4.47, -5.09), (-4.47, -3.61)])),
        Silkscreen(Polyline(0.25, [(4.47, -1.38), (4.47, 0.49)])),
        Silkscreen(Polyline(0.25, [(4.47, -5.09), (4.47, -3.61)])),
        Silkscreen(ArcPolyline(0.06, [Arc((4.48, 2.76), 0.03, 0, -360)])),
    ]
    courtyard = Courtyard(rectangle(8.94, 7.35))


# ======================================================================
# Component
# ======================================================================


class TYPEC31M12(jitx.Component):
    """
    Korean Hroparts Elec TYPE-C-31-M-12 USB-C 2.0 SMD receptacle.

    16 electrical positions (signal + power) + 4 THT mounting shell tabs.
    For USB 2.0 connectivity: use DP1/DN1 (A6/A7) and DP2/DN2 (B6/B7)
    + CC1/CC2 + VBUS (A4B9/B4A9) + GND (A1B12/B1A12).
    SBU1/SBU2 are left unconnected for USB 2.0-only designs.
    """

    mpn = "TYPE-C-31-M-12"
    manufacturer = "Korean Hroparts Elec"
    reference_designator_prefix = "J"
    datasheet = "https://datasheet.lcsc.com/datasheet/pdf/9e56b777c022540fcce7c7f67825f55e.pdf?productCode=C165948"

    # Signal / CC / SBU ports (8 SMD pads at 0.5 mm pitch)
    B8 = Port()  # SBU2
    A5 = Port()  # CC1
    B7 = Port()  # DN2  (USB D- side B)
    A6 = Port()  # DP1  (USB D+ side A)
    A7 = Port()  # DN1  (USB D- side A)
    B6 = Port()  # DP2  (USB D+ side B)
    A8 = Port()  # SBU1
    B5 = Port()  # CC2

    # Power ports — merged A/B-row pads
    A1B12 = Port()  # GND (left outer merged pad)
    B1A12 = Port()  # GND (right outer merged pad)
    B4A9 = Port()  # VBUS (right inner merged pad)
    A4B9 = Port()  # VBUS (left inner merged pad)

    # Shell / mounting tabs (THT, 4 pads; tied to GND on most designs)
    EH = [Port() for _ in range(4)]

    # Strain-relief shell anchor pins (unnamed circle TH pads in KiCad)
    SHELL = [Port() for _ in range(2)]

    landpattern = _TYPEC31M12Landpattern()

    def __init__(self) -> None:
        lp = self.landpattern

        # --- Symbol (all ports visible in schematic) ---
        self.symbol = BoxSymbol(
            rows=Row(
                left=PinGroup(
                    self.A4B9,
                    self.A1B12,
                    self.A5,
                    self.A6,
                    self.A7,
                    self.A8,
                    self.B4A9,
                    self.B1A12,
                    self.B5,
                    self.B6,
                    self.B7,
                    self.B8,
                ),
                right=PinGroup(
                    *self.EH,
                    *self.SHELL,
                ),
            ),
        )

        # --- Pad mapping (port → landpattern pad) ---
        self.mappings = [
            PadMapping(
                {
                    self.B8: lp.p[1],
                    self.A5: lp.p[2],
                    self.B7: lp.p[3],
                    self.A6: lp.p[4],
                    self.A7: lp.p[5],
                    self.B6: lp.p[6],
                    self.A8: lp.p[7],
                    self.B5: lp.p[8],
                    self.A1B12: lp.p[9],
                    self.B1A12: lp.p[10],
                    self.B4A9: lp.p[11],
                    self.A4B9: lp.p[12],
                    self.EH[1]: lp.p[13],
                    self.EH[0]: lp.p[14],
                    self.EH[3]: lp.p[15],
                    self.EH[2]: lp.p[16],
                    self.SHELL[0]: lp.p[17],
                    self.SHELL[1]: lp.p[18],
                }
            )
        ]


Device: type[TYPEC31M12] = TYPEC31M12
