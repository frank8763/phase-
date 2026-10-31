from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from navigation.phase21.interfaces import (
    KnownObstacle,
    PlannerRequest,
    PlannerResult,
    RiskState,
)
from navigation.phase21.local_planners.phase21_v4_config import (
    Phase21V4Config,
)
from navigation.phase21.local_planners.phase21_v4_fallback_planner import (
    Phase21V4FallbackPlanner,
)
from navigation.phase21.local_planners.phase21_v4_safe_detour import (
    MkMiniPhase21RiskSwitchFusionSACEnv as FormalPhase21V4Env,
)


@dataclass(slots=True)
class ShadowComparison:
    match: bool
    mismatches: tuple[str, ...]
    path_max_abs_error: float = 0.0
    outcome: str = "unknown"

    def as_info(self) -> dict[str, Any]:
        return {
            "phase21_v4_shadow_match":
                bool(self.match),
            "phase21_v4_shadow_mismatches":
                list(self.mismatches),
            "phase21_v4_shadow_path_max_abs_error":
                float(
                    self.path_max_abs_error
                ),
            "phase21_v4_shadow_outcome":
                str(self.outcome),
        }


def known_obstacles_from_v4_arrays(
    rectangles: np.ndarray,
    circles: np.ndarray,
) -> tuple[KnownObstacle, ...]:
    """
    Convert the formal v4 obstacle arrays to the independent interface.

    Formal v4 rectangle rows are:
        [center_x, center_y, half_x, half_y]

    KnownObstacle.rectangle expects full:
        [length, width]
    """
    rectangles = np.asarray(
        rectangles,
        dtype=np.float32,
    ).reshape(-1, 4)

    circles = np.asarray(
        circles,
        dtype=np.float32,
    ).reshape(-1, 3)

    obstacles: list[KnownObstacle] = []

    for index, row in enumerate(rectangles):
        obstacles.append(
            KnownObstacle(
                kind="rectangle",
                center=row[:2].astype(
                    np.float64
                ),
                size=(
                    2.0 * row[2:4]
                ).astype(np.float64),
                yaw=0.0,
                obstacle_id=f"v4_rect_{index}",
            )
        )

    for index, row in enumerate(circles):
        obstacles.append(
            KnownObstacle(
                kind="circle",
                center=row[:2].astype(
                    np.float64
                ),
                radius=float(row[2]),
                obstacle_id=f"v4_circle_{index}",
            )
        )

    return tuple(obstacles)


def phase21_v4_config_from_env(
    env: Any,
) -> Phase21V4Config:
    return Phase21V4Config(
        offsets=tuple(
            float(value)
            for value in env.phase21_v4_offsets
        ),
        approach_distances=tuple(
            float(value)
            for value in (
                env.phase21_v4_approach_distances
            )
        ),
        rejoin_distances=tuple(
            float(value)
            for value in (
                env.phase21_v4_rejoin_distances
            )
        ),
        min_known_margin=float(
            env.phase21_v4_min_known_margin
        ),
        min_sensor_margin=float(
            env.phase21_v4_min_sensor_margin
        ),
        max_p95_curvature=float(
            env.phase21_v4_max_p95_curvature
        ),
        max_heading_delta=float(
            env.phase21_v4_max_heading_delta
        ),
    )


