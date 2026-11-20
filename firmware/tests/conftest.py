import sys
from pathlib import Path

FIRMWARE = Path(__file__).resolve().parents[1]
# Append, not prepend: src/code.py and scripts/test.py would shadow the stdlib
# ``code`` (used by pdb) and ``test`` modules.
for p in (FIRMWARE / "src", FIRMWARE / "scripts", FIRMWARE / "tests"):
    if str(p) not in sys.path:
        sys.path.append(str(p))
