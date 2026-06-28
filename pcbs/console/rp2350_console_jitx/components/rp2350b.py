"""
Raspberry Pi RP2350B — dual-core (Cortex-M33 / Hazard3 RISC-V) microcontroller.

QFN-80-EP, 10×10 mm, 0.4 mm pitch, central exposed thermal pad = GND.
MPN "RP2350B"  ·  manufacturer Raspberry Pi  ·  LCSC C42415655 (Extended).

Footprint source: JITX QFN generator (Part(mpn="RP2350B") / "RP2350" do NOT
resolve in the JITX parts DB — verified by build-probe), using the datasheet
QFN-80 mechanical drawing.

Pin map source — verified against TWO independent datasheet sources:
  • Figure 3 "Pinout for QFN-80 10×10mm" (datasheet printed page 16) — the pad
    layout drawing (numbers + edge labels extracted with coordinates).
  • Tables 1427–1432 "Pin list" (datasheet printed pages 1335–1338, §14.8.2.2)
    — the authoritative QFN-80-Number column. Both agree on all 80 pads.

Mechanical (Figure 145 "QFN-80 package", datasheet printed page 1329, §14.2):
  D  (body length) : 10.00 mm BSC
  E  (body width)  : 10.00 mm BSC
  e  (lead pitch)  : 0.40 mm BSC
  b  (lead width)  : 0.150 / 0.200 / 0.250 mm (min/nom/max)
  L  (lead length) : 0.250 / 0.400 / 0.450 mm (min/nom/max)
  A  (height)      : 0.800 / 0.850 / 0.900 mm (min/nom/max)
  D2×E2 (exposed pad, reduced) : 3.350 / 3.400 / 3.450 mm → 3.40×3.40 nominal

Notable functional notes (datasheet §1.2.3 Table 3 + Tables 1427–1432):
  • HSTX (DVI/HDMI TMDS) is on GPIO12–GPIO19 (F0=HSTX) → the 4 TMDS pairs.
  • GPIO40–GPIO47 carry the 8 ADC inputs (ADC0–ADC7) on QFN-80 (Table 1119).
  • GPIO0–GPIO47 (48 pins) is the full bank used for the 2 controller ports,
    PWM audio, status LED, and DDC/HPD — exposed here as the GPIO[0..47] list.
  • QSPI_SS (pin 75) doubles as the USB BOOTSEL strap (Table 1428).
  • GND has no dedicated pin — it is the central exposed pad only (Table 1432).
"""

import jitx
from jitx import PadMapping
from jitx.model3d import Model3D
from jitx.net import Port
from jitx.shapes.composites import rectangle
from jitx.toleranced import Toleranced
from jitxlib.landpatterns.generators.qfn import QFN, QFNLead
from jitxlib.landpatterns.ipc import DensityLevel
from jitxlib.landpatterns.leads import LeadProfile
from jitxlib.landpatterns.package import RectanglePackage
from jitxlib.symbols.box import BoxSymbol, Column, PinGroup, Row

# Authoritative pad number → GPIO index, from datasheet Tables 1427/1119 and the
# QFN-80 pinout figure (both cross-checked). Key = QFN-80 pad number; value =
# GPIO number. GPIO40..47 are the ADC-capable pins (named GPIOx_ADCy in the
# figure); their primary function is still GPIOx, so they live in GPIO[40..47].
_GPIO_PAD_TO_INDEX = {
    77: 0,
    78: 1,
    79: 2,
    80: 3,
    1: 4,
    2: 5,
    3: 6,
    4: 7,
    6: 8,
    7: 9,
    8: 10,
    9: 11,
    11: 12,
    12: 13,
    13: 14,
    14: 15,
    16: 16,
    17: 17,
    18: 18,
    19: 19,
    20: 20,
    21: 21,
    22: 22,
    23: 23,
    25: 24,
    26: 25,
    27: 26,
    28: 27,
    36: 28,
    37: 29,
    38: 30,
    39: 31,
    40: 32,
    42: 33,
    43: 34,
    44: 35,
    45: 36,
    46: 37,
    47: 38,
    48: 39,
    49: 40,
    52: 41,
    53: 42,
    54: 43,
    55: 44,
    56: 45,
    57: 46,
    58: 47,
}

