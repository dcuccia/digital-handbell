"""Hardware-independent instrument logic.

Rules for this package (enforced by tests/test_core_imports.py):

- Import only ``math`` and other ``handbell.core`` modules. No ``board``,
  ``time``, ``gc`` or audio modules: platforms supply time and I/O.
- Keep CircuitPython compatibility: no ``typing``, ``dataclasses``, ``enum``,
  ``abc`` or ``max(..., default=)``.
- Times are integer microseconds from an arbitrary monotonic origin.
  CircuitPython floats keep about 22 significant bits, so absolute
  millisecond floats would lose precision within about an hour.
"""
