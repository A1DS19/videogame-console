"""
Minimal test design for TYPEC31M12 USB-C connector component.

Instantiates the component in isolation to verify the landpattern,
symbol, and pad-mapping are valid.
"""

import jitx
from jitx.container import inline
from jitx.sample import SampleDesign

from rp2350_console_jitx.components.usbc import TYPEC31M12


class TestUSBC(SampleDesign):
    @inline
    class circuit(jitx.Circuit):
        j1 = TYPEC31M12()
