"""Physical layout for the RP2350 console — outline, NPTH holes, floorplan, pours.

This module owns the *geometry and placement* side (the ``jitx-physical-layout``
layer): the 72 x 66 mm board outline with four M3 NPTH mounting holes, the inset
signal area the GND/V3V3 planes fill, the explicit component floorplan, and the
4-layer pour map. ``main.py`` owns the netlist; ``designs/console.py`` is the
top-level ``Design`` and the TMDS SI constraints. The design's inline circuit
calls ``floorplan(self)`` after the netlist is built — exactly as
``wireless_lighting_jitx`` does (``tx_floorplan(self, WirelessBoard)``).

Layout doctrine (spec §6 + the user's standing connector/placement rules)
------------------------------------------------------------------------
- **The #1 SI rule:** the 4 HDMI TMDS pairs are short + matched. The RP2350B
  (``mcu``, QFN-80, rot 0) carries its HSTX/TMDS pins (GPIO12..19) on its LEFT
  edge, so the **HDMI connector sits on the LEFT board edge directly left of the
  MCU**, with the TPD8S009 (``esd_hdmi``) hard against it in the TMDS path and the
  8 series-R right at the MCU's TMDS pins.
- **External connectors on the board EDGES, mouth out:** HDMI (LEFT), USB-C (TOP),
  the two JST-XH controller ports (RIGHT, P1 upper / P2 lower), the speaker JST-PH
  (BOTTOM). Each connector's ESD/clamp is hard against it: TPD8S009 behind HDMI,
  the 2 SRV05-4A per port at each JST-XH, the SMF5.0A at the USB-C VBUS entry.
- **Tight to the MCU:** flash (QSPI pins on the MCU's TOP edge) sits just above it;
  the 12 MHz crystal + load caps (XIN/XOUT on the BOTTOM edge) just below it; the
  core SMPS inductor ``l_core`` above-right at the VREG pins (TOP-right edge),
  polarity dot/P1 (= VREG_LX switch node) facing DOWN toward the MCU's VREG_LX.
- **Pin-anchored decoupling:** the RP2350's small bypass caps (8x IOVDD, USB/QSPI
  IO, ADC, the two V3V3 bulk, the core C6/C7/C9, the flash cap) live on the
  **BOTTOM side directly under their pads** (radial-out from the pad, power pad
  facing inward). Bottom-side placement keeps the whole TOP perimeter of the MCU
  clear for the TMDS / QSPI / XOSC escape — the SI-correct choice for a QFN-EP.
- Buck cluster (``buck`` + ``l_buck`` + caps + FB divider) by the USB-C/VBUS entry;
  audio amp by the speaker connector.

4-layer JLC04161H_7628 pour map (copper layer indices):
  L1 = 0 (top GND) · L2 = 1 (solid GND plane) · L3 = 2 (V3V3 power plane) ·
  L4 = 3 (bottom GND). GND stitching vias are added later in KiCad (pcb-route).

All coordinates are in the design frame (mm), origin at board centre, +y up.
"""

import jitx
from jitx import Pour
from jitx.layerindex import Side
from jitx.placement import Placement
from jitx.shapes import Shape
from jitx.shapes.composites import IDENTITY, ShapelyGeometry
from shapely import box
from shapely.geometry import Point

# --- Board envelope (origin-centred, 72 x 66 mm rounded rect). --------------
BOARD_WIDTH = 72.0
BOARD_HEIGHT = 66.0
BOARD_CORNER_RADIUS = 2.0
SIGNAL_INSET = 1.5  # copper kept this far off the board edge

# Four M3 NPTH mounting holes, 3 mm in from each edge (clear of all parts).
MOUNT_HOLE_R = 1.6  # M3 clearance hole = 3.2 mm dia
MOUNT_HOLE_CLEAR = 0.5  # copper/keepout ring around each hole
_HX = BOARD_WIDTH / 2 - 3.0
_HY = BOARD_HEIGHT / 2 - 3.0
MOUNT_HOLES = [(sx * _HX, sy * _HY) for sx in (-1, 1) for sy in (-1, 1)]

# Copper layer indices for the 4-layer JLC04161H_7628 substrate.
_L_TOP = 0  # top: GND fill
_L_GND = 1  # inner: solid GND reference plane
_L_PWR = 2  # inner: V3V3 power plane
_L_BOT = 3  # bottom: GND fill


