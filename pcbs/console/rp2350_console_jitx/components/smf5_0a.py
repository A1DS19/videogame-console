"""
Littelfuse/onsemi SMF5.0A — 5.0 V unidirectional TVS / ESD clamp, SOD-123FL.

LCSC C2759874 (as-built; mpn-resolved, so any JEDEC-equivalent SMF5.0A/SOD-123FL
reel is acceptable).  Datasheet: docs/datasheets/SMF5.0A.pdf.

Sourcing / footprint / 3D
-------------------------
``Part(mpn="SMF5.0A")`` resolves in the JITX/JLCPCB parts DB (verified by
build-probe), carrying the verified SOD-123FL footprint and a 3D model. This
module therefore **wraps** the DB part (like ``hdmi_a.py``) and re-exposes the
two terminals under clean names so the top-level netlist reads cleanly:

  A  — anode   (DB port ``A``)
  K  — cathode (DB port ``C``)

Orientation (datasheet "Electrical Characteristics", unidirectional device)
---------------------------------------------------------------------------
The SMF5.0A is **unidirectional**: 5.0 V working stand-off, ~6.4 V breakdown.
To protect a *positive* rail it must sit reverse-biased in normal operation —
i.e. **cathode (K) → the protected positive rail (VBUS, +5 V), anode (A) → GND**.
Wired the other way (anode on the +5 V rail) it is forward-biased and conducts
at ~0.7 V, shorting the rail. The board wires K→VBUS, A→GND accordingly.
"""

import jitx  # noqa: F401  (kept for parity with the other component modules)
from jitx.circuit import Circuit
from jitx.net import Net, Port
from jitxlib.parts import Part, PartQuery


class Smf5_0a(Circuit):
    """SMF5.0A 5 V unidirectional TVS (SOD-123FL, DB-resolved). A=anode, K=cathode."""

    A = Port()  # anode   -> GND  (for positive-rail protection)
    K = Port()  # cathode -> +rail (VBUS)

    def __init__(self) -> None:
        self.diode = Part(PartQuery(), mpn="SMF5.0A")
        # Pass-through nets: clean external name <-> DB port name.
        self.net_a = Net()
        self.net_a += self.A + self.diode.A
        self.net_k = Net()
        self.net_k += self.K + self.diode.C
