"""
Minimal test design for the Tpd8s009 component (D).

Instantiates a single Tpd8s009 in a SampleDesign circuit to verify the
component builds: the hand-built R-PDSO-N15 (SON-15) landpattern, the
BoxSymbol (8 TMDS channels left, VCC/NC right, 4x GND down), and the
PadMapping placing the TMDS channels on pins 1/3/4/6/7/9/10/12, GND on
pins 2/5/8/11, VCC on pins 13/15, and N.C. on pin 14.
"""

import jitx
from jitx.container import inline
from jitx.sample import SampleDesign

from rp2350_console_jitx.components.tpd8s009 import Tpd8s009


class TestTpd8s009(SampleDesign):
    @inline
    class circuit(jitx.Circuit):
        dut = Tpd8s009()


Design: type[TestTpd8s009] = TestTpd8s009
