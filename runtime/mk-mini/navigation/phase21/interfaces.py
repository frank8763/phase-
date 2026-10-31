from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray


FloatArray = NDArray[np.float64]
ObstacleKind = Literal["circle", "rectangle"]
PlannerSide = Literal["LEFT", "RIGHT", "NONE"]


def _as_vector(
    value: Any,
    *,
    name: str,
    length: int,
) -> FloatArray:
    array = np.asarray(value, dtype=np.float64).reshape(-1)

    if array.shape != (length,):
        raise ValueError(
            f"{name} must have shape ({length},), "
            f"got {array.shape}"
        )

    return array.copy()


def _as_points(
    value: Any,
    *,
    name: str,
    allow_empty: bool = True,
) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)

    if array.size == 0 and allow_empty:
        return np.empty((0, 2), dtype=np.float64)

    if array.ndim != 2 or array.shape[1] != 2:
        raise ValueError(
            f"{name} must have shape (N, 2), "
            f"got {array.shape}"
        )

    return array.copy()


@dataclass(slots=True)
class KnownObstacle:
    """
    已知静态地图中的障碍物。

    circle:
        center = [x, y]
        radius > 0

    rectangle:
        center = [x, y]
        size = [length, width]
        yaw = 世界坐标系中的旋转角
    """

    kind: ObstacleKind
    center: FloatArray
    radius: float | None = None
    size: FloatArray | None = None
    yaw: float = 0.0
    obstacle_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.center = _as_vector(
            self.center,
            name="KnownObstacle.center",
            length=2,
        )

        self.yaw = float(self.yaw)

        if self.kind == "circle":
            if self.radius is None:
                raise ValueError(
                    "circle obstacle requires radius"
                )

            self.radius = float(self.radius)

            if self.radius <= 0.0:
                raise ValueError(
                    "circle radius must be positive"
                )

            self.size = None

        elif self.kind == "rectangle":
            if self.size is None:
                raise ValueError(
                    "rectangle obstacle requires size"
                )

            self.size = _as_vector(
                self.size,
                name="KnownObstacle.size",
                length=2,
            )

            if np.any(self.size <= 0.0):
                raise ValueError(
                    "rectangle size must be positive"
                )

            self.radius = None

        else:
            raise ValueError(
                f"unsupported obstacle kind: {self.kind}"
            )


@dataclass(slots=True)
class RiskState:
    """
    风险检测器输出。

    风险检测器只负责描述风险状态，
    不负责生成候选路径。
    """

    mode: str = "NORMAL"
    risk: float = 0.0
    triggered: bool = False
    corridor_conflict: bool = False
    conflict_count: int = 0
    min_path_clearance: float = float("inf")
    conflict_center: FloatArray | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.mode = str(self.mode)
        self.risk = float(self.risk)
        self.triggered = bool(self.triggered)
        self.corridor_conflict = bool(
            self.corridor_conflict
        )
        self.conflict_count = int(self.conflict_count)
        self.min_path_clearance = float(
            self.min_path_clearance
        )

        if self.conflict_center is not None:
            self.conflict_center = _as_vector(
                self.conflict_center,
                name="RiskState.conflict_center",
                length=2,
            )


