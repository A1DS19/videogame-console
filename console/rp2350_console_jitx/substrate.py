"""4-layer substrate for the RP2350 console — JLCPCB JLC04161H_7628.

Phase 0 Task 0.3. The console uses JLCPCB's predefined 4-layer FR-4 stackup
(L1 signal · L2 solid GND · L3 power · L4 signal) with its controlled-impedance
routing structures:
  - DRS_100 — 100 Ω differential, for the 4 HDMI TMDS pairs (attached in Phase 3).
  - DRS_90  — 90 Ω differential (available if USB needs it).
  - RS_50   — 50 Ω single-ended.
The real top-level design (main.py, Phase 2) sets ``substrate = JLC04161H_7628()``
and attaches DRS_100 to the TMDS nets via
``design_constraint(...).routing_structure(JLC04161H_7628.DRS_100, ref_net=GND)``.
Matches ``wireless_lighting_jitx`` (the proven 4-layer + pcb-route flow).

This module also carries a trivial ``SubstrateSmoke`` design so the substrate is
proven to build before component modeling (the Phase 0 → 1 gate).
Build: rp2350_console_jitx.substrate.SubstrateSmoke
"""

import jitx
from jitx import Net
from jitx.circuit import Circuit
from jitx.container import inline
from jitx.design import Design
from jitx.shapes.composites import rectangle
from jitxlib.jlcpcb import JLC04161H_7628
from jitxlib.parts import Resistor

# Starting board envelope (finalized at the Phase 3 floorplan). Origin-centred.
_SMOKE_W = 80.0
_SMOKE_H = 60.0


class _SmokeBoard(jitx.Board):
    """Throwaway rectangular outline just to exercise the substrate build."""

    shape = rectangle(_SMOKE_W, _SMOKE_H, radius=2.0)
    signal_area = rectangle(_SMOKE_W - 3.0, _SMOKE_H - 3.0, radius=0.5)


class _SmokeCircuit(Circuit):
    """One pull-up resistor across the rails — minimal buildable netlist."""

    def __init__(self):
        self.V3V3 = Net(name="V3V3")
        self.GND = Net(name="GND")
        self.r = Resistor(resistance=10e3, case="0603")
        self.r.insert(self.V3V3, self.GND)


class SubstrateSmoke(Design):
    """Trivial design on JLC04161H_7628 — the Phase 0 substrate gate."""

    substrate = JLC04161H_7628()
    board = _SmokeBoard()

    @inline
    class circuit(_SmokeCircuit):
        pass