# Power-rail pads (datasheet Table 1432). Multiple pads per rail → indexed lists.
_IOVDD_PADS = [5, 15, 24, 29, 41, 50, 60, 76]  # 8 IO-supply pads
_DVDD_PADS = [10, 32, 51]  # 3 core-supply pads


class RP2350B(jitx.Component):
    """Raspberry Pi RP2350B microcontroller, QFN-80-EP (10×10 mm, 0.4 mm pitch)."""

    mpn = "RP2350B"
    manufacturer = "Raspberry Pi"
    lcsc = "C42415655"
    reference_designator_prefix = "U"
    datasheet = "https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf"
    model3ds = [Model3D("../../models/RP2350B.stp")]  # EasyEDA STEP for LCSC C42415655

    # --- GPIO bank (GPIO0..GPIO47) ---
    GPIO = [Port() for _ in range(48)]
    """General-purpose I/O GPIO0..GPIO47 (HSTX on 12–19; ADC0–7 on 40–47)."""

    # --- Power supplies (Table 1432) ---
    IOVDD = [Port() for _ in range(8)]
    """IO supply, 1.8–3.3 V (pads 5,15,24,29,41,50,60,76)."""
    DVDD = [Port() for _ in range(3)]
    """Digital core supply, 1.1 V (pads 10,32,51)."""
    ADC_AVDD = Port()
    """ADC analogue supply, 3.3 V (pad 59)."""
    USB_OTP_VDD = Port()
    """USB PHY & OTP supply, 3.3 V (pad 68)."""
    QSPI_IOVDD = Port()
    """QSPI IO supply, 1.8–3.3 V (pad 69)."""

    # --- Internal core voltage regulator (Table 1432) ---
    VREG_VIN = Port()
    """Core regulator input supply, 2.7–5.5 V (pad 64)."""
    VREG_LX = Port()
    """Core regulator switching output → external inductor (pad 63)."""
    VREG_FB = Port()
    """Core regulator feedback input (pad 65)."""
    VREG_AVDD = Port()
    """Core regulator analogue supply (pad 61)."""
    VREG_PGND = Port()
    """Core regulator power ground (pad 62)."""

    # --- QSPI flash interface (Table 1428) ---
    QSPI_SD0 = Port()  # pad 72
    QSPI_SD1 = Port()  # pad 74
    QSPI_SD2 = Port()  # pad 73
    QSPI_SD3 = Port()  # pad 70
    QSPI_SCLK = Port()  # pad 71
    QSPI_SS = Port()  # pad 75 — chip select, also USB BOOTSEL strap

    # --- USB (Table 1431) ---
    USB_DP = Port()  # pad 67
    USB_DM = Port()  # pad 66

    # --- Crystal oscillator (Table 1429) ---
    XIN = Port()  # pad 30
    XOUT = Port()  # pad 31

    # --- Debug + reset (Table 1430) ---
    SWCLK = Port()  # pad 33
    SWDIO = Port()  # pad 34
    RUN = Port()  # pad 35 — chip enable / reset_n

    # --- Ground: central exposed pad only (Table 1432, no dedicated pin) ---
    GND = Port()

    # QFN-80 landpattern from the datasheet mechanical drawing (Figure 145).
    landpattern = (
        QFN(num_leads=80)
        .lead_profile(
            LeadProfile(
                span=Toleranced.exact(10.0),  # D / E = 10.00 BSC
                pitch=0.4,  # e = 0.400 BSC
                type=QFNLead(
                    length=Toleranced.min_max(0.25, 0.45),  # L
                    width=Toleranced.min_typ_max(0.15, 0.20, 0.25),  # b
                ),
            ),
        )
        .package_body(
            RectanglePackage(
                width=Toleranced.exact(10.0),  # D = 10.00 BSC
                length=Toleranced.exact(10.0),  # E = 10.00 BSC
                height=Toleranced.min_max(0.8, 0.9),  # A
            )
        )
        .thermal_pad(rectangle(3.4, 3.4))  # D2×E2 reduced ePad = 3.40×3.40
        .density_level(DensityLevel.C)  # fine 0.4 mm pitch
    )

    def __init__(self) -> None:
        lp = self.landpattern

        # Schematic symbol: GPIO bank split across the two vertical edges,
        # power rails along the top, control/comms signals + GND along the bottom.
        self.symbol = BoxSymbol(
            rows=Row(
                left=PinGroup(self.GPIO[0:24]),
                right=PinGroup(self.GPIO[24:48]),
            ),
            columns=Column(
                up=[
                    PinGroup(
                        *self.IOVDD,
                        *self.DVDD,
                        self.ADC_AVDD,
                        self.USB_OTP_VDD,
                        self.QSPI_IOVDD,
                    ),
                    PinGroup(
                        self.VREG_VIN,
                        self.VREG_LX,
                        self.VREG_FB,
                        self.VREG_AVDD,
                        self.VREG_PGND,
                    ),
                ],
                down=[
                    PinGroup(
                        self.QSPI_SD0,
                        self.QSPI_SD1,
                        self.QSPI_SD2,
                        self.QSPI_SD3,
                        self.QSPI_SCLK,
                        self.QSPI_SS,
                    ),
                    PinGroup(
                        self.USB_DP,
                        self.USB_DM,
                        self.XIN,
                        self.XOUT,
                        self.SWCLK,
                        self.SWDIO,
                        self.RUN,
                        self.GND,
                    ),
                ],
            ),
        )

        # Explicit, fully-auditable port → pad map (the dead-board risk).
        mapping = {}
        for pad, idx in _GPIO_PAD_TO_INDEX.items():
            mapping[self.GPIO[idx]] = [lp.p[pad]]
        for i, pad in enumerate(_IOVDD_PADS):
            mapping[self.IOVDD[i]] = [lp.p[pad]]
        for i, pad in enumerate(_DVDD_PADS):
            mapping[self.DVDD[i]] = [lp.p[pad]]
        mapping[self.ADC_AVDD] = [lp.p[59]]
        mapping[self.VREG_AVDD] = [lp.p[61]]
        mapping[self.VREG_PGND] = [lp.p[62]]
        mapping[self.VREG_LX] = [lp.p[63]]
        mapping[self.VREG_VIN] = [lp.p[64]]
        mapping[self.VREG_FB] = [lp.p[65]]
        mapping[self.USB_DM] = [lp.p[66]]
        mapping[self.USB_DP] = [lp.p[67]]
        mapping[self.USB_OTP_VDD] = [lp.p[68]]
        mapping[self.QSPI_IOVDD] = [lp.p[69]]
        mapping[self.QSPI_SD3] = [lp.p[70]]
        mapping[self.QSPI_SCLK] = [lp.p[71]]
        mapping[self.QSPI_SD0] = [lp.p[72]]
        mapping[self.QSPI_SD2] = [lp.p[73]]
        mapping[self.QSPI_SD1] = [lp.p[74]]
        mapping[self.QSPI_SS] = [lp.p[75]]
        mapping[self.XIN] = [lp.p[30]]
        mapping[self.XOUT] = [lp.p[31]]
        mapping[self.SWCLK] = [lp.p[33]]
        mapping[self.SWDIO] = [lp.p[34]]
        mapping[self.RUN] = [lp.p[35]]
        mapping[self.GND] = [lp.thermal_pads[0]]

        self.mappings = [PadMapping(mapping)]


Device: type[RP2350B] = RP2350B
