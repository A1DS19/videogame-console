"""
Minimal test design for the RP2350B component (U).

Instantiates a single RP2350B in a SampleDesign circuit to verify the component
builds: the QFN-80-EP landpattern (10×10 mm, 0.4 mm pitch), the BoxSymbol, and
the full 80-pad PadMapping (incl. the EP→GND thermal pad).
"""

import jitx
from jitx.container import inline
from jitx.sample import SampleDesign

from rp2350_console_jitx.components.rp2350b import RP2350B


class TestRP2350B(SampleDesign):
    @inline
    class circuit(jitx.Circuit):
        dut = RP2350B()


Design: type[TestRP2350B] = TestRP2350B
