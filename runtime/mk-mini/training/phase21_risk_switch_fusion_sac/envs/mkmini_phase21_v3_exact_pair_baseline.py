#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

import numpy as np

from training.phase20_unknown_obstacle_adaptation.scripts.run_phase20_overnight import (
    Phase20UnknownAdaptationEnv,
)

from training.phase21_risk_switch_fusion_sac.envs.mkmini_phase21_v2_corridor_detect_control_failed import (
    MkMiniPhase21RiskSwitchFusionSACEnv as Phase21V2CorridorEnv,
)


class MkMiniPhase21RiskSwitchFusionSACEnv(
    Phase21V2CorridorEnv
):
    """
    Phase21 v3：传感器驱动的风险触发局部参考路径替换。

    保留：
        Phase19未知障碍环境；
        Phase20奖励、碰撞判定和325k SAC；
        186维观测；
        2维残差动作；
        原全局A*路径；
        原稳定车辆控制器。

    新增：
        LiDAR/Depth路径走廊冲突检测；
        传感器障碍点聚类；
        无真值的局部绕行曲线；
        运行时路径持久化。

    禁止：
        使用phase19_unknown_circles参与控制；
        使用障碍圆心或半径真值；
        将325k残差策略强行改成直接控制器；
        在动作上层伪造停车。
    """

    def __init__(
        self,
        *,
        phase21_v3_enable_detour: bool = True,
        phase21_v3_trigger_risk: float = 0.18,
        phase21_v3_conflict_margin: float = 0.06,
        phase21_v3_detour_offset: float = 0.68,
        phase21_v3_approach_distance: float = 0.35,
        phase21_v3_rejoin_distance: float = 1.25,
        phase21_v3_curve_points: int = 50,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.phase21_v3_enable_detour = bool(
            phase21_v3_enable_detour
        )

        self.phase21_v3_trigger_risk = float(
            phase21_v3_trigger_risk
        )

        self.phase21_v3_conflict_margin = float(
            phase21_v3_conflict_margin
        )

        self.phase21_v3_detour_offset = float(
            phase21_v3_detour_offset
        )

        self.phase21_v3_approach_distance = float(
            phase21_v3_approach_distance
        )

        self.phase21_v3_rejoin_distance = float(
            phase21_v3_rejoin_distance
        )

        self.phase21_v3_curve_points = int(
            phase21_v3_curve_points
        )

        self.phase21_v3_original_path = None
        self.phase21_v3_active_path = None

        self.phase21_v3_detour_applied = False
        self.phase21_v3_apply_count = 0
        self.phase21_v3_runtime_path_count = 0

        self.phase21_v3_conflict_center = np.full(
            2,
            np.nan,
            dtype=np.float32,
        )

        self.phase21_v3_approach_point = np.full(
            2,
            np.nan,
            dtype=np.float32,
        )

        self.phase21_v3_detour_point = np.full(
            2,
            np.nan,
            dtype=np.float32,
        )

        self.phase21_v3_rejoin_point = np.full(
            2,
            np.nan,
            dtype=np.float32,
        )

        self.phase21_v3_chosen_side = "NONE"
        self.phase21_v3_failure_reason = "none"

        # 记录绕行触发前的原始风险，避免路径替换后风险归零
        # 导致无法证明触发条件实际成立。
        self.phase21_v3_trigger_risk_value = 0.0
        self.phase21_v3_trigger_conflict_count = 0
        self.phase21_v3_trigger_min_path_clearance = float("inf")

    # ------------------------------------------------------------------
    # 禁用v2动作层修改
    # ------------------------------------------------------------------

    def _base_action(
        self,
        raw_obs,
    ):
        """
        跳过v2的动作缩放和转向强行修正。

        恢复Phase20原始基础动作语义。
        """

        action = super(
            Phase21V2CorridorEnv,
            self,
        )._base_action(
            raw_obs
        )

        return np.clip(
            np.asarray(
                action,
                dtype=np.float32,
            ).reshape(2),
            -1.0,
            1.0,
        )

    # ------------------------------------------------------------------
    # 路径接口
    # ------------------------------------------------------------------

    def _phase21_v3_objects(
        self,
    ) -> list[Any]:
        objects = []
        queue = [self]
        seen = set()

        while queue and len(objects) < 30:
            obj = queue.pop(0)

            if obj is None:
                continue

            identity = id(obj)

            if identity in seen:
                continue

            seen.add(identity)
            objects.append(obj)

            for name in (
                "inner",
                "env",
                "base_env",
            ):
                try:
                    child = getattr(
                        obj,
                        name,
                        None,
                    )
                except Exception:
                    child = None

                if (
                    child is not None
                    and child is not obj
                ):
                    queue.append(child)

        return objects

    def _phase21_v3_read_path(
        self,
    ) -> np.ndarray:
        getter = getattr(
            self,
            "get_phase14_smooth_path",
            None,
        )

        if callable(getter):
            try:
                path = np.asarray(
                    getter(),
                    dtype=np.float32,
                )
            except Exception:
                path = None
        else:
            path = None

        if (
            path is None
            or path.ndim != 2
            or len(path) < 3
        ):
            try:
                path = np.asarray(
                    self.phase19_planned_path,
                    dtype=np.float32,
                )
            except Exception:
                path = np.empty(
                    (0, 2),
                    dtype=np.float32,
                )

        if (
            path.ndim != 2
            or path.shape[1] < 2
            or len(path) < 3
        ):
            return np.empty(
                (0, 2),
                dtype=np.float32,
            )

        return path[:, :2].copy()

    def _phase21_v3_apply_path(
        self,
        path: np.ndarray,
    ) -> int:
        path = np.asarray(
            path,
            dtype=np.float32,
        ).reshape(-1, 2)

        if len(path) < 3:
            return 0

        robot_xy = np.asarray(
            self.robot_xy,
            dtype=np.float32,
        ).reshape(2)

        nearest_index = int(
            np.argmin(
                np.linalg.norm(
                    path - robot_xy,
                    axis=1,
                )
            )
        )

        path_names = (
            "smooth_ref_path",
            "path_world",
            "dense_path",
            "raw_astar_path",
            "path_xy",
            "path",
            "smooth_path",
            "global_path",
            "planned_path",
            "phase19_planned_path",
        )

        index_names = (
            "path_idx",
            "target_idx",
            "current_wp_idx",
            "nearest_idx",
        )

        changed = 0

        for obj in self._phase21_v3_objects():
            object_changed = False

            for name in path_names:
                if not hasattr(obj, name):
                    continue

                try:
                    setattr(
                        obj,
                        name,
                        path.copy(),
                    )

                    object_changed = True
                except Exception:
                    pass

            for name in index_names:
                if not hasattr(obj, name):
                    continue

                try:
                    setattr(
                        obj,
                        name,
                        nearest_index,
                    )
                except Exception:
                    pass

            if hasattr(
                obj,
                "_last_v7_smooth_sig",
            ):
                try:
                    obj._last_v7_smooth_sig = None
                except Exception:
                    pass

            if object_changed:
                changed += 1

        self.phase21_v3_runtime_path_count = int(
            changed
        )

        return changed

    @staticmethod
    def _phase21_v3_index_before(
        path: np.ndarray,
        start_index: int,
        distance: float,
    ) -> int:
        index = int(start_index)
        travelled = 0.0

        while index > 0:
            segment = float(
                np.linalg.norm(
                    path[index]
                    - path[index - 1]
                )
            )

            travelled += segment
            index -= 1

            if travelled >= distance:
                break

        return index

    @staticmethod
    def _phase21_v3_index_after(
        path: np.ndarray,
        start_index: int,
        distance: float,
    ) -> int:
        index = int(start_index)
        travelled = 0.0

        while index < len(path) - 1:
            segment = float(
                np.linalg.norm(
                    path[index + 1]
                    - path[index]
                )
            )

            travelled += segment
            index += 1

            if travelled >= distance:
                break

        return index

    def _phase21_v3_build_detour(
        self,
    ) -> bool:
        original = self.phase21_v3_original_path

        if (
            original is None
            or len(original) < 6
        ):
            self.phase21_v3_failure_reason = (
                "invalid_original_path"
            )
            return False

        (
            sensor_world,
            sensor_local,
        ) = self._phase21_sensor_points()

        if len(sensor_world) == 0:
            self.phase21_v3_failure_reason = (
                "no_sensor_points"
            )
            return False

        robot_xy = np.asarray(
            self.robot_xy,
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
            self.phase21_v3_failure_reason = (
                "future_path_too_short"
            )
            return False

        distances = (
            self._phase21_point_segment_distances(
                sensor_world,
                future_path,
            )
        )

        candidate = (
            (sensor_local[:, 0] > 0.05)
            & (
                sensor_local[:, 0]
                <= self.phase21_path_lookahead
                + 0.40
            )
            & (
                distances
                < self.phase21_corridor_radius
                + self.phase21_v3_conflict_margin
            )
        )

        if not np.any(candidate):
            self.phase21_v3_failure_reason = (
                "no_corridor_sensor_cluster"
            )
            return False

        conflict_points = sensor_world[
            candidate
        ]

        conflict_center = np.median(
            conflict_points,
            axis=0,
        ).astype(np.float32)

        conflict_index = int(
            np.argmin(
                np.linalg.norm(
                    original
                    - conflict_center,
                    axis=1,
                )
            )
        )

        approach_index = (
            self._phase21_v3_index_before(
                original,
                conflict_index,
                self.phase21_v3_approach_distance,
            )
        )

        rejoin_index = (
            self._phase21_v3_index_after(
                original,
                conflict_index,
                self.phase21_v3_rejoin_distance,
            )
        )

        if (
            approach_index >= conflict_index
            or rejoin_index <= conflict_index
            or rejoin_index >= len(original)
        ):
            self.phase21_v3_failure_reason = (
                "invalid_detour_indices"
            )
            return False

        approach = original[
            approach_index
        ].copy()

        rejoin = original[
            rejoin_index
        ].copy()

        tangent = rejoin - approach
        tangent_norm = float(
            np.linalg.norm(tangent)
        )

        if tangent_norm < 1e-6:
            self.phase21_v3_failure_reason = (
                "invalid_path_tangent"
            )
            return False

        tangent /= tangent_norm

        left_normal = np.asarray(
            [
                -tangent[1],
                tangent[0],
            ],
            dtype=np.float32,
        )

        path_point = original[
            conflict_index
        ]

        obstacle_lateral = float(
            np.dot(
                conflict_center
                - path_point,
                left_normal,
            )
        )

        if obstacle_lateral > 0.03:
            # 障碍位于路径左侧，向路径右侧绕。
            detour_sign = -1.0
            chosen_side = "RIGHT"

        elif obstacle_lateral < -0.03:
            detour_sign = 1.0
            chosen_side = "LEFT"

        else:
            # 障碍接近路径中心，选择LiDAR更空的一侧。
            if (
                self.phase21_last_left_min
                > self.phase21_last_right_min
            ):
                detour_sign = 1.0
                chosen_side = "LEFT"
            else:
                detour_sign = -1.0
                chosen_side = "RIGHT"

        detour_point = (
            path_point
            + detour_sign
            * self.phase21_v3_detour_offset
            * left_normal
        ).astype(np.float32)

        # 二次Bezier曲线：
        # approach → detour point → rejoin
        t = np.linspace(
            0.0,
            1.0,
            self.phase21_v3_curve_points,
            dtype=np.float32,
        )

        curve = (
            (
                (1.0 - t) ** 2
            )[:, None]
            * approach[None, :]
            + (
                2.0
                * (1.0 - t)
                * t
            )[:, None]
            * detour_point[None, :]
            + (
                t ** 2
            )[:, None]
            * rejoin[None, :]
        ).astype(np.float32)

        prefix = original[
            :approach_index
        ]

        suffix = original[
            rejoin_index + 1:
        ]

        active_path = np.concatenate(
            [
                prefix,
                curve,
                suffix,
            ],
            axis=0,
        ).astype(np.float32)

        if len(active_path) < 6:
            self.phase21_v3_failure_reason = (
                "generated_path_too_short"
            )
            return False

        changed = self._phase21_v3_apply_path(
            active_path
        )

        if changed <= 0:
            self.phase21_v3_failure_reason = (
                "no_runtime_path_owner"
            )
            return False

        self.phase21_v3_active_path = (
            active_path.copy()
        )

        self.phase21_v3_conflict_center = (
            conflict_center.copy()
        )

        self.phase21_v3_approach_point = (
            approach.copy()
        )

        self.phase21_v3_detour_point = (
            detour_point.copy()
        )

        self.phase21_v3_rejoin_point = (
            rejoin.copy()
        )

        self.phase21_v3_chosen_side = (
            chosen_side
        )

        self.phase21_v3_detour_applied = True
        self.phase21_v3_apply_count += 1
        self.phase21_v3_failure_reason = "none"

        return True

    def _phase21_v3_fill_info(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        output = dict(info or {})

        output.update({
            "phase21_version":
                "v3_sensor_local_reference",
            "phase21_sensor_only_switch": True,
            "phase21_ground_truth_used_for_control": False,
            "phase21_control_layer":
                "local_reference_path",
            "phase21_v3_enable_detour":
                bool(
                    self.phase21_v3_enable_detour
                ),
            "phase21_sac_semantics":
                "phase20_residual_preserved",

            "phase21_corridor_risk":
                float(self.phase21_last_risk),
            "phase21_min_path_clearance":
                float(
                    self.phase21_last_min_path_clearance
                ),
            "phase21_conflict_point_count":
                int(
                    self.phase21_last_conflict_count
                ),

            "phase21_v3_detour_applied":
                bool(
                    self.phase21_v3_detour_applied
                ),
            "phase21_v3_apply_count":
                int(
                    self.phase21_v3_apply_count
                ),
            "phase21_v3_runtime_path_count":
                int(
                    self.phase21_v3_runtime_path_count
                ),
            "phase21_v3_chosen_side":
                str(
                    self.phase21_v3_chosen_side
                ),
            "phase21_v3_failure_reason":
                str(
                    self.phase21_v3_failure_reason
                ),

            "phase21_v3_trigger_risk":
                float(
                    self.phase21_v3_trigger_risk_value
                ),
            "phase21_v3_trigger_conflict_count":
                int(
                    self.phase21_v3_trigger_conflict_count
                ),
            "phase21_v3_trigger_min_path_clearance":
                float(
                    self.phase21_v3_trigger_min_path_clearance
                ),

            "phase21_v3_original_path_len":
                int(
                    0
                    if self.phase21_v3_original_path
                    is None
                    else len(
                        self.phase21_v3_original_path
                    )
                ),
            "phase21_v3_active_path_len":
                int(
                    0
                    if self.phase21_v3_active_path
                    is None
                    else len(
                        self.phase21_v3_active_path
                    )
                ),

            "phase21_v3_conflict_center":
                self.phase21_v3_conflict_center.copy(),
            "phase21_v3_approach_point":
                self.phase21_v3_approach_point.copy(),
            "phase21_v3_detour_point":
                self.phase21_v3_detour_point.copy(),
            "phase21_v3_rejoin_point":
                self.phase21_v3_rejoin_point.copy(),
        })

        return output

    # ------------------------------------------------------------------
    # Gym接口
    # ------------------------------------------------------------------

    def reset(
        self,
        *args,
        **kwargs,
    ):
        self.phase21_v3_original_path = None
        self.phase21_v3_active_path = None
        self.phase21_v3_detour_applied = False
        self.phase21_v3_apply_count = 0
        self.phase21_v3_runtime_path_count = 0
        self.phase21_v3_chosen_side = "NONE"
        self.phase21_v3_failure_reason = "none"

        self.phase21_v3_trigger_risk_value = 0.0
        self.phase21_v3_trigger_conflict_count = 0
        self.phase21_v3_trigger_min_path_clearance = float("inf")

        self.phase21_v3_conflict_center[:] = np.nan
        self.phase21_v3_approach_point[:] = np.nan
        self.phase21_v3_detour_point[:] = np.nan
        self.phase21_v3_rejoin_point[:] = np.nan

        # 直接运行Phase20 reset，跳过v2动作状态机。
        output = Phase20UnknownAdaptationEnv.reset(
            self,
            *args,
            **kwargs,
        )

        if (
            isinstance(output, tuple)
            and len(output) == 2
        ):
            observation, info = output
            tuple_api = True
        else:
            observation = output
            info = {}
            tuple_api = False

        self.phase21_v3_original_path = (
            self._phase21_v3_read_path()
        )

        self._phase21_compute_corridor_state()

        if (
            self.phase21_v3_enable_detour
            and self.phase21_last_risk
            >= self.phase21_v3_trigger_risk
        ):
            self.phase21_v3_trigger_risk_value = float(
                self.phase21_last_risk
            )
            self.phase21_v3_trigger_conflict_count = int(
                self.phase21_last_conflict_count
            )
            self.phase21_v3_trigger_min_path_clearance = float(
                self.phase21_last_min_path_clearance
            )

            applied = (
                self._phase21_v3_build_detour()
            )

            if applied:
                # 重新生成与新参考路径一致的初始观测。
                try:
                    observation = (
                        self._phase19_refresh_initial_observation(
                            observation
                        )
                    )
                except Exception:
                    pass

        info = self._phase21_v3_fill_info(
            info
        )

        if tuple_api:
            return observation, info

        return observation

    def step(
        self,
        action,
    ):
        self._phase21_compute_corridor_state()

        if (
            self.phase21_v3_enable_detour
            and not self.phase21_v3_detour_applied
            and self.phase21_last_risk
            >= self.phase21_v3_trigger_risk
        ):
            self.phase21_v3_trigger_risk_value = float(
                self.phase21_last_risk
            )
            self.phase21_v3_trigger_conflict_count = int(
                self.phase21_last_conflict_count
            )
            self.phase21_v3_trigger_min_path_clearance = float(
                self.phase21_last_min_path_clearance
            )

            self._phase21_v3_build_detour()

        # 某些旧层每步会重新平滑路径，因此每步重新写入活动路径。
        if (
            self.phase21_v3_detour_applied
            and self.phase21_v3_active_path
            is not None
        ):
            self._phase21_v3_apply_path(
                self.phase21_v3_active_path
            )

        # 恢复Phase20原残差范围。
        if hasattr(
            self,
            "phase14_assist_scale",
        ):
            self.phase14_assist_scale = float(
                self.phase21_original_assist_scale
            )

        # 直接使用Phase20控制链，跳过v2动作修改。
        output = Phase20UnknownAdaptationEnv.step(
            self,
            action,
        )

        if len(output) == 5:
            (
                observation,
                reward,
                terminated,
                truncated,
                info,
            ) = output

            api_type = 5
        else:
            (
                observation,
                reward,
                done,
                info,
            ) = output

            api_type = 4

        self._phase21_compute_corridor_state()

        info = self._phase21_v3_fill_info(
            info
        )

        if api_type == 5:
            return (
                observation,
                reward,
                terminated,
                truncated,
                info,
            )

        return (
            observation,
            reward,
            done,
            info,
        )
