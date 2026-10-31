import math
import numpy as np

try:
    from training.phase9_static_no_dynamic.envs.mkmini_phase9i1_kinematic_guard_env import (
        MkMiniPhase9I1KinematicGuardEnv as Phase14BaseEnv,
    )
    PHASE14_BASE_NAME = "Phase9-I1 kinematic guard"
except Exception:
    try:
        from training.phase9_static_no_dynamic.envs.mkmini_phase9h3_kinematic_yaw_sync_env import (
            MkMiniPhase9H3KinematicYawSyncEnv as Phase14BaseEnv,
        )
        PHASE14_BASE_NAME = "Phase9-H3 kinematic yaw sync"
    except Exception:
        from training.phase9_static_no_dynamic.envs.mkmini_phase9g2_safe_speed_steer_env import (
            MkMiniPhase9G2SafeSpeedSteerEnv as Phase14BaseEnv,
        )
        PHASE14_BASE_NAME = "Phase9-G2 safe-speed-steer fallback"


class MkMiniPhase14Phase9YawSyncFastNavEnv(Phase14BaseEnv):
    """
    Phase14-D official route.

    Base:
        Phase9-G2 safe-speed-steer environment

    Control:
        Phase10/11-style stable car-like speed / steering parameters

    Policy:
        Keep inherited SAC residual action interface.

    Visualization:
        Expose goal_xy, raw_astar_path, smooth_ref_path for MuJoCo viewer.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.phase14_name = "phase14_phase9_yawsync_fast_nav"

        # Phase10/11 stable control target values
        # Phase11-F2 stable speed profile
        # RL does not directly control steer/wheel.
        # It only tunes/residuals around a stable car-like controller.
        self.phase14_base_name = PHASE14_BASE_NAME

        # Phase14-E fast but still stable profile
        self.phase14_assist_scale = 0.15

        # Phase10/11 parameter tuning range center
        self.phase14_p10_cte_gain = 0.18
        self.phase14_p10_goal_capture_speed = 3.20
        self.phase14_p10_min_wheel = 2.00
        self.phase14_p10_steer_gain = 0.96

        self.phase14_p10_min_lookahead = 0.72
        self.phase14_p10_max_lookahead = 1.85
        self.phase14_p10_lookahead_speed_gain = 0.85

        # faster than Phase11-F2, but not as wild as direct wheel control
        self.phase14_p10_speed_boost = 0.95
        self.phase14_p10_straight_wheel = 6.2 * self.phase14_p10_speed_boost
        self.phase14_p10_curve_wheel = 4.2 * self.phase14_p10_speed_boost

        # key fix: wheel steering and body yaw sync
        self.phase14_turn_after_body_ratio = 0.65
        self.phase14_p10_bicycle_yaw_gain = 1.55
        self.phase14_p10_bicycle_speed_gain = 0.036
        self.phase14_p10_bicycle_wheelbase = 0.42

        # A* safety expansion
        self.phase14_p10_astar_expand = 0.18

        self._phase14_apply_p10p11_params()

    def _phase14_targets(self):
        targets = [self]
        obj = self
        visited = set()

        for _ in range(8):
            if id(obj) in visited:
                break
            visited.add(id(obj))

            for name in ["inner", "env", "unwrapped"]:
                if hasattr(obj, name):
                    nxt = getattr(obj, name)
                    if nxt is not None and id(nxt) not in visited:
                        targets.append(nxt)
                        obj = nxt
                        break
            else:
                break

        return targets

    def _phase14_set_if_exists(self, obj, names, value, mode="set"):
        for name in names:
            if hasattr(obj, name):
                old = getattr(obj, name)
                try:
                    if mode == "max":
                        setattr(obj, name, max(float(old), float(value)))
                    elif mode == "min":
                        setattr(obj, name, min(float(old), float(value)))
                    else:
                        setattr(obj, name, float(value))
                except Exception:
                    pass

    def _phase14_apply_p10p11_params(self):
        for obj in self._phase14_targets():
            # Phase9-G2 speed/steer layer
            self._phase14_set_if_exists(
                obj,
                ["phase9g_astar_safety_expand", "astar_safety_margin", "astar_clearance",
                 "astar_expand", "astar_inflate_radius", "path_clearance", "astar_robot_radius"],
                self.phase14_p10_astar_expand,
                mode="max",
            )

            # Phase10-style controller parameters if present
            self._phase14_set_if_exists(obj, ["p10_cte_gain"], self.phase14_p10_cte_gain)
            self._phase14_set_if_exists(obj, ["p10_goal_capture_speed"], self.phase14_p10_goal_capture_speed)
            self._phase14_set_if_exists(obj, ["p10_min_wheel"], self.phase14_p10_min_wheel)
            self._phase14_set_if_exists(obj, ["p10_steer_gain"], self.phase14_p10_steer_gain)

            self._phase14_set_if_exists(obj, ["p10_min_lookahead"], self.phase14_p10_min_lookahead)
            self._phase14_set_if_exists(obj, ["p10_max_lookahead"], self.phase14_p10_max_lookahead)
            self._phase14_set_if_exists(obj, ["p10_lookahead_speed_gain"], self.phase14_p10_lookahead_speed_gain)
            self._phase14_set_if_exists(obj, ["p10_speed_boost"], self.phase14_p10_speed_boost)
            self._phase14_set_if_exists(obj, ["p10_straight_wheel"], self.phase14_p10_straight_wheel)
            self._phase14_set_if_exists(obj, ["p10_curve_wheel"], self.phase14_p10_curve_wheel)

            # Phase9 equivalent speed tuning
            self._phase14_set_if_exists(obj, ["phase9g_base_wheel_norm", "phase9e_base_wheel_norm", "phase9d_base_wheel_norm"], 1.0)
            self._phase14_set_if_exists(obj, ["phase9g_max_wheel_speed", "phase9e_max_wheel_speed", "phase9d_max_wheel_speed", "max_wheel_speed"], 48.0)
            self._phase14_set_if_exists(obj, ["phase9g_wheel_ctrlrange", "phase9e_wheel_ctrlrange", "phase9d_wheel_ctrlrange", "wheel_ctrlrange"], 56.0)
            self._phase14_set_if_exists(obj, ["phase9g_lookahead", "path_lookahead", "target_lookahead"], 1.15, mode="max")

            # yaw-sync / car-like kinematics
            self._phase14_set_if_exists(
                obj,
                ["phase9g_turn_after_body_ratio", "turn_after_body_ratio", "p10_turn_after_body_ratio"],
                self.phase14_turn_after_body_ratio,
            )
            self._phase14_set_if_exists(obj, ["p10_bicycle_yaw_gain", "bicycle_yaw_gain"], self.phase14_p10_bicycle_yaw_gain)
            self._phase14_set_if_exists(obj, ["p10_bicycle_speed_gain", "bicycle_speed_gain"], self.phase14_p10_bicycle_speed_gain)
            self._phase14_set_if_exists(obj, ["p10_bicycle_wheelbase", "bicycle_wheelbase"], self.phase14_p10_bicycle_wheelbase)

            # allow stronger steering response
            self._phase14_set_if_exists(obj, ["max_steer_delta", "preview_steer_max_delta"], 0.10, mode="max")

    def reset(self, **kwargs):
        out = super().reset(**kwargs)
        self._phase14_apply_p10p11_params()
        return out

    def step(self, action):
        self._phase14_apply_p10p11_params()

        # Phase14-F safety residual:
        # SAC action is scaled before entering the low-level controller.
        raw_action = np.asarray(action, dtype=np.float32)
        safe_action = np.clip(raw_action, -1.0, 1.0) * float(self.phase14_assist_scale)

        out = super().step(safe_action)

        # Phase14-E key fix: force body yaw to follow wheel steering.
        self._phase14_apply_bicycle_yaw_sync()

        if len(out) == 5:
            obs, reward, terminated, truncated, info = out
            info = self._phase14_fill_info(info)
            return obs, reward, terminated, truncated, info

        obs, reward, done, info = out
        info = self._phase14_fill_info(info)
        return obs, reward, done, info

    def _phase14_fill_info(self, info):
        if info is None:
            info = {}

        info["phase14_env"] = self.phase14_name
        info["phase14_speed_profile"] = "phase14_E_yawsync_fast_phase10_11_12_style"
        info["phase14_base_name"] = str(self.phase14_base_name)
        info["phase14_assist_scale"] = float(self.phase14_assist_scale)
        info["phase14_turn_after_body_ratio"] = float(self.phase14_turn_after_body_ratio)
        info["phase14_bicycle_yaw_gain"] = float(self.phase14_p10_bicycle_yaw_gain)
        info["phase14_bicycle_speed_gain"] = float(self.phase14_p10_bicycle_speed_gain)
        info["phase14_yaw_sync_steer"] = float(getattr(self, "phase14_last_yaw_sync_steer", 0.0))
        info["phase14_yaw_sync_wheel"] = float(getattr(self, "phase14_last_yaw_sync_wheel", 0.0))
        info["phase14_yaw_sync_v"] = float(getattr(self, "phase14_last_yaw_sync_v", 0.0))
        info["phase14_yaw_sync_yaw_rate"] = float(getattr(self, "phase14_last_yaw_sync_yaw_rate", 0.0))
        info["phase14_action_scaled"] = True
        info["phase14_action_assist_scale"] = float(self.phase14_assist_scale)
        info["phase14_p10_goal_capture_speed"] = float(self.phase14_p10_goal_capture_speed)
        info["phase14_p10_min_wheel"] = float(self.phase14_p10_min_wheel)
        info["phase14_p10_straight_wheel"] = float(self.phase14_p10_straight_wheel)
        info["phase14_p10_curve_wheel"] = float(self.phase14_p10_curve_wheel)

        goal = self.get_phase14_goal_xy()
        if goal is not None:
            info["phase14_goal_x"] = float(goal[0])
            info["phase14_goal_y"] = float(goal[1])

        raw = self.get_phase14_raw_astar_path()
        smooth = self.get_phase14_smooth_path()

        info["phase14_raw_astar_len"] = int(len(raw)) if raw is not None else 0
        info["phase14_smooth_path_len"] = int(len(smooth)) if smooth is not None else 0

        return info

    def _get_attr_recursive(self, names):
        for obj in self._phase14_targets():
            for name in names:
                if hasattr(obj, name):
                    val = getattr(obj, name)
                    if val is not None:
                        return val
        return None


    def _phase14_wrap_angle(self, a):
        return (float(a) + math.pi) % (2.0 * math.pi) - math.pi

    def _phase14_get_ctrl_steer_wheel(self):
        steer = None
        wheel = None

        # Prefer known actuator ids if available
        for obj in self._phase14_targets():
            if not hasattr(obj, "data"):
                continue

            data = obj.data

            try:
                if hasattr(obj, "id_lf_steer") and hasattr(obj, "id_rf_steer"):
                    steer = 0.5 * (
                        float(data.ctrl[obj.id_lf_steer]) +
                        float(data.ctrl[obj.id_rf_steer])
                    )
                elif hasattr(obj, "id_steer"):
                    steer = float(data.ctrl[obj.id_steer])
            except Exception:
                pass

            try:
                if hasattr(obj, "id_lr_wheel") and hasattr(obj, "id_rr_wheel"):
                    wheel = 0.5 * (
                        float(data.ctrl[obj.id_lr_wheel]) +
                        float(data.ctrl[obj.id_rr_wheel])
                    )
                elif hasattr(obj, "id_wheel"):
                    wheel = float(data.ctrl[obj.id_wheel])
            except Exception:
                pass

        # Fallback from info-like attrs if parent stores them
        for obj in self._phase14_targets():
            if steer is None:
                for name in ["last_steer", "p10_prev_steer", "current_steer", "steer"]:
                    if hasattr(obj, name):
                        try:
                            steer = float(getattr(obj, name))
                            break
                        except Exception:
                            pass

            if wheel is None:
                for name in ["last_wheel", "current_wheel", "wheel"]:
                    if hasattr(obj, name):
                        try:
                            wheel = float(getattr(obj, name))
                            break
                        except Exception:
                            pass

        if steer is None:
            steer = 0.0
        if wheel is None:
            wheel = self.phase14_p10_straight_wheel

        steer = float(np.clip(steer, -0.65, 0.65))
        wheel = max(0.0, float(wheel))
        return steer, wheel

    def _phase14_apply_bicycle_yaw_sync(self):
        """
        Force car-like body yaw synchronization after parent step.

        MuJoCo wheel steering alone may not rotate chassis enough because the
        simplified wheel/ground contact can slide. This kinematic correction
        follows the Phase10 idea: body yaw changes according to steer + wheel.
        """
        target = None
        for obj in self._phase14_targets():
            if hasattr(obj, "data") and hasattr(obj, "model"):
                target = obj
                break

        if target is None:
            return

        data = target.data

        try:
            qpos = data.qpos
            qvel = data.qvel
        except Exception:
            return

        if len(qpos) < 7:
            return

        steer, wheel = self._phase14_get_ctrl_steer_wheel()

        dt = 0.02
        for obj in self._phase14_targets():
            if hasattr(obj, "dt"):
                try:
                    dt = float(obj.dt)
                    break
                except Exception:
                    pass
            if hasattr(obj, "control_dt"):
                try:
                    dt = float(obj.control_dt)
                    break
                except Exception:
                    pass

        # Current yaw from free joint quaternion qpos[3:7]
        try:
            qw, qx, qy, qz = map(float, qpos[3:7])
            yaw = math.atan2(
                2.0 * (qw * qz + qx * qy),
                1.0 - 2.0 * (qy * qy + qz * qz),
            )
        except Exception:
            return

        v = self.phase14_p10_bicycle_speed_gain * wheel
        yaw_rate = (
            self.phase14_p10_bicycle_yaw_gain
            * v
            / max(self.phase14_p10_bicycle_wheelbase, 1e-3)
            * math.tan(steer)
        )

        yaw_new = self._phase14_wrap_angle(yaw + yaw_rate * dt)

        # update x/y according to yaw_new
        qpos[0] = float(qpos[0]) + v * math.cos(yaw_new) * dt
        qpos[1] = float(qpos[1]) + v * math.sin(yaw_new) * dt

        # yaw-only quaternion
        qpos[3] = math.cos(0.5 * yaw_new)
        qpos[4] = 0.0
        qpos[5] = 0.0
        qpos[6] = math.sin(0.5 * yaw_new)

        # qvel approximate
        if len(qvel) >= 6:
            qvel[0] = v * math.cos(yaw_new)
            qvel[1] = v * math.sin(yaw_new)
            qvel[5] = yaw_rate

        self.phase14_last_yaw_sync_steer = float(steer)
        self.phase14_last_yaw_sync_wheel = float(wheel)
        self.phase14_last_yaw_sync_v = float(v)
        self.phase14_last_yaw_sync_yaw_rate = float(yaw_rate)


    def get_phase14_goal_xy(self):
        val = self._get_attr_recursive(["goal_xy", "p10_locked_goal"])
        if val is None:
            return None
        arr = np.asarray(val, dtype=np.float32).reshape(-1)
        if arr.size < 2:
            return None
        return arr[:2].copy()

    def get_phase14_raw_astar_path(self):
        val = self._get_attr_recursive(["raw_astar_path", "path_world", "dense_path", "path"])
        if val is None:
            return None
        arr = np.asarray(val, dtype=np.float32)
        if arr.ndim != 2 or arr.shape[1] < 2 or len(arr) < 2:
            return None
        return arr[:, :2].copy()

    def get_phase14_smooth_path(self):
        val = self._get_attr_recursive(["smooth_ref_path"])
        if val is None:
            return None
        arr = np.asarray(val, dtype=np.float32)
        if arr.ndim != 2 or arr.shape[1] < 2 or len(arr) < 2:
            return None
        return arr[:, :2].copy()
