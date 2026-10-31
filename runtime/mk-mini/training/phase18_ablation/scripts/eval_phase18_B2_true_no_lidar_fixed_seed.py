import argparse
import csv
import glob
import math
import os
import re
import shutil
import random

import mujoco
import numpy as np
from stable_baselines3 import SAC

from training.phase17_fusion_safety_sac_nav.envs.mkmini_phase17c_lidar_camera_fusion_env import (
    MkMiniPhase17CLidarCameraFusionEnv as Phase17FullFusionEnv,
)


class MkMiniPhase18B2TrueNoLidarEnv(Phase17FullFusionEnv):
    """
    Phase18-B2 true LiDAR ablation.

    关闭：
    - Phase6 原始 LiDAR 32维
    - Phase6 LiDAR safety 4维
    - Phase6 基础模型的 LiDAR 输入
    - Phase17 新增 LiDAR 32维

    保留：
    - Camera / Depth
    - Safety Shield
    - 186维观测结构
    """

    PHASE6_LIDAR_START = 66
    PHASE6_LIDAR_END = 98

    PHASE6_SAFETY_START = 103
    PHASE6_SAFETY_END = 107

    def _phase18b2_mask_raw_obs(self, raw_obs):
        arr = np.asarray(raw_obs, dtype=np.float32).copy().reshape(-1)

        if arr.size >= self.PHASE6_LIDAR_END:
            arr[
                self.PHASE6_LIDAR_START:
                self.PHASE6_LIDAR_END
            ] = 1.0

        if arr.size >= self.PHASE6_SAFETY_END:
            arr[
                self.PHASE6_SAFETY_START:
                self.PHASE6_SAFETY_END
            ] = 1.0

        return arr

    def _base_action(self, raw_obs):
        masked = self._phase18b2_mask_raw_obs(raw_obs)
        return super()._base_action(masked)

    def _phase17c_get_lidar(self):
        return np.ones(
            self.phase17c_lidar_dim,
            dtype=np.float32,
        )

    def _phase17c_build_obs(self, base_obs):
        base = np.asarray(
            base_obs,
            dtype=np.float32,
        ).copy().reshape(-1)

        if base.size >= self.PHASE6_LIDAR_END:
            base[
                self.PHASE6_LIDAR_START:
                self.PHASE6_LIDAR_END
            ] = 1.0

        if base.size >= self.PHASE6_SAFETY_END:
            base[
                self.PHASE6_SAFETY_START:
                self.PHASE6_SAFETY_END
            ] = 1.0

        return super()._phase17c_build_obs(base)


MkMiniPhase17CLidarCameraFusionEnv = (
    MkMiniPhase18B2TrueNoLidarEnv
)


def reset_env(env, seed=None):
    try:
        out = env.reset(seed=seed)
    except TypeError:
        out = env.reset()
    if isinstance(out, tuple) and len(out) == 2:
        return out
    return out, {}


def step_env(env, action):
    out = env.step(action)
    if len(out) == 5:
        obs, reward, terminated, truncated, info = out
        return obs, reward, bool(terminated or truncated), info
    return out


def parse_step(path):
    name = os.path.basename(path)
    if "final" in name:
        return 999999999
    m = re.search(r"_(\d+)_steps\.zip$", name)
    if m:
        return int(m.group(1))
    return -1


def collect_models(ckpt_dir, min_steps):
    models = []
    for p in glob.glob(os.path.join(ckpt_dir, "*.zip")):
        step = parse_step(p)
        if step >= min_steps:
            models.append(p)
    return sorted(models, key=parse_step)


def get_robot_xy(env):
    if hasattr(env, "robot_xy"):
        try:
            a = np.asarray(env.robot_xy, dtype=np.float32).reshape(-1)
            if a.size >= 2:
                return float(a[0]), float(a[1])
        except Exception:
            pass

    try:
        return float(env.data.qpos[0]), float(env.data.qpos[1])
    except Exception:
        return None


