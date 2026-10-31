#!/usr/bin/env python3

import argparse
import csv
import math
import traceback
from datetime import datetime
from pathlib import Path

import numpy as np
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import CheckpointCallback

from training.phase19_unknown_obstacle_stress.envs.mkmini_phase19_formal_group_envs import (
    MkMiniPhase19AFullEnv,
)

from training.phase18_ablation.scripts.eval_phase18_A_full_fixed_seed import (
    robot_obstacle_contact,
    robot_sample_points,
)


ROOT = Path(__file__).resolve().parents[3]

PHASE20 = (
    ROOT
    / "training"
    / "phase20_unknown_obstacle_adaptation"
)

CHECKPOINT_DIR = PHASE20 / "checkpoints"
REPORT_DIR = PHASE20 / "reports"
RESULT_DIR = PHASE20 / "results"


def as_bool(value):
    if isinstance(value, tuple):
        value = value[0]

    if isinstance(value, dict):
        return any(as_bool(item) for item in value.values())

    if isinstance(value, (list, set)):
        return any(as_bool(item) for item in value)

    return bool(value)


def normalize_circles(value):
    array = np.asarray(
        value,
        dtype=np.float32,
    )

    if array.ndim == 1 and array.size >= 3:
        array = array.reshape(1, -1)

    if array.ndim != 2:
        return np.empty(
            (0, 3),
            dtype=np.float32,
        )

    return array[:, :3]


def normalize_rectangles(value):
    array = np.asarray(
        value,
        dtype=np.float32,
    )

    if array.ndim == 1 and array.size >= 4:
        array = array.reshape(1, -1)

    if array.ndim != 2:
        return np.empty(
            (0, 4),
            dtype=np.float32,
        )

    return array[:, :4]


def reset_compat(env, seed=None):
    try:
        output = env.reset(seed=seed)
    except TypeError:
        if seed is not None and hasattr(env, "seed"):
            try:
                env.seed(seed)
            except Exception:
                pass

        output = env.reset()

    if (
        isinstance(output, tuple)
        and len(output) == 2
        and isinstance(output[1], dict)
    ):
        return output[0], dict(output[1])

    return output, {}


def step_compat(env, action):
    output = env.step(action)

    if len(output) == 5:
        obs, reward, terminated, truncated, info = output

        return (
            obs,
            float(reward),
            bool(terminated or truncated),
            dict(info or {}),
        )

    obs, reward, done, info = output

    return (
        obs,
        float(reward),
        bool(done),
        dict(info or {}),
    )


