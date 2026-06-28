"""
Minimal test design for the AotaB201610S3R3 component (L).

Instantiates a single AOTA-B201610S3R3-101-T inductor in a SampleDesign to
verify the component builds: the 2-pad SMD landpattern (1.00 x 1.60 mm pads at
2.00 mm pitch), the InductorSymbol with SymbolMapping, and the PadMapping with
P1 = polarity-dot "+" terminal, P2 = "-" terminal.
"""

import jitx
from jitx.container import inline
from jitx.sample import SampleDesign

from rp2350_console_jitx.components.aota_b201610_3r3 import AotaB201610S3R3


class TestAotaB201610S3R3(SampleDesign):
    @inline
    class circuit(jitx.Circuit):
        dut = AotaB201610S3R3()


Design: type[TestAotaB201610S3R3] = TestAotaB201610S3R3
