import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TOOL = Path(__file__).with_name("supervise_process.py")


class SuperviseProcessTests(unittest.TestCase):
    def run_case(self, limit, code):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            receipt = root / "receipt.json"
            command = [
                sys.executable, str(TOOL),
                "--receipt", str(receipt),
                "--stdout", str(root / "stdout.bin"),
                "--stderr", str(root / "stderr.bin"),
                "--cwd", str(root),
                "--limit", str(limit),
                "--", sys.executable, "-c", code,
            ]
            completed = subprocess.run(command, check=False, timeout=5)
            return completed.returncode, json.loads(receipt.read_text(encoding="utf-8"))

    def test_zero_and_nonzero_are_distinct(self):
        code, receipt = self.run_case(2, "raise SystemExit(0)")
        self.assertEqual((code, receipt["numeric_child_returncode"]), (0, 0))
        code, receipt = self.run_case(2, "raise SystemExit(9)")
        self.assertEqual((code, receipt["numeric_child_returncode"]), (9, 9))

    def test_timeout_is_supervisor_124_and_confirmed_exit(self):
        code, receipt = self.run_case(0.2, "import time; time.sleep(10)")
        self.assertEqual(code, 124)
        self.assertTrue(receipt["timed_out"])
        self.assertTrue(receipt["child_confirmed_exited"])
        self.assertEqual(receipt["supervisor_returncode"], 124)

    @unittest.skipUnless(os.name == "nt", "Windows process-tree control")
    def test_timeout_terminates_descendant(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            receipt = root / "receipt.json"
            stdout = root / "stdout.bin"
            command = [
                sys.executable, str(TOOL), "--receipt", str(receipt),
                "--stdout", str(stdout), "--stderr", str(root / "stderr.bin"),
                "--cwd", str(root), "--limit", "1.0", "--", sys.executable,
                "-c", "import subprocess,sys,time; p=subprocess.Popen("
                "[sys.executable,'-c','import time;time.sleep(20)']);"
                "print(p.pid,flush=True);time.sleep(20)",
            ]
            self.assertEqual(subprocess.run(command, timeout=5).returncode, 124)
            pid = int(stdout.read_text().strip())
            probe = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"if(Get-Process -Id {pid} -ErrorAction SilentlyContinue){{exit 1}}"],
                check=False, timeout=5,
            )
            self.assertEqual(probe.returncode, 0)

    def test_invalid_limit_and_missing_input_fail_before_launch(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            base = [sys.executable, str(TOOL), "--receipt", str(root / "r"),
                    "--stdout", str(root / "o"), "--stderr", str(root / "e"),
                    "--cwd", str(root)]
            self.assertNotEqual(subprocess.run(
                base + ["--limit", "0", "--", sys.executable, "-c", "pass"]
            , timeout=5).returncode, 0)
            self.assertNotEqual(subprocess.run(
                base + ["--limit", "1", "--input", str(root / "missing"),
                        "--", sys.executable, "-c", "pass"]
            , timeout=5).returncode, 0)

    def test_launch_failure_writes_failed_receipt(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            receipt = root / "receipt.json"
            completed = subprocess.run([
                sys.executable, str(TOOL), "--receipt", str(receipt),
                "--stdout", str(root / "o"), "--stderr", str(root / "e"),
                "--cwd", str(root), "--limit", "1", "--",
                str(root / "absent.exe"),
            ], timeout=5)
            self.assertEqual(completed.returncode, 125)
            self.assertEqual(json.loads(receipt.read_text())["state"], "failed")


if __name__ == "__main__":
    unittest.main()
