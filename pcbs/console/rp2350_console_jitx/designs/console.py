"""Top-level RP2350 console design + SI constraints (TOP_LEVEL_PATH = designs/).

The netlist lives in ``..main.ConsoleCircuit``; this module owns the top-level
``Design`` (4-layer JLC04161H_7628 substrate + board outline) and the SI
constraints that, per the project convention (grep_gates), must live under
``designs/``: the 4 HDMI TMDS pairs are constrained to the JLC04161H_7628 100 Ohm
differential routing structure (DRS_100), GND-referenced, intra-pair skew-matched
(~0 +/- 1 ps) and kept short (insertion-loss cap).

Build: rp2350_console_jitx.designs.console.ConsoleBoard
"""

from jitx.container import inline
from jitx.design import Design
from jitx.si import ConstrainDiffPair, ReferencePlanes
from jitx.toleranced import Toleranced
from jitxlib.jlcpcb import JLC04161H_7628

from ..main import ConsoleCircuit
from ..placement import ConsoleBoard as _ConsoleBoard
from ..placement import floorplan


class ConsoleBoard(Design):
    """Top-level RP2350 console design.

    4-layer JLCPCB ``JLC04161H_7628`` (L1 signal / L2 GND / L3 power / L4 signal).
    The 100 Ohm differential routing structure (``JLC04161H_7628.DRS_100``) is
    attached to the 4 TMDS pairs below. Placement + the 4-layer GND/V3V3 pours
    live in ``..placement.floorplan`` (the 72 x 66 mm board + 4x M3 NPTH holes).
    """

    substrate = JLC04161H_7628()
    board = _ConsoleBoard()

    @inline
    class circuit(ConsoleCircuit):
        def __init__(self) -> None:
            super().__init__()  # build the whole netlist (incl. self.tmds_topos)
            # Place every component + pour the 4-layer GND/V3V3 planes.
            floorplan(self)
            # TMDS 100 Ohm differential SI constraints — must live under designs/.
            with ReferencePlanes(self.GND):
                self.tmds_constraint = (
                    ConstrainDiffPair(self.tmds_topos)
                    .timing_difference(Toleranced(0.0, 1e-12))
                    .insertion_loss(3.0)
                    .structure(JLC04161H_7628.DRS_100)
                )
