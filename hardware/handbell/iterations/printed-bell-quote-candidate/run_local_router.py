# SPDX-License-Identifier: MIT
"""Run a pinned LOCAL autorouter. Analytics disabled; no cloud/API/vendor use."""
import argparse
import subprocess
from pathlib import Path
import route

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--java", type=Path, required=True)
parser.add_argument("--jar", type=Path, required=True)
parser.add_argument("--passes", type=int, default=30)
args = parser.parse_args()
route.require(route.sha(args.jar) == "9084a4888937a7f31f857ecc12aa7a37407f51160e4d2892dff9c9bb47ae3102",
              "Expected reviewed Freerouting 1.9.0 release JAR")
work = route.HERE / "routing"
for folder in ("offline-home", "offline-temp"):
    (work / folder).mkdir(exist_ok=True)
command = [str(args.java), "-Dhttp.proxyHost=127.0.0.1", "-Dhttp.proxyPort=9",
           "-Dhttps.proxyHost=127.0.0.1", "-Dhttps.proxyPort=9",
           "-Duser.home="+str(work / "offline-home"), "-Djava.io.tmpdir="+str(work / "offline-temp"),
           "-jar", str(args.jar), "-da", "-de", str(work / "completion-input.dsn"),
           "-do", str(work / "completion-output.ses"), "-mp", str(args.passes), "-mt", "0",
           "-inc", "GroundFill", "-dct", "1", "-l", "en"]
route.require(not (work / "completion-output.ses").exists(), "Existing SES refused; archive the prior attempt explicitly")
with (work / "local-router.log").open("w", encoding="utf-8") as log:
    result = subprocess.run(command, cwd=work, stdout=log, stderr=subprocess.STDOUT, timeout=1200)
route.require(result.returncode == 0 and (work / "completion-output.ses").exists(),
              "Local routing did not produce a session; inspect local-router.log")
route.write(work / "local-router-binding.json", {
    "java_sha256": route.sha(args.java), "jar_sha256": route.sha(args.jar),
    "dsn_sha256": route.sha(work / "completion-input.dsn"), "ses_sha256": route.sha(work / "completion-output.ses"),
    "version": "Freerouting 1.9.0; locally executed, analytics disabled and HTTP(S) proxies pointed to loopback port9",
    "passes": args.passes, "optimizer_threads": 0,
})
print("Local session produced; native import and complete checks still required.")
