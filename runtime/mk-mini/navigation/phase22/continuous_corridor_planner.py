from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class CorridorCandidate:
    active_path: np.ndarray
    local_curve: np.ndarray

    approach_index: int
    rejoin_index: int

    side_sign: float
    offset: float
    approach_distance: float
    rejoin_distance: float
    shoulder: float

    known_margin: float
    sensor_margin: float
    p95_curvature: float
    max_heading_delta: float
    length_ratio: float
    reverse_count: int

    objective: float
    score: float
    feasible: bool


def _polyline_interpolate(
    path: np.ndarray,
    parameters: np.ndarray,
) -> np.ndarray:
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

    cumulative = np.concatenate([
        np.zeros(
            1,
            dtype=np.float32,
        ),
        np.cumsum(
            lengths,
        ).astype(np.float32),
    ])

    total = float(
        cumulative[-1]
    )

    if total <= 1e-6:
        return np.repeat(
            path[:1],
            len(parameters),
            axis=0,
        )

    output = []

    for parameter in parameters:
        distance = float(
            np.clip(
                parameter,
                0.0,
                1.0,
            )
            * total
        )

        index = int(
            np.searchsorted(
                cumulative,
                distance,
                side="right",
            )
            - 1
        )

        index = int(
            np.clip(
                index,
                0,
                len(path) - 2,
            )
        )

        local_length = float(
            lengths[index]
        )

        if local_length <= 1e-6:
            ratio = 0.0
        else:
            ratio = (
                distance
                - float(
                    cumulative[index]
                )
            ) / local_length

        point = (
            path[index]
            + float(ratio)
            * (
                path[index + 1]
                - path[index]
            )
        )

        output.append(point)

    return np.asarray(
        output,
        dtype=np.float32,
    )


def _open_uniform_knots(
    control_count: int,
    degree: int,
) -> np.ndarray:
    interior_count = (
        control_count
        - degree
        - 1
    )

    knots = [0.0] * (
        degree + 1
    )

    if interior_count > 0:
        interior = np.linspace(
            0.0,
            1.0,
            interior_count + 2,
            dtype=np.float64,
        )[1:-1]

        knots.extend(
            float(value)
            for value in interior
        )

    knots.extend(
        [1.0] * (
            degree + 1
        )
    )

    return np.asarray(
        knots,
        dtype=np.float64,
    )


def _de_boor(
    control_points: np.ndarray,
    degree: int,
    knots: np.ndarray,
    parameter: float,
) -> np.ndarray:
    control_points = np.asarray(
        control_points,
        dtype=np.float64,
    )

    control_count = len(
        control_points
    )

    if parameter >= 1.0:
        return control_points[-1].copy()

    span = int(
        np.searchsorted(
            knots,
            parameter,
            side="right",
        )
        - 1
    )

    span = int(
        np.clip(
            span,
            degree,
            control_count - 1,
        )
    )

    values = [
        control_points[
            span - degree + index
        ].copy()
        for index in range(
            degree + 1
        )
    ]

    for level in range(
        1,
        degree + 1,
    ):
        for index in range(
            degree,
            level - 1,
            -1,
        ):
            knot_index = (
                span
                - degree
                + index
            )

            denominator = (
                knots[
                    knot_index
                    + degree
                    - level
                    + 1
                ]
                - knots[
                    knot_index
                ]
            )

            if abs(
                denominator
            ) <= 1e-12:
                alpha = 0.0
            else:
                alpha = (
                    parameter
                    - knots[
                        knot_index
                    ]
                ) / denominator

            values[index] = (
                (
                    1.0
                    - alpha
                )
                * values[
                    index - 1
                ]
                + alpha
                * values[index]
            )

    return values[
        degree
    ]


def _sample_bspline(
    control_points: np.ndarray,
    sample_count: int,
) -> np.ndarray:
    degree = min(
        3,
        len(control_points) - 1,
    )

    knots = _open_uniform_knots(
        len(control_points),
        degree,
    )

    parameters = np.linspace(
        0.0,
        1.0,
        sample_count,
        dtype=np.float64,
    )

    curve = np.asarray([
        _de_boor(
            control_points,
            degree,
            knots,
            float(parameter),
        )
        for parameter in parameters
    ], dtype=np.float32)

    curve[0] = control_points[0]
    curve[-1] = control_points[-1]

    return curve