def _rounded_box(w: float, h: float, r: float):
    """A shapely rounded rectangle of size w x h, centred on the origin."""
    return box(-w / 2 + r, -h / 2 + r, w / 2 - r, h / 2 - r).buffer(
        r, join_style="round", quad_segs=16
    )


def _outline() -> Shape:
    """72 x 66 mm rounded-rect board outline with the four M3 holes punched out.

    JITX turns interior rings in the board ``shape`` polygon into ``Cutout``
    (drilled NPTH) features; the hole edges then read as board edges, so the
    router/DRC apply edge clearance to traces and vias near them automatically.
    """
    outline = _rounded_box(BOARD_WIDTH, BOARD_HEIGHT, BOARD_CORNER_RADIUS)
    for hx, hy in MOUNT_HOLES:
        outline = outline.difference(Point(hx, hy).buffer(MOUNT_HOLE_R, quad_segs=24))
    return Shape(ShapelyGeometry(outline), IDENTITY)


def _signal_area() -> Shape:
    """Inset rounded rect the GND/V3V3 pours fill, with a clearance disc removed
    around each mounting hole so copper never reaches the NPTH."""
    sa = _rounded_box(
        BOARD_WIDTH - 2 * SIGNAL_INSET,
        BOARD_HEIGHT - 2 * SIGNAL_INSET,
        max(BOARD_CORNER_RADIUS - SIGNAL_INSET, 0.5),
    )
    for hx, hy in MOUNT_HOLES:
        sa = sa.difference(
            Point(hx, hy).buffer(MOUNT_HOLE_R + MOUNT_HOLE_CLEAR, quad_segs=24)
        )
    return Shape(ShapelyGeometry(sa), IDENTITY)


class ConsoleBoard(jitx.Board):
    """72 x 66 mm RP2350 console board: rounded-rect outline, 4x M3 NPTH holes.

    ``signal_area`` is the inset region the top-level GND/V3V3 planes fill (copper
    held 1.5 mm off the edge and clear of the mounting holes).
    """

    shape = _outline()
    signal_area = _signal_area()


def _p(circuit, instance, x: float, y: float, rot: int = 0, side: Side = Side.Top):
    """Place ``instance`` at (x, y) mm, rotated ``rot`` deg, on ``side``."""
    circuit.place(instance, Placement((x, y), rotate=rot, on=side))


# Pose tables for the index-addressed part lists (keyed by structural index, not
# by any assembled name). Each tuple is (x, y) or (x, y, rot) in the board frame.

# 8 TMDS series-R at the MCU's left-edge TMDS pins, 2 cols feeding the ESD (W).
_TMDS_R_POSES = [
    (-7.3, 2.0),
    (-9.3, 2.0),
    (-7.3, 0.0),
    (-9.3, 0.0),
    (-7.3, -2.0),
    (-9.3, -2.0),
    (-7.3, -4.0),
    (-9.3, -4.0),
]

# RP2350 decoupling, pin-anchored on the BOTTOM side: each cap sits radially just
# outside the IOVDD/etc pad it serves (power pad facing the MCU), so the top
# perimeter stays clear for signal escape. (x, y, rot) — rot points the power pad
# inward toward the served pad. IOVDD pad order = [5,15,24,29,41,50,60,76].
#
# DE-CONGESTED (2026-06-27): pushed from radius 6.30 -> 7.2 so each cap's GND pad
# has room for a tap via AND the inner annulus (QFN courtyard 5.44 -> cap inner
# pad ~6.5) is a CLEAR via-fanout field for the QFN-80 0.4mm escape. The bottom
# side carries no opposite-side parts near the MCU, so spreading costs nothing.
# Still within the R14 decoupling window (nearest V3V3 pad < 2 mm).
_IOVDD_POSES = [
    (-6.55, 2.99, 245),
    (-6.74, -2.53, 291),
    (-3.43, -6.33, 332),
    (-0.89, -7.14, 353),
    (5.65, -4.47, 52),
    (7.19, -0.30, 88),
    (5.65, 4.47, 128),
    (-2.99, 6.55, 205),
]

# Controller ports on the RIGHT edge (JST-XH 1x10, long axis vertical), P1 upper.
_PORT_POSES = [(31.0, 14.0, 90), (31.0, -14.0, 90)]
# 2 SRV05-4A per port, inboard of each JST-XH (low array protects BTN0..3, high
# array BTN4..7). esd_ctrl order = [P1.lo, P1.hi, P2.lo, P2.hi].
_ESD_CTRL_POSES = [(25.5, 7.0), (25.5, 12.5), (25.5, -7.0), (25.5, -12.5)]
# Per-port 3V3 ferrite + local bulk cap, by each port's V3V3 (pin 10).
_FB_PORT_POSES = [(25.5, 18.0), (25.5, -18.0)]
_CB_PORT_POSES = [(25.5, 23.0), (25.5, -23.0)]


