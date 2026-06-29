"""rp2350_console_jitx — top-level design (ConsoleBoard), Phase 2 netlist.

The RP2350 game console: an RP2350B renders DVI-over-HDMI video through its HSTX
peripheral, plays a menu of games from a 16 MB QSPI flash, reads two 8-button
gamepads over the frozen JST-XH contract, and drives an onboard 8 Ohm speaker via
a mono Class-D amp. USB-C powered + programmed (native USB / UF2).

This file owns the whole board. ``ConsoleCircuit`` instantiates every component
(the modeled ICs/connectors from ``components/`` plus the simple passives, ferrite
beads, buttons and status LED pulled straight from the parts DB) and wires every
net, grouped by concern into four sections that mirror the spec
(``docs/specs/2026-06-25-rp2350-console-design.md``) and ``ARCHITECTURE.md``:

  2.1  Power + RP2350 core SMPS + flash + clock
  2.2  HDMI / HSTX video
  2.3  Two controller ports + console-side ESD
  2.4  PWM audio -> PAM8302A -> 8 Ohm speaker

Nets (ARCHITECTURE "Power tree"):
  VBUS  — 5 V from USB-C VBUS         V3V3 — 3.3 V buck output (the main rail)
  GND   — ground                     DVDD — 1.1 V RP2350 core (internal SMPS out)

GPIO assignment (frozen here; deterministic):
  HSTX video (4 TMDS pairs)  GPIO12..19  (D0=12/13, D1=14/15, D2=16/17, CLK=18/19)
  Controller P1 BTN0..7      GPIO0..7
  Controller P2 BTN0..7      GPIO8,9,10,11,20,21,22,23
  Audio PWM                  GPIO24      Amp SD/enable  GPIO25
  DDC SDA / SCL              GPIO26 / GPIO27 (+ pull-ups)
  HDMI HPD (via divider)     GPIO28      Status LED     GPIO29
  (GPIO30..47, incl. ADC GPIO40..47, left free for expansion.)

NOTE on the HSTX pin map: GPIO12..19 is the HSTX-capable bank (datasheet F0=HSTX,
see components/rp2350b.py). The exact lane->GPIO and +/- polarity assignment is
firmware/route-tunable (HSTX can remap lanes; diff polarity can be swapped in the
DVI driver), so the pair ordering below is a sensible default, not a hard pin lock.

Phase 2 was netlist-only; Phase 3.1 adds the TMDS differential constraints (each
HDMI pair routed on the JLC04161H_7628 100 Ohm differential routing structure,
GND-referenced, intra-pair skew ~0 — see section 2.2). Placement, floorplan and
copper pours remain Phase 3 — intentionally absent here.
"""

from jitx import Net
from jitx.circuit import Circuit
from jitx.net import DiffPair, Topology
from jitx.toleranced import Toleranced
from jitxlib.parts import Capacitor, Inductor, Part, PartQuery, Resistor, ResistorQuery
from jitxlib.voltage_divider import (
    VoltageDividerConstraints,
    voltage_divider_from_constraints,
)

from .components.aota_b201610_3r3 import AotaB201610S3R3
from .components.crystal_12mhz import Crystal12MHz
from .components.hdmi_a import HdmiA
from .components.jst_ph_2 import JstPH2
from .components.jst_xh_10 import JstXH10
from .components.pam8302a import PAM8302A
from .components.rp2350b import RP2350B
from .components.smf5_0a import Smf5_0a
from .components.srv05_4a import Srv05_4A
from .components.tlv62569 import Tlv62569
from .components.tpd8s009 import Tpd8s009
from .components.usbc import TYPEC31M12
from .components.w25q128jv import W25Q128JV

# Ferrite-bead MPNs (DB-resolved, expose p[1]/p[2]) — see task acceptance block.
_FB_POWER = (
    "GZ2012D601TF"  # 600 Ohm @ 100 MHz, 0805 — rail isolation (per-port 3V3, HDMI +5V)
)
_FB_ANALOG = "GZ2012D101TF"  # 100 Ohm @ 100 MHz, 0805 — low-DCR feed for ADC_AVDD
# Simple mechanical / indicator parts (DB-resolved, build-probed).
_BTN = dict(mpn="TS-1187A-B-A-B")  # 4-pad tactile (A+B = one pole, C+D = other)
_LED = dict(mpn="KT-0805G")  # 0805 green LED, ports A (anode) / K (cathode)


