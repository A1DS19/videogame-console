"""Physical layout for the arcade controller — board outline, signal area, floorplan.

The board IS the faceplate: the top side carries only the 8 THT buttons (a gamepad —
4-button D-pad + 4 action buttons); all SMD (16 resistors + 2 TVS) goes on the bottom;
the JST-XH connector sits on a board edge. ``main.py`` owns the netlist and calls
``floorplan()`` and shapes the GND pour from ``signal_area``.

Floorplan strategy (board IS the faceplate):
  - **8 tactile buttons on the TOP**, as a gamepad: a 4-button D-pad (cross, left
    cluster) + 4 action buttons (diamond, right cluster). Centers are >=18 mm apart so
    the Ø12.6 mm keycaps never collide; clusters are ~60 mm apart.
  - **All SMD on the BOTTOM** (16 resistors + 2 TVS). Each channel's two 0603s sit in
    the central clear zone of their button (between the THT holes at x=+-6.25) so the
    traces to the button pads stay short. Top buttons vs bottom SMD never collide
    (different sides), which is the whole point of the faceplate strategy.
  - **JST-XH connector on the bottom EDGE, Bottom side** (the only externally-mated part
    -> the perimeter; cable exits the back). The two TVS arrays sit hard against it so
    the ESD clamp is right at the port.

Mounting holes (4x M3 NPTH with keepouts) are added at the post-export KiCad stage where
the pcb-route `check_placement` R126 keepout gate validates them (they are mechanical,
net-less, and that gate only runs on the exported board).

All coordinates are in the design frame (mm), origin at board center, +y up.
"""

from jitx.board import Board
from jitx.layerindex import Side
from jitx.placement import Placement
from jitx.shapes.composites import rectangle

# Board envelope. Start ~120 x 70 mm (<=150 mm wide per the spec) with rounded corners;
# signal area inset 1.5 mm so the GND pour / routing / placement stays clear of the edge.
# Finalized at the floorplan task once cluster spacing + keycap clearance is dimensioned.
BOARD_WIDTH = 120.0
BOARD_HEIGHT = 70.0
BOARD_CORNER_RADIUS = 3.0
SIGNAL_INSET = 1.5


class ArcadeControllerBoard(Board):
    """~120 x 70 mm rounded-rectangle outline with an inset signal area.

    ``signal_area`` is the hole-free inset rectangle the top-level design fills with the
    GND pour, so copper never reaches the board edge.
    """

    shape = rectangle(BOARD_WIDTH, BOARD_HEIGHT, radius=BOARD_CORNER_RADIUS)
    signal_area = rectangle(
        BOARD_WIDTH - 2 * SIGNAL_INSET,
        BOARD_HEIGHT - 2 * SIGNAL_INSET,
        radius=max(BOARD_CORNER_RADIUS - SIGNAL_INSET, 0.5),
    )


# Gamepad button centers (mm). Index = BTN index per docs/interface-contract.md.
# Left cluster = D-pad cross (center ~x=-30); right cluster = action diamond (center ~x=+30).
# Neighbours are >=18 mm apart (keycap Ø12.6 clearance); the two clusters ~60 mm apart.
_BTN_XY = [
    (-30.0, 18.0),   # BTN0  D-pad Up
    (-30.0, -18.0),  # BTN1  D-pad Down
    (-48.0, 0.0),    # BTN2  D-pad Left
    (-12.0, 0.0),    # BTN3  D-pad Right
    (30.0, -18.0),   # BTN4  Action A
    (48.0, 0.0),     # BTN5  Action B
    (12.0, 0.0),     # BTN6  Action X
    (30.0, 18.0),    # BTN7  Action Y
]


def floorplan(circuit) -> None:
    """Place every component of ``circuit`` (an ``ArcadeControllerCircuit``).

    Called from the circuit's ``__init__`` after all components exist. Buttons go on the
    Top (the faceplate); every passive + TVS goes on the Bottom; the connector sits on the
    bottom edge. Placement requests live here (the JITX source = the layout authority).
    """
    place = circuit.place

    def at(inst, x, y, rot=0, side=Side.Top):
        place(inst, Placement((x, y), rotate=rot, on=side))

    # --- 8 tactile buttons on the TOP (the faceplate), gamepad arrangement. --------
    for i, (bx, by) in enumerate(_BTN_XY):
        at(circuit.sw[i], bx, by, 0, Side.Top)
        # This channel's two 0603s on the BOTTOM, in the button's central clear zone
        # (between the THT holes at x=+-6.25) so traces to the button pads stay short.
        at(circuit.rpu[i], bx - 2.5, by, 0, Side.Bottom)  # 10k pull-up
        at(circuit.rs[i], bx + 2.5, by, 0, Side.Bottom)  # 220 series

    # --- JST-XH connector on the bottom EDGE, Bottom side (cable exits the back). ---
    at(circuit.j1, 0.0, -31.0, 0, Side.Bottom)

    # --- Two TVS arrays on the BOTTOM, hard against the connector (ESD at the port). -
    at(circuit.d1, -10.0, -24.0, 0, Side.Bottom)  # protects BTN0..BTN3
    at(circuit.d2, 10.0, -24.0, 0, Side.Bottom)  # protects BTN4..BTN7
