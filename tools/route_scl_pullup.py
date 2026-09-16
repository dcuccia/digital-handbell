# SPDX-License-Identifier: MIT
"""Stage the remaining SCL pull-up connection; preserve the connected SDA branch."""
from experiments import route_core_distribution as experiment

experiment.BASE = "a83cc417c96b05dd15c187e648b9fd2a35ba857c3a66f7d13aaaa42ae3bd9fff"
experiment.PAIRS = (("R14.2", "IC4.13"),)
experiment.STAGE = "scl-pullup-routing"
experiment.INPUT_COMMIT = "b2203c8"
experiment.ROUTING_BOUNDS = (-20.5, -20.5, 20.5, 20.5)
experiment.TARGET_ANCHORS = {"IC4.13": [91.69, 92.7368]}

if __name__ == "__main__":
    experiment.main()
