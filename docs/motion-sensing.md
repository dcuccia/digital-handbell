# Motion sensing: strike and chest-stop/rest

Decision updated 2026-09-07: **the owner approved LSM6DSOX**, and it is integrated
in the [separate handbell schematic draft](../hardware/handbell/README.md),
using Adafruit PID 4438 source material and ST's fixed Mode 1 wiring.
LSM6DS3TR-C / PID 4503 is the economical runner-up, with sourcing and hardware
license-scope questions to resolve. Keep the stock LIS3DH as a comparison sensor
on the bench. The imported 5768 reference has not been modified.

This is a component/design direction, **not measured handbell recognition
performance or a frozen assembled BOM**.

## Is LIS3DH enough?

For a basic natural-strike prototype, plausibly yes: acceleration history,
hysteresis, and retrigger handling can recognize a ringing stroke. A removed
clapper means the stroke may not contain a physical impact, so a simple
"tap happened, play sound" implementation is not necessarily the right model.

For distinguishing **stroke, return, chest-stop, and rest** across different
grips and orientations, a gyro is worth evaluating now. An accelerometer
combines gravity with motion-induced acceleration, including tangential and
centripetal terms when mounted away from the rotation center. During a swing,
one acceleration vector cannot uniquely separate tilt from translation.

A gyro adds angular velocity. It helps identify rotation, reversal, and settling
and supports short-term relative orientation. It does not provide drift-free
absolute orientation, chest-relative position, or player intent.

**Neither sensor directly detects chest contact.** A soft chest stop may have
no sharp impulse; contact with a hand or table may resemble one. A useful
interaction can infer "return toward a rest pose and settle while a note is
sounding," but distinguishing actual chest contact from a similar motion may
eventually require an explicit contact input or a broader, documented
"hold still to damp" gesture.

Do not add a magnetometer initially. Compass heading is unnecessary for this
relative gesture, while the speaker magnet and any ferromagnetic shell or
fasteners complicate magnetic measurements.

