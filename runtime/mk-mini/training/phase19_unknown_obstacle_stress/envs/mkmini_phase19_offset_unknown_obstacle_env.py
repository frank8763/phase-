import numpy as np

from training.phase19_unknown_obstacle_stress.envs.mkmini_phase19_unknown_obstacle_env import (
    MkMiniPhase19UnknownObstacleEnv,
)


class MkMiniPhase19OffsetUnknownObstacleEnv(
    MkMiniPhase19UnknownObstacleEnv
):
    """
    在原A*路径生成后，将未知障碍放置在路径侧方。

    不修改：
    - 原A*路径
    - Phase17及更早环境
    - 已完成的Phase19中心障碍环境
    """

    def __init__(
        self,
        *args,
        unknown_lateral_offset=0.35,
        **kwargs,
    ):
        self.phase19_unknown_lateral_offset = float(
            unknown_lateral_offset
        )

        self.phase19_offset_side = 0
        self.phase19_centerline_point = np.zeros(
            2,
            dtype=np.float32,
        )
        self.phase19_selected_offset_point = np.zeros(
            2,
            dtype=np.float32,
        )
        self.phase19_actual_lateral_offset = 0.0
        self.phase19_path_tangent = np.zeros(
            2,
            dtype=np.float32,
        )

        super().__init__(*args, **kwargs)

    def _phase19_choose_unknown_center(self, path):
        center, _, fraction = (
            super()._phase19_choose_unknown_center(path)
        )

        center = np.asarray(
            center,
            dtype=np.float32,
        ).reshape(2)

        f0 = max(0.0, float(fraction) - 0.015)
        f1 = min(1.0, float(fraction) + 0.015)

        p0 = self._phase19_point_at_fraction(path, f0)
        p1 = self._phase19_point_at_fraction(path, f1)

        tangent = np.asarray(
            p1 - p0,
            dtype=np.float32,
        )

        tangent_norm = float(np.linalg.norm(tangent))

        if tangent_norm <= 1e-6:
            tangent = np.asarray(
                [1.0, 0.0],
                dtype=np.float32,
            )
        else:
            tangent = tangent / tangent_norm

        normal = np.asarray(
            [-tangent[1], tangent[0]],
            dtype=np.float32,
        )

        offset = self.phase19_unknown_lateral_offset

        candidates = [
            (
                1,
                center + offset * normal,
            ),
            (
                -1,
                center - offset * normal,
            ),
        ]

        start = np.asarray(
            self.robot_xy,
            dtype=np.float32,
        )

        goal = np.asarray(
            self.goal_xy,
            dtype=np.float32,
        )

        scored = []

        for side, point in candidates:
            point = np.asarray(
                point,
                dtype=np.float32,
            )

            known_clearance = (
                self._phase19_known_obstacle_clearance(point)
            )

            start_distance = float(
                np.linalg.norm(point - start)
            )

            goal_distance = float(
                np.linalg.norm(point - goal)
            )

            endpoint_valid = (
                start_distance
                >= self.phase19_endpoint_clearance
                and goal_distance
                >= self.phase19_endpoint_clearance
            )

            score = float(known_clearance)

            if not endpoint_valid:
                score -= 100.0

            scored.append(
                (
                    score,
                    known_clearance,
                    side,
                    point,
                )
            )

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        _, known_clearance, side, selected = scored[0]

        self.phase19_offset_side = int(side)
        self.phase19_centerline_point = center.copy()
        self.phase19_selected_offset_point = (
            selected.copy()
        )
        self.phase19_actual_lateral_offset = float(
            np.linalg.norm(selected - center)
        )
        self.phase19_path_tangent = tangent.copy()

        return (
            selected,
            float(known_clearance),
            float(fraction),
        )

    def reset(self, **kwargs):
        obs, info = super().reset(**kwargs)

        info["phase19_requested_lateral_offset"] = float(
            self.phase19_unknown_lateral_offset
        )

        info["phase19_actual_lateral_offset"] = float(
            self.phase19_actual_lateral_offset
        )

        info["phase19_offset_side"] = int(
            self.phase19_offset_side
        )

        info["phase19_centerline_point"] = (
            self.phase19_centerline_point.copy()
        )

        info["phase19_selected_offset_point"] = (
            self.phase19_selected_offset_point.copy()
        )

        info["phase19_path_tangent"] = (
            self.phase19_path_tangent.copy()
        )

        return obs, info
