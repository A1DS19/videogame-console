"""
Minimal test design for the TactileButton component (SW).

Instantiates a single TactileButton in a SampleDesign circuit to verify the
component builds correctly: the custom 4-pad through-hole landpattern, the
A/B switch symbol, and the same-column-common PadMapping (A = both left pads,
B = both right pads).
"""

import jitx
from jitx.container import inline
from jitx.sample import SampleDesign

from arcade_controller_jitx.components.tactile_button import TactileButton


class TestTactileButton(SampleDesign):
    @inline
    class circuit(jitx.Circuit):
        dut = TactileButton()


Design: type[TestTactileButton] = TestTactileButton
