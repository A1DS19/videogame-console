"""
XUNPU HDMI-001S — HDMI Type-A receptacle, 19-pin SMD right-angle board-edge.

LCSC: C720616.  Datasheet: docs/datasheets/HDMI-001S.pdf (single-sheet XunPu
manufacture drawing, "HDMI A TYPE 板上型").

Sourcing / footprint / 3D
-------------------------
Resolved from the JLCPCB parts DB by ``Part(mpn="HDMI-001S", manufacturer="XUNPU")``
(non-standard connector → DB-probe per the modeling rules). The DB part carries
the verified EasyEDA footprint AND a STEP 3D model
(3d-models/jitx-64d2337bb789d8dc4b95d06f.stp) automatically, so this module just
**wraps** it and re-exposes the 19 HDMI-A pins + 4 shell tabs under clean names.

Footprint cross-checked against the datasheet "RECOMMENDED P.C.B HOLE LAYOUT,
COMPONENT SIDE VIEW" (datasheet page 1, bottom-centre figure):
  - 19 SMD signal pads, single row, 0.50 mm pitch, 0.30 mm wide, spanning
    9.00 mm centre-to-centre  (DB: p[1..19] at x = +4.5 … -4.5, y = 5.1285)
  - 4 THT shell/mounting tabs at the corners, 14.50 mm apart horizontally and
    5.96 mm apart vertically  (DB: p[20..23] at x = ±7.25, y = 4.37 / -1.59)
  - Orientation: PIN 1 on the RIGHT, PIN 19 on the LEFT (datasheet bottom-left
    component-side view) — matches the DB pad x-coordinates.

Pinout (standard HDMI Type-A; datasheet pin numbering, DB port name in parens)
-----------------------------------------------------------------------------
   1  TMDS Data2+        (TMDS_Data_2p)       11  TMDS Clock Shield (TMDS_Clock_Shield)
   2  TMDS Data2 Shield  (TMDS_Data_2_Shield) 12  TMDS Clock-       (TMDS_Clockn)
   3  TMDS Data2-        (TMDS_Data_2n)        13  CEC              (CEC)
   4  TMDS Data1+        (TMDS_Data_1p)        14  Reserved / Utility (Reserved_N_C)
   5  TMDS Data1 Shield  (TMDS_Data_1_Shield) 15  DDC SCL          (SCL)
   6  TMDS Data1-        (TMDS_Data_1n)        16  DDC SDA          (SDA)
   7  TMDS Data0+        (TMDS_Data_0p)        17  DDC/CEC Ground   (DDC_CEC_Ground)
   8  TMDS Data0 Shield  (TMDS_Data_0_Shield) 18  +5 V Power       (P5V_Power)
   9  TMDS Data0-        (TMDS_Data_0n)        19  Hot Plug Detect  (Hot_Plug_Detect)
  10  TMDS Clock+        (TMDS_Clockp)
  tabs  4 shell/mounting tabs (GND0..GND3) → SHIELD[0..3]

The pin→port mapping above was verified against the DB landpattern map
(``jitx build --dump``): port TMDS_Data_2p → pad p[1] … Hot_Plug_Detect → p[19];
GND0→p[20] (top-left), GND1→p[21] (top-right), GND2→p[22] (bottom-left),
GND3→p[23] (bottom-right).
"""

import jitx
from jitx.circuit import Circuit
from jitx.net import Net, Port
from jitxlib.parts import Part, PartQuery


