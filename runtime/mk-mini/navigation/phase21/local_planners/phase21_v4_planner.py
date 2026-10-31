from __future__ import annotations

from typing import Any

import numpy as np

from navigation.phase21.interfaces import (
    PlannerRequest,
    PlannerResult,
)
from navigation.phase21.local_planners.phase21_v4_config import (
    Phase21V4Config,
)
from navigation.phase21.local_planners.phase21_v4_geometry import (
    index_after,
    index_before,
    known_margin,
    make_candidate,
    path_metrics,
    point_segment_distances,
)


class Phase21V4Planner:
    """
    Independent Phase21 v4 local planner.

    This class has no dependency on MuJoCo, Gymnasium, SAC, env.model,
    env.data, or runtime path owners.
    """

    def __init__(
        self,
        config: Phase21V4Config | None = None,
    ) -> None:
        self.config = (
            Phase21V4Config()
            if config is None
            else config
        )

    @staticmethod
    def _failure(
        request: PlannerRequest,
        reason: str,
        *,
        candidate_count: int = 0,
        feasible_count: int = 0,
        diagnostics: dict[str, Any] | None = None,
    ) -> PlannerResult:
        return PlannerResult.failed(
            original_path=request.original_path,
            reason=reason,
            candidate_count=candidate_count,
            feasible_count=feasible_count,
            diagnostics=diagnostics,
        )

    def plan(
        self,
        request: PlannerRequest,
    ) -> PlannerResult:
        original = np.asarray(
            request.original_path,
            dtype=np.float32,
        ).reshape(-1, 2)

        if len(original) < 6:
            return self._failure(
                request,
                "invalid_original_path",
            )

        sensor_world = np.asarray(
            request.sensor_points_world,
            dtype=np.float32,
        ).reshape(-1, 2)

        sensor_local = np.asarray(
            request.sensor_points_local,
            dtype=np.float32,
        ).reshape(-1, 2)

        if len(sensor_world) == 0:
            return self._failure(
                request,
                "no_sensor_points",
            )

        if len(sensor_world) != len(sensor_local):
            return self._failure(
                request,
                "sensor_point_count_mismatch",
                diagnostics={
                    "sensor_world_count": len(sensor_world),
                    "sensor_local_count": len(sensor_local),
                },
            )

        missing_parameters = [
            name
            for name in (
                "path_lookahead",
                "corridor_radius",
                "conflict_margin",
            )
            if getattr(request, name, None) is None
        ]

        if missing_parameters:
            return self._failure(
                request,
                "missing_runtime_parameter",
                diagnostics={
                    "missing_parameters": missing_parameters,
                },
            )

        path_lookahead = float(request.path_lookahead)
        corridor_radius = float(request.corridor_radius)
        conflict_margin = float(request.conflict_margin)
        robot_radius = float(request.robot_radius)

        robot_xy = np.asarray(
            request.robot_pose[:2],
            dtype=np.float32,
        ).reshape(2)

        nearest_robot_index = int(
            np.argmin(
                np.linalg.norm(
                    original - robot_xy,
                    axis=1,
                )
            )
        )

        future_path = original[
            nearest_robot_index:
        ]

        if len(future_path) < 3:
            return self._failure(
                request,
                "future_path_too_short",
                diagnostics={
                    "nearest_robot_index":
                        nearest_robot_index,
                },
            )

        sensor_path_distance = (
            point_segment_distances(
                sensor_world,
                future_path,
            )
        )

        conflict_mask = (
            (sensor_local[:, 0] > 0.05)
            & (
                sensor_local[:, 0]
                <= path_lookahead + 0.50
            )
            & (
                sensor_path_distance
                < corridor_radius
                + conflict_margin
            )
        )

        if not np.any(conflict_mask):
            return self._failure(
                request,
                "no_corridor_sensor_cluster",
                diagnostics={
                    "nearest_robot_index":
                        nearest_robot_index,
                    "minimum_sensor_path_distance":
                        float(
                            np.min(sensor_path_distance)
                        ),
                },
            )

        conflict_points = sensor_world[
            conflict_mask
        ]

        conflict_center = np.median(
            conflict_points,
            axis=0,
        ).astype(np.float32)

        conflict_index = int(
            np.argmin(
                np.linalg.norm(
                    original - conflict_center,
                    axis=1,
                )
            )
        )

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

        common_diagnostics: dict[str, Any] = {
            "nearest_robot_index":
                nearest_robot_index,
            "conflict_index":
                conflict_index,
            "conflict_count":
                int(np.count_nonzero(conflict_mask)),
            "conflict_center":
                conflict_center.tolist(),
        }

        if tangent_norm < 1e-6:
            return self._failure(
                request,
                "invalid_path_tangent",
                diagnostics=common_diagnostics,
            )

        tangent = tangent / tangent_norm

        left_normal = np.asarray(
            [
                -tangent[1],
                tangent[0],
            ],
            dtype=np.float32,
        )

        obstacle_lateral = float(
            np.dot(
                conflict_center
                - original[conflict_index],
                left_normal,
            )
        )

        if obstacle_lateral > 0.03:
            preferred_side = -1.0
        elif obstacle_lateral < -0.03:
            preferred_side = 1.0
        elif (
            float(request.left_min_clearance)
            > float(request.right_min_clearance)
        ):
            preferred_side = 1.0
        else:
            preferred_side = -1.0

        side_values = (
            preferred_side,
            -preferred_side,
        )

        best: dict[str, Any] | None = None
        candidate_count = 0
        feasible_count = 0

        for approach_distance in (
            self.config.approach_distances
        ):
            approach_index = index_before(
                original,
                conflict_index,
                approach_distance,
            )

            for rejoin_distance in (
                self.config.rejoin_distances
            ):
                rejoin_index = index_after(
                    original,
                    conflict_index,
                    rejoin_distance,
                )

                if (
                    approach_index >= conflict_index
                    or rejoin_index <= conflict_index
                    or rejoin_index >= len(original)
                ):
                    continue

                original_segment = original[
                    approach_index:
                    rejoin_index + 1
                ]

                original_segment_length = float(
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

                for side_sign in side_values:
                    for offset in self.config.offsets:
                        candidate_count += 1

                        try:
                            (
                                shifted_segment,
                                active_path,
                            ) = make_candidate(
                                original,
                                approach_index,
                                rejoin_index,
                                offset,
                                side_sign,
                            )
                        except Exception:
                            continue

                        candidate_known_margin = (
                            known_margin(
                                active_path,
                                request.known_obstacles,
                                robot_radius,
                            )
                        )

                        sensor_distance = (
                            point_segment_distances(
                                conflict_points,
                                shifted_segment,
                            )
                        )

                        candidate_sensor_margin = float(
                            np.min(sensor_distance)
                            - corridor_radius
                        )

                        metrics = path_metrics(
                            shifted_segment,
                            original_segment_length,
                        )

                        feasible = bool(
                            candidate_known_margin
                            >= self.config.min_known_margin
                            and candidate_sensor_margin
                            >= self.config.min_sensor_margin
                            and metrics["p95_curvature"]
                            <= self.config.max_p95_curvature
                            and metrics["max_heading_delta"]
                            <= self.config.max_heading_delta
                        )

                        if not feasible:
                            continue

                        feasible_count += 1

                        preference_bonus = (
                            0.05
                            if side_sign
                            == preferred_side
                            else 0.0
                        )

                        score = (
                            4.0
                            * min(
                                candidate_sensor_margin,
                                0.50,
                            )
                            + 2.0
                            * min(
                                candidate_known_margin,
                                0.50,
                            )
                            - 0.35
                            * metrics["p95_curvature"]
                            - 0.60
                            * metrics["max_heading_delta"]
                            - 0.30
                            * max(
                                0.0,
                                metrics["length_ratio"] - 1.0,
                            )
                            - 0.05 * offset
                            + preference_bonus
                        )

                        candidate = {
                            "score": float(score),
                            "active_path": active_path,
                            "known_margin": float(
                                candidate_known_margin
                            ),
                            "sensor_margin": float(
                                candidate_sensor_margin
                            ),
                            "p95_curvature": float(
                                metrics["p95_curvature"]
                            ),
                            "max_heading_delta": float(
                                metrics["max_heading_delta"]
                            ),
                            "length_ratio": float(
                                metrics["length_ratio"]
                            ),
                            "offset": float(offset),
                            "approach_distance": float(
                                approach_distance
                            ),
                            "rejoin_distance": float(
                                rejoin_distance
                            ),
                            "side_sign": float(side_sign),
                            "approach_point": original[
                                approach_index
                            ].copy(),
                            "detour_point": shifted_segment[
                                len(shifted_segment) // 2
                            ].copy(),
                            "rejoin_point": original[
                                rejoin_index
                            ].copy(),
                        }

                        if (
                            best is None
                            or candidate["score"]
                            > best["score"]
                        ):
                            best = candidate

        if best is None:
            diagnostics = dict(common_diagnostics)
            diagnostics.update({
                "obstacle_lateral":
                    obstacle_lateral,
                "preferred_side":
                    (
                        "LEFT"
                        if preferred_side > 0.0
                        else "RIGHT"
                    ),
            })

            return self._failure(
                request,
                "no_feasible_candidate",
                candidate_count=candidate_count,
                feasible_count=feasible_count,
                diagnostics=diagnostics,
            )

        chosen_side = (
            "LEFT"
            if best["side_sign"] > 0.0
            else "RIGHT"
        )

        diagnostics = dict(common_diagnostics)
        diagnostics.update({
            "obstacle_lateral":
                obstacle_lateral,
            "preferred_side":
                (
                    "LEFT"
                    if preferred_side > 0.0
                    else "RIGHT"
                ),
            "length_ratio":
                best["length_ratio"],
            "offset":
                best["offset"],
            "approach_distance":
                best["approach_distance"],
            "rejoin_distance":
                best["rejoin_distance"],
        })

        return PlannerResult(
            success=True,
            active_path=best["active_path"],
            chosen_side=chosen_side,
            candidate_family=(
                "phase21_v4_sine_squared_offset"
            ),
            failure_reason=None,
            known_margin=best["known_margin"],
            sensor_margin=best["sensor_margin"],
            p95_curvature=best["p95_curvature"],
            max_heading_delta=(
                best["max_heading_delta"]
            ),
            score=best["score"],
            candidate_count=candidate_count,
            feasible_count=feasible_count,
            approach_point=best["approach_point"],
            detour_point=best["detour_point"],
            rejoin_point=best["rejoin_point"],
            diagnostics=diagnostics,
        )


__all__ = ["Phase21V4Planner"]
