#!/usr/bin/env python3
from __future__ import annotations

import math
from typing import Any

import numpy as np

from training.phase20_unknown_obstacle_adaptation.scripts.run_phase20_overnight import (
    Phase20UnknownAdaptationEnv,
)


class MkMiniPhase21RiskSwitchFusionSACEnv(
    Phase20UnknownAdaptationEnv
):
    """
    Phase21 v2：

    1. 使用运行时LiDAR和Depth生成障碍点云；
    2. 检测障碍点是否侵入未来A*路径走廊；
    3. 不读取未知障碍真实坐标参与控制；
    4. TRACK模式完全保留Phase20原控制语义；
    5. 风险模式只修正基础转向、降低基础速度并渐进释放SAC残差；
    6. 修复旧Safety Shield的LiDAR方向和动作通道问题。

    动作语义：
        action[0] = steer
        action[1] = speed
    """

    MODE_TRACK = "TRACK"
    MODE_ASSIST = "ASSIST"
    MODE_AVOID = "AVOID"

    def __init__(
        self,
        *,
        phase21_path_lookahead: float = 2.20,
        phase21_corridor_margin: float = 0.08,
        phase21_risk_depth: float = 0.18,
        phase21_assist_enter_risk: float = 0.18,
        phase21_avoid_enter_risk: float = 0.45,
        phase21_avoid_exit_risk: float = 0.28,
        phase21_track_exit_risk: float = 0.10,
        phase21_clear_hold_steps: int = 5,
        phase21_assist_steer_gain: float = 0.26,
        phase21_avoid_steer_gain: float = 0.58,
        phase21_assist_min_speed_scale: float = 0.55,
        phase21_avoid_min_speed_scale: float = 0.25,
        phase21_assist_action_scale: float = 0.23,
        phase21_avoid_action_scale: float = 0.32,
        **kwargs: Any,
    ) -> None:
        # super().__init__之前先建立默认状态，
        # 防止父环境初始化过程中调用_base_action。
        self.phase21_mode = self.MODE_TRACK
        self.phase21_previous_mode = self.MODE_TRACK
        self.phase21_clear_counter = 0
        self.phase21_mode_switch_count = 0

        self.phase21_last_risk = 0.0
        self.phase21_last_min_path_clearance = float("inf")
        self.phase21_last_nearest_forward = float("inf")
        self.phase21_last_conflict_count = 0
        self.phase21_last_obstacle_side = "NONE"
        self.phase21_last_steer_direction = 0.0
        self.phase21_last_front_min = 1.0
        self.phase21_last_left_min = 1.0
        self.phase21_last_right_min = 1.0

        self.phase21_original_assist_scale = 0.15

        self.phase21_path_lookahead = float(
            phase21_path_lookahead
        )
        self.phase21_corridor_margin = float(
            phase21_corridor_margin
        )
        self.phase21_risk_depth = float(
            phase21_risk_depth
        )

        self.phase21_assist_enter_risk = float(
            phase21_assist_enter_risk
        )
        self.phase21_avoid_enter_risk = float(
            phase21_avoid_enter_risk
        )
        self.phase21_avoid_exit_risk = float(
            phase21_avoid_exit_risk
        )
        self.phase21_track_exit_risk = float(
            phase21_track_exit_risk
        )
        self.phase21_clear_hold_steps = int(
            phase21_clear_hold_steps
        )

        self.phase21_assist_steer_gain = float(
            phase21_assist_steer_gain
        )
        self.phase21_avoid_steer_gain = float(
            phase21_avoid_steer_gain
        )
        self.phase21_assist_min_speed_scale = float(
            phase21_assist_min_speed_scale
        )
        self.phase21_avoid_min_speed_scale = float(
            phase21_avoid_min_speed_scale
        )
        self.phase21_assist_action_scale = float(
            phase21_assist_action_scale
        )
        self.phase21_avoid_action_scale = float(
            phase21_avoid_action_scale
        )

        super().__init__(**kwargs)

        self.phase21_original_assist_scale = float(
            getattr(
                self,
                "phase14_assist_scale",
                0.15,
            )
        )

        robot_radius = float(
            getattr(
                self,
                "robot_radius",
                0.28,
            )
        )

        self.phase21_corridor_radius = (
            robot_radius
            + self.phase21_corridor_margin
        )

    # ------------------------------------------------------------------
    # LiDAR接口修复
    # ------------------------------------------------------------------

    def _phase17_try_get_lidar(self):
        """
        优先使用Phase17C的32线360°LiDAR。

        该数组索引0对应机器人正前方。
        """

        value = getattr(
            self,
            "phase17c_last_lidar",
            None,
        )

        if value is not None:
            try:
                lidar = np.asarray(
                    value,
                    dtype=np.float32,
                ).reshape(-1)

                if lidar.size >= 8:
                    return lidar
            except Exception:
                pass

        return super()._phase17_try_get_lidar()

    def _phase17_lidar_sectors(
        self,
        lidar,
    ):
        """
        360°LiDAR：
            index 0          = 正前方
            index递增方向    = 逆时针/左侧
            数组末尾         = 右前方

        修复旧代码把数组中点当正前方的问题。
        """

        lidar = np.asarray(
            lidar,
            dtype=np.float32,
        ).reshape(-1)

        lidar = np.nan_to_num(
            lidar,
            nan=1.0,
            posinf=1.0,
            neginf=0.0,
        )

        lidar = np.clip(
            lidar,
            0.0,
            10.0,
        )

        n = int(lidar.size)

        if n < 8:
            return super()._phase17_lidar_sectors(
                lidar
            )

        # 正前方约±22.5°。
        front_half = max(
            1,
            int(round(n * 22.5 / 360.0)),
        )

        # 左右前侧扇区各约45°。
        side_width = max(
            2,
            int(round(n * 45.0 / 360.0)),
        )

        front_indices = list(
            range(0, front_half + 1)
        ) + list(
            range(
                n - front_half,
                n,
            )
        )

        left_indices = list(
            range(
                front_half + 1,
                min(
                    n,
                    front_half
                    + 1
                    + side_width,
                ),
            )
        )

        right_start = max(
            0,
            n
            - front_half
            - side_width,
        )

        right_end = max(
            0,
            n - front_half,
        )

        right_indices = list(
            range(
                right_start,
                right_end,
            )
        )

        front = lidar[
            np.asarray(
                front_indices,
                dtype=np.int64,
            )
        ]

        left = lidar[
            np.asarray(
                left_indices,
                dtype=np.int64,
            )
        ]

        right = lidar[
            np.asarray(
                right_indices,
                dtype=np.int64,
            )
        ]

        if left.size == 0:
            left = front

        if right.size == 0:
            right = front

        return (
            float(np.min(front)),
            float(np.min(left)),
            float(np.min(right)),
        )

    def _phase17_apply_safety_shield(
        self,
        action,
    ):
        """
        修正动作语义：

            action[0] = steer
            action[1] = speed

        该层处理SAC动作；
        基础控制的最终限速还会在_base_action中执行。
        """

        action = np.asarray(
            action,
            dtype=np.float32,
        ).reshape(-1).copy()

        action = np.clip(
            action,
            -1.0,
            1.0,
        )

        self.phase17_shield_active = False
        self.phase17_shield_reason = "none"

        lidar = self._phase17_try_get_lidar()

        if lidar is None or action.size < 2:
            return action

        (
            front_min,
            left_min,
            right_min,
        ) = self._phase17_lidar_sectors(
            lidar
        )

        self.phase17_front_min = float(
            front_min
        )
        self.phase17_left_min = float(
            left_min
        )
        self.phase17_right_min = float(
            right_min
        )

        # 左侧障碍更近时向右转，steer为负。
        if left_min < right_min:
            escape_sign = -1.0
        elif right_min < left_min:
            escape_sign = 1.0
        else:
            escape_sign = float(
                self.phase21_last_steer_direction
            )

            if abs(escape_sign) < 0.5:
                escape_sign = -1.0

        if front_min < float(
            self.shield_front_stop
        ):
            action[1] = min(
                float(action[1]),
                float(self.shield_min_speed),
            )

            action[0] = np.clip(
                escape_sign
                * max(
                    abs(float(action[0])),
                    float(self.shield_turn_gain),
                ),
                -1.0,
                1.0,
            )

            self.phase17_shield_active = True
            self.phase17_shield_reason = (
                "front_stop_corrected"
            )

        elif front_min < float(
            self.shield_front_slow
        ):
            action[1] = min(
                float(action[1]),
                float(self.shield_slow_speed),
            )

            if (
                left_min
                < float(self.shield_side_near)
                or right_min
                < float(self.shield_side_near)
            ):
                action[0] = np.clip(
                    escape_sign
                    * max(
                        abs(float(action[0])),
                        0.5
                        * float(
                            self.shield_turn_gain
                        ),
                    ),
                    -1.0,
                    1.0,
                )

                self.phase17_shield_reason = (
                    "front_slow_side_corrected"
                )
            else:
                self.phase17_shield_reason = (
                    "front_slow_corrected"
                )

            self.phase17_shield_active = True

        return np.clip(
            action,
            -1.0,
            1.0,
        ).astype(np.float32)

    # ------------------------------------------------------------------
    # 传感器点云与路径走廊
    # ------------------------------------------------------------------

    def _phase21_get_future_path(
        self,
    ) -> np.ndarray:
        path = None

        getter = getattr(
            self,
            "get_phase14_smooth_path",
            None,
        )

        if callable(getter):
            try:
                path = getter()
            except Exception:
                path = None

        if path is None:
            path = getattr(
                self,
                "phase19_planned_path",
                None,
            )

        try:
            path = np.asarray(
                path,
                dtype=np.float32,
            )
        except Exception:
            return np.empty(
                (0, 2),
                dtype=np.float32,
            )

        if (
            path.ndim != 2
            or path.shape[1] < 2
            or len(path) < 2
        ):
            return np.empty(
                (0, 2),
                dtype=np.float32,
            )

        path = path[:, :2]

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

        future = path[
            nearest_index:
        ].copy()

        if len(future) < 2:
            return future

        segment_lengths = np.linalg.norm(
            np.diff(
                future,
                axis=0,
            ),
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

        keep = cumulative <= (
            self.phase21_path_lookahead
            + 0.20
        )

        future = future[keep]

        if len(future) < 2:
            future = path[
                nearest_index:
                min(
                    len(path),
                    nearest_index + 2,
                )
            ]

        return np.asarray(
            future,
            dtype=np.float32,
        )

    def _phase21_sensor_points(
        self,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        返回：
            points_world: 世界坐标障碍点
            points_local: 机器人局部坐标障碍点

        仅使用LiDAR和Depth，不使用障碍真值。
        """

        robot_xy = np.asarray(
            self.robot_xy,
            dtype=np.float32,
        ).reshape(2)

        yaw = float(
            self.robot_yaw
        )

        world_parts = []
        local_parts = []

        # 32线360° LiDAR。
        lidar = np.asarray(
            getattr(
                self,
                "phase17c_last_lidar",
                [],
            ),
            dtype=np.float32,
        ).reshape(-1)

        lidar_max_range = float(
            getattr(
                self,
                "phase17c_lidar_max_range",
                3.0,
            )
        )

        if lidar.size >= 8:
            lidar = np.clip(
                np.nan_to_num(
                    lidar,
                    nan=1.0,
                    posinf=1.0,
                    neginf=0.0,
                ),
                0.0,
                1.0,
            )

            distances = (
                lidar
                * lidar_max_range
            )

            relative_angles = (
                2.0
                * math.pi
                * np.arange(
                    lidar.size,
                    dtype=np.float32,
                )
                / float(lidar.size)
            )

            hit = (
                (distances > 0.05)
                & (
                    distances
                    < 0.985
                    * lidar_max_range
                )
            )

            if np.any(hit):
                selected_distance = (
                    distances[hit]
                )

                selected_angle = (
                    relative_angles[hit]
                )

                local = np.stack(
                    [
                        selected_distance
                        * np.cos(
                            selected_angle
                        ),
                        selected_distance
                        * np.sin(
                            selected_angle
                        ),
                    ],
                    axis=1,
                ).astype(np.float32)

                world_angle = (
                    yaw + selected_angle
                )

                world = robot_xy + np.stack(
                    [
                        selected_distance
                        * np.cos(
                            world_angle
                        ),
                        selected_distance
                        * np.sin(
                            world_angle
                        ),
                    ],
                    axis=1,
                ).astype(np.float32)

                local_parts.append(local)
                world_parts.append(world)

        # 15线前向Depth，FOV为±35°。
        depth = np.asarray(
            getattr(
                self,
                "phase17c_last_depth",
                [],
            ),
            dtype=np.float32,
        ).reshape(-1)

        depth_max_range = float(
            getattr(
                self,
                "phase17c_depth_max_range",
                3.0,
            )
        )

        if depth.size >= 3:
            depth = np.clip(
                np.nan_to_num(
                    depth,
                    nan=1.0,
                    posinf=1.0,
                    neginf=0.0,
                ),
                0.0,
                1.0,
            )

            distances = (
                depth
                * depth_max_range
            )

            relative_angles = np.linspace(
                -math.radians(35.0),
                math.radians(35.0),
                depth.size,
                dtype=np.float32,
            )

            hit = (
                (distances > 0.05)
                & (
                    distances
                    < 0.985
                    * depth_max_range
                )
            )

            if np.any(hit):
                selected_distance = (
                    distances[hit]
                )

                selected_angle = (
                    relative_angles[hit]
                )

                local = np.stack(
                    [
                        selected_distance
                        * np.cos(
                            selected_angle
                        ),
                        selected_distance
                        * np.sin(
                            selected_angle
                        ),
                    ],
                    axis=1,
                ).astype(np.float32)

                world_angle = (
                    yaw + selected_angle
                )

                world = robot_xy + np.stack(
                    [
                        selected_distance
                        * np.cos(
                            world_angle
                        ),
                        selected_distance
                        * np.sin(
                            world_angle
                        ),
                    ],
                    axis=1,
                ).astype(np.float32)

                local_parts.append(local)
                world_parts.append(world)

        if not world_parts:
            return (
                np.empty(
                    (0, 2),
                    dtype=np.float32,
                ),
                np.empty(
                    (0, 2),
                    dtype=np.float32,
                ),
            )

        return (
            np.concatenate(
                world_parts,
                axis=0,
            ).astype(np.float32),
            np.concatenate(
                local_parts,
                axis=0,
            ).astype(np.float32),
        )

    @staticmethod
    def _phase21_point_segment_distances(
        points: np.ndarray,
        path: np.ndarray,
    ) -> np.ndarray:
        points = np.asarray(
            points,
            dtype=np.float32,
        ).reshape(-1, 2)

        path = np.asarray(
            path,
            dtype=np.float32,
        ).reshape(-1, 2)

        if (
            len(points) == 0
            or len(path) < 2
        ):
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
            relative
            * vector[None, :, :],
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
            points[:, None, :]
            - closest,
            axis=2,
        )

        return np.min(
            distances,
            axis=1,
        ).astype(np.float32)

    def _phase21_compute_corridor_state(
        self,
    ) -> None:
        path = self._phase21_get_future_path()

        (
            points_world,
            points_local,
        ) = self._phase21_sensor_points()

        lidar = self._phase17_try_get_lidar()

        if lidar is not None:
            (
                front_min,
                left_min,
                right_min,
            ) = self._phase17_lidar_sectors(
                lidar
            )
        else:
            front_min = 1.0
            left_min = 1.0
            right_min = 1.0

        self.phase21_last_front_min = float(
            front_min
        )
        self.phase21_last_left_min = float(
            left_min
        )
        self.phase21_last_right_min = float(
            right_min
        )

        if (
            len(path) < 2
            or len(points_world) == 0
        ):
            self.phase21_last_risk = 0.0
            self.phase21_last_min_path_clearance = float(
                "inf"
            )
            self.phase21_last_nearest_forward = float(
                "inf"
            )
            self.phase21_last_conflict_count = 0
            self.phase21_last_obstacle_side = "NONE"
            self.phase21_last_steer_direction = 0.0
            return

        # 仅保留机器人前方及合理前视范围内的传感器点。
        candidate = (
            (points_local[:, 0] > 0.05)
            & (
                points_local[:, 0]
                <= self.phase21_path_lookahead
                + 0.50
            )
        )

        points_world = points_world[
            candidate
        ]

        points_local = points_local[
            candidate
        ]

        if len(points_world) == 0:
            self.phase21_last_risk = 0.0
            self.phase21_last_min_path_clearance = float(
                "inf"
            )
            self.phase21_last_nearest_forward = float(
                "inf"
            )
            self.phase21_last_conflict_count = 0
            self.phase21_last_obstacle_side = "NONE"
            self.phase21_last_steer_direction = 0.0
            return

        path_clearance = (
            self._phase21_point_segment_distances(
                points_world,
                path,
            )
        )

        min_clearance = float(
            np.min(
                path_clearance
            )
        )

        conflict = (
            path_clearance
            < self.phase21_corridor_radius
        )

        conflict_count = int(
            np.count_nonzero(
                conflict
            )
        )

        self.phase21_last_min_path_clearance = (
            min_clearance
        )

        self.phase21_last_conflict_count = (
            conflict_count
        )

        if conflict_count == 0:
            self.phase21_last_risk = 0.0
            self.phase21_last_nearest_forward = float(
                "inf"
            )
            self.phase21_last_obstacle_side = "NONE"
            self.phase21_last_steer_direction = 0.0
            return

        conflict_local = points_local[
            conflict
        ]

        conflict_clearance = path_clearance[
            conflict
        ]

        nearest_forward = float(
            np.min(
                conflict_local[:, 0]
            )
        )

        self.phase21_last_nearest_forward = (
            nearest_forward
        )

        penetration_depth = max(
            0.0,
            self.phase21_corridor_radius
            - float(
                np.min(
                    conflict_clearance
                )
            ),
        )

        corridor_risk = float(
            np.clip(
                penetration_depth
                / max(
                    self.phase21_risk_depth,
                    1e-6,
                ),
                0.0,
                1.0,
            )
        )

        forward_risk = float(
            np.clip(
                (
                    self.phase21_path_lookahead
                    - nearest_forward
                )
                / max(
                    self.phase21_path_lookahead,
                    1e-6,
                ),
                0.0,
                1.0,
            )
        )

        count_risk = float(
            np.clip(
                conflict_count / 6.0,
                0.0,
                1.0,
            )
        )

        risk = (
            corridor_risk
            * (
                0.50
                + 0.40 * forward_risk
                + 0.10 * count_risk
            )
        )

        self.phase21_last_risk = float(
            np.clip(
                risk,
                0.0,
                1.0,
            )
        )

        # 以机器人局部坐标判断障碍位于左侧还是右侧。
        weights = 1.0 / np.maximum(
            conflict_clearance,
            0.03,
        )

        mean_lateral = float(
            np.sum(
                conflict_local[:, 1]
                * weights
            )
            / max(
                float(np.sum(weights)),
                1e-6,
            )
        )

        if mean_lateral > 0.04:
            # 障碍在左，向右转。
            self.phase21_last_obstacle_side = "LEFT"
            self.phase21_last_steer_direction = -1.0

        elif mean_lateral < -0.04:
            # 障碍在右，向左转。
            self.phase21_last_obstacle_side = "RIGHT"
            self.phase21_last_steer_direction = 1.0

        else:
            self.phase21_last_obstacle_side = "CENTER"

            # 障碍居中时选择更空旷的一侧。
            if left_min > right_min:
                self.phase21_last_steer_direction = 1.0
            else:
                self.phase21_last_steer_direction = -1.0

    # ------------------------------------------------------------------
    # 风险状态机与控制
    # ------------------------------------------------------------------

    def _phase21_update_mode(
        self,
    ) -> None:
        risk = float(
            self.phase21_last_risk
        )

        old_mode = self.phase21_mode
        new_mode = old_mode

        if old_mode == self.MODE_TRACK:
            self.phase21_clear_counter = 0

            if risk >= self.phase21_avoid_enter_risk:
                new_mode = self.MODE_AVOID
            elif risk >= self.phase21_assist_enter_risk:
                new_mode = self.MODE_ASSIST

        elif old_mode == self.MODE_ASSIST:
            if risk >= self.phase21_avoid_enter_risk:
                self.phase21_clear_counter = 0
                new_mode = self.MODE_AVOID

            elif risk <= self.phase21_track_exit_risk:
                self.phase21_clear_counter += 1

                if (
                    self.phase21_clear_counter
                    >= self.phase21_clear_hold_steps
                ):
                    new_mode = self.MODE_TRACK
                    self.phase21_clear_counter = 0
            else:
                self.phase21_clear_counter = 0

        elif old_mode == self.MODE_AVOID:
            if risk <= self.phase21_avoid_exit_risk:
                self.phase21_clear_counter += 1

                if (
                    self.phase21_clear_counter
                    >= self.phase21_clear_hold_steps
                ):
                    new_mode = self.MODE_ASSIST
                    self.phase21_clear_counter = 0
            else:
                self.phase21_clear_counter = 0

        if new_mode != old_mode:
            self.phase21_previous_mode = old_mode
            self.phase21_mode = new_mode
            self.phase21_mode_switch_count += 1

    def _phase21_apply_action_scale(
        self,
    ) -> None:
        if not hasattr(
            self,
            "phase14_assist_scale",
        ):
            return

        if self.phase21_mode == self.MODE_AVOID:
            value = self.phase21_avoid_action_scale

        elif self.phase21_mode == self.MODE_ASSIST:
            value = self.phase21_assist_action_scale

        else:
            value = self.phase21_original_assist_scale

        self.phase14_assist_scale = float(
            value
        )

    def _phase21_steer_gain(
        self,
    ) -> float:
        if self.phase21_mode == self.MODE_AVOID:
            return self.phase21_avoid_steer_gain

        if self.phase21_mode == self.MODE_ASSIST:
            return self.phase21_assist_steer_gain

        return 0.0

    def _phase21_min_speed_scale(
        self,
    ) -> float:
        if self.phase21_mode == self.MODE_AVOID:
            return (
                self.phase21_avoid_min_speed_scale
            )

        if self.phase21_mode == self.MODE_ASSIST:
            return (
                self.phase21_assist_min_speed_scale
            )

        return 1.0

    def _base_action(
        self,
        raw_obs,
    ):
        """
        基础动作仍由原Phase7基础模型产生。

        只有风险模式才执行局部参考修正：
            action[0] = steer
            action[1] = speed
        """

        base_action = np.asarray(
            super()._base_action(
                raw_obs
            ),
            dtype=np.float32,
        ).reshape(2)

        if self.phase21_mode == self.MODE_TRACK:
            return np.clip(
                base_action,
                -1.0,
                1.0,
            ).astype(np.float32)

        risk = float(
            np.clip(
                self.phase21_last_risk,
                0.0,
                1.0,
            )
        )

        direction = float(
            self.phase21_last_steer_direction
        )

        steer_correction = (
            direction
            * self._phase21_steer_gain()
            * risk
        )

        base_action[0] = np.clip(
            base_action[0]
            + steer_correction,
            -1.0,
            1.0,
        )

        min_scale = (
            self._phase21_min_speed_scale()
        )

        speed_scale = max(
            min_scale,
            1.0 - 0.80 * risk,
        )

        base_action[1] = np.clip(
            base_action[1]
            * speed_scale,
            -1.0,
            1.0,
        )

        # 对真正前向危险执行最终基础速度保护。
        if (
            self.phase21_last_front_min
            < float(self.shield_front_stop)
        ):
            base_action[1] = min(
                float(base_action[1]),
                0.0,
            )

            base_action[0] = np.clip(
                direction
                * max(
                    abs(float(base_action[0])),
                    float(self.shield_turn_gain),
                ),
                -1.0,
                1.0,
            )

        elif (
            self.phase21_last_front_min
            < float(self.shield_front_slow)
        ):
            base_action[1] = min(
                float(base_action[1]),
                float(self.shield_slow_speed),
            )

        return np.clip(
            base_action,
            -1.0,
            1.0,
        ).astype(np.float32)

    def _phase21_fill_info(
        self,
        info: dict[str, Any],
        action_mode: str,
    ) -> dict[str, Any]:
        output = dict(
            info or {}
        )

        output.update({
            "phase21_version":
                "v2_path_corridor_sensor_only",
            "phase21_enabled": True,
            "phase21_sensor_only_switch": True,
            "phase21_ground_truth_used_for_control": False,
            "phase21_lidar_index_zero_is_front": True,
            "phase21_action_order":
                "steer_speed",
            "phase21_action_mode":
                str(action_mode),
            "phase21_mode":
                str(self.phase21_mode),
            "phase21_previous_mode":
                str(self.phase21_previous_mode),
            "phase21_mode_switch_count":
                int(self.phase21_mode_switch_count),
            "phase21_clear_counter":
                int(self.phase21_clear_counter),
            "phase21_corridor_risk":
                float(self.phase21_last_risk),
            "phase21_corridor_radius":
                float(self.phase21_corridor_radius),
            "phase21_min_path_clearance":
                float(
                    self.phase21_last_min_path_clearance
                ),
            "phase21_nearest_conflict_forward":
                float(
                    self.phase21_last_nearest_forward
                ),
            "phase21_conflict_point_count":
                int(
                    self.phase21_last_conflict_count
                ),
            "phase21_obstacle_side":
                str(
                    self.phase21_last_obstacle_side
                ),
            "phase21_steer_direction":
                float(
                    self.phase21_last_steer_direction
                ),
            "phase21_front_min":
                float(self.phase21_last_front_min),
            "phase21_left_min":
                float(self.phase21_last_left_min),
            "phase21_right_min":
                float(self.phase21_last_right_min),
            "phase21_phase14_assist_scale":
                float(
                    getattr(
                        self,
                        "phase14_assist_scale",
                        self.phase21_original_assist_scale,
                    )
                ),
        })

        return output

    def reset(
        self,
        *args,
        **kwargs,
    ):
        self.phase21_mode = self.MODE_TRACK
        self.phase21_previous_mode = self.MODE_TRACK
        self.phase21_clear_counter = 0
        self.phase21_mode_switch_count = 0

        self.phase21_last_risk = 0.0
        self.phase21_last_min_path_clearance = float(
            "inf"
        )
        self.phase21_last_nearest_forward = float(
            "inf"
        )
        self.phase21_last_conflict_count = 0
        self.phase21_last_obstacle_side = "NONE"
        self.phase21_last_steer_direction = 0.0

        if hasattr(
            self,
            "phase14_assist_scale",
        ):
            self.phase14_assist_scale = float(
                self.phase21_original_assist_scale
            )

        output = super().reset(
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

        self._phase21_compute_corridor_state()
        self._phase21_update_mode()
        self._phase21_apply_action_scale()

        info = self._phase21_fill_info(
            dict(info or {}),
            action_mode=self.MODE_TRACK,
        )

        if tuple_api:
            return observation, info

        return observation

    def step(
        self,
        action,
    ):
        # 使用当前传感器状态决定本步控制模式。
        self._phase21_compute_corridor_state()
        self._phase21_update_mode()
        self._phase21_apply_action_scale()

        action_mode = str(
            self.phase21_mode
        )

        policy_action = np.asarray(
            action,
            dtype=np.float32,
        ).reshape(2).copy()

        # 风险模式下同时向SAC残差注入避障方向，
        # 但仍保留策略原输出。
        if action_mode != self.MODE_TRACK:
            risk = float(
                np.clip(
                    self.phase21_last_risk,
                    0.0,
                    1.0,
                )
            )

            direction = float(
                self.phase21_last_steer_direction
            )

            policy_action[0] += (
                direction
                * 0.35
                * risk
            )

            policy_action[1] -= (
                0.45
                * risk
            )

        policy_action = np.clip(
            policy_action,
            -1.0,
            1.0,
        )

        output = super().step(
            policy_action
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

        # 记录执行后传感器风险，供下一步使用。
        self._phase21_compute_corridor_state()

        info = self._phase21_fill_info(
            dict(info or {}),
            action_mode=action_mode,
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
