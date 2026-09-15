# SPDX-License-Identifier: MIT
"""Stage only the amplifier GAIN connection using the bounded native-mask experiment."""
from experiments import route_core_distribution as experiment

experiment.PAIRS = (("U4.2", "GAIN0.2"),)
experiment.STAGE = "gain-routing"
experiment.INPUT_COMMIT = "2921fc8"
experiment.ROUTING_BOUNDS = (-20.5, -20.5, 20.5, 20.5)
experiment.SEARCH_MARGIN = 8
experiment.SEARCH_LIMIT = 160000

if __name__ == "__main__":
    experiment.main()
