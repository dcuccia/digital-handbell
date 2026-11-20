"""HGP-shaped messages (Go Go HarmoniYo Handbell Gesture Protocol v0).

The handbell does not depend on HGP code. It emits the same message shapes
over its link (USB serial now, a radio later) so tools and a future host can
read them. Times are milliseconds in device time, formatted from integer
microseconds without float rounding. Unknown ``type`` values, such as
``select``, are ignored by HGP hosts.
"""

HGP_VERSION = 0
RAW_COLS = ("t", "ax", "ay", "az", "gx", "gy", "gz")


def ms_text(t_us):
    """Format integer microseconds as a millisecond decimal string."""
    t_us = int(t_us)
    sign = "-" if t_us < 0 else ""
    t_us = abs(t_us)
    return "%s%d.%03d" % (sign, t_us // 1000, t_us % 1000)


def _num(x, digits=3):
    if isinstance(x, int):
        return str(x)
    text = ("%." + str(digits) + "f") % x
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text if text not in ("", "-0") else "0"


def _str(s):
    out = []
    for ch in str(s):
        if ch == '"' or ch == "\\":
            out.append("\\" + ch)
        elif ord(ch) < 0x20:
            out.append("\\u%04x" % ord(ch))
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def to_json(value):
    """Minimal JSON encoder for message values (dict, list, str, numbers, bool, None)."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return _num(value)
    if isinstance(value, str):
        return _str(value)
    if isinstance(value, Raw):
        return value.text
    if isinstance(value, dict):
        return "{" + ",".join(_str(k) + ":" + to_json(value[k]) for k in value) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(to_json(v) for v in value) + "]"
    raise TypeError("cannot encode %r" % (value,))


class Raw:
    """Pre-formatted JSON text (used for exact millisecond times)."""

    def __init__(self, text):
        self.text = text


def gesture(seq, g, t_us, bell=None, sel_us=None, vel=None, det_us=None, src="motion"):
    msg = {"type": "gesture", "seq": seq, "g": g, "t": Raw(ms_text(t_us))}
    if bell is not None:
        msg["bell"] = bell
    if sel_us is not None:
        msg["sel"] = Raw(ms_text(sel_us))
    if vel is not None:
        msg["vel"] = round(vel, 3)
    if det_us is not None:
        msg["det"] = Raw(ms_text(det_us))
    msg["src"] = src
    return to_json(msg)


def hello(device_id, name, app, sensors, gestures, sound=True):
    return to_json(
        {
            "type": "hello",
            "v": HGP_VERSION,
            "deviceId": device_id,
            "kind": "bell",
            "name": name,
            "app": app,
            "sensors": sensors,
            "gestures": list(gestures),
            "sound": sound,
        }
    )


def select(bell, sel_us, index, count, locked):
    return to_json(
        {
            "type": "select",
            "bell": bell,
            "sel": Raw(ms_text(sel_us)),
            "index": index,
            "count": count,
            "locked": locked,
        }
    )


def status(fields):
    msg = {"type": "status"}
    for key in fields:
        msg[key] = fields[key]
    return to_json(msg)


def raw_batch(rows):
    """``rows`` are (t_us, ax, ay, az, gx, gy, gz) tuples."""
    parts = []
    for r in rows:
        parts.append(
            "[" + ms_text(r[0]) + "," + ",".join(_num(v, 3) for v in r[1:]) + "]"
        )
    return '{"type":"raw","off":0,"cols":' + to_json(list(RAW_COLS)) + ',"s":[' + ",".join(parts) + "]}"