def get_robot_yaw(env):
    for name in ["robot_yaw", "_robot_yaw", "yaw"]:
        if hasattr(env, name):
            try:
                return float(getattr(env, name))
            except Exception:
                pass

    try:
        q = env.data.qpos[3:7]
        return math.atan2(
            2.0 * (q[0] * q[3] + q[1] * q[2]),
            1.0 - 2.0 * (q[2] * q[2] + q[3] * q[3]),
        )
    except Exception:
        return 0.0


def get_final_dist(env, info):
    if isinstance(info, dict):
        for k in [
            "final_goal_dist",
            "goal_dist",
            "dist_to_goal",
            "distance_to_goal",
            "final_dist",
        ]:
            if k in info:
                try:
                    return float(info[k])
                except Exception:
                    pass

    try:
        robot_xy = np.asarray(env.robot_xy, dtype=np.float32)
        goal_xy = np.asarray(env.goal_xy, dtype=np.float32)
        return float(np.linalg.norm(goal_xy - robot_xy))
    except Exception:
        return float("nan")


def geom_name(model, gid):
    name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, int(gid))
    return name or f"geom_{gid}"


def robot_obstacle_contact(env):
    hits = []

    try:
        for i in range(env.data.ncon):
            c = env.data.contact[i]
            n1 = geom_name(env.model, c.geom1).lower()
            n2 = geom_name(env.model, c.geom2).lower()
            pair = n1 + " " + n2

            robot = any(k in pair for k in [
                "chassis_collision",
                "wheel",
                "lidar_body",
                "fr3",
                "d435i",
            ])

            obs = any(k in pair for k in [
                "real_rect_obs",
                "real_circle_obs",
            ])

            if robot and obs:
                hits.append((n1, n2))
    except Exception:
        pass

    return hits


def robot_sample_points(env, half_len=0.43, half_wid=0.27):
    xy = get_robot_xy(env)
    if xy is None:
        return []

    x, y = xy
    yaw = get_robot_yaw(env)

    c = math.cos(yaw)
    s = math.sin(yaw)

    xs = np.linspace(-half_len, half_len, 5)
    ys = np.linspace(-half_wid, half_wid, 3)

    pts = []
    for lx in xs:
        for ly in ys:
            wx = x + c * float(lx) - s * float(ly)
            wy = y + s * float(lx) + c * float(ly)
            pts.append((wx, wy))

    return pts


def check_map_penetration(env, margin=0.02):
    pts = robot_sample_points(env)
    hits = []

    rects = np.asarray(getattr(env, "rect_obstacles", []), dtype=np.float32)
    circles = np.asarray(getattr(env, "circle_obstacles", []), dtype=np.float32)

    if rects.ndim == 1 and rects.size == 4:
        rects = rects.reshape(1, 4)

    if circles.ndim == 1 and circles.size == 3:
        circles = circles.reshape(1, 3)

    for px, py in pts:
        if rects.ndim == 2 and rects.shape[1] >= 4:
            for i, r in enumerate(rects):
                cx, cy, hx, hy = map(float, r[:4])
                if abs(px - cx) <= hx + margin and abs(py - cy) <= hy + margin:
                    hits.append(f"rect_{i}")

        if circles.ndim == 2 and circles.shape[1] >= 3:
            for i, c in enumerate(circles):
                cx, cy, rr = map(float, c[:3])
                if math.hypot(px - cx, py - cy) <= rr + margin:
                    hits.append(f"circle_{i}")

    return hits



