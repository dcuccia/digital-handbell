# SPDX-License-Identifier: MIT
"""Drive a DeepPCB routing job over its public API, with spending guards.

Uses the API documented at https://api.deeppcb.ai/swagger/deeppcb/swagger.json
(the same calls as the Apache-2.0 KiCad plugin), but always requests
CurrentProtectedWiring so existing copper is kept. The API key is read from
DEEPPCB_API_KEY or %USERPROFILE%/.deeppcb/api_key.txt and is never printed.

Typical use:
  python deeppcb_route.py create --dir <folder with .kicad_pcb/.kicad_pro> --state run.json
  python deeppcb_route.py status --state run.json
  python deeppcb_route.py start --state run.json --minutes 30 [--allow-paid --max-usd 15]
  python deeppcb_route.py wait --state run.json
  python deeppcb_route.py download --state run.json --out routed.kicad_pcb
"""
import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path

import requests

API = "https://api.deeppcb.ai/api/v1"
USD_PER_ROUTING_HOUR = 30.0  # published pay-as-you-go price, November 2026
TERMINAL = {"Stopped", "Failed", "Done"}


def api_key():
    key = os.environ.get("DEEPPCB_API_KEY")
    if not key:
        path = Path.home() / ".deeppcb" / "api_key.txt"
        if not path.exists():
            sys.exit(f"No API key: set DEEPPCB_API_KEY or create {path}")
        key = path.read_text(encoding="utf-8").strip()
    return key


def headers(content_type=None):
    h = {"accept": "*/*", "x-deeppcb-api-key": api_key(), "x-client-type": "KicadPlugin"}
    if content_type:
        h["Content-Type"] = content_type
    return h


def check(response):
    if response.status_code >= 400:
        sys.exit(f"HTTP {response.status_code}: {response.text[:500]}")
    return response


def load_state(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_state(path, state):
    Path(path).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def board_status(board_id):
    return check(requests.get(f"{API}/boards/{board_id}", headers=headers(), timeout=60)).json()


def summary(board):
    workflows = board.get("workflows") or []
    revisions = [r for w in workflows for r in w.get("revisions", [])]
    latest = revisions[-1] if revisions else {}
    stats = (latest.get("result") or {}).get("routingStats") or latest.get("routingStats")
    return {
        "status": board.get("boardStatus"),
        "requiresCredits": board.get("requiresCredits"),
        "creditsCostPerMinute": board.get("creditsCostPerMinute"),
        "revisions": [r.get("revisionNumber") for r in revisions],
        "latestStats": stats,
    }


def cmd_create(args):
    folder = Path(args.dir)
    files = [("kicadBoardFile", (f"{args.name}.kicad_pcb", (folder / "handbell.kicad_pcb").read_bytes())),
             ("kicadProjectFile", (f"{args.name}.kicad_pro", (folder / "handbell.kicad_pro").read_bytes()))]
    data = {"routingType": args.routing_type, "boardName": args.name,
            "requestId": str(uuid.uuid4()), "boardInputType": "Kicad", "smartConstraints": "false",
            # The API requires a webhook; this is the KiCad plugin's own placeholder endpoint.
            "webhookUrl": "https://plugin.kicad.deeppcb.ai", "webhookToken": "webhook_token"}
    r = check(requests.post(f"{API}/boards", headers=headers(), data=data, files=files, timeout=300))
    board_id = r.text.strip().strip('"')
    state = {"board_id": board_id, "name": args.name, "input_dir": str(folder), "routing_type": args.routing_type}
    save_state(args.state, state)
    time.sleep(5)
    print(json.dumps({"board_id": board_id, **summary(board_status(board_id))}, indent=2))


def cmd_status(args):
    state = load_state(args.state)
    board = board_status(state["board_id"])
    if args.raw:
        Path(args.raw).write_text(json.dumps(board, indent=2), encoding="utf-8")
    print(json.dumps(summary(board), indent=2))


def cmd_start(args):
    state = load_state(args.state)
    board = board_status(state["board_id"])
    if board.get("requiresCredits"):
        estimate = USD_PER_ROUTING_HOUR * args.minutes / 60
        if not args.allow_paid:
            sys.exit(f"Paid run required (about ${estimate:.2f} for {args.minutes} min); "
                     "re-run with --allow-paid --max-usd after owner approval")
        if estimate > args.max_usd:
            sys.exit(f"Estimated ${estimate:.2f} exceeds --max-usd {args.max_usd}")
    body = {"timeout": args.minutes, "maxBatchTimeout": 30, "timeToLive": 300,
            "maxInactivityWaitTimeout": 60, "jobType": "Routing",
            "routingType": state.get("routing_type", "CurrentProtectedWiring")}
    check(requests.patch(f"{API}/boards/{state['board_id']}/confirm",
                         headers=headers("application/json-patch+json"), json=body, timeout=60))
    state["started"] = {"minutes": args.minutes, "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    save_state(args.state, state)
    print("Routing started")


def cmd_wait(args):
    state = load_state(args.state)
    deadline = time.time() + args.max_wait * 60
    while True:
        s = summary(board_status(state["board_id"]))
        print(time.strftime("%H:%M:%S"), json.dumps(s), flush=True)
        if s["status"] in TERMINAL or time.time() > deadline:
            return
        time.sleep(args.poll)


def cmd_stop(args):
    state = load_state(args.state)
    check(requests.patch(f"{API}/boards/{state['board_id']}/stop",
                         headers=headers("application/json-patch+json"), timeout=60))
    print("Stop requested")


def cmd_download(args):
    state = load_state(args.state)
    revision = args.revision
    if revision is None:
        revs = summary(board_status(state["board_id"]))["revisions"]
        if not revs:
            sys.exit("No revisions available")
        revision = revs[-1]
    r = check(requests.get(f"{API}/boards/{state['board_id']}/revision-artifact", headers=headers(),
                           params={"revision": revision, "type": "KicadFile", "revisionType": "Tidy"},
                           timeout=300))
    Path(args.out).write_text(r.text, encoding="utf-8", newline="")
    print(f"Saved revision {revision} to {args.out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(required=True)
    p = sub.add_parser("create"); p.add_argument("--dir", required=True); p.add_argument("--state", required=True)
    p.add_argument("--name", default="handbell")
    p.add_argument("--routing-type", default="CurrentProtectedWiring",
                   choices=["CurrentProtectedWiring", "CurrentUnprotectedWiring"],
                   help="unprotected lets DeepPCB rip up existing copper; only safe with a merge against a frozen base")
    p.set_defaults(func=cmd_create)
    p = sub.add_parser("status"); p.add_argument("--state", required=True); p.add_argument("--raw")
    p.set_defaults(func=cmd_status)
    p = sub.add_parser("start"); p.add_argument("--state", required=True)
    p.add_argument("--minutes", type=int, required=True); p.add_argument("--allow-paid", action="store_true")
    p.add_argument("--max-usd", type=float, default=0.0); p.set_defaults(func=cmd_start)
    p = sub.add_parser("wait"); p.add_argument("--state", required=True)
    p.add_argument("--poll", type=int, default=30); p.add_argument("--max-wait", type=int, default=70)
    p.set_defaults(func=cmd_wait)
    p = sub.add_parser("stop"); p.add_argument("--state", required=True); p.set_defaults(func=cmd_stop)
    p = sub.add_parser("download"); p.add_argument("--state", required=True); p.add_argument("--out", required=True)
    p.add_argument("--revision", type=int); p.set_defaults(func=cmd_download)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
