from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Phase21V4Config:
    offsets: tuple[float, ...] = (
        0.34,
        0.44,
        0.54,
        0.64,
    )

    approach_distances: tuple[float, ...] = (
        0.45,
        0.70,
        0.95,
    )

    rejoin_distances: tuple[float, ...] = (
        1.20,
        1.60,
        2.00,
        2.40,
    )

    min_known_margin: float = 0.06
    min_sensor_margin: float = 0.025
    max_p95_curvature: float = 1.80
    max_heading_delta: float = 0.24

    def __post_init__(self) -> None:
        self.offsets = tuple(
            float(value)
            for value in self.offsets
        )
        self.approach_distances = tuple(
            float(value)
            for value in self.approach_distances
        )
        self.rejoin_distances = tuple(
            float(value)
            for value in self.rejoin_distances
        )

        self.min_known_margin = float(
            self.min_known_margin
        )
        self.min_sensor_margin = float(
            self.min_sensor_margin
        )
        self.max_p95_curvature = float(
            self.max_p95_curvature
        )
        self.max_heading_delta = float(
            self.max_heading_delta
        )

        if not self.offsets:
            raise ValueError(
                "offsets cannot be empty"
            )

        if not self.approach_distances:
            raise ValueError(
                "approach_distances cannot be empty"
            )

        if not self.rejoin_distances:
            raise ValueError(
                "rejoin_distances cannot be empty"
            )

        if any(value <= 0.0 for value in self.offsets):
            raise ValueError(
                "all offsets must be positive"
            )

        if any(
            value <= 0.0
            for value in self.approach_distances
        ):
            raise ValueError(
                "all approach distances must be positive"
            )

        if any(
            value <= 0.0
            for value in self.rejoin_distances
        ):
            raise ValueError(
                "all rejoin distances must be positive"
            )

        if self.min_known_margin < 0.0:
            raise ValueError(
                "min_known_margin cannot be negative"
            )

        if self.min_sensor_margin < 0.0:
            raise ValueError(
                "min_sensor_margin cannot be negative"
            )

        if self.max_p95_curvature <= 0.0:
            raise ValueError(
                "max_p95_curvature must be positive"
            )

        if self.max_heading_delta <= 0.0:
            raise ValueError(
                "max_heading_delta must be positive"
            )


__all__ = ["Phase21V4Config"]
