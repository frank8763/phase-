import math
import numpy as np

from training.phase7_residual_camera_aux.envs.mkmini_phase7_residual_camera_aux_env import (
    MkMiniPhase7ResidualCameraAuxEnv,
)


class MkMiniPhase9StaticNoDynamicEnv(MkMiniPhase7ResidualCameraAuxEnv):
    def __init__(
        self,
        base_model_path="training/phase6_clean/confirmed/phase6_v1_lidar_main_camera_goal_55k_confirmed.zip",
        residual_scale=0.06,
        max_steer_deg=35.0,
        speed_boost=1.15,
        turn_after_body_ratio=0.50,
        depth_rays=15,
        depth_range=3.5,
        depth_fov=90.0,
    ):
        super().__init__(
            base_model_path=base_model_path,
            residual_scale=residual_scale,
            depth_rays=depth_rays,
            depth_range=depth_range,
            depth_fov=depth_fov,
        )

        self.max_steer_deg = float(max_steer_deg)
        self.max_steer_rad = math.radians(self.max_steer_deg)
        self.speed_boost = float(speed_boost)
        self.turn_after_body_ratio = float(turn_after_body_ratio)

        self._apply_turn35_params()

    def _apply_turn35_params(self):
        target = self.inner

        # 最大转向角：35°
        if hasattr(target, "max_steer"):
            target.max_steer = float(self.max_steer_rad)

        # 转向响应稍微放开，但不重复累乘
        if hasattr(target, "max_steer_delta"):
            target.max_steer_delta = max(float(target.max_steer_delta), 0.014)

        if hasattr(target, "preview_steer_max_delta"):
            target.preview_steer_max_delta = max(float(target.preview_steer_max_delta), 0.10)

        # 如果底层存在通过车身比例参数，就改成 1/2
        for name in [
            "turn_after_body_ratio",
            "pass_body_ratio",
            "obstacle_pass_ratio",
            "clearance_body_ratio",
            "rear_clearance_ratio",
        ]:
            if hasattr(target, name):
                setattr(target, name, self.turn_after_body_ratio)


    def _v7_path_signature(self, path):
        arr = np.asarray(path, dtype=np.float32)
        if arr.ndim != 2 or arr.shape[0] < 2:
            return None
        return (
            int(arr.shape[0]),
            tuple(np.round(arr[0], 3)),
            tuple(np.round(arr[-1], 3)),
            tuple(np.round(np.mean(arr, axis=0), 3)),
        )

    def _v7_resample_path(self, path, step=0.06):
        pts = np.asarray(path, dtype=np.float32)
        if pts.ndim != 2 or pts.shape[0] < 2:
            return pts

        out = [pts[0]]
        for i in range(len(pts) - 1):
            a = pts[i]
            b = pts[i + 1]
            seg = b - a
            dist = float(np.linalg.norm(seg))
            if dist < 1e-6:
                continue
            n = max(1, int(np.ceil(dist / step)))
            for k in range(1, n + 1):
                out.append(a + seg * (k / n))
        return np.asarray(out, dtype=np.float32)

    def _v7_chaikin_smooth(self, path, iters=2):
        pts = np.asarray(path, dtype=np.float32)
        if pts.ndim != 2 or pts.shape[0] < 3:
            return pts

        for _ in range(int(iters)):
            new_pts = [pts[0]]
            for i in range(len(pts) - 1):
                p0 = pts[i]
                p1 = pts[i + 1]
                q = 0.75 * p0 + 0.25 * p1
                r = 0.25 * p0 + 0.75 * p1
                new_pts.extend([q, r])
            new_pts.append(pts[-1])
            pts = np.asarray(new_pts, dtype=np.float32)

        return pts

    def _apply_smooth_ref_path(self):
        # v7 smooth_ref_path:
        # A* 折线路径 -> 重采样 -> Chaikin 平滑 -> smooth_ref_path
        try:
            obj = self.inner

            raw = None
            for name in ["path_world", "dense_path", "path"]:
                if hasattr(obj, name):
                    cand = getattr(obj, name)
                    if cand is not None and len(cand) >= 3:
                        raw = np.asarray(cand, dtype=np.float32)
                        break

            if raw is None or raw.ndim != 2 or raw.shape[0] < 3:
                return

            sig = self._v7_path_signature(raw)
            if sig is None:
                return

            # 如果已经对同一条 path 平滑过，就不要反复平滑
            if getattr(self, "_last_v7_smooth_sig", None) == sig:
                return

            dense = self._v7_resample_path(raw, step=0.06)
            smooth = self._v7_chaikin_smooth(dense, iters=2)
            smooth = self._v7_resample_path(smooth, step=0.04)

            if smooth is None or len(smooth) < 3:
                return

            # 保留起点终点，避免目标漂移
            smooth[0] = raw[0]
            smooth[-1] = raw[-1]

            obj.raw_astar_path = raw.copy()
            obj.smooth_ref_path = smooth.copy()

            # 让底层优先追平滑路径
            for name in ["path_world", "dense_path", "path"]:
                if hasattr(obj, name):
                    setattr(obj, name, smooth.copy())

            for idx_name in ["wp_index", "target_idx", "path_idx"]:
                if hasattr(obj, idx_name):
                    setattr(obj, idx_name, 0)

            if hasattr(obj, "path_len"):
                obj.path_len = len(smooth)

            self._last_v7_smooth_sig = self._v7_path_signature(smooth)
            self.last_v7_smooth_points = int(len(smooth))
            self.last_v7_raw_points = int(len(raw))

        except Exception:
            pass





    def _phase8_apply_exact_scene_edit_once(self):
        """
        Phase8 exact scene edit:
        只执行一次，使用绝对坐标，避免每回合累计移动。

        删除红圈圆柱：
          real_circle_obs_9, real_circle_obs_10

        场景箱体调整：
          real_rect_obs_6：上方左侧箱体，向右移动 1m
          real_rect_obs_8：下方左侧箱体，向右上角移动 1m
          real_rect_obs_9：下方右侧箱体，向右上角移动 1m

        其他障碍物不动。
        """
        if getattr(self, "_phase8_exact_scene_edit_done", False):
            return

        try:
            import mujoco
        except Exception:
            return

        model = getattr(self.inner, "model", None)
        data = getattr(self.inner, "data", None)

        if model is None:
            model = getattr(self, "model", None)
        if data is None:
            data = getattr(self, "data", None)
        if model is None:
            return

        remove_geoms = {
            "real_circle_obs_9",
            "real_circle_obs_10",
        }

        # 使用绝对坐标，不会随 reset 重复累加
        set_geom_xy = {
            # 上面左侧箱体：之前约 (-6.083, 1.612)，向右 1m
            "real_rect_obs_6": (-5.083,  1.612),

            # 右下竖箱体：保持之前位置，不再移动
            "real_rect_obs_7": ( 5.638, -4.315),

            # 下面左侧箱体：之前约 (-3.202, -5.531)，向右上角 1m
            "real_rect_obs_8": (-2.202, -4.531),

            # 下面右侧箱体：之前约 (2.200, -3.850)，向右上角 1m
            "real_rect_obs_9": ( 3.200, -2.850),
        }

        removed = []
        moved = []

        for gid in range(model.ngeom):
            gname = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, gid)
            if not gname:
                continue

            if gname in remove_geoms:
                model.geom_rgba[gid, 3] = 0.0
                model.geom_contype[gid] = 0
                model.geom_conaffinity[gid] = 0
                model.geom_pos[gid, 2] = -10.0
                removed.append(gname)

            if gname in set_geom_xy:
                old_x = float(model.geom_pos[gid, 0])
                old_y = float(model.geom_pos[gid, 1])
                new_x, new_y = set_geom_xy[gname]

                model.geom_pos[gid, 0] = float(new_x)
                model.geom_pos[gid, 1] = float(new_y)

                moved.append((gname, round(old_x, 3), round(old_y, 3), round(new_x, 3), round(new_y, 3)))

        try:
            mujoco.mj_forward(model, data)
        except Exception:
            pass

        print("[Phase8 exact scene edit] removed:", removed)
        print("[Phase8 exact scene edit] set box xy:", moved)

        self._phase8_exact_scene_edit_done = True

    def reset(self, **kwargs):
        out = super().reset(**kwargs)
        self._apply_turn35_params()
        self._last_v7_smooth_sig = None
        self._apply_smooth_ref_path()
        self._phase8_apply_exact_scene_edit_once()
        return out

    def step(self, action):
        self._apply_turn35_params()
        self._apply_smooth_ref_path()

        action = np.asarray(action, dtype=np.float32).reshape(2)
        action = np.clip(action, -1.0, 1.0)

        base_action = self._base_action(self.last_raw_obs)
        residual_action = self.residual_scale * action
        final_action = np.clip(base_action + residual_action, -1.0, 1.0)

        # 只对前进速度做一次性放大，不改底层变量，避免指数爆炸
        if final_action[1] > 0.0:
            final_action[1] = np.clip(final_action[1] * self.speed_boost, -1.0, 1.0)

        # v7 speed fix:
        # v2 偶尔会出现负速度，导致绕圈/慢速修正。
        # v7 先禁止倒车，并提高正向速度。
        # clean v7: do not force reverse action into forward speed

        if final_action[1] > 0.0:
            final_action[1] = np.clip(final_action[1], -1.0, 1.0)

        # 目标附近仍然保持前进，不允许原地磨蹭
        try:
            goal_dist = float(np.linalg.norm(self.inner.goal_xy - self.inner.robot_xy))
        except Exception:
            goal_dist = 999.0

        if goal_dist < 3.0:
            final_action[1] = float(final_action[1])

        if goal_dist < 1.5:
            final_action[1] = float(final_action[1])

        self.last_base_action = base_action.astype(np.float32)
        self.last_residual_action = residual_action.astype(np.float32)
        self.last_final_action = final_action.astype(np.float32)
        self.last_v7_goal_dist = goal_dist

        # v7 real speed override:
        # action[1] 已经到 1.0 后，必须改所有 inner 层底层轮速。
        # 同时尽量关闭转弯降速。
        try:
            objs = []
            cur = self
            for _ in range(12):
                if cur is None or cur in objs:
                    break
                objs.append(cur)
                cur = getattr(cur, "inner", None) or getattr(cur, "env", None) or getattr(cur, "unwrapped", None)

            for obj in objs:
                if hasattr(obj, "max_wheel_speed"):
                    obj.max_wheel_speed = float(obj.max_wheel_speed)

                for name in [
                    "turn_speed_scale",
                    "corner_speed_scale",
                    "steer_speed_scale",
                    "speed_turn_scale",
                    "turn_slowdown",
                    "corner_slowdown",
                    "steer_slowdown",
                ]:
                    if hasattr(obj, name):
                        setattr(obj, name, 1.0)

                for name in [
                    "min_turn_speed",
                    "min_corner_speed",
                    "min_forward_speed",
                    "min_wheel_norm",
                ]:
                    if hasattr(obj, name):
                        setattr(obj, name, 0.85)

        except Exception:
            pass

        # 转弯时也不要让速度掉太低
        steer_abs = abs(float(final_action[0]))
        if steer_abs < 0.80:
            final_action[1] = float(final_action[1])
        else:
            final_action[1] = float(final_action[1])

        final_action[1] = np.clip(final_action[1], 0.0, 1.0)

        # v7 steer angle override:
        # v2 保持 35°，v7 测试提升到 40°
        try:
            import math
            objs = []
            cur = self
            for _ in range(12):
                if cur is None or cur in objs:
                    break
                objs.append(cur)
                cur = getattr(cur, "inner", None) or getattr(cur, "env", None) or getattr(cur, "unwrapped", None)

            for obj in objs:
                if hasattr(obj, "max_steer_deg"):
                    obj.max_steer_deg = 40.0
                if hasattr(obj, "max_steer_rad"):
                    obj.max_steer_rad = math.radians(40.0)
                if hasattr(obj, "max_steer_angle"):
                    obj.max_steer_angle = math.radians(40.0)
                if hasattr(obj, "steer_limit"):
                    obj.steer_limit = math.radians(40.0)
        except Exception:
            pass

        # v7 path safety:
        # v2 的 A* clearance 约 0.18，离障碍太近。
        # v7 扩大路径安全距离，并提前转弯。
        try:
            objs = []
            cur = self
            for _ in range(12):
                if cur is None or cur in objs:
                    break
                objs.append(cur)
                cur = getattr(cur, "inner", None) or getattr(cur, "env", None) or getattr(cur, "unwrapped", None)

            for obj in objs:
                # A* 障碍膨胀 / 安全距离
                for name in [
                    "astar_clearance",
                    "path_clearance",
                    "obstacle_clearance",
                    "planning_clearance",
                    "inflation_radius",
                    "obstacle_inflation",
                ]:
                    if hasattr(obj, name):
                        setattr(obj, name, max(float(getattr(obj, name)), 0.30))

                # 提前转弯：不要等车身过一半才转
                for name in [
                    "turn_after_body_ratio",
                    "turn_after_ratio",
                    "corner_after_body_ratio",
                ]:
                    if hasattr(obj, name):
                        setattr(obj, name, 0.32)

                # lookahead 不要太大，避免绕大圈；不要太小，避免贴障碍
                for name in [
                    "lookahead_distance",
                    "lookahead_dist",
                    "target_lookahead",
                ]:
                    if hasattr(obj, name):
                        v = float(getattr(obj, name))
                        setattr(obj, name, min(max(v, 0.90), 1.60))

        except Exception:
            pass

        self._apply_smooth_ref_path()
        out = self.inner.step(final_action)

        if len(out) == 5:
            raw_obs, reward, terminated, truncated, info = out
            done = bool(terminated or truncated)
            is_gymnasium = True
        else:
            raw_obs, reward, done, info = out
            terminated = bool(done)
            truncated = False
            is_gymnasium = False

        self.last_raw_obs = np.asarray(raw_obs, dtype=np.float32)

        path_error = float(self.inner._nearest_path_error())
        residual_norm = float(np.linalg.norm(residual_action))

        shaped_reward = float(reward)
        shaped_reward -= self.residual_penalty * residual_norm
        shaped_reward -= self.path_error_penalty * max(0.0, path_error - 0.22)

        obs = self._make_obs(self.last_raw_obs)

        if isinstance(info, dict):
            info["base_action"] = self.last_base_action.copy()
            info["residual_action"] = self.last_residual_action.copy()
            info["final_action"] = self.last_final_action.copy()
            info["v7_goal_dist"] = float(getattr(self, "last_v7_goal_dist", -1.0))
            info["v7_final_speed"] = float(self.last_final_action[1])
            info["v7_final_steer"] = float(self.last_final_action[0])
            info["v7_smooth_points"] = int(getattr(self, "last_v7_smooth_points", -1))
            info["v7_raw_points"] = int(getattr(self, "last_v7_raw_points", -1))

        if is_gymnasium:
            return obs, shaped_reward, terminated, truncated, info

        return obs, shaped_reward, bool(done), info
