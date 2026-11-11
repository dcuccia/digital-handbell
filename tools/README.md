# Engineering tools

[Project home](../README.md) · [Engineering workflow](../docs/agent-first-pcb-workflow.md) · [Agent policy](../AGENTS.md)

This directory contains Python/PowerShell utilities and source-specific
experiments, not a general-purpose PCB router or a one-command product build.
Many builders default to historical output locations. Read their help and
the linked procedure, and use a scratch output directory before executing.

| Task | Entry point / required context |
|---|---|
| Build/verify quote data | [build_quote_package.py](build_quote_package.py); [quote recipe](../hardware/handbell/quote-prep/2026-11-09-six-layer/README.md#reproduce-and-re-verify) |
| Review routing result invariants | [check_routing_result.py](check_routing_result.py); [routing tooling](../docs/routing-tooling.md) and the exact trial contract |
| Inspect original schematic adaptation | [check_handbell.py](check_handbell.py); [0.2 procedure](../hardware/handbell/README.md#reproduce-exports-and-checks), not a six-layer release check |
| Printed-bell CAD generation | [build_printed_bell.py](build_printed_bell.py), [check_printed_bell.py](check_printed_bell.py); [study instructions](../mechanical/studies/2026-09-13-printed-bell/README.md) |
| Earlier fit models | `build_mechanical.py`, `build_integrated_cartridge.py`, `build_t8_cartridge.py`; use each study's own README |
| Router experiments | [Quilter playbook](../docs/quilter-playbook.md), [November ledger](../docs/multilayer-gate-a-2026-11.md); paid runs and new uploads need separate approval |

For a change to the static quote builder, the existing focused test command
is:

```powershell
python -B -m unittest discover -s tools -p "test_build_quote_package.py"
```

Use the smallest existing check relevant to your change. A passing unit
test, native load or DRC run establishes only its stated scope. Native
KiCad/FreeCAD work needs the repository's bounded execution and source
preservation rules; do not run every experimental helper as a test suite.