class Phase20UnknownAdaptationEnv(
    MkMiniPhase19AFullEnv
):
    def __init__(
        self,
        randomized=False,
        random_seed=20020,
        terminate_on_collision=True,
        penetration_margin=0.02,
        safe_clearance=0.35,
    ):
        self.phase20_randomized = bool(randomized)

        self.phase20_rng = np.random.default_rng(
            int(random_seed)
        )

        self.phase20_terminate_on_collision = bool(
            terminate_on_collision
        )

        self.phase20_penetration_margin = float(
            penetration_margin
        )

        self.phase20_safe_clearance = float(
            safe_clearance
        )

        self.phase20_last_config = {
            "unknown_radius": 0.16,
            "unknown_lateral_offset": 0.40,
            "unknown_path_fraction": 0.55,
            "endpoint_clearance": 1.20,
        }

        super().__init__(
            unknown_count=1,
            unknown_radius=0.16,
            unknown_lateral_offset=0.40,
            unknown_path_fraction=0.55,
            endpoint_clearance=1.20,
        )

    def _sample_config(self):
        if not self.phase20_randomized:
            return {
                "unknown_radius": 0.16,
                "unknown_lateral_offset": 0.40,
                "unknown_path_fraction": 0.55,
                "endpoint_clearance": 1.20,
            }

        return {
            "unknown_radius": float(
                self.phase20_rng.uniform(
                    0.12,
                    0.20,
                )
            ),
            "unknown_lateral_offset": float(
                self.phase20_rng.uniform(
                    0.32,
                    0.52,
                )
            ),
            "unknown_path_fraction": float(
                self.phase20_rng.uniform(
                    0.40,
                    0.70,
                )
            ),
            "endpoint_clearance": float(
                self.phase20_rng.uniform(
                    1.00,
                    1.40,
                )
            ),
        }

    def _set_config_value(
        self,
        semantic,
        value,
    ):
        names = {
            "unknown_radius": [
                "unknown_radius",
                "phase19_unknown_radius",
                "_unknown_radius",
                "_phase19_unknown_radius",
            ],
            "unknown_lateral_offset": [
                "unknown_lateral_offset",
                "phase19_unknown_lateral_offset",
                "_unknown_lateral_offset",
                "_phase19_unknown_lateral_offset",
            ],
            "unknown_path_fraction": [
                "unknown_path_fraction",
                "phase19_unknown_path_fraction",
                "_unknown_path_fraction",
                "_phase19_unknown_path_fraction",
            ],
            "endpoint_clearance": [
                "endpoint_clearance",
                "phase19_endpoint_clearance",
                "_endpoint_clearance",
                "_phase19_endpoint_clearance",
            ],
        }

        changed = []

        for name in names[semantic]:
            if hasattr(self, name):
                setattr(
                    self,
                    name,
                    float(value),
                )

                changed.append(name)

        token_map = {
            "unknown_radius": (
                "unknown",
                "radius",
            ),
            "unknown_lateral_offset": (
                "unknown",
                "offset",
            ),
            "unknown_path_fraction": (
                "unknown",
                "fraction",
            ),
            "endpoint_clearance": (
                "endpoint",
                "clearance",
            ),
        }

        excluded = (
            "actual",
            "current",
            "selected",
            "min_",
            "last_",
        )

        tokens = token_map[semantic]

        for key, old_value in list(
            self.__dict__.items()
        ):
            lowered = key.lower()

            if any(
                word in lowered
                for word in excluded
            ):
                continue

            if not all(
                token in lowered
                for token in tokens
            ):
                continue

            if not isinstance(
                old_value,
                (
                    int,
                    float,
                    np.integer,
                    np.floating,
                ),
            ):
                continue

            setattr(
                self,
                key,
                float(value),
            )

            if key not in changed:
                changed.append(key)

        if not changed:
            raise RuntimeError(
                f"没有找到Phase19参数属性：{semantic}"
            )

    def _apply_config(self, config):
        for key, value in config.items():
            self._set_config_value(
                key,
                value,
            )

        self.phase20_last_config = dict(
            config
        )

    def _unknown_circles(self):
        value = getattr(
            self,
            "phase19_unknown_circles",
            [],
        )

        return normalize_circles(value)

    def _unknown_circle_indices(
        self,
        circles,
        unknown_circles,
    ):
        indices = set()

        for index, circle in enumerate(circles):
            for unknown in unknown_circles:
                center_error = float(
                    np.linalg.norm(
                        circle[:2]
                        - unknown[:2]
                    )
                )

                radius_error = abs(
                    float(
                        circle[2]
                        - unknown[2]
                    )
                )

                if (
                    center_error <= 1e-4
                    and radius_error <= 1e-4
                ):
                    indices.add(index)

        return indices

    def _classify_penetration(self):
        points = np.asarray(
            robot_sample_points(self),
            dtype=np.float32,
        ).reshape(-1, 2)

        rectangles = normalize_rectangles(
            getattr(
                self,
                "rect_obstacles",
                [],
            )
        )

        circles = normalize_circles(
            getattr(
                self,
                "circle_obstacles",
                [],
            )
        )

        unknown_circles = (
            self._unknown_circles()
        )

        unknown_indices = (
            self._unknown_circle_indices(
                circles,
                unknown_circles,
            )
        )

        unknown_hit = False
        known_hit = False
        hit_labels = set()

        margin = (
            self.phase20_penetration_margin
        )

        for px, py in points:
            px = float(px)
            py = float(py)

            for index, rectangle in enumerate(
                rectangles
            ):
                cx, cy, hx, hy = map(
                    float,
                    rectangle,
                )

                if (
                    abs(px - cx)
                    <= hx + margin
                    and abs(py - cy)
                    <= hy + margin
                ):
                    known_hit = True
                    hit_labels.add(
                        f"rect_{index}"
                    )

            for index, circle in enumerate(
                circles
            ):
                cx, cy, radius = map(
                    float,
                    circle,
                )

                if (
                    math.hypot(
                        px - cx,
                        py - cy,
                    )
                    <= radius + margin
                ):
                    if index in unknown_indices:
                        unknown_hit = True
                        hit_labels.add(
                            f"unknown_circle_{index}"
                        )
                    else:
                        known_hit = True
                        hit_labels.add(
                            f"known_circle_{index}"
                        )

        return (
            unknown_hit,
            known_hit,
            sorted(hit_labels),
        )

    def _unknown_clearance(self):
        points = np.asarray(
            robot_sample_points(self),
            dtype=np.float32,
        ).reshape(-1, 2)

        unknown_circles = (
            self._unknown_circles()
        )

        if len(unknown_circles) == 0:
            return float("inf")

        minimum = float("inf")

        for point in points:
            for circle in unknown_circles:
                clearance = (
                    float(
                        np.linalg.norm(
                            point
                            - circle[:2]
                        )
                    )
                    - float(circle[2])
                )

                minimum = min(
                    minimum,
                    clearance,
                )

        return minimum

    def reset(self, *args, **kwargs):
        seed = kwargs.get("seed")

        if seed is not None:
            self.phase20_rng = (
                np.random.default_rng(
                    int(seed) + 20020
                )
            )

        config = self._sample_config()
        self._apply_config(config)

        try:
            output = super().reset(
                *args,
                **kwargs,
            )
        except TypeError:
            output = super().reset()

        if (
            isinstance(output, tuple)
            and len(output) == 2
            and isinstance(output[1], dict)
        ):
            obs, info = output
            info = dict(info)
            tuple_api = True
        else:
            obs = output
            info = {}
            tuple_api = False

        unknown_circles = (
            self._unknown_circles()
        )

        if len(unknown_circles) != 1:
            raise RuntimeError(
                "Phase20 reset后未知障碍数量不是1"
            )

        actual_radius = float(
            unknown_circles[0, 2]
        )

        expected_radius = float(
            config["unknown_radius"]
        )

        if (
            abs(
                actual_radius
                - expected_radius
            )
            > 0.005
        ):
            raise RuntimeError(
                "Phase20随机半径未生效："
                f"expected={expected_radius}, "
                f"actual={actual_radius}"
            )

        actual_offset = info.get(
            "phase19_actual_lateral_offset",
            None,
        )

        if actual_offset is not None:
            if (
                abs(
                    abs(float(actual_offset))
                    - float(
                        config[
                            "unknown_lateral_offset"
                        ]
                    )
                )
                > 0.04
            ):
                raise RuntimeError(
                    "Phase20随机偏移未生效："
                    f"expected="
                    f"{config['unknown_lateral_offset']}, "
                    f"actual={actual_offset}"
                )

        info.update({
            "phase20_randomized":
                self.phase20_randomized,
            "phase20_unknown_radius":
                config["unknown_radius"],
            "phase20_unknown_lateral_offset":
                config[
                    "unknown_lateral_offset"
                ],
            "phase20_unknown_path_fraction":
                config[
                    "unknown_path_fraction"
                ],
            "phase20_endpoint_clearance":
                config[
                    "endpoint_clearance"
                ],
        })

        self.phase20_last_reset_info = dict(
            info
        )

        if tuple_api:
            return obs, info

        return obs

    def step(self, action):
        output = super().step(action)

        if len(output) == 5:
            (
                obs,
                reward,
                terminated,
                truncated,
                info,
            ) = output

            api_type = 5
        else:
            (
                obs,
                reward,
                done,
                info,
            ) = output

            api_type = 4

        info = dict(info or {})
        reward = float(reward)

        (
            unknown_penetration,
            known_penetration,
            penetration_hits,
        ) = self._classify_penetration()

        contact_hits = (
            robot_obstacle_contact(self)
        )

        physical_contact = bool(
            contact_hits
        )

        clearance = (
            self._unknown_clearance()
        )

        proximity_penalty = 0.0

        if (
            math.isfinite(clearance)
            and clearance
            < self.phase20_safe_clearance
            and not unknown_penetration
        ):
            ratio = (
                self.phase20_safe_clearance
                - clearance
            ) / self.phase20_safe_clearance

            proximity_penalty = (
                2.0
                * max(0.0, ratio) ** 2
            )

            reward -= proximity_penalty

        if unknown_penetration:
            reward -= 100.0

        if known_penetration:
            reward -= 60.0

        if physical_contact:
            reward -= 40.0

        collision = bool(
            unknown_penetration
            or known_penetration
            or physical_contact
        )

        info.update({
            "phase20_randomized":
                self.phase20_randomized,
            "phase20_unknown_penetration":
                unknown_penetration,
            "phase20_known_penetration":
                known_penetration,
            "phase20_physical_contact":
                physical_contact,
            "phase20_collision":
                collision,
            "phase20_penetration_hits":
                penetration_hits,
            "phase20_contact_hits":
                str(contact_hits),
            "phase20_unknown_clearance":
                clearance,
            "phase20_proximity_penalty":
                proximity_penalty,
            "phase20_forced_termination":
                bool(
                    collision
                    and self.phase20_terminate_on_collision
                ),
        })

        if (
            collision
            and self.phase20_terminate_on_collision
        ):
            if api_type == 5:
                terminated = True
            else:
                done = True

        if api_type == 5:
            return (
                obs,
                reward,
                terminated,
                truncated,
                info,
            )

        return (
            obs,
            reward,
            done,
            info,
        )


