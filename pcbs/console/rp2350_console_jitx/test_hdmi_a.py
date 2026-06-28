"""
Minimal test design for the HdmiA connector wrapper.

Instantiates a single HdmiA in a SampleDesign circuit to verify the DB part
resolves (footprint + 3D) and the 19 HDMI-A pins + 4 shell tabs net cleanly to
the wrapper's external ports.
"""

import jitx
from jitx.container import inline
from jitx.sample import SampleDesign

from rp2350_console_jitx.components.hdmi_a import HdmiA


class TestHdmiA(SampleDesign):
    @inline
    class circuit(jitx.Circuit):
        dut = HdmiA()


Design: type[TestHdmiA] = TestHdmiA
