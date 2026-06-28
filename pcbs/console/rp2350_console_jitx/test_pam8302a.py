"""
Minimal test design for the PAM8302A component (U).

Instantiates a single PAM8302A in a SampleDesign circuit to verify the
component builds correctly: the MSOP-8 SOP landpattern, the BoxSymbol with
SD/NC/IN+/IN- on the left and VO+/VO- on the right (VDD up, GND down), and the
PadMapping placing SD=1, NC=2, IN+=3, IN-=4, VO+=5, VDD=6, GND=7, VO-=8.
"""

import jitx
from jitx.container import inline
from jitx.sample import SampleDesign

from rp2350_console_jitx.components.pam8302a import PAM8302A


class TestPAM8302A(SampleDesign):
    @inline
    class circuit(jitx.Circuit):
        dut = PAM8302A()


Design: type[TestPAM8302A] = TestPAM8302A
