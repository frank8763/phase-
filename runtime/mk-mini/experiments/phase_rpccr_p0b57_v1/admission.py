"""Frozen B57 candidate eligibility; same numeric bounds as B56."""

from __future__ import annotations

import math


# The 0.40 m lateral trust radius is motivated by the existing 0.40 m
# low-level front-danger distance. B55 development outcomes were inspected
# before these bounds were specified, so only fresh seeds can assess them.
TRUST_RADIUS_M = 0.40
MAX_LENGTH_RATIO = 1.10
MIN_SENSOR_MARGIN_M = 0.10
MIN_KNOWN_MARGIN_M = 0.10


def decide(candidate):
    values = {
        "offset_m": float(candidate.offset),
        "length_ratio": float(candidate.length_ratio),
        "sensor_margin_m": float(candidate.sensor_margin),
        "known_margin_m": float(candidate.known_margin),
    }
    finite = all(math.isfinite(value) for value in values.values())
    accepted = bool(
        finite
        and values["offset_m"] <= TRUST_RADIUS_M
        and values["length_ratio"] <= MAX_LENGTH_RATIO
        and values["sensor_margin_m"] >= MIN_SENSOR_MARGIN_M
        and values["known_margin_m"] >= MIN_KNOWN_MARGIN_M
    )
    return {"accept": accepted, "features": values, "finite": finite}