def _build_control_points(
    segment: np.ndarray,
    signed_offset: float,
    shoulder: float,
) -> np.ndarray:
    parameters = np.asarray(
        [
            0.0,
            0.22,
            0.50,
            0.78,
            1.0,
        ],
        dtype=np.float32,
    )

    base_points = (
        _polyline_interpolate(
            segment,
            parameters,
        )
    )

    epsilon = 0.025

    before = _polyline_interpolate(
        segment,
        np.clip(
            parameters - epsilon,
            0.0,
            1.0,
        ),
    )

    after = _polyline_interpolate(
        segment,
        np.clip(
            parameters + epsilon,
            0.0,
            1.0,
        ),
    )

    tangents = (
        after - before
    )

    tangent_norms = np.linalg.norm(
        tangents,
        axis=1,
        keepdims=True,
    )

    tangents = tangents / np.maximum(
        tangent_norms,
        1e-6,
    )

    normals = np.stack(
        [
            -tangents[:, 1],
            tangents[:, 0],
        ],
        axis=1,
    )

    profile = np.asarray(
        [
            0.0,
            shoulder,
            1.0,
            shoulder,
            0.0,
        ],
        dtype=np.float32,
    )

    control_points = (
        base_points
        + float(
            signed_offset
        )
        * profile[:, None]
        * normals
    )

    control_points[0] = segment[0]
    control_points[-1] = segment[-1]

    return control_points.astype(
        np.float32
    )


def _reverse_count(
    curve: np.ndarray,
    original_segment: np.ndarray,
) -> int:
    sample_parameters = np.linspace(
        0.0,
        1.0,
        len(curve),
        dtype=np.float32,
    )

    baseline = _polyline_interpolate(
        original_segment,
        sample_parameters,
    )

    curve_vectors = np.diff(
        curve,
        axis=0,
    )

    baseline_vectors = np.diff(
        baseline,
        axis=0,
    )

    curve_norm = np.linalg.norm(
        curve_vectors,
        axis=1,
        keepdims=True,
    )

    baseline_norm = np.linalg.norm(
        baseline_vectors,
        axis=1,
        keepdims=True,
    )

    curve_vectors = (
        curve_vectors
        / np.maximum(
            curve_norm,
            1e-6,
        )
    )

    baseline_vectors = (
        baseline_vectors
        / np.maximum(
            baseline_norm,
            1e-6,
        )
    )

    alignment = np.sum(
        curve_vectors
        * baseline_vectors,
        axis=1,
    )

    return int(
        np.sum(
            alignment < -0.05
        )
    )