def set_episode_seed(env, seed):
    seed = int(seed)

    random.seed(seed)
    np.random.seed(seed)

    targets = [env]

    try:
        targets.extend(env._phase14_targets())
    except Exception:
        pass

    seen = set()

    rng_names = [
        "_phase17_rng",
        "phase17b_rng",
        "_phase15_rng",
        "phase15b_rng",
        "np_random",
    ]

    for target_index, obj in enumerate(targets):
        if obj is None or id(obj) in seen:
            continue

        seen.add(id(obj))

        for rng_index, name in enumerate(rng_names):
            if not hasattr(obj, name):
                continue

            rng_seed = seed + target_index * 1000 + rng_index * 37

            try:
                setattr(obj, name, np.random.default_rng(rng_seed))
            except Exception:
                pass


def eval_model(
    model_path,
    episodes,
    max_steps,
    success_dist,
    margin,
    base_seed,
):
    env = MkMiniPhase17CLidarCameraFusionEnv()
    model = SAC.load(model_path, env=env, device="cpu")

    rows = []

    for ep in range(1, episodes + 1):
        episode_seed = int(base_seed + ep - 1)
        set_episode_seed(env, episode_seed)
        obs, info = reset_env(env, seed=episode_seed)

        total_reward = 0.0
        collision = False
        contact_collision = False
        penetration = False
        timeout = False
        final_dist = float("nan")
        steps = 0
        first_hit = ""

        sync_rect = -1
        sync_circle = -1

        if isinstance(info, dict):
            sync_rect = int(info.get("phase17b_synced_rect_count", -1))
            sync_circle = int(info.get("phase17b_synced_circle_count", -1))

        for t in range(max_steps):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = step_env(env, action)

            steps = t + 1
            total_reward += float(reward)
            final_dist = get_final_dist(env, info)

            info_collision = False
            if isinstance(info, dict):
                info_collision = bool(
                    info.get("collision", False)
                    or info.get("collided", False)
                    or info.get("strict_collision", False)
                )
                timeout = bool(timeout or info.get("timeout", False))

            contact_hits = robot_obstacle_contact(env)
            map_hits = check_map_penetration(env, margin=margin)

            if contact_hits:
                contact_collision = True

            if map_hits:
                penetration = True
                first_hit = ",".join(map_hits[:5])

            collision = bool(info_collision or contact_collision or penetration)

            if collision:
                break

            if done:
                break

        if steps >= max_steps and not collision:
            timeout = True

        success = bool(
            (not collision)
            and (not timeout)
            and np.isfinite(final_dist)
            and final_dist <= success_dist
        )

        row = {
            "model": model_path,
            "episode": ep,
            "success": int(success),
            "collision": int(collision),
            "penetration": int(penetration),
            "contact_collision": int(contact_collision),
            "timeout": int(timeout),
            "steps": steps,
            "final_dist": final_dist,
            "reward": total_reward,
            "sync_rect_count": sync_rect,
            "sync_circle_count": sync_circle,
            "first_hit": first_hit,
        }

        rows.append(row)

        print(
            f"EP{ep:03d}",
            f"success={success}",
            f"collision={collision}",
            f"penetration={penetration}",
            f"contact={contact_collision}",
            f"timeout={timeout}",
            f"steps={steps}",
            f"final={final_dist:.3f}" if np.isfinite(final_dist) else "final=nan",
            f"reward={total_reward:.2f}",
            flush=True,
        )

    env.close()

    valid_final = [r["final_dist"] for r in rows if np.isfinite(r["final_dist"])]

    summary = {
        "model": model_path,
        "episodes": episodes,
        "success_rate": float(np.mean([r["success"] for r in rows])),
        "collision_rate": float(np.mean([r["collision"] for r in rows])),
        "penetration_rate": float(np.mean([r["penetration"] for r in rows])),
        "contact_collision_rate": float(np.mean([r["contact_collision"] for r in rows])),
        "timeout_rate": float(np.mean([r["timeout"] for r in rows])),
        "avg_steps": float(np.mean([r["steps"] for r in rows])),
        "avg_final_dist": float(np.mean(valid_final)) if valid_final else float("nan"),
        "avg_reward": float(np.mean([r["reward"] for r in rows])),
        "sync_rect_ok_rate": float(np.mean([1 if r["sync_rect_count"] == 10 else 0 for r in rows])),
        "sync_circle_ok_rate": float(np.mean([1 if r["sync_circle_count"] == 9 else 0 for r in rows])),
    }

    return summary, rows