class TMDSPair(DiffPair):
    """One HDMI TMDS differential pair (``.p`` / ``.n``).

    Used to build the connector-side differential *topology* (series-R output ->
    ESD shunt -> HDMI pin) so the 100 Ohm differential routing structure and the
    intra-pair skew match travel with the actual high-speed traces.
    """


class ConsoleCircuit(Circuit):
    """The whole console as one composition, wired in four spec-aligned sections."""

    def __init__(self) -> None:
        # =================================================================
        # Rail nets (plain Net — NO PowerSymbol/GroundSymbol per project rule).
        # =================================================================
        self.VBUS = Net(name="VBUS")  # 5 V from USB-C
        self.V3V3 = Net(name="V3V3")  # 3.3 V buck output (main rail)
        self.GND = Net(name="GND")
        self.DVDD = Net(name="DVDD")  # 1.1 V RP2350 core (internal SMPS output)

        # =================================================================
        # 2.1  POWER + CORE + FLASH + CLOCK
        # =================================================================
        self.usb = TYPEC31M12()  # USB-C 2.0 receptacle (power + UF2 data)
        self.tvs_vbus = Smf5_0a()  # VBUS 5 V TVS (unidirectional)
        self.buck = Tlv62569()  # 5 V -> 3.3 V synchronous buck
        self.l_buck = Inductor(inductance=2.2e-6, current_rating=1.5)  # buck output L
        self.mcu = RP2350B()  # the MCU
        self.l_core = AotaB201610S3R3()  # L1 — RP2350 core SMPS inductor (polarized)
        self.flash = W25Q128JV()  # 16 MB QSPI NOR flash
        self.xtal = Crystal12MHz()  # 12 MHz reference crystal
        self.btn_boot = Part(PartQuery(), **_BTN)  # BOOTSEL (QSPI_SS strap)
        self.btn_run = Part(PartQuery(), **_BTN)  # RUN reset
        self.led_status = Part(PartQuery(), **_LED)  # status LED
        self.fb_adc = Part(PartQuery(), mpn=_FB_ANALOG)  # ADC_AVDD ferrite

        # --- USB-C front end: VBUS / GND, CC sink resistors, D+/D- ---
        self.usbc_power_nets = [
            self.VBUS + self.usb.B4A9 + self.usb.A4B9,  # both VBUS merged pads
            self.GND + self.usb.A1B12 + self.usb.B1A12,  # both GND merged pads
            self.GND
            + self.usb.EH[0]
            + self.usb.EH[1]
            + self.usb.EH[2]
            + self.usb.EH[3],
            self.GND + self.usb.SHELL[0] + self.usb.SHELL[1],  # strain-relief shells
        ]
        # CC1 (A5) / CC2 (B5) each via 5.1 k to GND — UFP advertises default USB power.
        self.r_cc1 = Resistor(resistance=5.1e3, case="0603")
        self.r_cc1.insert(self.usb.A5, self.GND)
        self.r_cc2 = Resistor(resistance=5.1e3, case="0603")
        self.r_cc2.insert(self.usb.B5, self.GND)
        # SBU1/SBU2 unused on a USB-2.0-only design.
        self.usb.A8.no_connect()
        self.usb.B8.no_connect()
        # USB 2.0 data: tie both reversible-C positions. 27 Ohm series termination
        # (R7/R8) close to the MCU, REQUIRED for USB impedance per the RP2350 hardware
        # design guide §5.1 (the RP2350 PHY integrates pull-ups/downs but NOT series
        # termination); Pico 2 W §3.7 adds the same two resistors.
        self.r_usb_dp = Resistor(resistance=27.0, case="0402")
        self.r_usb_dm = Resistor(resistance=27.0, case="0402")
        self.usb_data_nets = [
            self.mcu.USB_DP + self.r_usb_dp.p1,            # D+: MCU pad -> 27R ...
            self.usb.A6 + self.usb.B6 + self.r_usb_dp.p2,  # ... -> connector D+
            self.mcu.USB_DM + self.r_usb_dm.p1,            # D-: MCU pad -> 27R ...
            self.usb.A7 + self.usb.B7 + self.r_usb_dm.p2,  # ... -> connector D-
        ]

        # --- VBUS TVS: unidirectional clamp, cathode on the +5 V rail (see smf5_0a) ---
        self.tvs_nets = [
            self.VBUS
            + self.tvs_vbus.K,  # cathode -> VBUS (reverse-biased in normal op)
            self.GND + self.tvs_vbus.A,  # anode -> GND
        ]

        # --- Buck TLV62569: VIN<-VBUS, EN high, SW->L->V3V3, FB divider ---
        self.buck_power_nets = [
            self.VBUS + self.buck.VIN,
            self.VBUS + self.buck.EN,  # tie EN high (always-on; do NOT float)
            self.GND + self.buck.GND,
        ]
        self.c_buck_in = Capacitor(capacitance=10e-6, case="0805")
        self.c_buck_in.insert(self.buck.VIN, self.buck.GND, short_trace=True)
        # SW -> output inductor -> V3V3.  short_trace needs two Ports; V3V3 is a Net,
        # so this insert is plain (the inductor is the switch-node element, not a
        # decoupling cap) — see grep-gate disposition.
        self.l_buck.insert(self.buck.SW, self.V3V3)
        # Output cap pinned across the inductor output (l_buck.p2 = V3V3) and the
        # buck ground return — both Ports, so short_trace keeps it at the output.
        self.c_buck_out = Capacitor(capacitance=22e-6, case="0805")
        self.c_buck_out.insert(self.l_buck.p2, self.buck.GND, short_trace=True)
        # FB divider from constraints (NEVER hand-picked): V3V3 -> FB -> GND.
        # TLV62569 VFB = 0.6 V nominal (datasheet "Feedback regulation voltage":
        # 0.588 / 0.600 / 0.612 V = 0.6 V +/-2%), so v_out = 0.6 V +/-2%.
        self.fb_div = voltage_divider_from_constraints(
            VoltageDividerConstraints(
                v_in=Toleranced.exact(3.3),
                v_out=Toleranced.percent(0.6, 2.0),
                current=50e-6,
                prec_series=[1.0, 0.1],
                base_query=ResistorQuery(case=["0402", "0603"]),
            )
        )
        self.fb_div_nets = [
            self.V3V3 + self.fb_div.hi,
            self.buck.FB + self.fb_div.out,
            self.GND + self.fb_div.lo,
        ]

        # --- RP2350 core SMPS (RPi Pico-2 exact): VREG_VIN<-3V3, LX->L1->DVDD ---
        self.VREG_LX = Net(name="VREG_LX")
        self.core_smps_nets = [
            self.V3V3 + self.mcu.VREG_VIN,  # core-regulator input from 3V3
            self.GND + self.mcu.VREG_PGND,  # core-regulator power ground
            # L1 (polarized): RPi Fig 25 puts the polarity dot on the DVDD/output side
            # (current exits at the dot). dot/P1 -> DVDD; P2 -> VREG_LX switch node.
            # Physical rotation confirmed against Fig 23 in the 3D view at the export.
            self.VREG_LX + self.mcu.VREG_LX + self.l_core.P2,
            self.DVDD + self.l_core.P1,
            # DVDD 1.1 V feeds the 3 core pads and the regulator feedback sense.
            self.DVDD
            + self.mcu.DVDD[0]
            + self.mcu.DVDD[1]
            + self.mcu.DVDD[2]
            + self.mcu.VREG_FB,
        ]
        # C6 (4.7 uF) core-reg input decoupling; C7 (4.7 uF) on DVDD; both pinned.
        self.c6_core_in = Capacitor(capacitance=4.7e-6, case="0402")
        self.c6_core_in.insert(self.mcu.VREG_VIN, self.mcu.VREG_PGND, short_trace=True)
        self.c7_core_out = Capacitor(capacitance=4.7e-6, case="0402")
        self.c7_core_out.insert(self.mcu.DVDD[0], self.mcu.GND, short_trace=True)
        # 2x 100 nF on the inner DVDD pads (DVDD[1]=pad32, DVDD[2]=pad51) close to the
        # pins per datasheet §6.1.3 (C7 4.7 uF above sits on the furthest DVDD pad).
        self.c_dvdd = [Capacitor(capacitance=100e-9, case="0402") for _ in range(2)]
        self.c_dvdd[0].insert(self.mcu.DVDD[1], self.mcu.GND, short_trace=True)
        self.c_dvdd[1].insert(self.mcu.DVDD[2], self.mcu.GND, short_trace=True)
        # R3 (33 Ohm) + C9 (4.7 uF) = VREG_AVDD RC filter off 3V3.
        self.r3_avdd = Resistor(resistance=33.0, case="0402")
        self.r3_avdd.insert(self.mcu.VREG_AVDD, self.V3V3)
        self.c9_avdd = Capacitor(capacitance=4.7e-6, case="0402")
        self.c9_avdd.insert(self.mcu.VREG_AVDD, self.mcu.VREG_PGND, short_trace=True)

        # --- RP2350 supply rails on V3V3 + per-pad decoupling ---
        self.mcu_rail_nets = [
            self.V3V3
            + self.mcu.IOVDD[0]
            + self.mcu.IOVDD[1]
            + self.mcu.IOVDD[2]
            + self.mcu.IOVDD[3]
            + self.mcu.IOVDD[4]
            + self.mcu.IOVDD[5]
            + self.mcu.IOVDD[6]
            + self.mcu.IOVDD[7]
            + self.mcu.USB_OTP_VDD
            + self.mcu.QSPI_IOVDD,
            self.GND + self.mcu.GND,  # central exposed pad = GND
        ]
        # One 100 nF per IOVDD pad (pin-anchored, short_trace to the EP GND).
        self.c_iovdd = [Capacitor(capacitance=100e-9, case="0402") for _ in range(8)]
        for i in range(8):
            self.c_iovdd[i].insert(self.mcu.IOVDD[i], self.mcu.GND, short_trace=True)
        # 100 nF on the USB and QSPI IO supplies.
        self.c_usb_otp = Capacitor(capacitance=100e-9, case="0402")
        self.c_usb_otp.insert(self.mcu.USB_OTP_VDD, self.mcu.GND, short_trace=True)
        self.c_qspi_io = Capacitor(capacitance=100e-9, case="0402")
        self.c_qspi_io.insert(self.mcu.QSPI_IOVDD, self.mcu.GND, short_trace=True)
        # ADC_AVDD: V3V3 through a ferrite bead + 100 nF (quiet analog supply).
        self.adc_avdd_nets = [
            self.V3V3 + self.fb_adc.p[1],
            self.mcu.ADC_AVDD + self.fb_adc.p[2],
        ]
        self.c_adc = Capacitor(capacitance=100e-9, case="0402")
        self.c_adc.insert(self.mcu.ADC_AVDD, self.mcu.GND, short_trace=True)
        # Two 10 uF bulk caps on V3V3 at the MCU.
        self.c_bulk_v3v3 = [Capacitor(capacitance=10e-6, case="0805") for _ in range(2)]
        self.c_bulk_v3v3[0].insert(self.mcu.IOVDD[0], self.mcu.GND, short_trace=True)
        self.c_bulk_v3v3[1].insert(self.mcu.IOVDD[7], self.mcu.GND, short_trace=True)

        # --- QSPI flash W25Q128 (3.3 V) ---
        self.flash_power_nets = [
            self.V3V3 + self.flash.VCC,
            self.GND + self.flash.GND,
        ]
        self.c_flash = Capacitor(capacitance=100e-9, case="0402")
        self.c_flash.insert(self.flash.VCC, self.flash.GND, short_trace=True)
        self.qspi_nets = [
            self.mcu.QSPI_SS + self.flash.CS,  # CS (also the BOOTSEL strap)
            self.mcu.QSPI_SCLK + self.flash.CLK,
            self.mcu.QSPI_SD0 + self.flash.IO0_DI,
            self.mcu.QSPI_SD1 + self.flash.IO1_DO,
            self.mcu.QSPI_SD2 + self.flash.IO2_WP,
            self.mcu.QSPI_SD3 + self.flash.IO3_HOLD,
        ]

        # --- 12 MHz crystal + 1k XOUT damping + load caps ---
        # R2 (1k) in series with XOUT: REQUIRED at 3.3 V IOVDD to keep the crystal from
        # being over-driven/damaged (RP2350 HW guide §4 Fig 10). The load cap stays on
        # the crystal side of R2.
        self.r_xosc = Resistor(resistance=1e3, case="0603")
        self.xtal_nets = [
            self.mcu.XIN + self.xtal.XIN,
            self.mcu.XOUT + self.r_xosc.p1,
            self.r_xosc.p2 + self.xtal.XOUT,
            self.GND + self.xtal.GND,
        ]
        # 2x 30 pF C0G load caps (XIN/XOUT crystal side to GND). Resonant-tank load
        # caps, NOT power decoupling -> short_trace intentionally NOT used. C0G/NP0
        # dielectric pinned so temperature/bias drift can't pull the oscillator.
        self.c_xin = Capacitor(
            capacitance=30e-12, case="0603", temperature_coefficient_code="C0G"
        )
        self.c_xin.insert(self.xtal.XIN, self.GND)
        self.c_xout = Capacitor(
            capacitance=30e-12, case="0603", temperature_coefficient_code="C0G"
        )
        self.c_xout.insert(self.xtal.XOUT, self.GND)

        # --- BOOTSEL + RUN buttons ---
        # BOOTSEL: pressing pulls QSPI_SS (flash CS strap) to GND at reset. R6 (1k) in
        # series limits contention current if the button is pressed while QSPI_SS is
        # being driven (XIP/CS active) — per RP2350 HW guide §3.1.
        self.r_boot = Resistor(resistance=1e3, case="0603")
        self.bootsel_nets = [
            self.mcu.QSPI_SS + self.r_boot.p1,
            self.r_boot.p2 + self.btn_boot.A + self.btn_boot.B,
            self.GND + self.btn_boot.C + self.btn_boot.D,
        ]
        # RUN reset: 10 k pull-up to V3V3, button to GND, 100 nF filter cap.
        self.RUN = Net(name="RUN")
        self.RUN += self.mcu.RUN
        self.r_run = Resistor(resistance=10e3, case="0603")
        self.r_run.insert(self.RUN, self.V3V3)
        self.run_btn_nets = [
            self.RUN + self.btn_run.A + self.btn_run.B,
            self.GND + self.btn_run.C + self.btn_run.D,
        ]
        # RUN RC reset filter cap -> NOT a power-rail cap, so short_trace not used.
        self.c_run = Capacitor(capacitance=100e-9, case="0603")
        self.c_run.insert(self.mcu.RUN, self.GND)

        # --- Status LED on GPIO29 (lit when the GPIO is driven high) ---
        self.LED_A = Net(name="LED_A")  # series-resistor / LED-anode node
        self.r_led = Resistor(resistance=1e3, case="0603")
        self.r_led.insert(self.mcu.GPIO[29], self.LED_A)
        self.led_nets = [
            self.LED_A + self.led_status.A,
            self.GND + self.led_status.K,
        ]

        # =================================================================
        # 2.2  HDMI / HSTX VIDEO
        # =================================================================
        self.hdmi = HdmiA()  # HDMI Type-A receptacle (Circuit wrapper)
        self.esd_hdmi = Tpd8s009()  # 8-ch TMDS ESD array
        self.fb_hdmi5v = Part(PartQuery(), mpn=_FB_POWER)  # +5 V feed ferrite

        # HSTX GPIO -> 0 Ohm series R -> ESD shunt node -> HDMI connector.
        # Pair order: D0=GPIO12/13, D1=14/15, D2=16/17, CLK=18/19.
        # 0 Ohm series Rs are SI placeholders. HSTX is a pseudo-differential LVCMOS
        # driver (neighbouring GPIOs driven complementary, delay-matched) — being
        # voltage-mode is exactly why an in-line series R / 0 Ohm jumper is tolerable
        # (a true current-mode TMDS driver would not be); swap in a small R for SI.
        _tmds_gpio_p = [12, 14, 16, 18]
        _tmds_gpio_n = [13, 15, 17, 19]
        _esd_p = [
            self.esd_hdmi.D0_P,
            self.esd_hdmi.D1_P,
            self.esd_hdmi.D2_P,
            self.esd_hdmi.D3_P,
        ]
        _esd_n = [
            self.esd_hdmi.D0_N,
            self.esd_hdmi.D1_N,
            self.esd_hdmi.D2_N,
            self.esd_hdmi.D3_N,
        ]
        _hdmi_p = [
            self.hdmi.TMDS_D0_P,
            self.hdmi.TMDS_D1_P,
            self.hdmi.TMDS_D2_P,
            self.hdmi.TMDS_CLK_P,
        ]
        _hdmi_n = [
            self.hdmi.TMDS_D0_N,
            self.hdmi.TMDS_D1_N,
            self.hdmi.TMDS_D2_N,
            self.hdmi.TMDS_CLK_N,
        ]
        # The series-R output -> ESD shunt -> HDMI pin segment is the actual
        # high-speed differential trace, so each pair is built as a DiffPair >>
        # topology (TMDSPair) that carries the 100 Ohm differential routing
        # structure + intra-pair skew match (constraints applied just below). The
        # GPIO -> series-R hop is a short low-speed stub, left a plain net.
        self.tmds_src = [TMDSPair() for _ in range(4)]  # series-R output side
        self.tmds_dst = [TMDSPair() for _ in range(4)]  # HDMI-connector side
        self.tmds_series = []  # the 8 series resistors
        self.tmds_nets = []  # GPIO -> series-R stub nets (not impedance-controlled)
        self.tmds_topos = []  # the 4 connector-side differential topologies
        for k in range(4):
            rp = Resistor(resistance=0.0, case="0402")
            rn = Resistor(resistance=0.0, case="0402")
            self.tmds_series.append(rp)
            self.tmds_series.append(rn)
            self.tmds_nets.append(self.mcu.GPIO[_tmds_gpio_p[k]] + rp.p1)
            self.tmds_nets.append(self.mcu.GPIO[_tmds_gpio_n[k]] + rn.p1)
            src = self.tmds_src[k]
            dst = self.tmds_dst[k]
            # series-R outputs feed the src diff-pair; the ESD shunt nodes + HDMI
            # connector pins land on the dst diff-pair (each P/N stays one net).
            self += src.p + rp.p2
            self += src.n + rn.p2
            self += dst.p + _esd_p[k] + _hdmi_p[k]
            self += dst.n + _esd_n[k] + _hdmi_n[k]
            # ordered differential path src -> dst carries the SI constraints.
            self += src >> dst
            self.tmds_topos.append(Topology(src, dst))
        # The 100 Ohm DRS_100 + skew-match SI constraints on self.tmds_topos are
        # applied at the top-level design (designs/console.py) — SI constraints must
        # live under designs/ per the project convention (grep_gates).

        # ESD array power + ground; NC unconnected.
        self.esd_power_nets = [
            self.V3V3 + self.esd_hdmi.VCC[0] + self.esd_hdmi.VCC[1],
            self.GND
            + self.esd_hdmi.GND[0]
            + self.esd_hdmi.GND[1]
            + self.esd_hdmi.GND[2]
            + self.esd_hdmi.GND[3],
        ]
        self.esd_hdmi.NC.no_connect()

        # HDMI shields + connector GND + mounting tabs -> GND.
        self.hdmi_gnd_nets = [
            self.GND
            + self.hdmi.TMDS_D0_SH
            + self.hdmi.TMDS_D1_SH
            + self.hdmi.TMDS_D2_SH
            + self.hdmi.TMDS_CLK_SH,
            self.GND + self.hdmi.GND,  # pin 17 DDC/CEC ground
            self.GND
            + self.hdmi.SHIELD[0]
            + self.hdmi.SHIELD[1]
            + self.hdmi.SHIELD[2]
            + self.hdmi.SHIELD[3],
        ]
        # +5 V (pin 18) from VBUS through a ferrite bead (source-side output).
        self.hdmi_v5_nets = [
            self.VBUS + self.fb_hdmi5v.p[1],
            self.hdmi.V5 + self.fb_hdmi5v.p[2],
        ]
        # DDC I2C: SDA=GPIO26, SCL=GPIO27, with 4.7 k pull-ups to V3V3.
        self.ddc_nets = [
            self.mcu.GPIO[26] + self.hdmi.SDA,
            self.mcu.GPIO[27] + self.hdmi.SCL,
        ]
        # DDC bus pull-ups live at this (board / bus-composition) level — named
        # r_ddc_* (the console is the I2C master that composes the HDMI-sink slave).
        self.r_ddc_sda = Resistor(resistance=4.7e3, case="0603")
        self.r_ddc_sda.insert(self.hdmi.SDA, self.V3V3)
        self.r_ddc_scl = Resistor(resistance=4.7e3, case="0603")
        self.r_ddc_scl.insert(self.hdmi.SCL, self.V3V3)
        # HPD (pin 19) -> divider -> GPIO28 (5 V-class line knocked to a 3V3-safe level).
        self.hpd_div = voltage_divider_from_constraints(
            VoltageDividerConstraints(
                v_in=Toleranced.exact(5.0),
                v_out=Toleranced.percent(3.0, 8.0),
                current=20e-6,
                prec_series=[1.0, 0.1],
                base_query=ResistorQuery(case=["0402", "0603"]),
            )
        )
        self.hpd_nets = [
            self.hdmi.HPD + self.hpd_div.hi,
            self.mcu.GPIO[28] + self.hpd_div.out,
            self.GND + self.hpd_div.lo,
        ]
        # CEC (pin 13) + UTILITY (pin 14) intentionally unused this revision.

        # =================================================================
        # 2.3  TWO CONTROLLER PORTS + CONSOLE-SIDE ESD
        # =================================================================
        self.ports = [JstXH10(), JstXH10()]  # P1, P2 (JST-XH 1x10, frozen contract)
        self.esd_ctrl = [Srv05_4A() for _ in range(4)]  # 2 SRV05-4A per port
        self.fb_ports = [Part(PartQuery(), mpn=_FB_POWER) for _ in range(2)]  # 3V3 feed
        self.c_port_bulk = [Capacitor(capacitance=10e-6, case="0805") for _ in range(2)]

        # P1 -> GPIO0..7 ; P2 -> GPIO8,9,10,11,20,21,22,23.
        _port_gpio = [
            [0, 1, 2, 3, 4, 5, 6, 7],
            [8, 9, 10, 11, 20, 21, 22, 23],
        ]
        self.ctrl_nets = []
        for p in range(2):
            j = self.ports[p]
            fb = self.fb_ports[p]
            d_lo = self.esd_ctrl[p * 2]  # protects BTN0..3
            d_hi = self.esd_ctrl[p * 2 + 1]  # protects BTN4..7
            # GND return (pin 9); 3V3-out (pin 10) fed through a per-port ferrite.
            self.ctrl_nets.append(self.GND + j.GND)
            self.ctrl_nets.append(self.V3V3 + fb.p[1])
            self.ctrl_nets.append(fb.p[2] + j.V3V3)
            # Local bulk cap on the (post-ferrite) port 3V3 rail.
            self.c_port_bulk[p].insert(j.V3V3, j.GND, short_trace=True)
            # ESD array rails.
            self.ctrl_nets.append(self.V3V3 + d_lo.VCC + d_hi.VCC)
            self.ctrl_nets.append(self.GND + d_lo.GND + d_hi.GND)
            # Indexed port + IO lists (no getattr / string keys).
            btns = [j.BTN0, j.BTN1, j.BTN2, j.BTN3, j.BTN4, j.BTN5, j.BTN6, j.BTN7]
            io_lo = [d_lo.IO1, d_lo.IO2, d_lo.IO3, d_lo.IO4]
            io_hi = [d_hi.IO1, d_hi.IO2, d_hi.IO3, d_hi.IO4]
            for i in range(8):
                io = io_lo[i] if i < 4 else io_hi[i - 4]
                # Each active-low button line: MCU GPIO + connector pin + ESD shunt.
                self.ctrl_nets.append(self.mcu.GPIO[_port_gpio[p][i]] + btns[i] + io)

        # =================================================================
        # 2.4  AUDIO: PWM -> RC LPF -> AC-couple -> PAM8302A -> 8 Ohm speaker
        # =================================================================
        self.amp = PAM8302A()  # mono filterless Class-D amp (5 V)
        self.spk = JstPH2()  # 8 Ohm speaker connector (JST-PH 2-pin)

        # Reconstruction RC LPF: corner = 1/(2*pi*3.3k*2.2nF) ~= 21.9 kHz.
        self.r_lpf = Resistor(resistance=3.3e3, case="0603")
        # RC time-constant cap (filter), NOT power decoupling -> no short_trace.
        self.c_lpf = Capacitor(capacitance=2.2e-9, case="0603")
        self.c_lpf.insert(self.r_lpf.p2, self.GND)
        # Gain resistor Rin at the amp input. Per datasheet GV = 20*log10(150k/(10k+Rin)):
        # max gain is 23.5 dB at Rin=0 (the BOM "2x(142k/Rin)" note overstates it).
        # Target ~24 dB -> Rin = 0 Ohm (the achievable max); the footprint lets a
        # larger value be fitted later to back gain off (gain falls as Rin rises).
        self.r_in = Resistor(resistance=0.0, case="0603")
        # AC-coupling cap: signal cap (with the amp's internal 10k forms the input
        # high-pass, ~16 Hz at 1 uF) -> NOT power decoupling, so no short_trace.
        self.c_ac = Capacitor(capacitance=1e-6, case="0603")
        self.c_ac.insert(self.r_lpf.p2, self.r_in.p1)
        self.audio_nets = [
            self.mcu.GPIO[24] + self.r_lpf.p1,  # PWM in
            self.r_in.p2 + self.amp.INP,  # gain resistor -> IN+
            self.GND + self.amp.INN,  # single-ended input reference
        ]
        # Amp shutdown (active-low): driven by GPIO25, 100 k pull-up to V3V3
        # -> default HIGH = amp ENABLED at boot (firmware mutes by driving low).
        self.SD = Net(name="AMP_SD")
        self.SD += self.amp.SD + self.mcu.GPIO[25]
        self.r_sd = Resistor(resistance=100e3, case="0603")
        self.r_sd.insert(self.SD, self.V3V3)
        # Amp supply = 5 V VBUS; 1 uF + 10 uF local bulk (pinned).
        self.amp_power_nets = [
            self.VBUS + self.amp.VDD,
            self.GND + self.amp.GND,
        ]
        self.c_amp_1u = Capacitor(capacitance=1e-6, case="0603")
        self.c_amp_1u.insert(self.amp.VDD, self.amp.GND, short_trace=True)
        self.c_amp_10u = Capacitor(capacitance=10e-6, case="0805")
        self.c_amp_10u.insert(self.amp.VDD, self.amp.GND, short_trace=True)
        # Filterless BTL outputs route straight to the speaker (NO AC-couple).
        self.amp_out_nets = [
            self.amp.OUTP + self.spk.SPK_P,
            self.amp.OUTN + self.spk.SPK_N,
        ]
        self.amp.NC.no_connect()


# The top-level Design (ConsoleBoard: substrate + board outline) and the TMDS SI
# constraints live in designs/console.py (TOP_LEVEL_PATH). This module is the
# netlist only. Build: rp2350_console_jitx.designs.console.ConsoleBoard
