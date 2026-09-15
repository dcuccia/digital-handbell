# SPDX-License-Identifier: MIT
"""Stage the short charge-indicator branch without changing existing copper."""
from experiments import route_core_distribution as experiment

experiment.PAIRS = (("R2.1", "CHG0.C"),)
experiment.STAGE = "charge-led-routing"
experiment.INPUT_COMMIT = "4163f28"
experiment.ROUTING_BOUNDS = (-20.5, -20.5, 20.5, 20.5)

if __name__ == "__main__":
    experiment.main()