def build_planner_request_from_env(
    env: Any,
) -> PlannerRequest:
    """
    Build a pure-planner request from the formal runtime environment.

    This is the environment adapter boundary. It is allowed to read env
    state, but the returned PlannerRequest contains no env/model/data.
    """
    original_path = getattr(
        env,
        "phase21_v3_original_path",
        None,
    )

    if original_path is None:
        raise ValueError(
            "phase21_v3_original_path is None"
        )

    sensor_world, sensor_local = (
        env._phase21_sensor_points()
    )

    rectangles, circles = (
        env._phase21_v4_known_map_obstacles()
    )

    robot_xy = np.asarray(
        env.robot_xy,
        dtype=np.float64,
    ).reshape(2)

    robot_yaw = float(
        getattr(
            env,
            "robot_yaw",
            0.0,
        )
    )

    active_path = getattr(
        env,
        "phase21_v3_active_path",
        None,
    )

    risk_state = RiskState(
        mode=str(
            getattr(
                env,
                "phase21_mode",
                "UNKNOWN",
            )
        ),
        risk=float(
            getattr(
                env,
                "phase21_risk",
                0.0,
            )
        ),
        triggered=bool(
            getattr(
                env,
                "phase21_triggered",
                False,
            )
        ),
        corridor_conflict=bool(
            getattr(
                env,
                "phase21_corridor_conflict",
                False,
            )
        ),
        conflict_count=int(
            getattr(
                env,
                "phase21_conflict_count",
                0,
            )
        ),
        min_path_clearance=float(
            getattr(
                env,
                "phase21_min_path_clearance",
                float("inf"),
            )
        ),
    )

    return PlannerRequest(
        original_path=np.asarray(
            original_path,
            dtype=np.float64,
        ).reshape(-1, 2),
        robot_pose=np.asarray(
            [
                robot_xy[0],
                robot_xy[1],
                robot_yaw,
            ],
            dtype=np.float64,
        ),
        sensor_points_world=np.asarray(
            sensor_world,
            dtype=np.float64,
        ).reshape(-1, 2),
        sensor_points_local=np.asarray(
            sensor_local,
            dtype=np.float64,
        ).reshape(-1, 2),
        known_obstacles=(
            known_obstacles_from_v4_arrays(
                rectangles,
                circles,
            )
        ),
        risk_state=risk_state,
        runtime_path=(
            None
            if active_path is None
            else np.asarray(
                active_path,
                dtype=np.float64,
            ).reshape(-1, 2)
        ),
        path_lookahead=float(
            env.phase21_path_lookahead
        ),
        corridor_radius=float(
            env.phase21_corridor_radius
        ),
        conflict_margin=float(
            env.phase21_v3_conflict_margin
        ),
        robot_radius=float(
            getattr(
                env,
                "robot_radius",
                0.28,
            )
        ),
        left_min_clearance=float(
            getattr(
                env,
                "phase21_last_left_min",
                0.0,
            )
        ),
        right_min_clearance=float(
            getattr(
                env,
                "phase21_last_right_min",
                0.0,
            )
        ),
    )


def _normalize_failure_reason(
    value: Any,
) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()

    if normalized.lower() in {
        "",
        "none",
        "null",
        "success",
    }:
        return None

    return normalized


def compare_shadow_result(
    env: Any,
    shadow_result: PlannerResult,
    old_success: bool,
    *,
    path_atol: float = 1e-5,
    metric_atol: float = 1e-5,
) -> ShadowComparison:
    """
    Compare formal v4 control with the fallback shadow planner.

    Expected improvement:
        formal v4 fails with no_feasible_candidate
        and shadow Hermite fallback succeeds.

    That case is not a mismatch.
    """
    mismatches: list[str] = []
    path_max_abs_error = 0.0

    route = str(
        shadow_result.diagnostics.get(
            "planner_route",
            "unknown",
        )
    )

    old_candidate_count = int(
        getattr(
            env,
            "phase21_v4_candidate_count",
            0,
        )
    )

    old_feasible_count = int(
        getattr(
            env,
            "phase21_v4_feasible_count",
            0,
        )
    )

    primary_candidate_count = int(
        shadow_result.diagnostics.get(
            "primary_candidate_count",
            shadow_result.candidate_count,
        )
    )

    primary_feasible_count = int(
        shadow_result.diagnostics.get(
            "primary_feasible_count",
            shadow_result.feasible_count,
        )
    )

    def compare_primary_counts() -> None:
        if (
            primary_candidate_count
            != old_candidate_count
        ):
            mismatches.append(
                "primary_candidate_count"
            )

        if (
            primary_feasible_count
            != old_feasible_count
        ):
            mismatches.append(
                "primary_feasible_count"
            )

    old_reason = _normalize_failure_reason(
        getattr(
            env,
            "phase21_v3_failure_reason",
            None,
        )
    )

    primary_reason = _normalize_failure_reason(
        shadow_result.diagnostics.get(
            "primary_failure_reason",
            shadow_result.failure_reason,
        )
    )

    if old_success:
        if not shadow_result.success:
            mismatches.append(
                "success_regressed"
            )

            return ShadowComparison(
                match=False,
                mismatches=tuple(mismatches),
                outcome="regression",
            )

        if route != "primary_success":
            mismatches.append(
                "fallback_used_on_formal_success"
            )

            return ShadowComparison(
                match=False,
                mismatches=tuple(mismatches),
                outcome="regression",
            )

        compare_primary_counts()

        old_side = str(
            getattr(
                env,
                "phase21_v3_chosen_side",
                "NONE",
            )
        )

        if shadow_result.chosen_side != old_side:
            mismatches.append(
                "chosen_side"
            )

        old_path = np.asarray(
            getattr(
                env,
                "phase21_v3_active_path",
                np.empty((0, 2)),
            ),
            dtype=np.float32,
        ).reshape(-1, 2)

        new_path = np.asarray(
            shadow_result.active_path,
            dtype=np.float32,
        ).reshape(-1, 2)

        if old_path.shape != new_path.shape:
            mismatches.append(
                "active_path_shape"
            )

        elif old_path.size:
            path_max_abs_error = float(
                np.max(
                    np.abs(
                        old_path - new_path
                    )
                )
            )

            if not np.allclose(
                old_path,
                new_path,
                rtol=0.0,
                atol=float(path_atol),
            ):
                mismatches.append(
                    "active_path_values"
                )

        metric_pairs = (
            (
                "score",
                shadow_result.score,
                "phase21_v4_selected_score",
            ),
            (
                "known_margin",
                shadow_result.known_margin,
                "phase21_v4_selected_known_margin",
            ),
            (
                "sensor_margin",
                shadow_result.sensor_margin,
                "phase21_v4_selected_sensor_margin",
            ),
            (
                "p95_curvature",
                shadow_result.p95_curvature,
                "phase21_v4_selected_p95_curvature",
            ),
            (
                "max_heading_delta",
                shadow_result.max_heading_delta,
                "phase21_v4_selected_max_heading_delta",
            ),
        )

        for (
            label,
            new_value,
            old_attribute,
        ) in metric_pairs:
            old_value = float(
                getattr(
                    env,
                    old_attribute,
                    float("nan"),
                )
            )

            if not np.isclose(
                float(new_value),
                old_value,
                rtol=0.0,
                atol=float(metric_atol),
                equal_nan=True,
            ):
                mismatches.append(label)

        return ShadowComparison(
            match=not mismatches,
            mismatches=tuple(mismatches),
            path_max_abs_error=(
                path_max_abs_error
            ),
            outcome=(
                "primary_preserved"
                if not mismatches
                else "primary_mismatch"
            ),
        )

    if shadow_result.success:
        if route != "fallback_success":
            mismatches.append(
                "unexpected_primary_success"
            )

            return ShadowComparison(
                match=False,
                mismatches=tuple(mismatches),
                outcome="primary_mismatch",
            )

        compare_primary_counts()

        if old_reason != primary_reason:
            mismatches.append(
                "primary_failure_reason"
            )

        return ShadowComparison(
            match=not mismatches,
            mismatches=tuple(mismatches),
            outcome=(
                "fallback_improved"
                if not mismatches
                else "primary_mismatch"
            ),
        )

    compare_primary_counts()

    if old_reason != primary_reason:
        mismatches.append(
            "primary_failure_reason"
        )

    return ShadowComparison(
        match=not mismatches,
        mismatches=tuple(mismatches),
        outcome=(
            "fallback_not_improved"
            if not mismatches
            else "primary_mismatch"
        ),
    )


