# SPDX-License-Identifier: MIT
"""Final authorized staged SCL correction with the exact redundant 3V3 pair removed."""
import route_core_distribution as experiment

experiment.BASE = "a83cc417c96b05dd15c187e648b9fd2a35ba857c3a66f7d13aaaa42ae3bd9fff"
experiment.PAIRS = (("R14.2", "IC4.13"),)
experiment.STAGE = "scl-final-correction"
experiment.INPUT_COMMIT = "b2203c8"
experiment.ROUTING_BOUNDS = (-20.5, -20.5, 20.5, 20.5)
experiment.TARGET_ANCHORS = {"IC4.13": [91.69, 92.7368]}
experiment.REMOVED_TRACK_UUIDS = (
    "548c8552-ff4c-56b3-83d9-9d0a5389e3e2",
    "76a37864-74d8-5963-bcc4-18eb043accfd",
)
experiment.FRONT_ONLY = True

if __name__ == "__main__":
    experiment.main()
