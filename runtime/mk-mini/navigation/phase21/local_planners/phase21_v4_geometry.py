from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from navigation.phase21.interfaces import KnownObstacle


def point_segment_distances(
    points: np.ndarray,
    path: np.ndarray,
) -> np.ndarray:
    """Return each point's minimum distance to a polyline."""
    points = np.asarray(
        points,
        dtype=np.float32,
    ).reshape(-1, 2)

    path = np.asarray(
        path,
        dtype=np.float32,
    ).reshape(-1, 2)

    if len(points) == 0 or len(path) < 2:
        return np.full(
            len(points),
            float("inf"),
            dtype=np.float32,
        )

    start = path[:-1]
    end = path[1:]
    vector = end - start

    denominator = np.sum(
        vector * vector,
        axis=1,
    )
    denominator = np.maximum(
        denominator,
        1e-8,
    )

    relative = (
        points[:, None, :]
        - start[None, :, :]
    )

    projection = np.sum(
        relative * vector[None, :, :],
        axis=2,
    ) / denominator[None, :]

    projection = np.clip(
        projection,
        0.0,
        1.0,
    )

    closest = (
        start[None, :, :]
        + projection[:, :, None]
        * vector[None, :, :]
    )

    distances = np.linalg.norm(
        points[:, None, :] - closest,
        axis=2,
    )

    return np.min(
        distances,
        axis=1,
    ).astype(np.float32)


def index_before(
    path: np.ndarray,
    start_index: int,
    distance: float,
) -> int:
    path = np.asarray(
        path,
        dtype=np.float32,
    ).reshape(-1, 2)

    index = int(start_index)
    travelled = 0.0

    while index > 0:
        segment = float(
            np.linalg.norm(
                path[index] - path[index - 1]
            )
        )

        travelled += segment
        index -= 1

        if travelled >= float(distance):
            break

    return index


def index_after(
    path: np.ndarray,
    start_index: int,
    distance: float,
) -> int:
    path = np.asarray(
        path,
        dtype=np.float32,
    ).reshape(-1, 2)

    index = int(start_index)
    travelled = 0.0

    while index < len(path) - 1:
        segment = float(
            np.linalg.norm(
                path[index + 1] - path[index]
            )
        )

        travelled += segment
        index += 1

        if travelled >= float(distance):
            break

    return index


def densify_path(
    path: np.ndarray,
    spacing: float = 0.025,
) -> np.ndarray:
    path = np.asarray(
        path,
        dtype=np.float32,
    ).reshape(-1, 2)

    if len(path) < 2:
        return path.copy()

    pieces: list[np.ndarray] = []

    for index in range(len(path) - 1):
        start = path[index]
        end = path[index + 1]

        length = float(
            np.linalg.norm(end - start)
        )

        count = max(
            2,
            int(
                math.ceil(
                    length / max(float(spacing), 1e-4)
                )
            )
            + 1,
        )

        segment = np.linspace(
            start,
            end,
            count,
            dtype=np.float32,
        )

        if index > 0:
            segment = segment[1:]

        pieces.append(segment)

    return np.concatenate(
        pieces,
        axis=0,
    ).astype(np.float32)


def known_margin(
    path: np.ndarray,
    known_obstacles: Sequence[KnownObstacle],
    robot_radius: float,
) -> float:
    """
    Match the Phase21 v4 baseline margin calculation.

    Rectangle yaw is intentionally ignored because the formal v4 baseline
    treated known rectangles as axis-aligned.
    """
    dense = densify_path(path)
    robot_radius = float(robot_radius)
    margins: list[float] = []

    circles = [
        obstacle
        for obstacle in known_obstacles
        if obstacle.kind == "circle"
    ]

    if circles:
        centers = np.asarray(
            [obstacle.center for obstacle in circles],
            dtype=np.float32,
        ).reshape(-1, 2)

        radii = np.asarray(
            [obstacle.radius for obstacle in circles],
            dtype=np.float32,
        ).reshape(-1)

        distances = np.linalg.norm(
            dense[:, None, :]
            - centers[None, :, :],
            axis=2,
        )

        circle_margin = (
            distances
            - radii[None, :]
            - robot_radius
        )

        margins.append(
            float(np.min(circle_margin))
        )

    rectangles = [
        obstacle
        for obstacle in known_obstacles
        if obstacle.kind == "rectangle"
    ]

    if rectangles:
        centers = np.asarray(
            [obstacle.center for obstacle in rectangles],
            dtype=np.float32,
        ).reshape(-1, 2)

        half_sizes = 0.5 * np.asarray(
            [obstacle.size for obstacle in rectangles],
            dtype=np.float32,
        ).reshape(-1, 2)

        delta = (
            np.abs(
                dense[:, None, :]
                - centers[None, :, :]
            )
            - half_sizes[None, :, :]
        )

        outside = np.maximum(
            delta,
            0.0,
        )

        distances = np.linalg.norm(
            outside,
            axis=2,
        )

        rectangle_margin = (
            distances - robot_radius
        )

        margins.append(
            float(np.min(rectangle_margin))
        )

    if not margins:
        return float("inf")

    return float(min(margins))


