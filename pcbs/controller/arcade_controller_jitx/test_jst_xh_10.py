"""
Minimal test design for the JstXH10 component (J).

Instantiates a single JstXH10 in a SampleDesign circuit to verify
the component builds correctly (landpattern, symbol, PadMapping).
"""

import jitx
from jitx.container import inline
from jitx.sample import SampleDesign

from arcade_controller_jitx.components.jst_xh_10 import JstXH10


class TestJstXH10(SampleDesign):
    @inline
    class circuit(jitx.Circuit):
        dut = JstXH10()


Design: type[TestJstXH10] = TestJstXH10