class MkMiniPhase21V4ShadowCompareEnv(
    FormalPhase21V4Env
):
    """
    Shadow validation environment.

    Runtime control remains entirely with the formal v4 implementation.
    The independent planner runs on the same inputs only for comparison.
    """

    def __init__(
        self,
        *,
        phase21_v4_shadow_strict: bool = False,
        phase21_v4_shadow_path_atol: float = 1e-5,
        phase21_v4_shadow_metric_atol: float = 1e-5,
        **kwargs: Any,
    ) -> None:
        self.phase21_v4_shadow_strict = bool(
            phase21_v4_shadow_strict
        )
        self.phase21_v4_shadow_path_atol = float(
            phase21_v4_shadow_path_atol
        )
        self.phase21_v4_shadow_metric_atol = float(
            phase21_v4_shadow_metric_atol
        )

        self.phase21_v4_shadow_compare_count = 0
        self.phase21_v4_shadow_mismatch_count = 0
        self.phase21_v4_shadow_exception_count = 0
        self.phase21_v4_shadow_improvement_count = 0
        self.phase21_v4_shadow_neutral_count = 0
        self.phase21_v4_shadow_regression_count = 0
        self.phase21_v4_shadow_last_match = True
        self.phase21_v4_shadow_last_mismatches: tuple[
            str,
            ...,
        ] = ()
        self.phase21_v4_shadow_last_path_max_abs_error = (
            0.0
        )
        self.phase21_v4_shadow_last_exception = "none"
        self.phase21_v4_shadow_last_outcome = "none"
        self.phase21_v4_shadow_last_result: (
            PlannerResult | None
        ) = None

        super().__init__(**kwargs)

        self._phase21_v4_shadow_planner = (
            Phase21V4FallbackPlanner(
                phase21_v4_config_from_env(self)
            )
        )

    def _phase21_v3_build_detour(
        self,
    ) -> bool:
        shadow_result: PlannerResult | None = None
        shadow_exception: Exception | None = None

        try:
            request = build_planner_request_from_env(
                self
            )

            shadow_result = (
                self._phase21_v4_shadow_planner.plan(
                    request
                )
            )

        except Exception as exc:
            shadow_exception = exc

        # Formal v4 remains the only implementation that can mutate
        # runtime paths or influence vehicle control.
        old_success = bool(
            super()._phase21_v3_build_detour()
        )

        self.phase21_v4_shadow_compare_count += 1

        if shadow_exception is not None:
            self.phase21_v4_shadow_exception_count += 1
            self.phase21_v4_shadow_mismatch_count += 1
            self.phase21_v4_shadow_last_match = False
            self.phase21_v4_shadow_last_mismatches = (
                "shadow_exception",
            )
            self.phase21_v4_shadow_last_path_max_abs_error = (
                0.0
            )
            self.phase21_v4_shadow_last_exception = (
                f"{type(shadow_exception).__name__}: "
                f"{shadow_exception}"
            )
            self.phase21_v4_shadow_last_outcome = (
                "shadow_exception"
            )
            self.phase21_v4_shadow_last_result = None

            if self.phase21_v4_shadow_strict:
                raise RuntimeError(
                    "Phase21 v4 shadow planner failed"
                ) from shadow_exception

            return old_success

        assert shadow_result is not None

        comparison = compare_shadow_result(
            self,
            shadow_result,
            old_success,
            path_atol=(
                self.phase21_v4_shadow_path_atol
            ),
            metric_atol=(
                self.phase21_v4_shadow_metric_atol
            ),
        )

        self.phase21_v4_shadow_last_result = (
            shadow_result
        )
        self.phase21_v4_shadow_last_match = (
            comparison.match
        )
        self.phase21_v4_shadow_last_mismatches = (
            comparison.mismatches
        )
        self.phase21_v4_shadow_last_path_max_abs_error = (
            comparison.path_max_abs_error
        )
        self.phase21_v4_shadow_last_exception = "none"
        self.phase21_v4_shadow_last_outcome = (
            comparison.outcome
        )

        if comparison.outcome == "fallback_improved":
            self.phase21_v4_shadow_improvement_count += 1

        elif comparison.outcome == "fallback_not_improved":
            self.phase21_v4_shadow_neutral_count += 1

        elif not comparison.match:
            self.phase21_v4_shadow_regression_count += 1

        if not comparison.match:
            self.phase21_v4_shadow_mismatch_count += 1

            if self.phase21_v4_shadow_strict:
                raise AssertionError(
                    "Phase21 v4 shadow mismatch: "
                    + ", ".join(
                        comparison.mismatches
                    )
                )

        return old_success

    def _phase21_v3_fill_info(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        info = super()._phase21_v3_fill_info(
            info
        )

        info.update({
            "phase21_v4_shadow_compare_count":
                int(
                    self.phase21_v4_shadow_compare_count
                ),
            "phase21_v4_shadow_mismatch_count":
                int(
                    self.phase21_v4_shadow_mismatch_count
                ),
            "phase21_v4_shadow_exception_count":
                int(
                    self.phase21_v4_shadow_exception_count
                ),
            "phase21_v4_shadow_improvement_count":
                int(
                    self.phase21_v4_shadow_improvement_count
                ),
            "phase21_v4_shadow_neutral_count":
                int(
                    self.phase21_v4_shadow_neutral_count
                ),
            "phase21_v4_shadow_regression_count":
                int(
                    self.phase21_v4_shadow_regression_count
                ),
            "phase21_v4_shadow_last_outcome":
                str(
                    self.phase21_v4_shadow_last_outcome
                ),
            "phase21_v4_shadow_last_candidate_family":
                (
                    None
                    if self.phase21_v4_shadow_last_result
                    is None
                    else self.phase21_v4_shadow_last_result
                    .candidate_family
                ),
            "phase21_v4_shadow_last_planner_route":
                (
                    None
                    if self.phase21_v4_shadow_last_result
                    is None
                    else self.phase21_v4_shadow_last_result
                    .diagnostics.get(
                        "planner_route"
                    )
                ),
            "phase21_v4_shadow_last_match":
                bool(
                    self.phase21_v4_shadow_last_match
                ),
            "phase21_v4_shadow_last_mismatches":
                list(
                    self.phase21_v4_shadow_last_mismatches
                ),
            "phase21_v4_shadow_last_path_max_abs_error":
                float(
                    self.phase21_v4_shadow_last_path_max_abs_error
                ),
            "phase21_v4_shadow_last_exception":
                str(
                    self.phase21_v4_shadow_last_exception
                ),
        })

        return info


__all__ = [
    "MkMiniPhase21V4ShadowCompareEnv",
    "ShadowComparison",
    "build_planner_request_from_env",
    "compare_shadow_result",
    "known_obstacles_from_v4_arrays",
    "phase21_v4_config_from_env",
]
