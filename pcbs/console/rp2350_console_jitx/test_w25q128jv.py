"""
Minimal test design for the W25Q128JV component (U).

Instantiates a single W25Q128JV in a SampleDesign circuit to verify the
component builds correctly: the SOIC-8 208-mil landpattern, the BoxSymbol
with the SPI/QSPI signals on the left and VCC/GND on the columns, and the
PadMapping with the datasheet pin numbers (1=/CS .. 8=VCC).
"""

import jitx
from jitx.container import inline
from jitx.sample import SampleDesign

from rp2350_console_jitx.components.w25q128jv import W25Q128JV


class TestW25Q128JV(SampleDesign):
    @inline
    class circuit(jitx.Circuit):
        dut = W25Q128JV()


Design: type[TestW25Q128JV] = TestW25Q128JV
