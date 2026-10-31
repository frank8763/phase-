import numpy as np
import mujoco

from training.phase17_fusion_safety_sac_nav.envs.mkmini_phase17a_random_scene_robust_env import (
    MkMiniPhase17ARandomSceneRobustEnv,
)


class MkMiniPhase17BRandomObstacleEnv(MkMiniPhase17ARandomSceneRobustEnv):
    """
    Phase17-B:
    Random obstacle perturbation environment.

    Based on Phase17-A:
        obs noise
        action disturbance
        controller randomization

    Add:
        in-memory MuJoCo obstacle position perturbation
        no XML overwrite
    """

    def __init__(
        self,
        obstacle_xy_noise=0.35,
        max_random_obstacles=4,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.phase17b_name = "phase17b_random_obstacle"
        self.phase17b_obstacle_xy_noise = float(obstacle_xy_noise)
        self.phase17b_max_random_obstacles = int(max_random_obstacles)
        self.phase17b_rng = np.random.default_rng()

        self._phase17b_base_geom_pos = {}
        self._phase17b_last_randomized = []

    def _phase17b_model_data(self):
        for obj in self._phase14_targets():
            if hasattr(obj, "model") and hasattr(obj, "data"):
                return obj.model, obj.data
        return None, None

    def _phase17b_sync_obstacle_arrays_from_geoms(self, model):
        """
        Sync sensor/planner obstacle arrays from active MuJoCo obstacle geoms.

        Reason:
        Phase8 exact scene edit and Phase17B random obstacle perturbation move
        model.geom_pos. If rect_obstacles / circle_obstacles are not updated,
        LiDAR / depth / A* / safety shield will see old obstacle positions.
        """
        rects = []
        circles = []

        for gid in range(model.ngeom):
            name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, gid)
            if not name:
                continue

            low = name.lower()

            if not ("real_rect_obs" in low or "real_circle_obs" in low):
                continue

            # inactive / hidden obstacles should not remain in sensor maps
            if int(model.geom_contype[gid]) == 0 and int(model.geom_conaffinity[gid]) == 0:
                continue

            if float(model.geom_rgba[gid][3]) <= 0.01:
                continue

            if float(model.geom_pos[gid][2]) < -1.0:
                continue

            x = float(model.geom_pos[gid][0])
            y = float(model.geom_pos[gid][1])

            if "real_rect_obs" in low:
                hx = float(model.geom_size[gid][0])
                hy = float(model.geom_size[gid][1])
                rects.append([x, y, hx, hy])

            elif "real_circle_obs" in low:
                r = float(model.geom_size[gid][0])
                circles.append([x, y, r])

        rects = np.asarray(rects, dtype=np.float32)
        circles = np.asarray(circles, dtype=np.float32)

        # Sync to all wrapper / inner targets that may be used by planner or sensor utils.
        targets = []
        try:
            targets.extend(self._phase14_targets())
        except Exception:
            pass

        targets.append(self)

        seen = set()
        for obj in targets:
            if obj is None or id(obj) in seen:
                continue
            seen.add(id(obj))

            try:
                obj.rect_obstacles = rects.copy()
            except Exception:
                pass

            try:
                obj.circle_obstacles = circles.copy()
            except Exception:
                pass

        self.phase17b_synced_rect_count = int(len(rects))
        self.phase17b_synced_circle_count = int(len(circles))

    def _phase17b_collect_obstacle_geoms(self, model):
        ids = []

        for gid in range(model.ngeom):
            try:
                name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, gid)
            except Exception:
                name = None

            if not name:
                continue

            if (
                "real_rect_obs_" in name
                or "real_circle_obs_" in name
                or "obs_" in name
            ):
                # avoid robot/wheel/body geoms accidentally matched by weak names
                if "wheel" in name or "base" in name or "robot" in name:
                    continue
                ids.append((gid, name))

        return ids

    def _phase17b_save_base_positions(self, model):
        if self._phase17b_base_geom_pos:
            return

        for gid, name in self._phase17b_collect_obstacle_geoms(model):
            self._phase17b_base_geom_pos[name] = np.array(model.geom_pos[gid], dtype=np.float64).copy()

    def _phase17b_restore_base_positions(self, model):
        if not self._phase17b_base_geom_pos:
            return

        for gid, name in self._phase17b_collect_obstacle_geoms(model):
            if name in self._phase17b_base_geom_pos:
                model.geom_pos[gid][:] = self._phase17b_base_geom_pos[name]

    def _phase17b_randomize_obstacles(self):
        model, data = self._phase17b_model_data()
        if model is None or data is None:
            return

        self._phase17b_save_base_positions(model)
        self._phase17b_restore_base_positions(model)

        geoms = self._phase17b_collect_obstacle_geoms(model)
        if not geoms:
            self._phase17b_last_randomized = []
            return

        self.phase17b_rng.shuffle(geoms)
        selected = geoms[:max(1, min(self.phase17b_max_random_obstacles, len(geoms)))]

        randomized = []

        for gid, name in selected:
            base = self._phase17b_base_geom_pos.get(name)
            if base is None:
                continue

            dx = float(self.phase17b_rng.uniform(-self.phase17b_obstacle_xy_noise, self.phase17b_obstacle_xy_noise))
            dy = float(self.phase17b_rng.uniform(-self.phase17b_obstacle_xy_noise, self.phase17b_obstacle_xy_noise))

            new_pos = base.copy()
            new_pos[0] += dx
            new_pos[1] += dy

            model.geom_pos[gid][:] = new_pos
            randomized.append((name, float(new_pos[0]), float(new_pos[1])))

        try:
            mujoco.mj_forward(model, data)
        except Exception:
            pass

        self._phase17b_sync_obstacle_arrays_from_geoms(model)

        self._phase17b_last_randomized = randomized

        # Try to refresh inherited path if the parent exposes a path smoother/planner.
        for obj in self._phase14_targets():
            for method_name in ["_apply_smooth_ref_path", "_p10_get_path"]:
                if hasattr(obj, method_name):
                    try:
                        getattr(obj, method_name)()
                    except Exception:
                        pass

    def reset(self, **kwargs):
        out = super().reset(**kwargs)

        # Randomize after parent reset / Phase8 exact scene edit.
        self._phase17b_randomize_obstacles()

        if isinstance(out, tuple):
            obs, info = out
            if info is None:
                info = {}
            info = self._phase17b_fill_info(info)
            return obs, info

        return out

    def step(self, action):
        out = super().step(action)

        if len(out) == 5:
            obs, reward, terminated, truncated, info = out
            info = self._phase17b_fill_info(info)
            return obs, reward, terminated, truncated, info

        obs, reward, done, info = out
        info = self._phase17b_fill_info(info)
        return obs, reward, done, info

    def _phase17b_fill_info(self, info):
        if info is None:
            info = {}

        info["phase17b_env"] = self.phase17b_name
        info["phase17b_obstacle_xy_noise"] = float(self.phase17b_obstacle_xy_noise)
        info["phase17b_randomized_count"] = int(len(self._phase17b_last_randomized))
        info["phase17b_synced_rect_count"] = int(getattr(self, "phase17b_synced_rect_count", -1))
        info["phase17b_synced_circle_count"] = int(getattr(self, "phase17b_synced_circle_count", -1))

        if self._phase17b_last_randomized:
            info["phase17b_randomized_names"] = ",".join([x[0] for x in self._phase17b_last_randomized[:8]])
        else:
            info["phase17b_randomized_names"] = ""

        return info
