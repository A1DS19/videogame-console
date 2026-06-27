"""
Minimal test design for the Srv05_4A component (D).

Instantiates a single Srv05_4A in a SampleDesign circuit to verify the
component builds correctly: the SOT-23-6 landpattern, the BoxSymbol with
IO1..IO4 on one side and GND/VCC on the other, and the PadMapping with
IO lines on pins 1/3/4/6, GND on pin 2, VCC on pin 5.
"""

import jitx
from jitx.container import inline
from jitx.sample import SampleDesign

from rp2350_console_jitx.components.srv05_4a import Srv05_4A


class TestSrv05_4A(SampleDesign):
    @inline
    class circuit(jitx.Circuit):
        dut = Srv05_4A()


Design: type[TestSrv05_4A] = TestSrv05_4A
