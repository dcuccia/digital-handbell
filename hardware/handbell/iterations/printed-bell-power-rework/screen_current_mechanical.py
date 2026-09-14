# SPDX-License-Identifier: MIT
"""Post-rebind service screen for this package only; never accepts stage1 embedded inputs."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MECHANICAL = ROOT / "mechanical" / "studies" / "2026-09-13-printed-bell"


def main():
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT / "tools"))
    import check_printed_bell_power_rework as check
    route = check.generator()
    paths = [MECHANICAL / name for name in ("printed-bell.FCStd", "artifact-manifest.json", "fit-report.json",
                                           "completion.json", "review-status.json")]
    bindings = {str(p.relative_to(ROOT)): check.sha(p) for p in paths}
    expected = {key: check.sha(HERE / filename) for key, filename in (
        ("placement", "placement-manifest.json"), ("pcb", "handbell.kicad_pcb"),
        ("schematic", "handbell.kicad_sch"), ("contact_interface", "battery-contact-interface.json"))}
    native = paths[0].read_bytes()
    with ZipFile(io.BytesIO(native)) as archive:
        tree = ET.fromstring(archive.read("Document.xml"))
        for key, digest in expected.items():
            item = tree.find(f".//ObjectData/Object[@name='Raw_{key}']/Properties/Property[@name='Text']/String")
            check.require(item is not None, "Current model lacks embedded "+key)
            check.require(hashlib.sha256(base64.b64decode(item.attrib["value"], validate=True)).hexdigest() == digest,
                          "Mechanical rebind required: current model does not embed this power-rework "+key)
    result = subprocess.run([sys.executable, str(ROOT / "tools" / "check_printed_bell.py")],
                            cwd=ROOT, capture_output=True, text=True, timeout=120)
    check.require(result.returncode == 0, "Current mechanical evidence invalid: "+result.stdout+result.stderr)
    pcb = check.native_api(route)
    graph = check.CopperGraph(pcb, HERE / "handbell.kicad_pcb")
    errors = []
    service = check.service_and_contact_screen(route, graph, errors)
    check.require(not errors, "; ".join(errors))
    labels = [{"text": label["text"], "screen_bounds_xy_mm": label["reserved_full_rectangle_xy_mm"]}
              for label in service["labels"]]
    helper = route.SOURCE / "screen_service_labels.py"
    tool = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "FreeCAD 1.1" / "bin" / "FreeCADCmd.exe"
    with tempfile.TemporaryDirectory(prefix=".rebound-labels-", dir=HERE / "reports") as directory:
        work = Path(directory)
        (work / "released.FCStd").write_bytes(native)
        route.write(work / "request.json", labels)
        # Only this pure, explicit-work-directory function is reused. No old HERE globals are changed.
        bootstrap = (f"import runpy\nm=runpy.run_path({str(helper)!r})\n"
                     f"m['mechanical_screen'](m['Path']({str(work)!r}))\n")
        run = subprocess.run([str(tool), "--user-cfg", str(work / "user.cfg"),
                              "--system-cfg", str(work / "system.cfg")], input=bootstrap, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
        check.require(run.returncode == 0 and (work / "completed.json").exists(),
                      "Fresh rebound visibility result absent: "+run.stdout)
        review = check.read_json(work / "completed.json")
        check.require(review["request_sha256"] == check.sha(work / "request.json"), "Stale geometry screen")
        check.require(check.sha(work / "released.FCStd") == bindings[str(paths[0].relative_to(ROOT))],
                      "Read-only screen changed copied native")
    check.require(all(label["clear"] for label in review["labels"]), "Rebound service text is obscured")
    service["mechanical_visibility"] = "Screened against exactly rebound current model, not the old placement"
    service["mechanical_rebind_required"] = False
    check.require(bindings == {str(p.relative_to(ROOT)): check.sha(p) for p in paths}, "Mechanical inputs changed")
    check.require(expected == {key: check.sha(HERE / filename) for key, filename in (
        ("placement", "placement-manifest.json"), ("pcb", "handbell.kicad_pcb"),
        ("schematic", "handbell.kicad_sch"), ("contact_interface", "battery-contact-interface.json"))},
        "Electrical inputs changed")
    route.write(HERE / "reports" / "service-label-current-mechanical-review.json",
                {"scope": "Exact rebound CAD visibility only; not physical, current, charge or safety qualification",
                 "electrical_inputs_sha256": expected, "current_mechanical_bindings_sha256": bindings,
                 "helper_sha256": check.sha(helper), "tool_sha256": check.sha(__file__),
                 "freecad_cli_sha256": check.sha(tool), "service": service, "mechanical": review})


if __name__ == "__main__":
    main()