def path_metrics(
    path: np.ndarray,
    original_length: float,
) -> dict[str, float]:
    path = np.asarray(
        path,
        dtype=np.float32,
    ).reshape(-1, 2)

    vectors = np.diff(
        path,
        axis=0,
    )

    lengths = np.linalg.norm(
        vectors,
        axis=1,
    )

    valid = lengths > 1e-5
    vectors = vectors[valid]
    lengths = lengths[valid]

    if len(vectors) < 2:
        return {
            "length": float("inf"),
            "length_ratio": float("inf"),
            "max_heading_delta": float("inf"),
            "p95_curvature": float("inf"),
        }

    headings = np.unwrap(
        np.arctan2(
            vectors[:, 1],
            vectors[:, 0],
        )
    )

    heading_delta = np.abs(
        np.diff(headings)
    )

    mean_segment_length = 0.5 * (
        lengths[:-1] + lengths[1:]
    )

    curvature = (
        heading_delta
        / np.maximum(
            mean_segment_length,
            1e-5,
        )
    )

    total_length = float(
        np.sum(lengths)
    )

    return {
        "length": total_length,
        "length_ratio": float(
            total_length
            / max(float(original_length), 1e-6)
        ),
        "max_heading_delta": float(
            np.max(heading_delta)
        ),
        "p95_curvature": float(
            np.percentile(
                curvature,
                95.0,
            )
        ),
    }


def make_candidate(
    original: np.ndarray,
    approach_index: int,
    rejoin_index: int,
    offset: float,
    side_sign: float,
) -> tuple[np.ndarray, np.ndarray]:
    original = np.asarray(
        original,
        dtype=np.float32,
    ).reshape(-1, 2)

    segment = original[
        int(approach_index):
        int(rejoin_index) + 1
    ].copy()

    if len(segment) < 5:
        raise ValueError(
            "candidate segment too short"
        )

    segment_vectors = np.diff(
        segment,
        axis=0,
    )

    segment_lengths = np.linalg.norm(
        segment_vectors,
        axis=1,
    )

    cumulative = np.concatenate(
        [
            np.zeros(
                1,
                dtype=np.float32,
            ),
            np.cumsum(
                segment_lengths
            ).astype(np.float32),
        ]
    )

    total = float(
        cumulative[-1]
    )

    if total < 0.20:
        raise ValueError(
            "candidate segment length too short"
        )

    parameter = cumulative / total

    tangent = np.gradient(
        segment,
        axis=0,
    )

    tangent_norm = np.linalg.norm(
        tangent,
        axis=1,
        keepdims=True,
    )

    tangent = tangent / np.maximum(
        tangent_norm,
        1e-6,
    )

    normal = np.stack(
        [
            -tangent[:, 1],
            tangent[:, 0],
        ],
        axis=1,
    )

    profile = np.sin(
        math.pi * parameter
    ) ** 2

    shifted_segment = (
        segment
        + float(side_sign)
        * float(offset)
        * profile[:, None]
        * normal
    ).astype(np.float32)

    active_path = np.concatenate(
        [
            original[:int(approach_index)],
            shifted_segment,
            original[int(rejoin_index) + 1:],
        ],
        axis=0,
    ).astype(np.float32)

    return shifted_segment, active_path


__all__ = [
    "densify_path",
    "index_after",
    "index_before",
    "known_margin",
    "make_candidate",
    "path_metrics",
    "point_segment_distances",
]
