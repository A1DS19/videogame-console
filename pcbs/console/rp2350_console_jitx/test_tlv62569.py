"""
Minimal test design for the Tlv62569 component (U).

Instantiates a single Tlv62569 in a SampleDesign circuit to verify the
component builds correctly: the SOT-23-5 (DBV) landpattern, the BoxSymbol with
VIN/EN on the left, SW/FB on the right and GND down, and the PadMapping with
EN=p[1], GND=p[2], SW=p[3], VIN=p[4], FB=p[5].
"""

import jitx
from jitx.container import inline
from jitx.sample import SampleDesign

from rp2350_console_jitx.components.tlv62569 import Tlv62569


class TestTlv62569(SampleDesign):
    @inline
    class circuit(jitx.Circuit):
        dut = Tlv62569()


Design: type[TestTlv62569] = TestTlv62569
