import hashlib
import math

import mujoco
import numpy as np

from training.phase17_fusion_safety_sac_nav.envs.mkmini_phase17c_lidar_camera_fusion_env import (
    MkMiniPhase17CLidarCameraFusionEnv,
)


class MkMiniPhase19UnknownObstacleEnv(
    MkMiniPhase17CLidarCameraFusionEnv
):
    """
    Phase19 未知障碍压力测试环境。

    原则：
    1. 先完整执行 Phase17 reset，完成 A* 路径生成。
    2. 再把隐藏圆柱激活到原路径上。
    3. 未知障碍加入在线传感器和碰撞数组。
    4. 不重新调用 A*，不修改原路径。
    5. 下一回合规划前，先彻底移除上一回合未知障碍。
    """

    HIDDEN_GEOM_NAMES = (
        "real_circle_obs_9",
        "real_circle_obs_10",
    )

    PHASE6_LIDAR_START = 66
    PHASE6_LIDAR_END = 98
    PHASE6_SAFETY_START = 103
    PHASE6_SAFETY_END = 107
    PHASE6_OBS_END = 107
    PHASE7_OBS_END = 127
    BASE_OBS_END = 129
    FULL_OBS_DIM = 186

    def __init__(
        self,
        *args,
        unknown_count=1,
        unknown_radius=0.28,
        unknown_path_fraction=0.55,
        endpoint_clearance=1.20,
        **kwargs,
    ):
        self.phase19_unknown_count = int(
            np.clip(unknown_count, 1, len(self.HIDDEN_GEOM_NAMES))
        )
        self.phase19_unknown_radius = float(unknown_radius)
        self.phase19_unknown_path_fraction = float(
            np.clip(unknown_path_fraction, 0.30, 0.75)
        )
        self.phase19_endpoint_clearance = float(endpoint_clearance)

        self.phase19_unknown_circles = np.empty(
            (0, 3),
            dtype=np.float32,
        )
        self.phase19_unknown_geom_ids = []
        self.phase19_planned_path = None
        self.phase19_path_hash_before = ""
        self.phase19_path_hash_after = ""
        self.phase19_path_unchanged = False
        self.phase19_min_unknown_clearance = float("inf")
        self.phase19_unknown_contact = False

        super().__init__(*args, **kwargs)

    # ------------------------------------------------------------------
    # 对象链与数组管理
    # ------------------------------------------------------------------

    def _phase19_object_chain(self):
        objects = []
        seen = set()
        current = self

        while current is not None and id(current) not in seen:
            seen.add(id(current))
            objects.append(current)

            try:
                local = object.__getattribute__(current, "__dict__")
                current = local.get("inner")
            except Exception:
                current = None

        return objects

    def _phase19_remove_previous_unknown_arrays(self):
        unknown = np.asarray(
            self.phase19_unknown_circles,
            dtype=np.float32,
        ).reshape(-1, 3)

        if unknown.size == 0:
            return

        for obj in self._phase19_object_chain():
            local = object.__getattribute__(obj, "__dict__")

            if "circle_obstacles" not in local:
                continue

            circles = np.asarray(
                local["circle_obstacles"],
                dtype=np.float32,
            ).reshape(-1, 3)

            keep = np.ones(len(circles), dtype=bool)

            for ux, uy, ur in unknown:
                match = (
                    np.linalg.norm(
                        circles[:, :2]
                        - np.asarray([ux, uy], dtype=np.float32),
                        axis=1,
                    )
                    < 1e-4
                ) & (np.abs(circles[:, 2] - ur) < 1e-4)

                keep &= ~match

            local["circle_obstacles"] = circles[keep].copy()

        self.phase19_unknown_circles = np.empty(
            (0, 3),
            dtype=np.float32,
        )

    def _phase19_hide_unknown_geoms(self):
        model = getattr(self, "model", None)
        data = getattr(self, "data", None)

        if model is None:
            return

        for name in self.HIDDEN_GEOM_NAMES:
            gid = mujoco.mj_name2id(
                model,
                mujoco.mjtObj.mjOBJ_GEOM,
                name,
            )

            if gid < 0:
                continue

            model.geom_rgba[gid, 3] = 0.0
            model.geom_contype[gid] = 0
            model.geom_conaffinity[gid] = 0
            model.geom_pos[gid, 2] = -10.0

        if data is not None:
            mujoco.mj_forward(model, data)

        self.phase19_unknown_geom_ids = []

    def _phase19_clean_before_parent_reset(self):
        # 必须发生在 super().reset() 之前，
        # 防止上一回合未知障碍进入下一回合 A* 地图。
        self._phase19_remove_previous_unknown_arrays()
        self._phase19_hide_unknown_geoms()

    # ------------------------------------------------------------------
    # 路径读取与未知障碍位置选择
    # ------------------------------------------------------------------

    def _phase19_get_followed_path(self):
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
                if path.ndim == 2 and len(path) >= 3:
                    return path.copy()
            except Exception:
                pass

        for name in (
            "smooth_ref_path",
            "path_world",
            "dense_path",
            "raw_astar_path",
        ):
            try:
                path = np.asarray(
                    getattr(self, name),
                    dtype=np.float32,
                )
            except Exception:
                continue

            if path.ndim == 2 and len(path) >= 3:
                return path.copy()

        raise RuntimeError("Phase19：没有找到有效路径。")

    @staticmethod
    def _phase19_path_hash(path):
        arr = np.ascontiguousarray(
            np.asarray(path, dtype=np.float32)
        )
        return hashlib.sha256(arr.tobytes()).hexdigest()

    @staticmethod
    def _phase19_point_at_fraction(path, fraction):
        path = np.asarray(path, dtype=np.float32)
        segments = np.diff(path, axis=0)
        lengths = np.linalg.norm(segments, axis=1)
        cumulative = np.concatenate(
            [np.asarray([0.0]), np.cumsum(lengths)]
        )

        total = float(cumulative[-1])
        if total <= 1e-6:
            return path[len(path) // 2].copy()

        target = float(np.clip(fraction, 0.0, 1.0)) * total
        index = int(
            np.clip(
                np.searchsorted(cumulative, target) - 1,
                0,
                len(segments) - 1,
            )
        )

        seg_len = float(lengths[index])
        if seg_len <= 1e-6:
            return path[index].copy()

        alpha = (
            target - float(cumulative[index])
        ) / seg_len

        return (
            path[index]
            + alpha * segments[index]
        ).astype(np.float32)

    def _phase19_known_obstacle_clearance(self, point):
        x = float(point[0])
        y = float(point[1])
        clearances = []

        rects = np.asarray(
            getattr(
                self,
                "rect_obstacles",
                np.empty((0, 4)),
            ),
            dtype=np.float32,
        ).reshape(-1, 4)

        for cx, cy, hx, hy in rects:
            dx = max(abs(x - float(cx)) - float(hx), 0.0)
            dy = max(abs(y - float(cy)) - float(hy), 0.0)
            clearances.append(math.hypot(dx, dy))

        circles = np.asarray(
            getattr(
                self,
                "circle_obstacles",
                np.empty((0, 3)),
            ),
            dtype=np.float32,
        ).reshape(-1, 3)

        for cx, cy, radius in circles:
            clearances.append(
                math.hypot(
                    x - float(cx),
                    y - float(cy),
                )
                - float(radius)
            )

        if not clearances:
            return float("inf")

        return float(min(clearances))

    def _phase19_choose_unknown_center(self, path):
        start = np.asarray(self.robot_xy, dtype=np.float32)
        goal = np.asarray(self.goal_xy, dtype=np.float32)

        fractions = np.unique(
            np.concatenate(
                [
                    np.asarray(
                        [self.phase19_unknown_path_fraction],
                        dtype=np.float32,
                    ),
                    np.linspace(
                        0.35,
                        0.75,
                        17,
                        dtype=np.float32,
                    ),
                ]
            )
        )

        best = None

        for fraction in fractions:
            point = self._phase19_point_at_fraction(
                path,
                float(fraction),
            )

            start_dist = float(np.linalg.norm(point - start))
            goal_dist = float(np.linalg.norm(point - goal))

            if (
                start_dist < self.phase19_endpoint_clearance
                or goal_dist < self.phase19_endpoint_clearance
            ):
                continue

            clearance = self._phase19_known_obstacle_clearance(
                point
            )

            score = (
                clearance
                - 0.10
                * abs(
                    float(fraction)
                    - self.phase19_unknown_path_fraction
                )
            )

            candidate = (
                score,
                clearance,
                float(fraction),
                point,
            )

            if best is None or candidate[0] > best[0]:
                best = candidate

        if best is None:
            point = self._phase19_point_at_fraction(
                path,
                self.phase19_unknown_path_fraction,
            )
            clearance = self._phase19_known_obstacle_clearance(
                point
            )
            return point, clearance, self.phase19_unknown_path_fraction

        return best[3], best[1], best[2]

    # ------------------------------------------------------------------
    # MuJoCo 障碍激活
    # ------------------------------------------------------------------

    def _phase19_find_active_circle_template(self):
        model = self.model

        for gid in range(model.ngeom):
            name = mujoco.mj_id2name(
                model,
                mujoco.mjtObj.mjOBJ_GEOM,
                gid,
            )

            if not name:
                continue

            if not name.startswith("real_circle_obs_"):
                continue

            if name in self.HIDDEN_GEOM_NAMES:
                continue

            if float(model.geom_rgba[gid, 3]) <= 0.05:
                continue

            if int(model.geom_contype[gid]) == 0:
                continue

            if float(model.geom_pos[gid, 2]) < -1.0:
                continue

            return gid

        raise RuntimeError(
            "Phase19：没有找到可复制的活动圆形障碍模板。"
        )

    def _phase19_activate_geom(
        self,
        geom_name,
        center,
        radius,
    ):
        model = self.model

        gid = mujoco.mj_name2id(
            model,
            mujoco.mjtObj.mjOBJ_GEOM,
            geom_name,
        )

        if gid < 0:
            raise RuntimeError(
                f"Phase19：找不到几何体 {geom_name}"
            )

        template_gid = self._phase19_find_active_circle_template()

        template_pos = model.geom_pos[template_gid].copy()
        template_size = model.geom_size[template_gid].copy()
        template_rgba = model.geom_rgba[template_gid].copy()

        model.geom_pos[gid] = template_pos
        model.geom_pos[gid, 0] = float(center[0])
        model.geom_pos[gid, 1] = float(center[1])

        model.geom_size[gid] = template_size
        model.geom_size[gid, 0] = float(radius)

        model.geom_rgba[gid] = template_rgba
        model.geom_rgba[gid, 0] = 1.0
        model.geom_rgba[gid, 1] = 0.15
        model.geom_rgba[gid, 2] = 0.05
        model.geom_rgba[gid, 3] = 1.0

        model.geom_contype[gid] = model.geom_contype[
            template_gid
        ]
        model.geom_conaffinity[gid] = model.geom_conaffinity[
            template_gid
        ]

        return gid

    def _phase19_append_unknown_to_arrays(self, circles):
        circles = np.asarray(
            circles,
            dtype=np.float32,
        ).reshape(-1, 3)

        owners = 0
        counts = []

        for obj in self._phase19_object_chain():
            local = object.__getattribute__(obj, "__dict__")

            if "circle_obstacles" not in local:
                continue

            base = np.asarray(
                local["circle_obstacles"],
                dtype=np.float32,
            ).reshape(-1, 3)

            local["circle_obstacles"] = np.vstack(
                [base, circles]
            ).astype(np.float32)

            owners += 1
            counts.append(len(local["circle_obstacles"]))

        if owners == 0:
            raise RuntimeError(
                "Phase19：没有找到 circle_obstacles 所有者。"
            )

        return owners, counts

    # ------------------------------------------------------------------
    # reset 初始观测刷新
    # ------------------------------------------------------------------

    def _phase19_refresh_initial_observation(self, parent_obs):
        parent_obs = np.asarray(
            parent_obs,
            dtype=np.float32,
        ).reshape(-1)

        if parent_obs.size != self.FULL_OBS_DIM:
            raise RuntimeError(
                f"Phase19：父环境观测维度异常："
                f"{parent_obs.size} != {self.FULL_OBS_DIM}"
            )

        phase6_obs = parent_obs[
            : self.PHASE6_OBS_END
        ].copy()

        inner = object.__getattribute__(
            self,
            "__dict__",
        ).get("inner")

        if inner is None:
            raise RuntimeError("Phase19：找不到 inner 环境。")

        lidar = np.asarray(
            inner._get_lidar(),
            dtype=np.float32,
        ).reshape(-1)

        safety = np.asarray(
            inner._get_safety_feat(lidar),
            dtype=np.float32,
        ).reshape(-1)

        if lidar.size != 32 or safety.size != 4:
            raise RuntimeError(
                "Phase19：Phase6 LiDAR/Safety 维度异常。"
            )

        phase6_obs[
            self.PHASE6_LIDAR_START:
            self.PHASE6_LIDAR_END
        ] = lidar

        phase6_obs[
            self.PHASE6_SAFETY_START:
            self.PHASE6_SAFETY_END
        ] = safety

        inner.last_lidar = lidar.copy()
        inner.last_safety = safety.copy()

        raw_obs = np.asarray(
            inner._build_phase7_obs(phase6_obs),
            dtype=np.float32,
        ).reshape(-1)

        if raw_obs.size != self.PHASE7_OBS_END:
            raise RuntimeError(
                f"Phase19：Phase7 观测维度异常："
                f"{raw_obs.size}"
            )

        self.last_raw_obs = raw_obs.copy()

        base_action = np.asarray(
            self._base_action(raw_obs),
            dtype=np.float32,
        ).reshape(-1)

        if base_action.size != 2:
            raise RuntimeError(
                "Phase19：基础动作维度异常。"
            )

        self.last_base_action = base_action.copy()

        base_obs = np.concatenate(
            [raw_obs, base_action],
            dtype=np.float32,
        )

        full_obs = self._phase17c_build_obs(base_obs)

        if full_obs.size != self.FULL_OBS_DIM:
            raise RuntimeError(
                f"Phase19：刷新后观测维度异常："
                f"{full_obs.size}"
            )

        return full_obs.astype(np.float32)

    # ------------------------------------------------------------------
    # 信息记录
    # ------------------------------------------------------------------

    def _phase19_detect_unknown_contact(self):
        unknown_ids = set(self.phase19_unknown_geom_ids)

        if not unknown_ids:
            return False

        for index in range(int(self.data.ncon)):
            contact = self.data.contact[index]

            if (
                int(contact.geom1) in unknown_ids
                or int(contact.geom2) in unknown_ids
            ):
                return True

        return False

    def _phase19_fill_info(self, info):
        if info is None:
            info = {}

        circles = np.asarray(
            self.phase19_unknown_circles,
            dtype=np.float32,
        ).reshape(-1, 3)

        if len(circles):
            clearances = [
                float(
                    np.linalg.norm(
                        np.asarray(self.robot_xy)
                        - circle[:2]
                    )
                    - circle[2]
                )
                for circle in circles
            ]

            current_clearance = min(clearances)
            self.phase19_min_unknown_clearance = min(
                self.phase19_min_unknown_clearance,
                current_clearance,
            )
        else:
            current_clearance = float("inf")

        self.phase19_unknown_contact = (
            self.phase19_unknown_contact
            or self._phase19_detect_unknown_contact()
        )

        info["phase19_unknown_count"] = int(len(circles))
        info["phase19_unknown_circles"] = circles.copy()
        info["phase19_path_hash_before"] = (
            self.phase19_path_hash_before
        )
        info["phase19_path_hash_after"] = (
            self.phase19_path_hash_after
        )
        info["phase19_path_unchanged"] = bool(
            self.phase19_path_unchanged
        )
        info["phase19_astar_replanned"] = False
        info["phase19_current_unknown_clearance"] = float(
            current_clearance
        )
        info["phase19_min_unknown_clearance"] = float(
            self.phase19_min_unknown_clearance
        )
        info["phase19_unknown_contact"] = bool(
            self.phase19_unknown_contact
        )

        return info

    # ------------------------------------------------------------------
    # Gym API
    # ------------------------------------------------------------------

    def reset(self, **kwargs):
        self._phase19_clean_before_parent_reset()

        out = super().reset(**kwargs)

        if isinstance(out, tuple) and len(out) == 2:
            parent_obs, info = out
        else:
            parent_obs = out
            info = {}

        # 到这里时 A*、圆角、加密、平滑、Phase17随机化均已完成。
        planned_path = self._phase19_get_followed_path()
        self.phase19_planned_path = planned_path.copy()

        self.phase19_path_hash_before = (
            self._phase19_path_hash(planned_path)
        )

        center, known_clearance, fraction = (
            self._phase19_choose_unknown_center(planned_path)
        )

        unknown_circles = []
        geom_ids = []

        for index in range(self.phase19_unknown_count):
            geom_name = self.HIDDEN_GEOM_NAMES[index]

            if index == 0:
                obstacle_center = center.copy()
            else:
                second_fraction = min(
                    0.78,
                    fraction + 0.16,
                )
                obstacle_center = self._phase19_point_at_fraction(
                    planned_path,
                    second_fraction,
                )

            gid = self._phase19_activate_geom(
                geom_name,
                obstacle_center,
                self.phase19_unknown_radius,
            )

            geom_ids.append(gid)
            unknown_circles.append(
                [
                    float(obstacle_center[0]),
                    float(obstacle_center[1]),
                    self.phase19_unknown_radius,
                ]
            )

        unknown_circles = np.asarray(
            unknown_circles,
            dtype=np.float32,
        )

        owner_count, owner_circle_counts = (
            self._phase19_append_unknown_to_arrays(
                unknown_circles
            )
        )

        self.phase19_unknown_circles = (
            unknown_circles.copy()
        )
        self.phase19_unknown_geom_ids = geom_ids

        mujoco.mj_forward(self.model, self.data)

        # 禁止重新规划，只重新采集未知障碍加入后的传感器观测。
        obs = self._phase19_refresh_initial_observation(
            parent_obs
        )

        path_after = self._phase19_get_followed_path()
        self.phase19_path_hash_after = (
            self._phase19_path_hash(path_after)
        )
        self.phase19_path_unchanged = (
            self.phase19_path_hash_before
            == self.phase19_path_hash_after
        )

        self.phase19_min_unknown_clearance = float("inf")
        self.phase19_unknown_contact = False

        path_min_distance = float(
            np.min(
                np.linalg.norm(
                    planned_path[:, None, :]
                    - unknown_circles[None, :, :2],
                    axis=2,
                )
            )
        )

        info["phase19_unknown_inserted_after_astar"] = True
        info["phase19_known_clearance_before_insert"] = float(
            known_clearance
        )
        info["phase19_selected_path_fraction"] = float(
            fraction
        )
        info["phase19_path_min_distance_to_unknown"] = (
            path_min_distance
        )
        info["phase19_array_owner_count"] = int(owner_count)
        info["phase19_owner_circle_counts"] = list(
            owner_circle_counts
        )

        info = self._phase19_fill_info(info)

        return obs, info

    def step(self, action):
        out = super().step(action)

        if len(out) == 5:
            obs, reward, terminated, truncated, info = out
            info = self._phase19_fill_info(info)
            return (
                obs,
                reward,
                terminated,
                truncated,
                info,
            )

        obs, reward, done, info = out
        info = self._phase19_fill_info(info)
        return obs, reward, done, info
