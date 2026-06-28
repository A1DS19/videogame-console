"""
Minimal test design for the JstPH2 component (J).

Instantiates a single JstPH2 in a SampleDesign circuit to verify the component
builds correctly (landpattern, symbol, PadMapping, 3D model).
"""

import jitx
from jitx.container import inline
from jitx.sample import SampleDesign

from rp2350_console_jitx.components.jst_ph_2 import JstPH2


class TestJstPH2(SampleDesign):
    @inline
    class circuit(jitx.Circuit):
        dut = JstPH2()


Design: type[TestJstPH2] = TestJstPH2