def choose_best(summaries):
    if not summaries:
        return None

    def key(s):
        return (
            s["success_rate"],
            -s["collision_rate"],
            -s["penetration_rate"],
            -s["timeout_rate"],
            s["avg_reward"],
            -s["avg_steps"],
            -s["avg_final_dist"],
        )

    return sorted(summaries, key=key, reverse=True)[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ckpt_dir",
        default="training/phase17_fusion_safety_sac_nav/checkpoints/phase17_D_fusion_sac_parallel_200k",
    )
    parser.add_argument("--min_steps", type=int, default=170000)
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--max_steps", type=int, default=1000)
    parser.add_argument("--success_dist", type=float, default=0.90)
    parser.add_argument("--margin", type=float, default=0.02)
    parser.add_argument("--base_seed", type=int, default=18000)
    parser.add_argument(
        "--out_summary",
        default="training/phase17_fusion_safety_sac_nav/reports/phase17_D_after_sync_overnight_summary.csv",
    )
    parser.add_argument(
        "--out_episodes",
        default="training/phase17_fusion_safety_sac_nav/reports/phase17_D_after_sync_overnight_episodes.csv",
    )
    parser.add_argument(
        "--best_out",
        default="training/best_models/mkmini_phase17_D_after_sync_best.zip",
    )
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out_summary), exist_ok=True)
    os.makedirs(os.path.dirname(args.out_episodes), exist_ok=True)
    os.makedirs(os.path.dirname(args.best_out), exist_ok=True)

    models = collect_models(args.ckpt_dir, args.min_steps)

    print("[Phase18-B2 True No LiDAR Fixed-Seed Eval]")
    print("ckpt_dir:", args.ckpt_dir)
    print("min_steps:", args.min_steps)
    print("episodes:", args.episodes)
    print("success_dist:", args.success_dist)
    print("base_seed:", args.base_seed)
    print("models:")
    for m in models:
        print(" ", m)

    if not models:
        raise FileNotFoundError("No checkpoint found.")

    all_summaries = []
    all_rows = []

    for model_path in models:
        print("=" * 100)
        print("Evaluating:", model_path)

        summary, rows = eval_model(
            model_path=model_path,
            episodes=args.episodes,
            max_steps=args.max_steps,
            success_dist=args.success_dist,
            margin=args.margin,
            base_seed=args.base_seed,
        )

        all_summaries.append(summary)
        all_rows.extend(rows)

        print("SUMMARY:", summary, flush=True)

        with open(args.out_summary, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "model",
                    "episodes",
                    "success_rate",
                    "collision_rate",
                    "penetration_rate",
                    "contact_collision_rate",
                    "timeout_rate",
                    "avg_steps",
                    "avg_final_dist",
                    "avg_reward",
                    "sync_rect_ok_rate",
                    "sync_circle_ok_rate",
                ],
            )
            writer.writeheader()
            writer.writerows(all_summaries)

        with open(args.out_episodes, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "model",
                    "episode",
                    "success",
                    "collision",
                    "penetration",
                    "contact_collision",
                    "timeout",
                    "steps",
                    "final_dist",
                    "reward",
                    "sync_rect_count",
                    "sync_circle_count",
                    "first_hit",
                ],
            )
            writer.writeheader()
            writer.writerows(all_rows)

    best = choose_best(all_summaries)
    if best is not None:
        shutil.copyfile(best["model"], args.best_out)
        print("=" * 100)
        print("[BEST MODEL]")
        print(best)
        print("saved best model to:", args.best_out)

    print("saved summary:", args.out_summary)
    print("saved episodes:", args.out_episodes)


if __name__ == "__main__":
    main()
