import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import inspect_native_guard_fixture as target


class FakeDllHandle:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class NativeFixtureHelperTests(unittest.TestCase):
    def test_stale_child_outputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "case-stdout.bin").write_bytes(b"old")
            with self.assertRaisesRegex(RuntimeError, "stale"):
                target.run_child([sys.executable, "-c", "pass"], root, 1, "case")

    def test_child_nonzero_and_timeout_are_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            nonzero = target.run_child(
                [sys.executable, "-c", "raise SystemExit(7)"], root, 2, "nonzero")
            with self.assertRaisesRegex(RuntimeError, "version"):
                target.require_child_success(nonzero, "version")
            timeout = target.run_child(
                [sys.executable, "-c", "import time;time.sleep(5)"],
                root, 0.1, "timeout")
            with self.assertRaisesRegex(RuntimeError, "DRC"):
                target.require_child_success(timeout, "DRC")
            self.assertTrue(timeout["child_confirmed_exited"])

    def test_drc_missing_malformed_nonobject_and_missing_arrays(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "drc.json"
            with self.assertRaisesRegex(RuntimeError, "absent"):
                target.validate_drc_report(path)
            path.write_text("{", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                target.validate_drc_report(path)
            path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "not an object"):
                target.validate_drc_report(path)
            path.write_text('{"violations":[]}', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "missing array"):
                target.validate_drc_report(path)
            valid = {"violations": [], "unconnected_items": [], "schematic_parity": []}
            path.write_text(json.dumps(valid), encoding="utf-8")
            self.assertEqual(target.validate_drc_report(path), valid)

    def test_dll_handle_lives_through_readback_and_closes_on_success(self):
        handle = FakeDllHandle()
        with mock.patch.object(
            target, "read_native",
            side_effect=lambda pcb, path: self.assertFalse(handle.closed) or {"ok": True}
        ):
            result = target.native_readback(
                Path("K"), Path("fixture"), add_dll=lambda _: handle,
                importer=lambda _: object())
        self.assertEqual(result, {"ok": True})
        self.assertTrue(handle.closed)

    def test_dll_handle_closes_on_readback_failure(self):
        handle = FakeDllHandle()
        with mock.patch.object(target, "read_native", side_effect=RuntimeError("boom")):
            with self.assertRaisesRegex(RuntimeError, "boom"):
                target.native_readback(
                    Path("K"), Path("fixture"), add_dll=lambda _: handle,
                    importer=lambda _: object())
        self.assertTrue(handle.closed)


if __name__ == "__main__":
    unittest.main()