class HdmiA(Circuit):
    """HDMI Type-A SMD receptacle (XUNPU HDMI-001S, LCSC C720616).

    Wraps the DB-resolved ``Part`` and re-exposes the 19 HDMI-A pins plus the
    four shell/mounting tabs (SHIELD[0..3], all GND in the connector). The DB
    part supplies the footprint and the 3D model.
    """

    # --- TMDS channels (pins 1..12): each channel is +, shield, - ---
    TMDS_D2_P = Port()  # pin 1
    TMDS_D2_SH = Port()  # pin 2
    TMDS_D2_N = Port()  # pin 3
    TMDS_D1_P = Port()  # pin 4
    TMDS_D1_SH = Port()  # pin 5
    TMDS_D1_N = Port()  # pin 6
    TMDS_D0_P = Port()  # pin 7
    TMDS_D0_SH = Port()  # pin 8
    TMDS_D0_N = Port()  # pin 9
    TMDS_CLK_P = Port()  # pin 10
    TMDS_CLK_SH = Port()  # pin 11
    TMDS_CLK_N = Port()  # pin 12

    # --- Auxiliary / control (pins 13..19) ---
    CEC = Port()  # pin 13 — Consumer Electronics Control
    UTILITY = Port()  # pin 14 — Reserved (N.C. on HDMI <1.4) / Utility/HEAC+
    SCL = Port()  # pin 15 — DDC clock
    SDA = Port()  # pin 16 — DDC data
    GND = Port()  # pin 17 — DDC/CEC ground
    V5 = Port()  # pin 18 — +5 V power
    HPD = Port()  # pin 19 — Hot Plug Detect

    # --- Shell / mounting tabs (THT; all GND) ---
    SHIELD = [Port() for _ in range(4)]

    def __init__(self) -> None:
        # DB-resolved connector: footprint + 3D model come from the parts DB.
        self.conn = Part(PartQuery(), mpn="HDMI-001S", manufacturer="XUNPU")
        c = self.conn

        # One pass-through net per pin: external clean name <-> DB port name.
        self.net_d2p = Net()
        self.net_d2p += self.TMDS_D2_P + c.TMDS_Data_2p
        self.net_d2sh = Net()
        self.net_d2sh += self.TMDS_D2_SH + c.TMDS_Data_2_Shield
        self.net_d2n = Net()
        self.net_d2n += self.TMDS_D2_N + c.TMDS_Data_2n

        self.net_d1p = Net()
        self.net_d1p += self.TMDS_D1_P + c.TMDS_Data_1p
        self.net_d1sh = Net()
        self.net_d1sh += self.TMDS_D1_SH + c.TMDS_Data_1_Shield
        self.net_d1n = Net()
        self.net_d1n += self.TMDS_D1_N + c.TMDS_Data_1n

        self.net_d0p = Net()
        self.net_d0p += self.TMDS_D0_P + c.TMDS_Data_0p
        self.net_d0sh = Net()
        self.net_d0sh += self.TMDS_D0_SH + c.TMDS_Data_0_Shield
        self.net_d0n = Net()
        self.net_d0n += self.TMDS_D0_N + c.TMDS_Data_0n

        self.net_clkp = Net()
        self.net_clkp += self.TMDS_CLK_P + c.TMDS_Clockp
        self.net_clksh = Net()
        self.net_clksh += self.TMDS_CLK_SH + c.TMDS_Clock_Shield
        self.net_clkn = Net()
        self.net_clkn += self.TMDS_CLK_N + c.TMDS_Clockn

        self.net_cec = Net()
        self.net_cec += self.CEC + c.CEC
        self.net_util = Net()
        self.net_util += self.UTILITY + c.Reserved_N_C
        self.net_scl = Net()
        self.net_scl += self.SCL + c.SCL
        self.net_sda = Net()
        self.net_sda += self.SDA + c.SDA
        self.net_gnd = Net()
        self.net_gnd += self.GND + c.DDC_CEC_Ground
        self.net_v5 = Net()
        self.net_v5 += self.V5 + c.P5V_Power
        self.net_hpd = Net()
        self.net_hpd += self.HPD + c.Hot_Plug_Detect

        # Shell/mounting tabs: GND0..GND3 -> SHIELD[0..3].
        self.net_sh0 = Net()
        self.net_sh0 += self.SHIELD[0] + c.GND0
        self.net_sh1 = Net()
        self.net_sh1 += self.SHIELD[1] + c.GND1
        self.net_sh2 = Net()
        self.net_sh2 += self.SHIELD[2] + c.GND2
        self.net_sh3 = Net()
        self.net_sh3 += self.SHIELD[3] + c.GND3