@dataclass(slots=True)
class PlannerRequest:
    """
    独立局部规划器输入。

    该对象不能包含 MuJoCo env 对象，也不能依赖
    self.model、self.data 或仿真障碍真值。
    """

    original_path: FloatArray
    robot_pose: FloatArray
    sensor_points_world: FloatArray
    sensor_points_local: FloatArray
    known_obstacles: tuple[KnownObstacle, ...]
    risk_state: RiskState
    runtime_path: FloatArray | None = None

    # v4运行时控制参数。由环境适配层从当前env读取并传入。
    path_lookahead: float | None = None
    corridor_radius: float | None = None
    conflict_margin: float | None = None
    robot_radius: float = 0.28
    left_min_clearance: float = 0.0
    right_min_clearance: float = 0.0

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.original_path = _as_points(
            self.original_path,
            name="PlannerRequest.original_path",
            allow_empty=False,
        )

        self.robot_pose = _as_vector(
            self.robot_pose,
            name="PlannerRequest.robot_pose",
            length=3,
        )

        self.sensor_points_world = _as_points(
            self.sensor_points_world,
            name="PlannerRequest.sensor_points_world",
        )

        self.sensor_points_local = _as_points(
            self.sensor_points_local,
            name="PlannerRequest.sensor_points_local",
        )

        self.known_obstacles = tuple(
            self.known_obstacles
        )

        if not isinstance(self.risk_state, RiskState):
            raise TypeError(
                "risk_state must be a RiskState instance"
            )

        if self.runtime_path is not None:
            self.runtime_path = _as_points(
                self.runtime_path,
                name="PlannerRequest.runtime_path",
            )

        if self.path_lookahead is not None:
            self.path_lookahead = float(
                self.path_lookahead
            )
            if self.path_lookahead <= 0.0:
                raise ValueError(
                    "PlannerRequest.path_lookahead must be positive"
                )

        if self.corridor_radius is not None:
            self.corridor_radius = float(
                self.corridor_radius
            )
            if self.corridor_radius <= 0.0:
                raise ValueError(
                    "PlannerRequest.corridor_radius must be positive"
                )

        if self.conflict_margin is not None:
            self.conflict_margin = float(
                self.conflict_margin
            )
            if self.conflict_margin < 0.0:
                raise ValueError(
                    "PlannerRequest.conflict_margin cannot be negative"
                )

        self.robot_radius = float(
            self.robot_radius
        )
        if self.robot_radius <= 0.0:
            raise ValueError(
                "PlannerRequest.robot_radius must be positive"
            )

        self.left_min_clearance = float(
            self.left_min_clearance
        )
        self.right_min_clearance = float(
            self.right_min_clearance
        )


@dataclass(slots=True)
class PlannerResult:
    """
    独立局部规划器输出。
    """

    success: bool
    active_path: FloatArray
    chosen_side: PlannerSide = "NONE"
    candidate_family: str | None = None
    failure_reason: str | None = None

    known_margin: float = float("-inf")
    sensor_margin: float = float("-inf")
    p95_curvature: float = float("inf")
    max_heading_delta: float = float("inf")
    score: float = float("inf")

    candidate_count: int = 0
    feasible_count: int = 0

    approach_point: FloatArray | None = None
    detour_point: FloatArray | None = None
    rejoin_point: FloatArray | None = None

    diagnostics: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self.success = bool(self.success)

        self.active_path = _as_points(
            self.active_path,
            name="PlannerResult.active_path",
        )

        if self.chosen_side not in {
            "LEFT",
            "RIGHT",
            "NONE",
        }:
            raise ValueError(
                "chosen_side must be LEFT, RIGHT or NONE"
            )

        self.known_margin = float(self.known_margin)
        self.sensor_margin = float(self.sensor_margin)
        self.p95_curvature = float(
            self.p95_curvature
        )
        self.max_heading_delta = float(
            self.max_heading_delta
        )
        self.score = float(self.score)

        self.candidate_count = int(
            self.candidate_count
        )
        self.feasible_count = int(
            self.feasible_count
        )

        for field_name in (
            "approach_point",
            "detour_point",
            "rejoin_point",
        ):
            value = getattr(self, field_name)

            if value is not None:
                setattr(
                    self,
                    field_name,
                    _as_vector(
                        value,
                        name=f"PlannerResult.{field_name}",
                        length=2,
                    ),
                )

    @classmethod
    def failed(
        cls,
        *,
        original_path: FloatArray,
        reason: str,
        candidate_count: int = 0,
        feasible_count: int = 0,
        diagnostics: dict[str, Any] | None = None,
    ) -> "PlannerResult":
        return cls(
            success=False,
            active_path=original_path,
            chosen_side="NONE",
            failure_reason=str(reason),
            candidate_count=candidate_count,
            feasible_count=feasible_count,
            diagnostics=(
                {} if diagnostics is None
                else dict(diagnostics)
            ),
        )

    def as_info(self) -> dict[str, Any]:
        return {
            "planner_success": self.success,
            "planner_chosen_side": self.chosen_side,
            "planner_candidate_family":
                self.candidate_family,
            "planner_failure_reason":
                self.failure_reason,
            "planner_known_margin":
                self.known_margin,
            "planner_sensor_margin":
                self.sensor_margin,
            "planner_p95_curvature":
                self.p95_curvature,
            "planner_max_heading_delta":
                self.max_heading_delta,
            "planner_score": self.score,
            "planner_candidate_count":
                self.candidate_count,
            "planner_feasible_count":
                self.feasible_count,
        }


__all__ = [
    "FloatArray",
    "KnownObstacle",
    "PlannerRequest",
    "PlannerResult",
    "RiskState",
]