Background: Adafruit's [acceleration/gravity explanation](https://learn.adafruit.com/sensors-in-makecode/accelerometer)
and [gyro calibration guide](https://learn.adafruit.com/adafruit-sensorlab-gyroscope-calibration).

## Candidate comparison

| Candidate | What it provides | Why / why not |
|---|---|---|
| LIS3DH, stock on 5768 | Three acceleration axes; no gyro | Already available for comparison, low sensor current, sufficient for initial stroke experiments; less information for ambiguous return/damping motions |
| **LSM6DSOX, Adafruit 4438** | Acceleration plus angular rate; 2.5 x 3 x 0.83 mm LGA-14L; +/-2/4/8/16 g and up to +/-2000 degrees/s gyro ranges | Primary upgrade: documented board, straightforward raw I2C driver, clear CC BY-SA hardware notice, plausible sensor-only budget premium |
| LSM6DS3TR-C, Adafruit 4503 | Same six measurement axes and similar ranges/package envelope | Lower retrieved component price; clarify conflicting hardware license notices and distributor/manufacturer lifecycle descriptions before production selection |

All permit regulated 3.3 V operation. **Neither is a drop-in replacement for
LIS3DH:** package, pin mapping, unused-pin instructions, address straps,
decoupling, and driver differ. Raw 1S LiPo can exceed the sensors' supply limits.
Review exact VDD/VDDIO requirements and MPN/package suffix.

ST datasheets:
[LIS3DH](https://www.st.com/resource/en/datasheet/lis3dh.pdf),
[LSM6DS3TR-C](https://www.st.com/resource/en/datasheet/lsm6ds3tr-c.pdf),
[LSM6DSOX](https://www.st.com/resource/en/datasheet/lsm6dsox.pdf).
Published sensor currents depend on mode, ODR, and supply; do not substitute
them for measured whole-instrument runtime.

## Keep the software path simple

Both upgrade candidates use the same MIT-licensed
[Adafruit CircuitPython LSM6DS library](https://github.com/adafruit/Adafruit_CircuitPython_LSM6DS/tree/cdfc14a687a138aa0f2c6abab061bfc1bfafa561).
The inspected classes are:

| Sensor | Class | Units |
|---|---|---|
| LSM6DSOX | `adafruit_lsm6ds.lsm6dsox.LSM6DSOX` | `.acceleration`: m/s^2; `.gyro`: **radians/second** |
| LSM6DS3TR-C | `adafruit_lsm6ds.lsm6ds3trc.LSM6DS3TRC` | Same |
| LIS3DH | `adafruit_lis3dh.LIS3DH_I2C` | `.acceleration`: m/s^2 |

Use ordinary I2C polling and explicit range/ODR settings first. Hardware FIFO,
interrupt, and SPI features do not automatically imply equivalent convenient
APIs in this driver. The inspected library does not expose a general FIFO
streaming interface, full interrupt/wake configuration, or automatic sensor
fusion.

LSM6DSOX's machine-learning core is optional headroom, not a prerequisite.
The driver does implement UCF-based `load_mlc()` / `read_mlc_output()`, but an
externally prepared configuration and a relevant model are still needed.
Start with a transparent temporal state machine, not a training pipeline.

Documentation traps discovered during source inspection:

- Older SOX guide text shows obsolete construction and degrees/second.
  The pinned current driver uses the subclass module and returns radians/second.
- The inspected DS3TR-C simple example uses XIAO-specific `IMU_PWR` and bus
  aliases, not the Prop-Maker Feather's wiring.
- LIS3DH's convenient `shake()` samples with sleeps over a default roughly
  100 ms window; do not assume it is a low-latency instrument trigger.
- **Bring-up gate:** the pinned LSM6DS base class defines `_i3c_disable` at
  CTRL9_XL bit 1, then redefines it at bit 0. The SOX constructor uses the
  redefined descriptor. ST specifies bit 1 for I3C disable and reserved bit 0
  clear. Verify a corrected driver revision or narrowly reviewed initialization
  before using this snapshot; do not merely set another bit while leaving the
  reserved bit set.

Exact defect evidence:
[base driver lines 202-208](https://github.com/adafruit/Adafruit_CircuitPython_LSM6DS/blob/cdfc14a687a138aa0f2c6abab061bfc1bfafa561/adafruit_lsm6ds/__init__.py#L202-L208),
[SOX constructor lines 54-58](https://github.com/adafruit/Adafruit_CircuitPython_LSM6DS/blob/cdfc14a687a138aa0f2c6abab061bfc1bfafa561/adafruit_lsm6ds/lsm6dsox.py#L54-L58),
ST DS12814 Rev 3 p.65 and the
[ST register definition](https://github.com/STMicroelectronics/lsm6dsox-pid/blob/9570c27f142448b9e9d83bc9b746a5851c0ee785/lsm6dsox_reg.h#L541-L560).
Tracked under E06 as [issue #13](https://github.com/dcuccia/digital-handbell/issues/13).
Required register outcome: bit 1 set, bit 0 clear, other bits preserved.
No driver code is vendored or patched here, and no I2C failure has been measured
on a physical bell. Keep hub/pass-through/OIS/DEN disabled for the draft's
grounded SDx/SCx and NC auxiliary outputs.

See [LSM6DS driver source](https://github.com/adafruit/Adafruit_CircuitPython_LSM6DS/blob/cdfc14a687a138aa0f2c6abab061bfc1bfafa561/adafruit_lsm6ds/__init__.py)
and [LIS3DH source](https://github.com/adafruit/Adafruit_CircuitPython_LIS3DH/blob/cd40b482a098a62ecce1b4c62a1f1930be984e16/adafruit_lis3dh.py).

## Inexpensive comparison on the existing Feather

Connect a 4438 breakout to 5768's STEMMA QT connector: 3.3 V, GND, SDA/GPIO2,
and SCL/GPIO3. The onboard LIS3DH uses **0x18**; the external IMU defaults to
**0x6A**, optionally 0x6B, so both can coexist without removing the stock sensor.

QT carries no interrupt line. If needed, wire IMU INT1 to a separate unused
GPIO; do not share the onboard LIS3DH's GPIO22 interrupt indiscriminately.
For the derivative, retain an INT1 connection and provision for INT2. Account
for the parallel I2C pullups on the host and breakout.

Guides: [4438](https://learn.adafruit.com/lsm6dsox-and-ism330dhc-6-dof-imu),
[4503](https://learn.adafruit.com/adafruit-lsm6ds3tr-c-6-dof-accel-gyro-imu),
[5768 pinouts](https://learn.adafruit.com/adafruit-rp2040-prop-maker-feather/pinouts).
No breakout or other parts have been ordered.

## Proposed non-ML state machine

1. **Ready/rest:** estimate gyro bias and gravity direction only during
   sustained low motion; use hysteresis to rearm.
2. **Stroke candidate:** detect a coherent excursion using acceleration and
   angular-rate history, with short-term relative orientation where useful.
3. **Strike/sounding:** trigger at a chosen trajectory feature and continue
   sensing while audio plays. Suppress duplicates without preventing deliberate
   repeated strokes.
4. **Damp candidate:** combine recent sounding/stroke context, the return
   trajectory, relative pose, and settling. A tap is supporting evidence, not a
   requirement or proof.
5. **Damped/rest:** confirm the selected low-motion hold and fade the existing
   audio tails; require departure/rearming for the next strike.

Thresholds, sampling cadence, and dwell times remain experimental. Do not delay
every strike behind a long classification window or block sensing until a note
finishes.

Compare gyro-enabled and acceleration-only decisions on the same traces:
soft/tapped chest stops, hovering near the chest, hand/table contact, pickup,
set-down, walking, rapid strokes, different grips/orientations, and loud
speaker-induced vibration. Measure false/missed strikes, false damping,
latency/jitter, saturation, and current. No measured recognition rates exist yet.

## Cost and assembly implications

Retrieved LCSC primary-stock listings on 2026-09-07, USD per **bare chip**:

| Exact MPN / catalog code | 10+ | 100+ |
|---|---:|---:|
| [LIS3DHTR / C15134](https://www.lcsc.com/product-detail/C15134.html) | $1.6439 | $1.3302 |
| [LSM6DS3TR-C / C967633](https://www.lcsc.com/product-detail/C967633.html) | $1.3275 | $1.0554 |
| [LSM6DSOXTR / C481766](https://www.lcsc.com/product-detail/C481766.html) | $3.3186 | $2.7205 |

SOX's sensor-line premium in those listings is approximately **$1.67 at ten**
or **$1.39 at 100**. That fits the owner's stated latitude through this sourcing
channel, but **does not establish the final assembled-BOM delta**. Authorized
distributor prices differed, and all stock/pricing must be requoted.

The inspected JLC listings for [C481766](https://jlcpcb.com/partdetail/C481766)
and [C967633](https://jlcpcb.com/partdetail/STMicroelectronics-LSM6DS3TRC/C967633)
marked both candidates Extended, **Standard-only assembly with required X-ray**.
Confirm the complete job: do not assume Economic assembly merely because
components occupy one face. This may already be constrained by other BOM
parts; it is not automatically an incremental charge attributable only to the
sensor upgrade.

For DS3TR-C, [ST labels the part Active](https://www.st.com/en/mems-and-sensors/lsm6ds3tr-c.html)
while the inspected Mouser listing described EOL/restricted availability.
Manufacturer discontinuation is not established; resolve the discrepancy
before a production choice.

## Provenance and decision gate

SOX hardware source:
[Adafruit-LSM6DSOX-PCB](https://github.com/adafruit/Adafruit-LSM6DSOX-PCB/tree/c05abef4675b0380fbf3d23171615a2f1ac0b130),
commit `c05abef4675b0380fbf3d23171615a2f1ac0b130`, EAGLE
`Adafruit_LSM6DSOX.sch` / `.brd`, CC BY-SA 3.0.

DS3TR-C source:
[Adafruit-LSM6DS3TR-C-PCB](https://github.com/adafruit/Adafruit-LSM6DS3TR-C-PCB/tree/9bf02b7214d35f2699bfd24737865511e4f9f114),
commit `9bf02b7214d35f2699bfd24737865511e4f9f114`, EAGLE
`Adafruit_LSM6DS3.sch` / `.brd`. README/`license.txt` specify CC BY-SA 3.0,
but a separate `LICENSE` contains MIT. Preserve all notices and clarify scope
before distributing an adaptation; a GitHub badge is not sufficient.

The [4438 hardware reference](../hardware/reference/adafruit-4438/README.md) is
now vendored with full notices; the software and DS3TR-C hardware are not.
The derivative uses the imported SOX symbol/footprint with reviewed Mode 1
connections, not a pin-compatible replacement. Before freezing the design,
require the comparison dataset, full electrical review and exact assembly
quote/availability. E03/E06 own the experiments and driver bring-up; E04 owns
the schematic and its remaining decisions.
