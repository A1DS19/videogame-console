"""arcade_controller_jitx — top-level design (ArcadeController).

A wired 8-button tactile gamepad PCB where the board IS the faceplate. Eight 12x12 mm
through-hole tactile buttons (SW1-SW8) return active-low switch signals over a keyed,
detachable JST-XH 1x10 tether to an out-of-repo 3.3 V RP2040 "console". The board
carries controller-end pull-ups, per-line series resistors, and two 4-channel TVS
arrays at the connector. It is NOT "fully passive" -- that was consciously dropped for
ESD robustness.

The console interface is FROZEN in ``docs/interface-contract.md`` (the single source of
truth both repos cite) and the design is specified in
``docs/specs/2026-06-24-arcade-controller-design.md``.

Net summary:
  - Power : V3V3 arrives from the console on connector pin 10 (J1.V3V3) and feeds the 8
            pull-ups + both TVS VCC pins. GND (J1.GND, pin 9) is the return + shield
            drain (bonded single-point at the console end).
  - Channel i (i = 0..7), per the spec:
      V3V3 --[Rpu_i 10k]-- BTNi_INT --[SWi]-- GND          (switch-to-GND, pull-up)
      BTNi_INT --[Rs_i 220]-- BTNi_OUT --+-- J1.BTNi       (to the cable/console)
                                         +-- TVS ch i      (clamp at the connector)
    Idle = HIGH (~3V3 through 10k+220); pressed = LOW (~71 mV). Active-low.
  - ESD   : two SRV05-4A arrays -- D1 protects BTN0..BTN3 (IO1..IO4), D2 protects
            BTN4..BTN7 (IO1..IO4). Each VCC -> V3V3, GND -> GND. (RCLAMP3328P 8-ch was
            the ideal part but is absent from the JITX parts DB -- see docs/sourcing.md.)

Substrate: the framework default ``SampleSubstrate`` (2-layer FR-4, JLCPCB-class fab
rules) matches the spec's "JLCPCB 2-layer" target; the bottom copper is a GND plane.

Debounce is owned by the console firmware (no RC on the controller).
"""

import jitx
from jitx import Net, Pour
from jitx.circuit import Circuit
from jitx.container import inline
from jitx.sample import SampleDesign
from jitxlib.parts import Resistor
from jitxlib.symbols.net_symbols import GroundSymbol, PowerSymbol

from .placement import ArcadeControllerBoard, floorplan

from .components.jst_xh_10 import JstXH10
from .components.srv05_4a import Srv05_4A
from .components.tactile_button import TactileButton


class ArcadeControllerCircuit(Circuit):
    """The whole arcade controller: 8 button channels + connector + ESD, one composition.

    Wiring is grouped by concern; the 8 identical channels are built in a loop (DRY) and
    every net expression / passive is kept in a list attribute so the structural walk
    traverses it.
    """

    def __init__(self):
        # =================================================================
        # Power-rail nets (top-level symbols are legal here).
        # =================================================================
        self.GND = Net(name="GND", symbol=GroundSymbol())
        self.V3V3 = Net(name="V3V3", symbol=PowerSymbol())  # 3.3 V from the console (J1 pin 10)

        # =================================================================
        # Components: connector, two 4-ch TVS arrays, eight tactile buttons.
        # =================================================================
        self.j1 = JstXH10()  # JST-XH 1x10 tether connector
        self.d1 = Srv05_4A()  # TVS array -> BTN0..BTN3
        self.d2 = Srv05_4A()  # TVS array -> BTN4..BTN7
        self.sw = [TactileButton() for _ in range(8)]  # SW1..SW8

        # =================================================================
        # Connector power pins: GND (pin 9), V3V3 (pin 10).
        # =================================================================
        self.connector_power_nets = [
            self.GND + self.j1.GND,
            self.V3V3 + self.j1.V3V3,
        ]

        # =================================================================
        # TVS power: each array's VCC -> V3V3 rail, GND -> GND.
        # =================================================================
        self.tvs_power_nets = [
            self.V3V3 + self.d1.VCC + self.d2.VCC,
            self.GND + self.d1.GND + self.d2.GND,
        ]

        # =================================================================
        # Eight button channels (DRY). Each TVS handles four lines, so the
        # i-th channel's clamp is IO((i % 4) + 1) on D1 (i<4) or D2 (i>=4).
        # =================================================================
        self.btn_int = [Net(name=f"BTN{i}_INT") for i in range(8)]
        self.btn_out = [Net(name=f"BTN{i}_OUT") for i in range(8)]
        self.rpu = []  # 10 k pull-ups (controller-end, to V3V3)
        self.rs = []  # 220 ohm series resistors (ESD/EOS limit)
        self.channel_nets = []  # switch + TVS + connector wiring per channel

        for i in range(8):
            intn = self.btn_int[i]
            outn = self.btn_out[i]

            # 10 k pull-up: V3V3 -> BTNi_INT.
            rpu = Resistor(resistance=10e3, case="0603")
            rpu.insert(self.V3V3, intn)
            self.rpu.append(rpu)

            # Switch SWi: terminal A on BTNi_INT, terminal B on GND. Pressing bridges
            # A<->B, pulling BTNi_INT to GND (active-low).
            self.channel_nets.append(intn + self.sw[i].A)
            self.channel_nets.append(self.GND + self.sw[i].B)

            # 220 ohm series: BTNi_INT -> BTNi_OUT. Pinned to the Bourns CR0603-JW
            # series (same family as the 10k pull-ups) so it resolves to a DB part
            # that carries a 3D model — the unpinned 220 ohm optimizer pick had none,
            # leaving its footprint without a STEP in the board export. See
            # docs/sourcing.md.
            rs = Resistor(resistance=220, case="0603", mpn="CR0603-JW-221ELF")
            rs.insert(intn, outn)
            self.rs.append(rs)

            # ESD clamp on BTNi_OUT (at the connector): D1.IOx for i<4, else D2.IOx.
            tvs = self.d1 if i < 4 else self.d2
            io_port = getattr(tvs, f"IO{(i % 4) + 1}")
            self.channel_nets.append(outn + io_port)

            # Connector signal pin BTNi -> BTNi_OUT (to the cable / console).
            self.channel_nets.append(outn + getattr(self.j1, f"BTN{i}"))

        # =================================================================
        # Physical layout: bottom-layer GND plane + the floorplan (placement.py).
        # =================================================================
        # GND pour on the bottom copper (layer 1 of the 2-layer stackup), shaped to the
        # board's inset signal_area so copper never reaches the board edge.
        self.GND += Pour(ArcadeControllerBoard.signal_area, layer=1)

        # Place every component (real gamepad floorplan authored in the placement task).
        floorplan(self)


class ArcadeController(SampleDesign):
    """Top-level arcade-controller design.

    Inherits ``SampleSubstrate`` (2-layer FR-4, JLCPCB-class fab rules) from
    ``SampleDesign`` and overrides the board with the real outline
    (``ArcadeControllerBoard``); supplies the real circuit + floorplan.
    """

    board = ArcadeControllerBoard()

    @inline
    class circuit(ArcadeControllerCircuit):
        pass
