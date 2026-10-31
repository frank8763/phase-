import math
import numpy as np
import mujoco

from training.phase9_static_no_dynamic.envs.mkmini_phase9h3_kinematic_yaw_sync_env import (
    MkMiniPhase9H3KinematicYawSyncEnv as H3BaseEnv,
)


class MkMiniPhase9I1KinematicGuardEnv(H3BaseEnv):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.i1_enable_guard = True

        self.i1_min_steer = 0.14
        self.i1_yaw_ratio_min = 0.68
        self.i1_min_speed_scale = 0.78

        self.i1_curve_start = 0.18
        self.i1_curve_max_steer = 0.52
        self.i1_curve_speed_mid = 9.0
        self.i1_curve_speed_min = 5.0

        self.i12_corner_entry_steer = 0.20
        self.i12_corner_release_ratio = 0.84
        self.i12_corner_hold_steps = 16
        self.i12_corner_speed_scale = 0.68
        self.i12_corner_hold = 0
        self.i12_prev_steer_abs = 0.0

        if hasattr(self, "h2_steer_alpha"):
            self.h2_steer_alpha = 0.18

        if hasattr(self, "h2_steer_ready_err"):
            self.h2_steer_ready_err = 0.040

        if hasattr(self, "max_steer_delta"):
            self.max_steer_delta = max(float(self.max_steer_delta), 0.150)

        if hasattr(self, "h3_kinematic_gain"):
            self.h3_kinematic_gain = min(float(self.h3_kinematic_gain) + 0.030, 0.66)

        if hasattr(self, "h3_velocity_align_gain"):
            self.h3_velocity_align_gain = min(float(self.h3_velocity_align_gain) + 0.020, 0.24)

        if hasattr(self, "h3_max_extra_dyaw"):
            self.h3_max_extra_dyaw = min(float(self.h3_max_extra_dyaw), 0.017)

        self.i15_enable_steer_lag_guard = True
        self.i15_min_target_steer = 0.17
        self.i15_steer_lag_err = 0.050
        self.i15_steer_lag_ratio = 0.72
        self.i15_speed_scale_min = 0.52
        self.i15_hold_steps = 10
        self.i15_hold = 0

        self._i15_patch_front_steer_response()

        print("[Phase9-I1.5 steer-lag guard] enabled")

    def _i15_patch_front_steer_response(self):
        model = self.model

        for jname in ["left_front_steer_joint", "right_front_steer_joint"]:
            jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, jname)
            if jid < 0:
                continue

            dof = int(model.jnt_dofadr[jid])
            model.dof_damping[dof] = 0.35
            model.dof_frictionloss[dof] = 0.0

            if hasattr(model, "dof_armature"):
                model.dof_armature[dof] = 0.008

        for aname in ["left_front_steer_act", "right_front_steer_act"]:
            aid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, aname)
            if aid < 0:
                continue

            if model.actuator_gainprm.shape[1] > 0:
                model.actuator_gainprm[aid, 0] = 1650.0

            if model.actuator_biasprm.shape[1] > 2:
                model.actuator_biasprm[aid, 1] = -1650.0
                model.actuator_biasprm[aid, 2] = -37.0

            if hasattr(model, "actuator_forcerange"):
                model.actuator_forcerange[aid, 0] = -820.0
                model.actuator_forcerange[aid, 1] = 820.0

    def _expected_yaw_rate_i1(self, steer, wheel):
        wheel_radius = float(getattr(self, "wheel_radius", 0.075))
        wheel_base = float(getattr(self, "wheel_base", 0.42))
        v = wheel * wheel_radius
        return v / max(wheel_base, 1e-4) * math.tan(steer)

    def _i15_get_real_front_steer(self):
        vals = []

        for jname in ["left_front_steer_joint", "right_front_steer_joint"]:
            jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, jname)
            if jid < 0:
                continue

            qadr = int(self.model.jnt_qposadr[jid])
            vals.append(float(self.data.qpos[qadr]))

        if len(vals) == 0:
            return None

        return float(sum(vals) / len(vals))

    def _apply_wheel_ctrl(self, lf, rf, lr, rr):
        if not self.i1_enable_guard:
            return super()._apply_wheel_ctrl(lf, rf, lr, rr)

        steer = 0.5 * (float(lf) + float(rf))
        wheel = 0.5 * (float(lr) + float(rr))
        steer_abs = abs(steer)

        lr = wheel
        rr = wheel

        if steer_abs > self.i1_curve_start:
            cap = float(
                np.interp(
                    steer_abs,
                    [self.i1_curve_start, self.i1_curve_max_steer],
                    [self.i1_curve_speed_mid, self.i1_curve_speed_min],
                )
            )
            wheel = float(np.clip(wheel, -cap, cap))
            lr = wheel
            rr = wheel

        if (
            steer_abs > self.i12_corner_entry_steer
            and self.i12_prev_steer_abs <= self.i12_corner_entry_steer
        ):
            self.i12_corner_hold = self.i12_corner_hold_steps

        self.i12_prev_steer_abs = steer_abs

        if self.i12_corner_hold > 0 and abs(wheel) > 0.2:
            expected_entry = self._expected_yaw_rate_i1(steer, wheel)

            actual_entry = 0.0
            if self.data.qvel.shape[0] > 5:
                actual_entry = float(self.data.qvel[5])

            ratio_entry = 1.0
            if abs(expected_entry) > 1e-4:
                ratio_entry = abs(actual_entry) / abs(expected_entry)

            if ratio_entry < self.i12_corner_release_ratio:
                wheel *= self.i12_corner_speed_scale
                lr = wheel
                rr = wheel
                self.i12_corner_hold -= 1
            else:
                self.i12_corner_hold = 0

        if (
            self.i15_enable_steer_lag_guard
            and steer_abs > self.i15_min_target_steer
            and abs(wheel) > 0.2
        ):
            real_steer = self._i15_get_real_front_steer()

            if real_steer is not None:
                real_abs = abs(real_steer)
                lag_err = steer_abs - real_abs
                same_dir = steer * real_steer > 0.0
                ratio = real_abs / max(steer_abs, 1e-4)

                need_wait = False

                if not same_dir and real_abs > 0.03:
                    need_wait = True

                if lag_err > self.i15_steer_lag_err:
                    need_wait = True

                if ratio < self.i15_steer_lag_ratio:
                    need_wait = True

                if need_wait:
                    self.i15_hold = self.i15_hold_steps

                if self.i15_hold > 0:
                    ratio_clip = float(np.clip(ratio, 0.0, self.i15_steer_lag_ratio))
                    scale = float(
                        np.interp(
                            ratio_clip,
                            [0.0, self.i15_steer_lag_ratio],
                            [self.i15_speed_scale_min, 1.0],
                        )
                    )

                    wheel *= scale
                    lr = wheel
                    rr = wheel
                    self.i15_hold -= 1

        if steer_abs > self.i1_min_steer and abs(wheel) > 0.2:
            expected = self._expected_yaw_rate_i1(steer, wheel)

            actual = 0.0
            if self.data.qvel.shape[0] > 5:
                actual = float(self.data.qvel[5])

            if abs(expected) > 1e-4:
                same_dir = actual * expected > 0.0
                ratio = abs(actual) / abs(expected)

                if (not same_dir) or ratio < self.i1_yaw_ratio_min:
                    ratio = float(np.clip(ratio, 0.0, self.i1_yaw_ratio_min))
                    scale = float(
                        np.interp(
                            ratio,
                            [0.0, self.i1_yaw_ratio_min],
                            [self.i1_min_speed_scale, 1.0],
                        )
                    )

                    wheel *= scale
                    lr = wheel
                    rr = wheel

        return super()._apply_wheel_ctrl(lf, rf, lr, rr)

    def reset(self, *args, **kwargs):
        out = super().reset(*args, **kwargs)
        self.i12_corner_hold = 0
        self.i12_prev_steer_abs = 0.0
        self.i15_hold = 0
        return out
