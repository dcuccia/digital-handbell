"""Single-button input grammar.

Turns debounced press/release edges into higher-level events:

``down``       press edge (immediate; use for latency-critical actions such as damp)
``up``         release edge
``click``      short press; delayed by ``double_ms`` only when a double is mapped
``double``     two short presses within ``double_ms``
``long``       released after ``long_ms`` and before ``very_long_ms``
``long_hint``  emitted once while held past ``long_ms`` (feedback only)
``very_long``  emitted while still held at ``very_long_ms``; the release is then ignored
"""

EVENTS = ("down", "up", "click", "double", "long", "long_hint", "very_long")

DEFAULT_TIMING = {"double_ms": 300, "long_ms": 800, "very_long_ms": 5000}


class ButtonGrammar:
    def __init__(self, double_ms=300, long_ms=800, very_long_ms=5000):
        if not 0 < double_ms < long_ms < very_long_ms:
            raise ValueError("button timing must satisfy 0 < double_ms < long_ms < very_long_ms")
        self._double_us = int(double_ms * 1000)
        self._long_us = int(long_ms * 1000)
        self._very_long_us = int(very_long_ms * 1000)
        self.double_enabled = True
        self.reset()

    def reset(self):
        self._pressed = False
        self._down_t = 0
        self._consumed = False
        self._release_consumed = False
        self._hinted = False
        self._pending_click_t = None

    @property
    def pressed(self):
        return self._pressed

    def consume_release(self):
        """The press already acted (for example ``down`` -> damp).

        Its release then yields only ``up`` (no click/double/long), and any
        pending click is dropped. ``very_long`` still fires while held, so a
        mode escape mapped to it keeps working.
        """
        self._release_consumed = True
        self._pending_click_t = None

    def press(self, t):
        out = []
        if self._pressed:
            return out
        self._pressed = True
        self._down_t = t
        self._consumed = False
        self._release_consumed = False
        self._hinted = False
        out.append("down")
        return out

    def release(self, t):
        out = []
        if not self._pressed:
            return out
        self._pressed = False
        out.append("up")
        if self._consumed or self._release_consumed:
            return out
        held = t - self._down_t
        if held >= self._long_us:
            out.append("long")
            return out
        if not self.double_enabled:
            self._pending_click_t = None
            out.append("click")
            return out
        if self._pending_click_t is not None and self._down_t - self._pending_click_t <= self._double_us:
            self._pending_click_t = None
            out.append("double")
            return out
        self._pending_click_t = t
        return out

    def tick(self, now):
        out = []
        if self._pressed and not self._consumed:
            held = now - self._down_t
            if held >= self._very_long_us:
                self._consumed = True
                self._pending_click_t = None
                out.append("very_long")
            elif held >= self._long_us and not self._hinted:
                self._hinted = True
                out.append("long_hint")
        if self._pending_click_t is not None and not self._pressed and now - self._pending_click_t > self._double_us:
            self._pending_click_t = None
            out.append("click")
        return out