def evaluate_model(
    model,
    randomized,
    episodes,
    base_seed,
    output_csv,
):
    env = Phase20UnknownAdaptationEnv(
        randomized=randomized,
        random_seed=base_seed,
        terminate_on_collision=True,
    )

    rows = []

    for episode in range(
        1,
        episodes + 1,
    ):
        seed = base_seed + episode - 1

        obs, reset_info = reset_compat(
            env,
            seed=seed,
        )

        obs = np.asarray(
            obs,
            dtype=np.float32,
        )

        done = False
        steps = 0
        total_reward = 0.0

        collision = False
        unknown_penetration = False
        known_penetration = False
        physical_contact = False
        timeout = False

        minimum_clearance = float("inf")
        final_info = dict(reset_info)

        while not done and steps < 1000:
            action, _ = model.predict(
                obs,
                deterministic=True,
            )

            (
                obs,
                reward,
                done,
                info,
            ) = step_compat(
                env,
                action,
            )

            obs = np.asarray(
                obs,
                dtype=np.float32,
            )

            final_info = dict(info)
            steps += 1
            total_reward += float(reward)

            collision |= as_bool(
                info.get(
                    "phase20_collision",
                    False,
                )
            )

            unknown_penetration |= as_bool(
                info.get(
                    "phase20_unknown_penetration",
                    False,
                )
            )

            known_penetration |= as_bool(
                info.get(
                    "phase20_known_penetration",
                    False,
                )
            )

            physical_contact |= as_bool(
                info.get(
                    "phase20_physical_contact",
                    False,
                )
            )

            timeout |= as_bool(
                info.get(
                    "timeout",
                    False,
                )
            )

            timeout |= as_bool(
                info.get(
                    "TimeLimit.truncated",
                    False,
                )
            )

            clearance = float(
                info.get(
                    "phase20_unknown_clearance",
                    float("inf"),
                )
            )

            minimum_clearance = min(
                minimum_clearance,
                clearance,
            )

        if steps >= 1000 and not done:
            timeout = True

        final_dist = float(
            np.linalg.norm(
                np.asarray(
                    env.robot_xy,
                    dtype=np.float32,
                )
                - np.asarray(
                    env.goal_xy,
                    dtype=np.float32,
                )
            )
        )

        success = bool(
            final_dist <= 0.90
            and not collision
            and not timeout
        )

        config = getattr(
            env,
            "phase20_last_config",
            {},
        )

        row = {
            "condition":
                "randomized"
                if randomized
                else "fixed",
            "episode": episode,
            "seed": seed,
            "success": success,
            "collision": collision,
            "unknown_penetration":
                unknown_penetration,
            "known_penetration":
                known_penetration,
            "physical_contact":
                physical_contact,
            "timeout": timeout,
            "steps": steps,
            "final_dist": final_dist,
            "reward": total_reward,
            "min_unknown_clearance":
                minimum_clearance,
            "unknown_radius":
                config.get(
                    "unknown_radius"
                ),
            "unknown_lateral_offset":
                config.get(
                    "unknown_lateral_offset"
                ),
            "unknown_path_fraction":
                config.get(
                    "unknown_path_fraction"
                ),
            "endpoint_clearance":
                config.get(
                    "endpoint_clearance"
                ),
        }

        rows.append(row)

        print(
            f"EVAL {row['condition']}",
            f"EP{episode:03d}",
            f"seed={seed}",
            f"success={success}",
            f"collision={collision}",
            f"steps={steps}",
            f"final={final_dist:.3f}",
            flush=True,
        )

    env.close()

    output_csv.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_csv.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys()),
        )

        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)

    return {
        "condition":
            "randomized"
            if randomized
            else "fixed",
        "episodes": total,
        "success_rate": (
            sum(row["success"] for row in rows)
            / total
        ),
        "collision_rate": (
            sum(row["collision"] for row in rows)
            / total
        ),
        "unknown_penetration_rate": (
            sum(
                row["unknown_penetration"]
                for row in rows
            )
            / total
        ),
        "known_penetration_rate": (
            sum(
                row["known_penetration"]
                for row in rows
            )
            / total
        ),
        "physical_contact_rate": (
            sum(
                row["physical_contact"]
                for row in rows
            )
            / total
        ),
        "timeout_rate": (
            sum(row["timeout"] for row in rows)
            / total
        ),
        "avg_steps": float(
            np.mean(
                [
                    row["steps"]
                    for row in rows
                ]
            )
        ),
        "avg_final_dist": float(
            np.mean(
                [
                    row["final_dist"]
                    for row in rows
                ]
            )
        ),
        "avg_reward": float(
            np.mean(
                [
                    row["reward"]
                    for row in rows
                ]
            )
        ),
    }


