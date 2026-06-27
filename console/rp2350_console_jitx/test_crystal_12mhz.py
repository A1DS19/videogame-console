"""
Minimal test design for the Crystal12MHz component (Y).

Instantiates a single Crystal12MHz in a SampleDesign circuit to verify the
component builds: the hand-built 4-pad SMD3225 landpattern, the BoxSymbol with
XIN/XOUT on the sides and GND down, and the PadMapping (XIN=pad1, XOUT=pad3,
GND=pads 2 & 4).
"""

import jitx
from jitx.container import inline
from jitx.sample import SampleDesign

from rp2350_console_jitx.components.crystal_12mhz import Crystal12MHz


class TestCrystal12MHz(SampleDesign):
    @inline
    class circuit(jitx.Circuit):
        dut = Crystal12MHz()


Design: type[TestCrystal12MHz] = TestCrystal12MHz