def floorplan(circuit) -> None:
    """Place every component and pour the 4-layer GND/V3V3 planes.

    Called from the top-level design's inline circuit (designs/console.py) right
    after ``ConsoleCircuit.__init__`` builds the netlist. Uses the real
    ``self.<attr>`` instances directly (no string-keyed name model).
    """
    # =================================================================
    # MCU — central, rot 0 (TMDS/HSTX on its LEFT edge faces the HDMI).
    # =================================================================
    _p(circuit, circuit.mcu, 0.0, 0.0)

    # =================================================================
    # HDMI / TMDS video — LEFT edge (the SI-critical cluster).
    # =================================================================
    # HDMI receptacle on the LEFT edge: mouth -x (out), SMD pads +x (toward MCU).
    _p(circuit, circuit.hdmi.conn, -29.5, -1.5, 270)
    # TPD8S009 straight-through ESD, hard against HDMI, in the TMDS path.
    _p(circuit, circuit.esd_hdmi, -13.0, -1.5, 90)
    # 8 series-R right at the MCU TMDS pins.
    for r, (x, y) in zip(circuit.tmds_series, _TMDS_R_POSES):
        _p(circuit, r, x, y)
    # HDMI +5 V feed ferrite, DDC pull-ups, HPD divider — around the HDMI.
    _p(circuit, circuit.fb_hdmi5v, -20.0, 6.0)
    _p(circuit, circuit.r_ddc_sda, -16.0, 9.0)
    _p(circuit, circuit.r_ddc_scl, -19.0, 9.0)
    _p(circuit, circuit.hpd_div.r_hi, -18.5, -7.5)
    _p(circuit, circuit.hpd_div.r_lo, -21.0, -7.5)  # clear of the HDMI body

    # =================================================================
    # Flash + core SMPS — hug the MCU's TOP edge (QSPI + VREG pins).
    # =================================================================
    _p(circuit, circuit.flash, -3.5, 10.0)  # QSPI flash above the MCU
    # Core inductor: dot/P1 (= VREG_LX switch node) faces DOWN toward VREG_LX.
    _p(circuit, circuit.l_core, 4.0, 9.0, 270)
    _p(circuit, circuit.r3_avdd, 7.0, 9.0)  # VREG_AVDD RC series-R

    # =================================================================
    # USB-C + buck (5 V -> 3.3 V) — TOP edge, the VBUS entry.
    # =================================================================
    _p(circuit, circuit.usb, 10.0, 27.5, 180)  # mouth +y, out the top edge
    _p(circuit, circuit.tvs_vbus.diode, 5.0, 22.0)  # VBUS clamp at the entry
    _p(circuit, circuit.r_cc1, 16.2, 26.7)  # clear of the buck body below
    _p(circuit, circuit.r_cc2, 16.2, 29.7)
    _p(circuit, circuit.buck, 18.0, 23.0)
    _p(circuit, circuit.l_buck, 18.0, 18.5)
    _p(circuit, circuit.c_buck_in, 21.5, 23.0)
    _p(circuit, circuit.c_buck_out, 21.5, 19.0)  # clear of the port ferrite L5
    _p(circuit, circuit.fb_div.r_hi, 13.5, 21.0)
    _p(circuit, circuit.fb_div.r_lo, 13.5, 19.0)

    # =================================================================
    # Crystal + audio + buttons + status LED — MCU BOTTOM edge / lower board.
    # =================================================================
    _p(circuit, circuit.xtal, 0.0, -10.0)  # XIN/XOUT on the MCU bottom edge
    _p(circuit, circuit.c_xin, -4.2, -10.0)
    _p(circuit, circuit.c_xout, 4.2, -10.0)
    # Audio: PWM -> RC LPF -> AC-couple -> amp -> speaker (bottom-left). Passives
    # in two columns on a 3 mm vertical pitch so the 0603 courtyards clear.
    _p(circuit, circuit.amp, -10.0, -13.0)
    _p(circuit, circuit.r_sd, -14.3, -8.5)
    _p(circuit, circuit.r_lpf, -14.3, -11.5)
    _p(circuit, circuit.c_lpf, -14.3, -14.5)
    _p(circuit, circuit.r_in, -17.0, -11.5)
    _p(circuit, circuit.c_ac, -17.0, -14.5)
    # c_amp_1u hugs the amp VBUS pin (right edge of the MSOP), rot 90 to clear the body.
    _p(circuit, circuit.c_amp_1u, -5.4, -13.325, 90)
    _p(circuit, circuit.c_amp_10u, -11.0, -16.8)  # VBUS bulk below the amp
    _p(circuit, circuit.spk, -10.0, -28.5)  # JST-PH on the BOTTOM edge
    # BOOTSEL + RUN buttons (6 mm tactile, ~9 mm bbox) spread across the lower
    # board, well clear of the crystal cluster above; RUN RC right of btn_run;
    # status LED + series-R by the MCU's lower-right edge.
    _p(circuit, circuit.btn_boot, -3.0, -22.0)
    _p(circuit, circuit.btn_run, 7.0, -22.0)
    _p(circuit, circuit.r_run, 14.0, -20.5)
    _p(circuit, circuit.c_run, 14.0, -23.5)
    _p(circuit, circuit.r_led, 16.5, -14.0)
    _p(circuit, circuit.led_status, 20.5, -14.0)
    # ADC_AVDD ferrite (quiet analog supply), by the MCU's right-edge ADC pins.
    _p(circuit, circuit.fb_adc, 9.0, 3.0, 90)

    # =================================================================
    # Two controller ports — RIGHT edge (P1 upper, P2 lower), ESD hard against.
    # =================================================================
    for port, (x, y, rot) in zip(circuit.ports, _PORT_POSES):
        _p(circuit, port, x, y, rot)
    for d, (x, y) in zip(circuit.esd_ctrl, _ESD_CTRL_POSES):
        _p(circuit, d, x, y)
    for fb, (x, y) in zip(circuit.fb_ports, _FB_PORT_POSES):
        _p(circuit, fb, x, y)
    for cb, (x, y) in zip(circuit.c_port_bulk, _CB_PORT_POSES):
        _p(circuit, cb, x, y)

    # =================================================================
    # RP2350 pin-anchored decoupling — BOTTOM side, under the served pads.
    # =================================================================
    for c, (x, y, rot) in zip(circuit.c_iovdd, _IOVDD_POSES):
        _p(circuit, c, x, y, rot, Side.Bottom)
    # Small (100 nF) per-pin caps stay in the decoupling window but are spread to
    # radius ~7 so each keeps a clear GND-via spot; the three top-edge ones are on
    # a wider pitch. V3V3 pad faces the MCU pads they serve.
    _p(circuit, circuit.c_usb_otp, -0.3, 6.0, 0, Side.Bottom)  # USB_OTP_VDD (R14 window)
    _p(circuit, circuit.c_qspi_io, 2.5, 6.0, 0, Side.Bottom)  # QSPI_IOVDD (R14 window)
    _p(circuit, circuit.c_adc, 8.2, 4.0, 125, Side.Bottom)  # ADC_AVDD (outboard, own net)
    # Core/bulk caps (4.7 µF + 10 µF) are R14-exempt (>=1.5 µF), so push them OUT
    # of the inner ring entirely — into the open B-side annulus and the wide-open
    # area below the MCU — leaving the inner ring for the QFN via fanout + the GND
    # taps of the small caps.
    _p(circuit, circuit.c7_core_out, -8.6, 0.3, 268, Side.Bottom)  # DVDD[0], left outer
    _p(circuit, circuit.c6_core_in, 3.0, 9.4, 0, Side.Bottom)  # VREG_VIN, top outer
    _p(circuit, circuit.c9_avdd, 7.3, 8.6, 142, Side.Bottom)  # VREG_AVDD, top-right outer
    _p(circuit, circuit.c_bulk_v3v3[0], -5.5, -9.5, 0, Side.Bottom)  # bulk, below-left
    _p(circuit, circuit.c_bulk_v3v3[1], 3.6, -8.9, 0, Side.Bottom)  # bulk, below-right
    _p(circuit, circuit.c_flash, 0.125, 11.4, 0, Side.Bottom)  # under flash VCC pad

    # =================================================================
    # 4-layer pours: GND on L1/L2/L4, V3V3 on the L3 power plane.
    # =================================================================
    sa = ConsoleBoard.signal_area
    circuit.GND += Pour(sa, layer=_L_TOP)
    circuit.GND += Pour(sa, layer=_L_GND)
    circuit.V3V3 += Pour(sa, layer=_L_PWR)
    circuit.GND += Pour(sa, layer=_L_BOT)