def _evaluate_candidate(
    env: Any,
    original: np.ndarray,
    sensor_points: np.ndarray,
    conflict_index: int,
    side_sign: float,
    offset: float,
    approach_distance: float,
    rejoin_distance: float,
    shoulder: float,
    preferred_side: float,
) -> CorridorCandidate | None:
    approach_index = (
        env._phase21_v3_index_before(
            original,
            conflict_index,
            float(
                approach_distance
            ),
        )
    )

    rejoin_index = (
        env._phase21_v3_index_after(
            original,
            conflict_index,
            float(
                rejoin_distance
            ),
        )
    )

    if (
        approach_index
        >= conflict_index
        or rejoin_index
        <= conflict_index
        or rejoin_index
        >= len(original)
    ):
        return None

    original_segment = original[
        approach_index:
        rejoin_index + 1
    ].copy()

    if len(
        original_segment
    ) < 6:
        return None

    original_length = float(
        np.sum(
            np.linalg.norm(
                np.diff(
                    original_segment,
                    axis=0,
                ),
                axis=1,
            )
        )
    )

    if original_length < 0.25:
        return None

    signed_offset = (
        float(side_sign)
        * float(offset)
    )

    control_points = (
        _build_control_points(
            original_segment,
            signed_offset,
            float(shoulder),
        )
    )

    sample_count = max(
        80,
        len(original_segment),
    )

    local_curve = _sample_bspline(
        control_points,
        sample_count,
    )

    active_path = np.concatenate(
        [
            original[
                :approach_index
            ],
            local_curve,
            original[
                rejoin_index + 1:
            ],
        ],
        axis=0,
    ).astype(np.float32)

    known_margin = float(
        env._phase21_v4_known_margin(
            active_path
        )
    )

    sensor_distance = (
        env._phase21_point_segment_distances(
            sensor_points,
            local_curve,
        )
    )

    sensor_margin = float(
        np.min(
            sensor_distance
        )
        - env.phase21_corridor_radius
    )

    metrics = (
        env._phase21_v4_path_metrics(
            local_curve,
            original_length,
        )
    )

    reverse_count = _reverse_count(
        local_curve,
        original_segment,
    )

    known_violation = max(
        0.0,
        env.phase21_v4_min_known_margin
        - known_margin,
    )

    sensor_violation = max(
        0.0,
        env.phase21_v4_min_sensor_margin
        - sensor_margin,
    )

    curvature_violation = max(
        0.0,
        metrics["p95_curvature"]
        - env.phase21_v4_max_p95_curvature,
    )

    heading_violation = max(
        0.0,
        metrics["max_heading_delta"]
        - env.phase21_v4_max_heading_delta,
    )

    objective = (
        150.0
        * known_violation
        + 180.0
        * sensor_violation
        + 8.0
        * curvature_violation
        + 12.0
        * heading_violation
        + 30.0
        * reverse_count
        + 0.20
        * max(
            0.0,
            metrics["length_ratio"]
            - 1.0,
        )
    )

    feasible = bool(
        known_margin
        >= env.phase21_v4_min_known_margin
        and sensor_margin
        >= env.phase21_v4_min_sensor_margin
        and metrics[
            "p95_curvature"
        ]
        <= env.phase21_v4_max_p95_curvature
        and metrics[
            "max_heading_delta"
        ]
        <= env.phase21_v4_max_heading_delta
        and reverse_count == 0
    )

    preference_bonus = (
        0.05
        if side_sign
        == preferred_side
        else 0.0
    )

    score = (
        4.0
        * min(
            sensor_margin,
            0.50,
        )
        + 2.0
        * min(
            known_margin,
            0.50,
        )
        - 0.35
        * metrics[
            "p95_curvature"
        ]
        - 0.60
        * metrics[
            "max_heading_delta"
        ]
        - 0.30
        * max(
            0.0,
            metrics[
                "length_ratio"
            ]
            - 1.0,
        )
        - 0.04
        * offset
        + preference_bonus
    )

    return CorridorCandidate(
        active_path=active_path,
        local_curve=local_curve,
        approach_index=int(
            approach_index
        ),
        rejoin_index=int(
            rejoin_index
        ),
        side_sign=float(
            side_sign
        ),
        offset=float(offset),
        approach_distance=float(
            approach_distance
        ),
        rejoin_distance=float(
            rejoin_distance
        ),
        shoulder=float(shoulder),
        known_margin=known_margin,
        sensor_margin=sensor_margin,
        p95_curvature=float(
            metrics[
                "p95_curvature"
            ]
        ),
        max_heading_delta=float(
            metrics[
                "max_heading_delta"
            ]
        ),
        length_ratio=float(
            metrics[
                "length_ratio"
            ]
        ),
        reverse_count=int(
            reverse_count
        ),
        objective=float(
            objective
        ),
        score=float(score),
        feasible=feasible,
    )


