import math
import numpy as np
import mujoco

from training.phase9_static_no_dynamic.envs.mkmini_phase9_static_no_dynamic_env import (
    MkMiniPhase9StaticNoDynamicEnv,
)


class MkMiniPhase9H2SteerFirstNoDiffEnv(MkMiniPhase9StaticNoDynamicEnv):
    """
    Phase9-H2: steer-first + no differential turning.

    目标：
    1. 不继承 G4/G5
    2. 禁止后轮差速掉头
    3. 前轮还没转到位时，先减速/刹车
    4. 大转角低速
    5. 只在 Phase9 内生效
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.h2_max_steer = 0.52          # 约 30°
        self.h2_steer_alpha = 0.11        # 前轮平滑
        self.h2_wheel_alpha = 0.08        # 后轮速度平滑
        self.h2_steer_ready_err = 0.06    # 实际转角未到位阈值
        self.h2_reverse_hold_steps = 24   # 换向先停一小段
        self.h2_reverse_hold = 0

        self._h2_lf = 0.0
        self._h2_rf = 0.0
        self._h2_lr = 0.0
        self._h2_rr = 0.0
        self._h2_last_steer_cmd = 0.0

        # 提前看远一点，避免到墙边才转
        self._set_if_exists("lookahead_dist", 1.55)
        self._set_if_exists("lookahead", 1.55)
        self._set_if_exists("astar_lookahead", 1.55)
        self._set_if_exists("path_lookahead", 1.55)

        # 不让路径贴障碍太近
        self._set_if_exists("astar_expand", 0.34)
        self._set_if_exists("robot_radius", 0.28)

        # 全局限速
        self._set_if_exists("max_wheel_speed", 18.0)
        self._set_if_exists("base_wheel_norm", 0.58)

        self._patch_vehicle_runtime()

        print(
            "[Phase9-H2.1 steer-first-yaw-lag-brake] enabled: "
            "base=Phase9-A, no G4/G5, rear_sync, steer_first_brake"
        )

    def _set_if_exists(self, name, value):
        if hasattr(self, name):
            try:
                setattr(self, name, value)
            except Exception:
                pass

    def _mj_id(self, obj_type, name):
        idx = mujoco.mj_name2id(self.model, obj_type, name)
        if idx < 0:
            raise RuntimeError(f"MuJoCo object not found: {name}")
        return int(idx)

    def _patch_vehicle_runtime(self):
        model = self.model
        self.max_steer = self.h2_max_steer

        # 前轮转向关节：温和扩大到 30°，不要 50°/0.90rad
        for jname in ["left_front_steer_joint", "right_front_steer_joint"]:
            jid = self._mj_id(mujoco.mjtObj.mjOBJ_JOINT, jname)
            model.jnt_limited[jid] = 1
            model.jnt_range[jid, 0] = -self.h2_max_steer
            model.jnt_range[jid, 1] = +self.h2_max_steer

            dof = int(model.jnt_dofadr[jid])
            model.dof_damping[dof] = 0.8
            model.dof_frictionloss[dof] = 0.0
            if hasattr(model, "dof_armature"):
                model.dof_armature[dof] = 0.02

        # 前轮转向 actuator：温和增强，不暴力
        for aname in ["left_front_steer_act", "right_front_steer_act"]:
            aid = self._mj_id(mujoco.mjtObj.mjOBJ_ACTUATOR, aname)

            if hasattr(model, "actuator_ctrllimited"):
                model.actuator_ctrllimited[aid] = 1
            model.actuator_ctrlrange[aid, 0] = -self.h2_max_steer
            model.actuator_ctrlrange[aid, 1] = +self.h2_max_steer

            if hasattr(model, "actuator_forcelimited"):
                model.actuator_forcelimited[aid] = 1
            if hasattr(model, "actuator_forcerange"):
                model.actuator_forcerange[aid, 0] = -600.0
                model.actuator_forcerange[aid, 1] = +600.0

            if model.actuator_gainprm.shape[1] > 0:
                model.actuator_gainprm[aid, 0] = 1200.0

        # actuator id
        self.id_lf_steer = self._mj_id(mujoco.mjtObj.mjOBJ_ACTUATOR, "left_front_steer_act")
        self.id_rf_steer = self._mj_id(mujoco.mjtObj.mjOBJ_ACTUATOR, "right_front_steer_act")
        self.id_lr_wheel = self._mj_id(mujoco.mjtObj.mjOBJ_ACTUATOR, "left_rear_wheel_act")
        self.id_rr_wheel = self._mj_id(mujoco.mjtObj.mjOBJ_ACTUATOR, "right_rear_wheel_act")

        # joint qpos address，用于判断真实前轮是否转到位
        self.j_lf_steer = self._mj_id(mujoco.mjtObj.mjOBJ_JOINT, "left_front_steer_joint")
        self.j_rf_steer = self._mj_id(mujoco.mjtObj.mjOBJ_JOINT, "right_front_steer_joint")
        self.qadr_lf_steer = int(model.jnt_qposadr[self.j_lf_steer])
        self.qadr_rf_steer = int(model.jnt_qposadr[self.j_rf_steer])

        # 温和提高轮胎/地面摩擦，不暴力改
        touched = []
        for gid in range(model.ngeom):
            gname = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, gid) or ""
            bid = int(model.geom_bodyid[gid])
            bname = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, bid) or ""
            lname = (gname + " " + bname).lower()

            if "wheel" in lname:
                model.geom_friction[gid, 0] = 8.0
                model.geom_friction[gid, 1] = 1.2
                model.geom_friction[gid, 2] = 0.10
                touched.append(gname or bname)

            if "floor" in lname or "ground" in lname:
                model.geom_friction[gid, 0] = 6.0
                model.geom_friction[gid, 1] = 0.8
                model.geom_friction[gid, 2] = 0.08

        print("[Phase9-H2 friction touched]", touched[:20])

    def _actual_front_steer(self):
        lf = float(self.data.qpos[self.qadr_lf_steer])
        rf = float(self.data.qpos[self.qadr_rf_steer])
        return 0.5 * (lf + rf)

    def _lowpass(self, old, new, alpha):
        return float((1.0 - alpha) * old + alpha * new)

    def _ackermann_from_steer_speed(self, steer, wheel_speed):
        # 1. 限制前轮最大转角
        steer = float(np.clip(steer, -self.h2_max_steer, self.h2_max_steer))

        # 2. 如果转向方向突然反了，先刹一小段，避免掉头转圈
        if (
            self._h2_last_steer_cmd * steer < 0.0
            and abs(self._h2_last_steer_cmd) > 0.16
            and abs(steer) > 0.16
        ):
            self.h2_reverse_hold = self.h2_reverse_hold_steps

        self._h2_last_steer_cmd = steer

        # 3. 前轮转向指令低通
        steer_cmd = self._lowpass(
            0.5 * (self._h2_lf + self._h2_rf),
            steer,
            self.h2_steer_alpha,
        )

        # 4. 后轮速度先限幅
        max_wheel_speed = float(getattr(self, "max_wheel_speed", 24.0))
        wheel_speed = float(np.clip(wheel_speed, -max_wheel_speed, max_wheel_speed))

        # 5. 大转角低速
        abs_steer = abs(steer_cmd)
        if abs_steer > 0.12:
            limit = float(np.interp(abs_steer, [0.12, self.h2_max_steer], [5.2, 1.3]))
            wheel_speed = float(np.clip(wheel_speed, -limit, limit))

        # 6. 前轮还没转到位，不允许车身继续往前冲
        actual_steer = self._actual_front_steer()
        steer_err = abs(steer_cmd - actual_steer)

        if abs_steer > 0.18 and steer_err > self.h2_steer_ready_err:
            wheel_speed *= 0.05

        # H2.1: yaw-lag brake
        # 前轮已经转向，但车身 yaw 没明显响应时，继续限速，避免“轮子转了车身还往前冲”
        if abs_steer > 0.18 and abs(wheel_speed) > 0.4:
            yaw_rate = 0.0
            if self.data.qvel.shape[0] > 5:
                yaw_rate = float(self.data.qvel[5])

            expected_sign = 1.0 if steer_cmd * wheel_speed > 0.0 else -1.0
            if yaw_rate * expected_sign < 0.08:
                wheel_speed *= 0.35

        # 7. 换向保护期间，直接刹车
        if self.h2_reverse_hold > 0:
            wheel_speed = 0.0
            self.h2_reverse_hold -= 1

        # 8. 禁止大转角倒车，因为容易原地掉头
        if abs_steer > 0.20 and wheel_speed < 0.0:
            wheel_speed = 0.0

        # 9. 前轮左右同角，先不要复杂内外轮 Ackermann，避免视觉和动力学发散
        lf = steer_cmd
        rf = steer_cmd

        # 10. 后轮完全同步，不允许差速
        lr = wheel_speed
        rr = wheel_speed

        # 11. 后轮速度低通
        lr = self._lowpass(self._h2_lr, lr, self.h2_wheel_alpha)
        rr = self._lowpass(self._h2_rr, rr, self.h2_wheel_alpha)

        self._h2_lf = lf
        self._h2_rf = rf
        self._h2_lr = lr
        self._h2_rr = rr

        return lf, rf, lr, rr

    def _apply_wheel_ctrl(self, lf, rf, lr, rr):
        # 彻底禁止后轮差速
        avg = 0.5 * (lr + rr)

        # 如果出现一正一反，说明上层想让它差速掉头，直接刹住
        if lr * rr < 0.0:
            avg = 0.0

        # 大转角继续限速
        steer_abs = max(abs(lf), abs(rf))
        if steer_abs > 0.22:
            limit = float(np.interp(steer_abs, [0.22, self.h2_max_steer], [4.0, 1.3]))
            avg = float(np.clip(avg, -limit, limit))

        lr = avg
        rr = avg

        self.last_lf_steer = lf
        self.last_rf_steer = rf
        self.last_lr_wheel = lr
        self.last_rr_wheel = rr

        self.data.ctrl[:] = 0.0
        self.data.ctrl[self.id_lf_steer] = lf
        self.data.ctrl[self.id_rf_steer] = rf
        self.data.ctrl[self.id_lr_wheel] = lr
        self.data.ctrl[self.id_rr_wheel] = rr

    def reset(self, *args, **kwargs):
        out = super().reset(*args, **kwargs)

        self._h2_lf = 0.0
        self._h2_rf = 0.0
        self._h2_lr = 0.0
        self._h2_rr = 0.0
        self._h2_last_steer_cmd = 0.0
        self.h2_reverse_hold = 0

        return out