def write_summary(
    summaries,
    args,
):
    summary_csv = (
        RESULT_DIR
        / "phase20_overnight_summary.csv"
    )

    with summary_csv.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(
                summaries[0].keys()
            ),
        )

        writer.writeheader()
        writer.writerows(summaries)

    report = [
        "# Phase20 未知障碍适应训练报告",
        "",
        f"- 完成时间：{datetime.now():%Y-%m-%d %H:%M:%S}",
        f"- 固定场景训练步数：{args.fixed_steps}",
        f"- 随机场景训练步数：{args.random_steps}",
        f"- 总训练步数：{args.fixed_steps + args.random_steps}",
        f"- 初始模型：{args.init_model}",
        "",
        "## 评估结果",
        "",
        "|模型阶段|场景|回合数|成功率|碰撞率|未知障碍穿透率|已知障碍穿透率|物理接触率|超时率|平均步数|平均奖励|",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in summaries:
        report.append(
            f"|{row['model_stage']}|"
            f"{row['condition']}|"
            f"{row['episodes']}|"
            f"{row['success_rate']:.4f}|"
            f"{row['collision_rate']:.4f}|"
            f"{row['unknown_penetration_rate']:.4f}|"
            f"{row['known_penetration_rate']:.4f}|"
            f"{row['physical_contact_rate']:.4f}|"
            f"{row['timeout_rate']:.4f}|"
            f"{row['avg_steps']:.2f}|"
            f"{row['avg_reward']:.2f}|"
        )

    report.extend([
        "",
        "## Phase19基线",
        "",
        "- Phase19 A组未知障碍成功率：0.1700",
        "- Phase19 A组未知障碍碰撞率：0.8267",
        "- Phase19无未知障碍成功率：0.9367",
        "",
        "## 自动判断",
        "",
    ])

    final_fixed = next(
        row
        for row in summaries
        if (
            row["model_stage"]
            == "phase20_final"
            and row["condition"]
            == "fixed"
        )
    )

    final_random = next(
        row
        for row in summaries
        if (
            row["model_stage"]
            == "phase20_final"
            and row["condition"]
            == "randomized"
        )
    )

    fixed_delta = (
        final_fixed["success_rate"]
        - 0.17
    )

    report.append(
        f"- 固定未知障碍成功率相对Phase19提升："
        f"{fixed_delta:+.4f}"
    )

    report.append(
        f"- 最终固定场景成功率："
        f"{final_fixed['success_rate']:.4f}"
    )

    report.append(
        f"- 最终随机场景成功率："
        f"{final_random['success_rate']:.4f}"
    )

    if (
        final_fixed["success_rate"] >= 0.70
        and final_random["success_rate"] >= 0.60
    ):
        report.append(
            "- 结论：Phase20适应训练达到初步通过标准。"
        )
    elif final_fixed["success_rate"] >= 0.50:
        report.append(
            "- 结论：适应训练有效，但仍需继续训练或增加局部重规划。"
        )
    else:
        report.append(
            "- 结论：单纯继续SAC训练提升不足，下一步应加入局部重规划或更强避障奖励。"
        )

    (
        REPORT_DIR
        / "phase20_overnight_report.md"
    ).write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--init_model",
        required=True,
    )

    parser.add_argument(
        "--fixed_steps",
        type=int,
        default=50000,
    )

    parser.add_argument(
        "--random_steps",
        type=int,
        default=150000,
    )

    parser.add_argument(
        "--stage_a_eval_episodes",
        type=int,
        default=50,
    )

    parser.add_argument(
        "--final_eval_episodes",
        type=int,
        default=100,
    )

    parser.add_argument(
        "--device",
        default="cpu",
    )

    parser.add_argument(
        "--learning_rate",
        type=float,
        default=1e-4,
    )

    args = parser.parse_args()

    for directory in [
        CHECKPOINT_DIR,
        REPORT_DIR,
        RESULT_DIR,
    ]:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    failed_file = (
        REPORT_DIR
        / "PHASE20_OVERNIGHT_FAILED.txt"
    )

    done_file = (
        REPORT_DIR
        / "PHASE20_OVERNIGHT_DONE.txt"
    )

    failed_file.unlink(
        missing_ok=True
    )

    done_file.unlink(
        missing_ok=True
    )

    print("=" * 100)
    print("PHASE20 OVERNIGHT TRAINING")
    print("init_model =", args.init_model)
    print("fixed_steps =", args.fixed_steps)
    print("random_steps =", args.random_steps)
    print("device =", args.device)
    print("=" * 100)

    fixed_env = Phase20UnknownAdaptationEnv(
        randomized=False,
        random_seed=20020,
        terminate_on_collision=True,
    )

    model = SAC.load(
        args.init_model,
        env=fixed_env,
        device=args.device,
    )

    model.learning_rate = (
        args.learning_rate
    )

    model.lr_schedule = (
        lambda _: args.learning_rate
    )

    stage_a_callback = CheckpointCallback(
        save_freq=25000,
        save_path=str(
            CHECKPOINT_DIR
            / "stage_a_fixed"
        ),
        name_prefix="phase20_stage_a",
        save_replay_buffer=False,
        save_vecnormalize=False,
    )

    print("开始Phase20A固定参数训练")

    model.learn(
        total_timesteps=args.fixed_steps,
        reset_num_timesteps=False,
        callback=stage_a_callback,
        progress_bar=False,
    )

    stage_a_model = (
        CHECKPOINT_DIR
        / "phase20_stage_a_fixed_50k.zip"
    )

    model.save(str(stage_a_model))

    stage_a_summary = evaluate_model(
        model=model,
        randomized=False,
        episodes=args.stage_a_eval_episodes,
        base_seed=21000,
        output_csv=(
            RESULT_DIR
            / "phase20_stage_a_fixed_eval.csv"
        ),
    )

    stage_a_summary[
        "model_stage"
    ] = "phase20_stage_a"

    random_env = Phase20UnknownAdaptationEnv(
        randomized=True,
        random_seed=22000,
        terminate_on_collision=True,
    )

    model.set_env(random_env)

    fixed_env.close()

    stage_b_callback = CheckpointCallback(
        save_freq=25000,
        save_path=str(
            CHECKPOINT_DIR
            / "stage_b_randomized"
        ),
        name_prefix="phase20_stage_b",
        save_replay_buffer=False,
        save_vecnormalize=False,
    )

    print("开始Phase20B随机未知障碍训练")

    model.learn(
        total_timesteps=args.random_steps,
        reset_num_timesteps=False,
        callback=stage_b_callback,
        progress_bar=False,
    )

    final_model = (
        CHECKPOINT_DIR
        / "phase20_final_200k.zip"
    )

    model.save(str(final_model))

    random_env.close()

    final_fixed_summary = evaluate_model(
        model=model,
        randomized=False,
        episodes=args.final_eval_episodes,
        base_seed=23000,
        output_csv=(
            RESULT_DIR
            / "phase20_final_fixed_eval.csv"
        ),
    )

    final_fixed_summary[
        "model_stage"
    ] = "phase20_final"

    final_random_summary = evaluate_model(
        model=model,
        randomized=True,
        episodes=args.final_eval_episodes,
        base_seed=24000,
        output_csv=(
            RESULT_DIR
            / "phase20_final_randomized_eval.csv"
        ),
    )

    final_random_summary[
        "model_stage"
    ] = "phase20_final"

    summaries = [
        stage_a_summary,
        final_fixed_summary,
        final_random_summary,
    ]

    write_summary(
        summaries,
        args,
    )

    done_file.write_text(
        "\n".join([
            "Phase20通宵训练与评估已完成",
            f"完成时间：{datetime.now():%Y-%m-%d %H:%M:%S}",
            f"最终模型：{final_model}",
            (
                "最终报告："
                f"{REPORT_DIR / 'phase20_overnight_report.md'}"
            ),
            (
                "结果汇总："
                f"{RESULT_DIR / 'phase20_overnight_summary.csv'}"
            ),
        ]) + "\n",
        encoding="utf-8",
    )

    print("Phase20通宵训练完成")
    print("最终模型：", final_model)
    print(
        "最终报告：",
        REPORT_DIR
        / "phase20_overnight_report.md",
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        REPORT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        (
            REPORT_DIR
            / "PHASE20_OVERNIGHT_FAILED.txt"
        ).write_text(
            "\n".join([
                f"失败时间：{datetime.now():%Y-%m-%d %H:%M:%S}",
                "",
                traceback.format_exc(),
            ]),
            encoding="utf-8",
        )

        raise