def search_continuous_corridor(
    env: Any,
    original: np.ndarray,
    sensor_points: np.ndarray,
    conflict_points: np.ndarray,
    conflict_center: np.ndarray,
    conflict_index: int,
    preferred_side: float,
) -> tuple[
    CorridorCandidate | None,
    int,
]:
    tangent_start = max(
        0,
        conflict_index - 2,
    )

    tangent_end = min(
        len(original) - 1,
        conflict_index + 2,
    )

    tangent = (
        original[tangent_end]
        - original[tangent_start]
    )

    tangent_norm = float(
        np.linalg.norm(tangent)
    )

    if tangent_norm <= 1e-6:
        return None, 0

    tangent = (
        tangent
        / tangent_norm
    )

    normal = np.asarray(
        [
            -tangent[1],
            tangent[0],
        ],
        dtype=np.float32,
    )

    relative_points = (
        conflict_points
        - original[
            conflict_index
        ]
    )

    lateral = (
        relative_points
        @ normal
    )

    longitudinal = (
        relative_points
        @ tangent
    )

    clearance = (
        float(
            env.phase21_corridor_radius
        )
        + float(
            env.phase21_v4_min_sensor_margin
        )
        + 0.08
    )

    approach_base = float(
        np.clip(
            max(
                0.45,
                -float(
                    np.min(
                        longitudinal
                    )
                )
                + 0.75,
            ),
            0.35,
            2.60,
        )
    )

    rejoin_base = float(
        np.clip(
            max(
                1.10,
                float(
                    np.max(
                        longitudinal
                    )
                )
                + 1.35,
            ),
            1.00,
            5.00,
        )
    )

    best_feasible = None
    candidate_count = 0

    for side_sign in (
        preferred_side,
        -preferred_side,
    ):
        if side_sign > 0.0:
            required_offset = (
                float(
                    np.max(
                        lateral
                    )
                )
                + clearance
            )
        else:
            required_offset = -(
                float(
                    np.min(
                        lateral
                    )
                )
                - clearance
            )

        required_offset = float(
            np.clip(
                required_offset,
                0.22,
                1.80,
            )
        )

        for initial_scale in (
            1.00,
            1.15,
            1.30,
        ):
            for initial_shoulder in (
                0.55,
                0.75,
                0.92,
            ):
                parameters = np.asarray(
                    [
                        required_offset
                        * initial_scale,
                        approach_base,
                        rejoin_base,
                        initial_shoulder,
                    ],
                    dtype=np.float64,
                )

                bounds = (
                    (0.22, 1.80),
                    (0.35, 2.60),
                    (1.00, 5.00),
                    (0.40, 1.00),
                )

                base_steps = np.asarray(
                    [
                        0.22,
                        0.35,
                        0.55,
                        0.15,
                    ],
                    dtype=np.float64,
                )

                current = None

                for scale in (
                    1.0,
                    0.50,
                    0.25,
                    0.125,
                ):
                    trial_parameters = [
                        parameters.copy()
                    ]

                    for dimension in range(
                        len(parameters)
                    ):
                        for direction in (
                            -1.0,
                            1.0,
                        ):
                            trial = (
                                parameters.copy()
                            )

                            trial[
                                dimension
                            ] += (
                                direction
                                * base_steps[
                                    dimension
                                ]
                                * scale
                            )

                            lower, upper = (
                                bounds[
                                    dimension
                                ]
                            )

                            trial[
                                dimension
                            ] = np.clip(
                                trial[
                                    dimension
                                ],
                                lower,
                                upper,
                            )

                            trial_parameters.append(
                                trial
                            )

                    round_best = current

                    for trial in (
                        trial_parameters
                    ):
                        candidate_count += 1

                        candidate = (
                            _evaluate_candidate(
                                env=env,
                                original=original,
                                sensor_points=(
                                    sensor_points
                                ),
                                conflict_index=(
                                    conflict_index
                                ),
                                side_sign=(
                                    side_sign
                                ),
                                offset=float(
                                    trial[0]
                                ),
                                approach_distance=float(
                                    trial[1]
                                ),
                                rejoin_distance=float(
                                    trial[2]
                                ),
                                shoulder=float(
                                    trial[3]
                                ),
                                preferred_side=(
                                    preferred_side
                                ),
                            )
                        )

                        if candidate is None:
                            continue

                        if (
                            round_best is None
                            or candidate.objective
                            < round_best.objective
                            or (
                                candidate.objective
                                == round_best.objective
                                and candidate.score
                                > round_best.score
                            )
                        ):
                            round_best = (
                                candidate
                            )

                        if candidate.feasible:
                            if (
                                best_feasible
                                is None
                                or candidate.score
                                > best_feasible.score
                            ):
                                best_feasible = (
                                    candidate
                                )

                    if round_best is not None:
                        current = round_best

                        parameters = np.asarray(
                            [
                                current.offset,
                                current.approach_distance,
                                current.rejoin_distance,
                                current.shoulder,
                            ],
                            dtype=np.float64,
                        )

    return (
        best_feasible,
        candidate_count,
    )
