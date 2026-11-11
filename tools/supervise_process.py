#!/usr/bin/env python3
"""Run one command under a hard deadline and preserve a machine-readable receipt."""

from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_kill_job():
    """Return a Windows job which terminates all assigned descendants on close."""
    if os.name != "nt":
        return None
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = ctypes.c_void_p
    kernel32.SetInformationJobObject.argtypes = [
        ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32
    ]
    kernel32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.sizeof(ctypes.c_void_p) != 8:
        raise RuntimeError("only 64-bit Windows is supported")
    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [(name, ctypes.c_uint64) for name in (
            "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
            "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]
    class BASIC(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", ctypes.c_uint32),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", ctypes.c_uint32),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", ctypes.c_uint32),
            ("SchedulingClass", ctypes.c_uint32),
        ]
    class EXTENDED(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", BASIC), ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]
    info = EXTENDED()
    info.BasicLimitInformation.LimitFlags = 0x2000
    if not kernel32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
        kernel32.CloseHandle(job)
        raise ctypes.WinError(ctypes.get_last_error())
    return kernel32, job


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--stdout", required=True, type=Path)
    parser.add_argument("--stderr", required=True, type=Path)
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--limit", required=True, type=float)
    parser.add_argument("--input", action="append", default=[], type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("missing command")

    if os.name != "nt":
        parser.error("full process-tree supervision is implemented only on Windows")
    if not args.limit > 0:
        parser.error("--limit must be positive and finite")
    if not all(map(lambda x: x == x and x != float("inf"), [args.limit])):
        parser.error("--limit must be positive and finite")
    outputs = [args.receipt.resolve(), args.stdout.resolve(), args.stderr.resolve()]
    if len(set(outputs)) != 3 or any(path.exists() for path in outputs):
        parser.error("receipt/stdout/stderr must be unique new files")
    missing = [str(path) for path in args.input if not path.is_file()]
    if missing:
        parser.error("missing input: " + ", ".join(missing))
    for path in (args.receipt, args.stdout, args.stderr):
        path.parent.mkdir(parents=True, exist_ok=True)
    executable = Path(command[0]).resolve()
    receipt = {
        "schema_version": 1,
        "state": "prepared",
        "supervisor_pid": os.getpid(),
        "prepared_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "command": command,
        "cwd": str(args.cwd.resolve()),
        "hard_limit_seconds": args.limit,
        "executable_sha256": sha256(executable) if executable.is_file() else None,
        "input_sha256": {str(p.resolve()): sha256(p) for p in args.input},
        "supervisor_sha256": sha256(Path(__file__).resolve()),
        "stdout": str(args.stdout.resolve()),
        "stderr": str(args.stderr.resolve()),
    }
    if not executable.is_file():
        receipt.update(
            state="failed", failed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
            error=f"executable not found: {executable}", child_pid=None,
            child_confirmed_exited=True,
        )
        write_json(args.receipt, receipt)
        return 125
    write_json(args.receipt, receipt)
    started = time.monotonic()
    timed_out = False
    job_info = None
    child = None
    try:
        job_info = make_kill_job()
        kernel32, job = job_info
        ntdll = ctypes.WinDLL("ntdll")
        ntdll.NtResumeProcess.argtypes = [ctypes.c_void_p]
        ntdll.NtResumeProcess.restype = ctypes.c_long
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | 0x00000004  # CREATE_SUSPENDED
        env = os.environ.copy()
        env["SUPERVISED_PROCESS_RECEIPT"] = str(args.receipt.resolve())
        with args.stdout.open("xb", buffering=0) as stdout, args.stderr.open("xb", buffering=0) as stderr:
            child = subprocess.Popen(
                command, cwd=args.cwd, stdin=subprocess.DEVNULL, stdout=stdout,
                stderr=stderr, creationflags=flags, env=env
            )
            if not kernel32.AssignProcessToJobObject(job, ctypes.c_void_p(int(child._handle))):
                raise ctypes.WinError(ctypes.get_last_error())
            if ntdll.NtResumeProcess(ctypes.c_void_p(int(child._handle))) != 0:
                raise RuntimeError("NtResumeProcess failed")
            receipt.update(
                state="running", child_pid=child.pid,
                launched_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
            )
            write_json(args.receipt, receipt)
            returncode = child.wait(timeout=args.limit)
    except subprocess.TimeoutExpired:
        timed_out = True
        kernel32.CloseHandle(job)
        job_info = None
        returncode = child.wait(timeout=10)
    except Exception as exc:
        if job_info:
            job_info[0].CloseHandle(job_info[1])
            job_info = None
        if child is not None:
            if child.poll() is None:
                # Assignment may have failed while the process was suspended and
                # therefore outside the job. Kill that exact process explicitly.
                child.kill()
            child.wait(timeout=10)
        receipt.update(
            state="failed", failed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
            error=f"{type(exc).__name__}: {exc}",
            child_pid=None if child is None else child.pid,
            child_confirmed_exited=child is None or child.poll() is not None,
        )
        write_json(args.receipt, receipt)
        return 125
    finally:
        if job_info:
            job_info[0].CloseHandle(job_info[1])

    receipt.update(
        state="completed",
        completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        elapsed_seconds=round(time.monotonic() - started, 6),
        timed_out=timed_out,
        numeric_child_returncode=returncode,
        supervisor_returncode=124 if timed_out else returncode,
        child_confirmed_exited=child.poll() is not None,
        timeout_termination=(
            "Windows kill-on-close job terminated the child process tree"
            if timed_out and os.name == "nt" else
            "exact child killed and waited" if timed_out else "not needed"
        ),
        stdout_bytes=args.stdout.stat().st_size,
        stderr_bytes=args.stderr.stat().st_size,
        stdout_sha256=sha256(args.stdout),
        stderr_sha256=sha256(args.stderr),
    )
    write_json(args.receipt, receipt)
    return 124 if timed_out else returncode


if __name__ == "__main__":
    raise SystemExit(main())
