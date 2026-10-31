#!/usr/bin/env python3
"""B83-P1; full reset, frozen Phase baseline vs LiDAR footprint RP-CCR. Development seed only."""
from __future__ import annotations
import functools, gzip, hashlib, importlib.util, json, math, os, sys, time, traceback
from datetime import datetime
from pathlib import Path
from types import MethodType

ROOT = Path.home() / 'catkin_ws/src/mk-mini'
HERE = Path(__file__).resolve().parent
SEED = int(os.environ.get('RPCCR_SEED', '73105157'))
EXPECTED = '4072c19e02ba5c7c6b218a268c4ff1d987d2352eada01a3de918854d7173fc9f'
LIMIT = 600
os.environ.update(PYTHONDONTWRITEBYTECODE='1', MUJOCO_GL='egl', CUDA_VISIBLE_DEVICES='',
                  OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
sys.dont_write_bytecode = True

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''): h.update(chunk)
    return h.hexdigest()

def save(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)


def _v2_dense_poses(np, dense):
    dense = np.asarray(dense, dtype=float)

    if dense.ndim != 2 or dense.shape[0] < 3:
        raise RuntimeError("V2_INVALID_CONSUMER_DENSE_PATH")

    if dense.shape[1] == 3:
        poses = dense.copy()

    elif dense.shape[1] == 2:
        delta = np.diff(dense, axis=0)
        heading = np.arctan2(delta[:, 1], delta[:, 0])
        heading = np.r_[heading, heading[-1]]
        poses = np.column_stack((dense, heading))

    else:
        raise RuntimeError("V2_UNSUPPORTED_DENSE_PATH_SHAPE")

    if not np.isfinite(poses).all():
        raise RuntimeError("V2_NONFINITE_DENSE_PATH")

    return dense, poses



def _v2_escape_certificate(
    np, field, poses, actual_start, guard, tolerance=0.025
):
    """Fail-closed, start-only clearance recovery certificate."""
    try:
        p = np.asarray(poses, dtype=float)
        start = np.asarray(actual_start, dtype=float).reshape(3)

        if p.ndim != 2 or p.shape[1] != 3 or len(p) < 2:
            return False

        if not np.isfinite(p).all() or not np.isfinite(start).all():
            return False

        if np.linalg.norm(p[0, :2] - start[:2]) > 0.03:
            return False

        # The actual robot heading, not the first segment's heading,
        # defines the initial full-footprint pose.
        p = p.copy()
        p[0] = start

        samples = []
        for i in range(len(p) - 1):
            p0 = p[i]
            p1 = p[i + 1]
            distance = float(np.linalg.norm(p1[:2] - p0[:2]))
            dyaw = math.atan2(
                math.sin(float(p1[2] - p0[2])),
                math.cos(float(p1[2] - p0[2])),
            )
            n = max(
                1,
                int(math.ceil(distance / 0.01)),
                int(math.ceil(abs(dyaw) / 0.05)),
            )

            for k in range(n):
                t = k / n
                samples.append([
                    float(p0[0] + t * (p1[0] - p0[0])),
                    float(p0[1] + t * (p1[1] - p0[1])),
                    float(p0[2] + t * dyaw),
                ])

        samples.append(p[-1].tolist())
        sampled = np.asarray(samples, dtype=float)
        clearance = np.asarray(
            field.pose_values(sampled), dtype=float
        ).reshape(-1)

        if not np.isfinite(clearance).all():
            return False

        c0 = float(clearance[0])

        # Only a small, positive, near-threshold start deficit is allowed.
        if c0 < float(guard) - float(tolerance) - 1e-9:
            return False

        safe_indices = np.flatnonzero(
            clearance >= float(guard) - 1e-6
        )
        if len(safe_indices) == 0:
            return False

        first_safe = int(safe_indices[0])

        # Before reaching the normal guard, the path may not worsen
        # the initial clearance by more than 0.1 mm.
        if np.min(clearance[:first_safe + 1]) < c0 - 1e-4:
            return False

        # Once normal clearance is reached, it must remain satisfied.
        if np.any(clearance[first_safe:] < float(guard) - 1e-6):
            return False

        return True

    except Exception:
        return False


import v132_recovery_state as _v132_state

def main():
    from instrumentation import Audit
    _v648_audit = Audit()
    if Path.cwd().resolve() != ROOT.resolve(): raise RuntimeError('WRONG_PROJECT_DIRECTORY')
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT/'experiments/phase_rpccr_p0b68_v1'))
    sys.path.insert(0, str(ROOT/'experiments/phase_rpccr_p0b76_online_gate_v1'))
    import numpy as np
    import torch
    import mujoco
    import phase_v554u_physics_bridge
    import search_worker as H
    from contact_contract import GeometryCatalog, ContactRecorder
    from stable_baselines3 import SAC
    from envs.phase22.mkmini_phase22_v1_continuous_corridor_env import MkMiniPhase22V1ContinuousCorridorEnv as Env
    from envs.phase21.mkmini_phase21_v11_candidate_recovery_env import MkMiniPhase21V11CandidateRecoveryEnv as Parent
    import envs.phase22.mkmini_phase22_v1_continuous_corridor_env as module
    import navigation.phase22.continuous_corridor_planner as planner
    from training.phase21_risk_switch_fusion_sac.tests import eval_phase21_v3_exact_pair_5ep as E
    X,A,W,B,P,G,C = H.X,H.A,H.W,H.B,H.P,H.G,H.C
    B.NP,B.TORCH,B.MJ = np,torch,mujoco
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    b76 = ROOT/'experiments/phase_rpccr_p0b76_online_gate_v1'
    frozen = dict(json.loads((b76/'preflight.json').read_text())['original_hashes'])
    frozen.update(json.loads((b76/'b71_implementation_hashes.json').read_text()))
    for path, digest in frozen.items():
        if not Path(path).is_file() or sha(path)!=digest: raise RuntimeError('FROZEN_FILE_MISMATCH:'+path)
    if sha(B.MODEL)!=EXPECTED: raise RuntimeError('SAC_HASH_MISMATCH')
    fp = Path(__file__).resolve().parent/'footprint_map_b70_v513.py'
    spec = importlib.util.spec_from_file_location('b83_footprint_frozen',fp)
    F = importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=F
    spec.loader.exec_module(F)
    import inspect as _v23_inspect
    import types as _v23_types
    import math as _v23_math

    _v23_original_plan = F.old.plan
    _v23_plan_source = _v23_inspect.getsource(_v23_original_plan)

    import re as _v26_re
    _v26_grid_pattern = _v26_re.compile(
        r'(np\.linspace\([^)]*?,\s*(?:num\s*=\s*)?)5(\s*\))'
    )
    _v26_grid_hits = list(_v26_grid_pattern.finditer(_v23_plan_source))
    if len(_v26_grid_hits) != 1:
        raise RuntimeError('V2_6_RUNTIME_GRID_ANCHOR_MISMATCH:' + str(len(_v26_grid_hits)))
    _v23_plan_source = _v26_grid_pattern.sub(
        lambda m: m.group(1) + '9' + m.group(2),
        _v23_plan_source,
        count=1,
    )
    print('V2_6_STEERING_GRID=9', flush=True)
    print('V2_9_ESCAPE_DEPTH_CAP=8', flush=True)
    print('V2_9_ESCAPE_DEPTH_USES_PARENT_CHAIN=TRUE', flush=True)

    _v23_start_old = '''    if observed.pose_values([start])[0] < observed.guard:
        return finish(None, 'start_occupied_no_teleport')'''

    _v23_start_new = '''    start_clearance = float(observed.pose_values([start])[0])
    _v23_hard_guard = float(observed.guard)
    _v23_required_margin = float(cfg.margin)

    start_edge = bool(
        start_clearance >= _v23_hard_guard - 1e-8
        and start_clearance < _v23_required_margin - 1e-8
    )

    print('V575_MARGIN_RECOVERY_GATE', {
        'start_clearance_m': float(start_clearance),
        'hard_guard_m': _v23_hard_guard,
        'required_margin_m': _v23_required_margin,
        'margin_recovery_active': bool(start_edge),
        'policy': 'dense_certified_recovery_then_full_margin',
    }, flush=True)

    if start_clearance < _v23_hard_guard - 1e-8:
        return finish(None, 'start_occupied_no_teleport')'''

    _v23_loop_old = '''            if np.min(clearance) < clearance_floor - 1e-9:
                continue'''

    _v23_loop_new = "            if (\n                index != 0\n                and len(piece) >= 4\n                and np.min(clearance) < clearance_floor - 1e-9\n            ):\n                _v36_guard = max(float(observed.guard), float(clearance_floor))\n                _v36_c0 = float(\n                    observed.pose_values([pose])[0]\n                )\n\n                if _v36_c0 >= _v36_guard - 1e-8:\n\n                    _v36_full = np.asarray(\n                        observed.pose_values(\n                            np.vstack((pose[None, :], piece))\n                        ),\n                        dtype=float\n                    ).reshape(-1)\n\n                    if (\n                        len(_v36_full) == len(piece) + 1\n                        and np.isfinite(_v36_full).all()\n                    ):\n                        for _v36_cut in range(\n                            len(piece) - 1, 1, -1\n                        ):\n                            _v36_prefix = _v36_full[\n                                :_v36_cut + 1\n                            ]\n\n                            if not np.all(\n                                _v36_prefix\n                                >= _v36_guard - 1e-8\n                            ):\n                                continue\n\n                            _v36_reach = float(\n                                np.linalg.norm(\n                                    np.asarray(\n                                        piece[\n                                            _v36_cut - 1, :2\n                                        ],\n                                        dtype=float\n                                    )\n                                    - np.asarray(\n                                        pose[:2],\n                                        dtype=float\n                                    )\n                                )\n                            )\n\n                            if _v36_reach < 0.08:\n                                continue\n\n                            # V571: validate dense clearance before committing\n                            # a sampled-safe prefix. If it fails, try shorter.\n                            _v36_candidate = np.asarray(\n                                piece[:_v36_cut], dtype=float\n                            )\n\n                            _v36_edge_path = np.vstack((\n                                pose[None, :], _v36_candidate\n                            ))\n\n                            _v36_dense = []\n\n                            for _v36_i in range(\n                                len(_v36_edge_path) - 1\n                            ):\n                                _v36_p0 = _v36_edge_path[_v36_i]\n                                _v36_p1 = _v36_edge_path[_v36_i + 1]\n\n                                _v36_dist = float(\n                                    np.linalg.norm(\n                                        _v36_p1[:2] - _v36_p0[:2]\n                                    )\n                                )\n\n                                _v36_dyaw = math.atan2(\n                                    math.sin(float(\n                                        _v36_p1[2] - _v36_p0[2]\n                                    )),\n                                    math.cos(float(\n                                        _v36_p1[2] - _v36_p0[2]\n                                    )),\n                                )\n\n                                _v36_n = max(\n                                    1,\n                                    int(math.ceil(\n                                        _v36_dist / 0.01\n                                    )),\n                                    int(math.ceil(\n                                        abs(_v36_dyaw) / 0.05\n                                    )),\n                                )\n\n                                for _v36_k in range(_v36_n):\n                                    _v36_t = (\n                                        _v36_k / float(_v36_n)\n                                    )\n\n                                    _v36_dense.append([\n                                        float(\n                                            _v36_p0[0]\n                                            + _v36_t\n                                            * (_v36_p1[0] - _v36_p0[0])\n                                        ),\n                                        float(\n                                            _v36_p0[1]\n                                            + _v36_t\n                                            * (_v36_p1[1] - _v36_p0[1])\n                                        ),\n                                        float(\n                                            _v36_p0[2]\n                                            + _v36_t * _v36_dyaw\n                                        ),\n                                    ])\n\n                            _v36_dense.append(\n                                _v36_edge_path[-1].tolist()\n                            )\n\n                            _v36_dense_values = np.asarray(\n                                observed.pose_values(\n                                    np.asarray(\n                                        _v36_dense, dtype=float\n                                    )\n                                ),\n                                dtype=float,\n                            ).reshape(-1)\n\n                            _v36_dense_guard = max(\n                                float(observed.guard),\n                                float(cfg.margin),\n                                float(clearance_floor),\n                            )\n\n                            _v36_dense_c0 = float(\n                                observed.pose_values([pose])[0]\n                            )\n\n                            _v36_dense_reason = None\n\n                            if (\n                                _v36_dense_values.size < 2\n                                or not np.isfinite(\n                                    _v36_dense_values\n                                ).all()\n                            ):\n                                _v36_dense_reason = (\n                                    'NONFINITE_OR_EMPTY'\n                                )\n\n                            elif (\n                                _v36_dense_c0\n                                >= _v36_dense_guard - 1e-8\n                            ):\n                                if float(\n                                    np.min(_v36_dense_values)\n                                ) < _v36_dense_guard - 1e-8:\n                                    _v36_dense_reason = (\n                                        'POST_SAFE_REENTRY'\n                                    )\n\n                            else:\n                                _v36_dense_safe_idx = np.flatnonzero(\n                                    _v36_dense_values\n                                    >= _v36_dense_guard - 1e-8\n                                )\n\n                                if _v36_dense_safe_idx.size > 0:\n                                    _v36_dense_first = int(\n                                        _v36_dense_safe_idx[0]\n                                    )\n\n                                    if float(np.min(\n                                        _v36_dense_values[\n                                            :_v36_dense_first + 1\n                                        ]\n                                    )) < float(start_clearance) - 1e-4:\n                                        _v36_dense_reason = (\n                                            'ESCAPE_PREFIX_REGRESSION'\n                                        )\n\n                                    elif float(np.min(\n                                        _v36_dense_values[\n                                            _v36_dense_first:\n                                        ]\n                                    )) < _v36_dense_guard - 1e-8:\n                                        _v36_dense_reason = (\n                                            'ESCAPE_THEN_REENTRY'\n                                        )\n\n                                elif float(\n                                    np.min(_v36_dense_values)\n                                ) < float(start_clearance) - 1e-4:\n                                    _v36_dense_reason = (\n                                        'PRE_ESCAPE_REGRESSION'\n                                    )\n\n                            if _v36_dense_reason is not None:\n                                _v571_count = int(\n                                    stats.get(\n                                        'v571_dense_prefix_rejections',\n                                        0\n                                    )\n                                ) + 1\n\n                                stats[\n                                    'v571_dense_prefix_rejections'\n                                ] = _v571_count\n\n                                if _v571_count <= 5:\n                                    print(\n                                        'V571_DENSE_PREFIX_REJECTED_TRY_SHORTER',\n                                        {\n                                            'node_index': int(index),\n                                            'cut': int(_v36_cut),\n                                            'reason': _v36_dense_reason,\n                                            'dense_min_clearance_m': (\n                                                float(np.min(\n                                                    _v36_dense_values\n                                                ))\n                                                if _v36_dense_values.size\n                                                else None\n                                            ),\n                                            'dense_guard_m': (\n                                                _v36_dense_guard\n                                            ),\n                                        },\n                                        flush=True\n                                    )\n\n                                continue\n\n                            _v36_original_count = int(\n                                len(piece)\n                            )\n\n                            piece = np.asarray(\n                                piece[:_v36_cut],\n                                dtype=float\n                            ).copy()\n\n                            clearance = np.asarray(\n                                observed.pose_values(piece),\n                                dtype=float\n                            )\n\n                            if (\n                                not np.isfinite(\n                                    clearance\n                                ).all()\n                                or float(\n                                    np.min(clearance)\n                                ) < _v36_guard - 1e-8\n                            ):\n                                raise RuntimeError(\n                                    'V36_SHORT_PREFIX_SAFETY_FAILED'\n                                )\n\n                            print(\n                                'V36_SAFE_NODE_SHORT_PREFIX',\n                                {\n                                    'node_index':\n                                        int(index),\n                                    'original_samples':\n                                        _v36_original_count,\n                                    'retained_samples':\n                                        int(len(piece)),\n                                    'reach_m':\n                                        _v36_reach,\n                                    'start_clearance_m':\n                                        _v36_c0,\n                                    'end_clearance_m':\n                                        float(\n                                            clearance[-1]\n                                        ),\n                                },\n                                flush=True\n                            )\n\n                            break\n            if (\n                index == 0\n                and start_edge\n                and len(piece) >= 4\n                and np.min(clearance) < clearance_floor - 1e-9\n            ):\n                _v35_full = np.asarray(\n                    observed.pose_values(\n                        np.vstack((pose[None, :], piece))\n                    ),\n                    dtype=float\n                ).reshape(-1)\n\n                if (\n                    len(_v35_full) == len(piece) + 1\n                    and np.isfinite(_v35_full).all()\n                ):\n                    _v35_guard = max(float(observed.guard), float(clearance_floor))\n                    _v35_c0 = float(_v35_full[0])\n                    _v35_original_count = len(piece)\n\n                    for _v35_cut in range(\n                        _v35_original_count - 1, 1, -1\n                    ):\n                        _v35_prefix = _v35_full[\n                            :_v35_cut + 1\n                        ]\n\n                        _v35_safe = np.flatnonzero(\n                            _v35_prefix\n                            >= _v35_guard - 1e-8\n                        )\n\n                        if _v35_safe.size == 0:\n                            continue\n\n                        _v35_first = int(\n                            _v35_safe[0]\n                        )\n\n                        # 至少两个连续安全采样位置。\n                        if (\n                            _v35_cut - _v35_first < 1\n                        ):\n                            continue\n\n                        _v35_valid = bool(\n                            np.all(\n                                _v35_prefix[\n                                    :_v35_first\n                                ] >= _v35_c0 - 1e-5\n                            )\n                            and np.all(\n                                _v35_prefix[\n                                    _v35_first:\n                                ] >= _v35_guard - 1e-8\n                            )\n                        )\n\n                        if not _v35_valid:\n                            continue\n\n                        _v35_reach = float(\n                            np.linalg.norm(\n                                np.asarray(piece[_v35_cut - 1, :2], dtype=float)\n                                - np.asarray(pose[:2], dtype=float)\n                            )\n                        )\n                        if _v35_reach < 0.08:\n                            continue\n\n                        # 更新真正的搜索运动原语，\n                        # 不是仅修改可视化轨迹。\n                        piece = np.asarray(\n                            piece[:_v35_cut],\n                            dtype=float\n                        ).copy()\n\n                        clearance = np.asarray(\n                            observed.pose_values(piece),\n                            dtype=float\n                        )\n\n                        print(\n                            'V35_SHORT_PRIMITIVE',\n                            {\n                                'node_index': int(index),\n                                'original_samples':\n                                    int(_v35_original_count),\n                                'retained_samples':\n                                    int(len(piece)),\n                                'start_clearance_m':\n                                    float(_v35_c0),\n                                'endpoint_clearance_m':\n                                    float(clearance[-1]),\n                            },\n                            flush=True\n                        )\n                        break\n            if np.min(clearance) < clearance_floor - 1e-9:\n                continue\n            if np.min(clearance) < observed.guard:\n                _v29_current_clearance = float(observed.pose_values([nodes[index][0]])[0])\n                _v29_escape_depth = 0\n                _v29_cursor = index\n                while _v29_cursor is not None:\n                    _v29_node = nodes[_v29_cursor]\n                    if _v29_node[1] is None:\n                        break\n                    _v29_node_clearance = float(observed.pose_values([_v29_node[0]])[0])\n                    if _v29_node_clearance >= float(observed.guard) - 1e-8:\n                        break\n                    _v29_escape_depth += 1\n                    _v29_cursor = _v29_node[1]\n                _start_edge_primitive_ok = False\n                _edge_clearance = np.asarray([], dtype=float)\n                _safe_idx = np.asarray([], dtype=int)\n\n                if index == 0 and start_edge and len(clearance) >= 2:\n                    _edge_clearance = observed.pose_values(\n                        np.vstack((pose[None, :], piece))\n                    )\n\n                    _safe_idx = np.flatnonzero(\n                        _edge_clearance\n                        >= float(observed.guard) - 1e-8\n                    )\n\n                    if _safe_idx.size > 0:\n                        _first_safe = int(_safe_idx[0])\n\n                        _start_edge_primitive_ok = bool(\n                            np.all(\n                                _edge_clearance[:_first_safe]\n                                >= start_clearance - 1e-5\n                            )\n                            and np.all(\n                                _edge_clearance[_first_safe:]\n                                >= float(observed.guard) - 1e-8\n                            )\n                        )\n\n                if (not _start_edge_primitive_ok and start_edge and _v29_current_clearance < float(observed.guard) - 1e-8 and _v29_escape_depth < 8 and len(clearance) >= 2 and float(clearance[-1]) < float(observed.guard) - 1e-8):\n                    _v27_min_clearance = float(np.min(clearance))\n                    _v27_net_gain = float(clearance[-1] - clearance[0])\n                    if (_v27_min_clearance >= start_clearance - 1e-5 and _v27_net_gain >= -0.005):\n                        _start_edge_primitive_ok = True\n                        print('V2_9_BOUNDED_ESCAPE_ACCEPTED', {'node_index': int(index), 'escape_depth': int(_v29_escape_depth), 'current_clearance_m': _v29_current_clearance, 'min_clearance_m': _v27_min_clearance, 'net_gain_m': _v27_net_gain}, flush=True)\n                if not _start_edge_primitive_ok:\n                    if index == 0 and start_edge:\n                        stats.setdefault(\n                            'v2_4_edge_candidate_rejections', []\n                        ).append({\n                            'steering': float(steering),\n                            'min_piece_clearance_m': float(\n                                np.min(clearance)\n                            ),\n                            'first_piece_clearance_m': float(\n                                clearance[0]\n                            ),\n                            'last_piece_clearance_m': float(\n                                clearance[-1]\n                            ),\n                            'start_clearance_m': float(\n                                start_clearance\n                            ),\n                            'guard_m': float(observed.guard),\n                            'safe_sample_count': int(\n                                np.count_nonzero(\n                                    _edge_clearance\n                                    >= float(observed.guard) - 1e-8\n                                )\n                            ),\n                            'reason': 'EDGE_ESCAPE_CERTIFICATE_FAILED',\n                        })\n\n                    continue\n            _v40_edge_path = np.vstack((\n                pose[None, :], piece\n            ))\n            _v40_dense = []\n            for _i in range(len(_v40_edge_path) - 1):\n                _p0 = _v40_edge_path[_i]\n                _p1 = _v40_edge_path[_i + 1]\n                _dist = float(np.linalg.norm(_p1[:2] - _p0[:2]))\n                _dyaw = math.atan2(\n                    math.sin(float(_p1[2] - _p0[2])),\n                    math.cos(float(_p1[2] - _p0[2])),\n                )\n                _n = max(\n                    1,\n                    int(math.ceil(_dist / 0.01)),\n                    int(math.ceil(abs(_dyaw) / 0.05)),\n                )\n                for _k in range(_n):\n                    _t = _k / float(_n)\n                    _v40_dense.append([\n                        float(_p0[0] + _t * (_p1[0] - _p0[0])),\n                        float(_p0[1] + _t * (_p1[1] - _p0[1])),\n                        float(_p0[2] + _t * _dyaw),\n                    ])\n            _v40_dense.append(_v40_edge_path[-1].tolist())\n            _v40_clearance = np.asarray(\n                observed.pose_values(np.asarray(_v40_dense, dtype=float)),\n                dtype=float,\n            ).reshape(-1)\n\n            _v40_values = np.asarray(\n                _v40_clearance,\n                dtype=float\n            ).reshape(-1)\n\n            _v40_guard = max(\n                float(observed.guard),\n                float(cfg.margin),\n                float(clearance_floor)\n            )\n\n            _v40_c0 = float(\n                observed.pose_values([pose])[0]\n            )\n\n            _v40_reason = None\n\n            if (\n                _v40_values.size < 2\n                or not np.isfinite(_v40_values).all()\n            ):\n                _v40_reason = 'NONFINITE_OR_EMPTY'\n\n            elif _v40_c0 >= _v40_guard - 1e-8:\n\n                # 已经进入安全区域的搜索节点：\n                # 全部连续插值采样都必须安全。\n                if float(np.min(_v40_values)) < (\n                    _v40_guard - 1e-8\n                ):\n                    _v40_reason = 'POST_SAFE_REENTRY'\n\n            else:\n\n                # 原起点处于允许的临界脱困区域。\n                # 沿用最终证书的原则：\n                # 脱困前不得低于原起点安全间隙；\n                # 一旦进入安全区域，不可重新跌出。\n                _v40_safe = np.flatnonzero(\n                    _v40_values\n                    >= _v40_guard - 1e-8\n                )\n\n                if _v40_safe.size > 0:\n\n                    _v40_first = int(\n                        _v40_safe[0]\n                    )\n\n                    if float(np.min(\n                        _v40_values[:_v40_first + 1]\n                    )) < start_clearance - 1e-4:\n\n                        _v40_reason = 'ESCAPE_PREFIX_REGRESSION'\n\n                    elif float(np.min(\n                        _v40_values[_v40_first:]\n                    )) < _v40_guard - 1e-8:\n\n                        _v40_reason = 'ESCAPE_THEN_REENTRY'\n\n                elif float(\n                    np.min(_v40_values)\n                ) < start_clearance - 1e-4:\n\n                    _v40_reason = 'PRE_ESCAPE_REGRESSION'\n\n            if _v40_reason is not None:\n\n                _v40_key = (\n                    'v40_early_rejected_'\n                    + _v40_reason.lower()\n                )\n\n                stats[_v40_key] = (\n                    int(stats.get(_v40_key, 0)) + 1\n                )\n\n                if stats[_v40_key] <= 5:\n\n                    print(\n                        'V40_EDGE_REJECTED',\n                        {\n                            'reason': _v40_reason,\n                            'node_index': int(index),\n                            'start_clearance_m':\n                                _v40_c0,\n                            'dense_min_clearance_m':\n                                float(\n                                    np.min(_v40_values)\n                                ) if _v40_values.size\n                                else None,\n                            'guard_m': _v40_guard,\n                            'count': stats[_v40_key],\n                        },\n                        flush=True\n                    )\n\n                continue\n"

    _v23_assembly_old = (
        '            path = np.concatenate([start[None, :]]+pieces[::-1], axis=0)'
    )

    _v23_assembly_new = (
        '            path = np.concatenate([start[None, :]]+pieces[::-1], axis=0)'
    )

    _v23_final_old = '''            if observed.pose_values(path).min() < cfg.margin-1e-8:
                raise RuntimeError('Final continuous samples fail map margin')'''

    _v23_final_new = "            _final_dense = []\n            for _i in range(len(path) - 1):\n                _p0 = path[_i]\n                _p1 = path[_i + 1]\n                _dist = float(np.linalg.norm(_p1[:2] - _p0[:2]))\n                _dyaw = math.atan2(\n                    math.sin(float(_p1[2] - _p0[2])),\n                    math.cos(float(_p1[2] - _p0[2])),\n                )\n                _n = max(\n                    1,\n                    int(math.ceil(_dist / 0.01)),\n                    int(math.ceil(abs(_dyaw) / 0.05)),\n                )\n                for _k in range(_n):\n                    _t = _k / float(_n)\n                    _final_dense.append([\n                        float(_p0[0] + _t * (_p1[0] - _p0[0])),\n                        float(_p0[1] + _t * (_p1[1] - _p0[1])),\n                        float(_p0[2] + _t * _dyaw),\n                    ])\n            _final_dense.append(path[-1].tolist())\n            _final_clearance = np.asarray(\n                observed.pose_values(np.asarray(_final_dense, dtype=float)),\n                dtype=float,\n            ).reshape(-1)\n\n            if not np.isfinite(_final_clearance).all():\n                raise RuntimeError('V2_3_NONFINITE_FINAL_CLEARANCE')\n\n            _escape_ok = False\n\n            if start_edge:\n                _safe_idx = np.flatnonzero(\n                    _final_clearance >= float(observed.guard) - 1e-8\n                )\n\n                _escape_ok = bool(\n                    len(_final_clearance) > 0\n                    and _final_clearance[0] > 0.0\n                    and _final_clearance[0]\n                        >= float(observed.guard) - 1e-8\n                    and len(_safe_idx) > 0\n                    and np.min(\n                        _final_clearance[:int(_safe_idx[0]) + 1]\n                    ) >= float(_final_clearance[0]) - 1e-4\n                    and np.all(\n                        _final_clearance[int(_safe_idx[0]):]\n                        >= float(observed.guard) - 1e-8\n                    )\n                )\n\n                if not _escape_ok:\n                    _v31_safe_first = (\n                        int(_safe_idx[0]) if len(_safe_idx) else -1\n                    )\n                    _v31_pre_min = (\n                        float(np.min(\n                            _final_clearance[:_v31_safe_first + 1]\n                        ))\n                        if _v31_safe_first >= 0 else None\n                    )\n                    _v31_post_min = (\n                        float(np.min(\n                            _final_clearance[_v31_safe_first:]\n                        ))\n                        if _v31_safe_first >= 0 else None\n                    )\n                    print('V3_1_ESCAPE_CERTIFICATE_DIAGNOSTIC', {\n                        'start_clearance_m': float(_final_clearance[0]),\n                        'guard_m': float(observed.guard),\n                        'first_safe_index': _v31_safe_first,\n                        'pre_safe_min_m': _v31_pre_min,\n                        'post_safe_min_m': _v31_post_min,\n                        'start_gate_pass': bool(\n                            len(_final_clearance) > 0\n                            and _final_clearance[0] > 0.0\n                            and _final_clearance[0]\n                                >= float(observed.guard) - 0.025 - 1e-9\n                        ),\n                        'pre_safe_monotonic_pass': bool(\n                            _v31_safe_first >= 0\n                            and _v31_pre_min\n                                >= float(_final_clearance[0]) - 1e-4\n                        ),\n                        'post_safe_margin_pass': bool(\n                            _v31_safe_first >= 0\n                            and np.all(\n                                _final_clearance[_v31_safe_first:]\n                                >= float(observed.guard) - 1e-8\n                            )\n                        ),\n                    }, flush=True)\n                    stats['v38_rejected_goal_escape'] = int(stats.get('v38_rejected_goal_escape', 0)) + 1\n                    if stats['v38_rejected_goal_escape'] <= 8:\n                        print('V38_REJECTED_GOAL_CANDIDATE', {'reason': 'start_escape_certificate', 'count': stats['v38_rejected_goal_escape']}, flush=True)\n                    continue\n\n            elif float(np.min(_final_clearance)) < float(observed.guard) - 1e-8:\n                stats['v38_rejected_goal_margin'] = int(stats.get('v38_rejected_goal_margin', 0)) + 1\n                if stats['v38_rejected_goal_margin'] <= 8:\n                    print('V38_REJECTED_GOAL_CANDIDATE', {'reason': 'map_margin', 'count': stats['v38_rejected_goal_margin']}, flush=True)\n                continue\n\n            stats['start_edge_escape_certified'] = bool(_escape_ok)"

    for _old, _new, _name in [
        (_v23_start_old, _v23_start_new, "START_GATE"),
        (_v23_loop_old, _v23_loop_new, "FIRST_PRIMITIVE_GATE"),
        (_v23_assembly_old, _v23_assembly_new, "PATH_ASSEMBLY"),
        (_v23_final_old, _v23_final_new, "FINAL_CONTINUOUS_GATE"),
    ]:
        _n = _v23_plan_source.count(_old)
        if _n != 1:
            raise RuntimeError(
                'V2_3_PLANNER_ANCHOR_MISMATCH:' + _name + ':' + str(_n)
            )
        _v23_plan_source = _v23_plan_source.replace(_old, _new, 1)

    _v41_old_key = 'def key(pose):\n        return (round((pose[0]-cfg.lower)/cfg.search_resolution),\n                round((pose[1]-cfg.lower)/cfg.search_resolution),\n                round((pose[2] % (2*math.pi))*cfg.heading_bins/(2*math.pi)) % cfg.heading_bins)'
    _v41_new_key = 'def key(pose):\n        return (round((pose[0]-cfg.lower)/(cfg.search_resolution / (2.0 if start_edge else 1.0))),\n                round((pose[1]-cfg.lower)/(cfg.search_resolution / (2.0 if start_edge else 1.0))),\n                round((pose[2] % (2*math.pi))*cfg.heading_bins/(2*math.pi)) % cfg.heading_bins)'
    if _v23_plan_source.count(_v41_old_key) != 1:
        raise RuntimeError('V41_STATE_KEY_ANCHOR_MISMATCH')
    _v23_plan_source = _v23_plan_source.replace(
        _v41_old_key, _v41_new_key, 1
    )
    print('V41_START_EDGE_XY_RESOLUTION_FACTOR=0.5',
          flush=True)

    _v23_compiled = compile(
        _v23_plan_source,
        _v23_original_plan.__code__.co_filename,
        'exec',
    )

    _v23_plan_code = next(
        c for c in _v23_compiled.co_consts
        if isinstance(c, _v23_types.CodeType)
        and c.co_name == _v23_original_plan.__name__
    )

    _v23_plan_globals = dict(_v23_original_plan.__globals__)

    _v23_plan = _v23_types.FunctionType(
        _v23_plan_code,
        _v23_plan_globals,
        _v23_original_plan.__name__,
        _v23_original_plan.__defaults__,
        _v23_original_plan.__closure__,
    )

    _v23_plan.__kwdefaults__ = _v23_original_plan.__kwdefaults__
    _v23_plan.__annotations__ = _v23_original_plan.__annotations__


    def _v23_wrapped_plan(observed, start, goal, wheel_base, max_steer):
        _start = np.asarray(start, dtype=float).reshape(3)
        _c0 = float(observed.pose_values([_start])[0])
        _guard = float(observed.guard)

        _eligible = bool(
            0.0 < _c0 < _guard
            and _guard - _c0 <= 0.025 + 1e-9
        )

        if _eligible:
            # This changes only the heuristic grid's start cell.
            # Every motion primitive and final trajectory is still checked
            # against the unchanged full-footprint clearance criterion.
            observed.free = np.asarray(observed.free, dtype=bool).copy()
            _sx, _sy = observed.indices([_start[:2]])[0]
            observed.free[_sx, _sy] = True

        return _v23_plan(observed, _start, goal, wheel_base, max_steer)


    F.old.plan = _v23_wrapped_plan

    print(
        'V2_6_BOUNDED_ESCAPE_PATCH_ACTIVE',
        'guard_m=0.05',
        'maximum_initial_deficit_m=0.025',
        'dense_resolution_m=0.01',
        'global_guard_lowered=False',
        'source_files_modified=False',
        flush=True,
    )
    if not (b76/'contact_contract.py').is_file(): raise RuntimeError('B71_CONTACT_CONTRACT_MISSING')
    model = SAC.load(str(B.MODEL),device='cpu')
    shift = B.load_shift(SEED)
    out = __import__('pathlib').Path(__import__('os').environ['V541_OUTPUT_DIR'])
    out = __import__('pathlib').Path(__import__('os').environ['V541_OUTPUT_DIR'])
    out.mkdir(parents=True,exist_ok=False)
    (out/'assets').mkdir()
    (out/'assets/meshes_fixed').symlink_to(ROOT/'training/assets/mkmini_real/meshes_fixed',target_is_directory=True)
    B.OUT = out
    os.chdir(out)
    for key in ('XDG_CACHE_HOME','MESA_SHADER_CACHE_DIR','__GL_SHADER_DISK_CACHE_PATH'):
        os.environ[key]=str(out/'cache')
    os.environ['MPLCONFIGDIR']=str(out/'cache/matplotlib')
    sys.addaudithook(B.write_guard)
    P.install()

    # V2.5: exact V1 long-goal reset transplant; runtime only.

    import gymnasium as gym

    import math

    pass  # json imported at module scope

    import numpy as np

    import mujoco

    from training.envs.mkmini_real_indoor_phase2_astar_sac_env import MkMiniRealIndoorPhase2AStarSACEnv as Phase2Base

    from envs.phase22.mkmini_phase22_v1_continuous_corridor_env import MkMiniPhase22V1ContinuousCorridorEnv as PhaseEnv

    from training.phase21_risk_switch_fusion_sac.tests import eval_phase21_v3_exact_pair_5ep as E

    MIN_STRAIGHT = 6.8

    MAX_STRAIGHT = 7.7

    MIN_PATH = 7.0

    ENDPOINT_TOL = 0.3

    MAX_ATTEMPTS = 12000

    def long_goal_reset(self, seed=None, options=None):
        gym.Env.reset(self, seed=seed)

        self.step_count = 0
        self.prev_action[:] = 0.0

        distance_candidates = 0
        path_candidates = 0
        selected = None

        for attempt in range(1, MAX_ATTEMPTS + 1):
            start = np.asarray(
                self._sample_free_xy(),
                dtype=np.float32
            ).reshape(2)

            goal = np.asarray(
                self._sample_free_xy(),
                dtype=np.float32
            ).reshape(2)

            straight = float(np.linalg.norm(goal - start))

            if not (MIN_STRAIGHT <= straight <= MAX_STRAIGHT):
                if attempt % 2000 == 0:
                    print(
                        "LONG_GOAL_RESET_PROGRESS",
                        json.dumps({
                            "attempt": attempt,
                            "distance_candidates": distance_candidates,
                            "native_path_candidates": path_candidates,
                        }),
                        flush=True
                    )
                continue

            distance_candidates += 1

            # 使用现有环境的原生 A* 路径生成接口。
            path = self._plan_astar(start, goal)

            if path is None or len(path) < 5 or len(path) > 42:
                continue

            path_array = np.asarray(
                path,
                dtype=np.float64
            ).reshape(-1, 2)

            if not np.isfinite(path_array).all():
                continue

            path_length = float(
                np.linalg.norm(
                    np.diff(path_array, axis=0),
                    axis=1
                ).sum()
            )

            if path_length < MIN_PATH:
                continue

            path_candidates += 1

            selected = (
                start.copy(),
                goal.copy(),
                path,
                straight,
                path_length,
                attempt,
            )
            break

        if selected is None:
            raise RuntimeError(
                "NO_VALID_LONG_GOAL_TASK:"
                + json.dumps({
                    "seed": seed,
                    "attempts": MAX_ATTEMPTS,
                    "distance_candidates": distance_candidates,
                    "native_path_candidates": path_candidates,
                    "min_straight_m": MIN_STRAIGHT,
                    "max_straight_m": MAX_STRAIGHT,
                    "min_path_m": MIN_PATH,
                })
            )

        start, goal, path, straight, path_length, attempt = selected

        self.robot_xy = start.astype(np.float32)
        self.goal_xy = goal.astype(np.float32)
        self.robot_yaw = float(
            self.np_random.uniform(-math.pi, math.pi)
        )

        self.path_world = path
        self.wp_index = min(2, len(self.path_world) - 1)

        self.prev_goal_dist = float(self._goal_distance())
        self.prev_wp_dist = float(self._waypoint_distance())

        self._sync_mujoco()

        print(
            "LONG_GOAL_RESET_SELECTED",
            json.dumps({
                "seed": seed,
                "attempt": attempt,
                "start_xy": self.robot_xy.tolist(),
                "goal_xy": self.goal_xy.tolist(),
                "straight_distance_m": straight,
                "base_astar_path_length_m": path_length,
                "base_astar_path_points": len(path),
            }),
            flush=True
        )

        return self._get_obs(), {}

    Phase2Base.reset = long_goal_reset

    original_reset_env = E.reset_env

    def checked_reset_env(env, seed):
        obs = original_reset_env(env, seed)

        start = np.asarray(
            env.robot_xy, dtype=np.float64
        ).reshape(2)

        goal = np.asarray(
            env.goal_xy, dtype=np.float64
        ).reshape(2)

        raw_path = getattr(
            env, "phase21_v3_original_path", None
        )

        if raw_path is None:
            raise RuntimeError(
                "LONG_GOAL_NATIVE_GLOBAL_PATH_MISSING"
            )

        path = np.asarray(
            raw_path, dtype=np.float64
        )

        if (
            path.ndim != 2
            or path.shape[1] != 2
            or len(path) < 2
            or not np.isfinite(path).all()
        ):
            raise RuntimeError(
                "LONG_GOAL_NATIVE_GLOBAL_PATH_INVALID:"
                + repr(path.shape)
            )

        straight = float(np.linalg.norm(goal - start))

        path_length = float(
            np.linalg.norm(
                np.diff(path, axis=0),
                axis=1
            ).sum()
        )

        start_error = float(
            np.linalg.norm(path[0] - start)
        )

        goal_error = float(
            np.linalg.norm(path[-1] - goal)
        )

        metrics = {
            "seed": seed,
            "start_xy": start.tolist(),
            "goal_xy": goal.tolist(),
            "straight_distance_m": straight,
            "global_path_length_m": path_length,
            "path_points": len(path),
            "path_start_error_m": start_error,
            "path_goal_error_m": goal_error,
        }

        print(
            "LONG_GOAL_NATIVE_GATE_METRICS",
            json.dumps(metrics),
            flush=True
        )

        # ============================================================
        # LONG-GOAL INITIAL-POSE CLEARANCE GATE
        # ============================================================
        try:
            _is_free_fn = getattr(env, "_is_free", None)
            _collision_fn = getattr(env, "_check_collision", None)
            _lidar_fn = getattr(env, "_simulate_lidar", None)

            if not callable(_is_free_fn):
                raise RuntimeError("MISSING_NATIVE_IS_FREE")

            if not callable(_collision_fn):
                raise RuntimeError("MISSING_NATIVE_COLLISION_CHECK")

            if not callable(_lidar_fn):
                raise RuntimeError("MISSING_NATIVE_LIDAR")

            # 检查机器人占地半径以外，是否还保留至少 0.20 m 的地图净空。
            _map_free_020 = bool(
                _is_free_fn(start, margin=0.20)
            )

            _start_collision = bool(_collision_fn())

            # 在完整环境重置后重新读取 LiDAR。
            _lidar = np.asarray(
                _lidar_fn(),
                dtype=np.float64
            ).reshape(-1)

            _finite_lidar = _lidar[np.isfinite(_lidar)]

            if _finite_lidar.size == 0:
                raise RuntimeError("NO_FINITE_INITIAL_LIDAR")

            _min_lidar = float(np.min(_finite_lidar))

            # 估计起点在已知地图中，机器人名义半径之外的额外净空。
            _map_extra_margin = -1.0

            if _map_free_020:
                _lo = 0.0
                _hi = 1.5

                for _ in range(18):
                    _mid = (_lo + _hi) * 0.5

                    if bool(_is_free_fn(start, margin=_mid)):
                        _lo = _mid
                    else:
                        _hi = _mid

                _map_extra_margin = float(_lo)

            # 检查起点是否已经与场景障碍物接触。
            _obstacle_contacts = []

            for _ci in range(int(env.data.ncon)):
                _contact = env.data.contact[_ci]
                _g1 = int(_contact.geom1)
                _g2 = int(_contact.geom2)

                _n1 = mujoco.mj_id2name(
                    env.model,
                    mujoco.mjtObj.mjOBJ_GEOM,
                    _g1
                ) or ("geom_" + str(_g1))

                _n2 = mujoco.mj_id2name(
                    env.model,
                    mujoco.mjtObj.mjOBJ_GEOM,
                    _g2
                ) or ("geom_" + str(_g2))

                _a = str(_n1).lower()
                _b = str(_n2).lower()
                _joined = _a + " " + _b

                _floor_contact = any(
                    _token in _joined
                    for _token in ("floor", "ground", "plane")
                )

                _robot_like = lambda _n: any(
                    _token in _n
                    for _token in (
                        "wheel", "chassis", "robot",
                        "base_link", "vehicle", "car_body",
                        "bumper", "tire"
                    )
                )

                _obstacle_like = lambda _n: any(
                    _token in _n
                    for _token in (
                        "obs", "wall", "obstacle",
                        "table", "cabinet", "rect", "circle"
                    )
                )

                _robot_obstacle_pair = (
                    (_robot_like(_a) and _obstacle_like(_b))
                    or
                    (_robot_like(_b) and _obstacle_like(_a))
                )

                if (
                    not _floor_contact
                    and _robot_obstacle_pair
                    and float(_contact.dist) <= 1e-4
                ):
                    _obstacle_contacts.append({
                        "geom1": str(_n1),
                        "geom2": str(_n2),
                        "distance_m": float(_contact.dist),
                    })

        except Exception as _clearance_exc:
            raise RuntimeError(
                "LONG_GOAL_START_CLEARANCE_AUDIT_FAILED:"
                + repr(_clearance_exc)
            )

        _radius = getattr(env, "robot_radius", None)

        _clearance_metrics = {
            "start_xy": start.tolist(),
            "goal_xy": goal.tolist(),
            "straight_distance_m": float(straight),
            "global_path_length_m": float(path_length),
            "robot_radius_m": (
                float(_radius) if _radius is not None else None
            ),
            "known_map_free_with_extra_020m": bool(_map_free_020),
            "known_map_extra_margin_m": float(_map_extra_margin),
            "initial_min_lidar_m": float(_min_lidar),
            "initial_map_collision": bool(_start_collision),
            "initial_obstacle_contacts": _obstacle_contacts,
            "initial_obstacle_contact_count": len(_obstacle_contacts),
        }

        metrics.update(_clearance_metrics)

        print(
            "LONG_GOAL_START_CLEARANCE = "
            + json.dumps(_clearance_metrics, sort_keys=True),
            flush=True
        )

        # 如果起点净空不足，立即阻止正式配对导航。
        if (
            not _map_free_020
            or _map_extra_margin < 0.19
            or _start_collision
            or _min_lidar < 0.35
            or len(_obstacle_contacts) > 0
        ):
            raise RuntimeError(
                "LONG_GOAL_INITIAL_START_UNSAFE:"
                + json.dumps(_clearance_metrics, sort_keys=True)
            )

        print("LONG_GOAL_START_CLEARANCE_GATE = PASS", flush=True)

        passed = (
            MIN_STRAIGHT <= straight <= MAX_STRAIGHT
            and path_length >= MIN_PATH
            and start_error <= ENDPOINT_TOL
            and goal_error <= ENDPOINT_TOL
        )

        if not passed:
            raise RuntimeError(
                "LONG_GOAL_NATIVE_GATE_FAIL:"
                + json.dumps(metrics)
            )

        print("LONG_GOAL_NATIVE_GATE = PASS", flush=True)
        print(
            "LONG_GOAL_PAIRED_ROLLOUT_START = TRUE",
            flush=True
        )

        return obs

    E.reset_env = checked_reset_env

    print("LONG_GOAL_RESET_PATCH_INSTALLED=TRUE", flush=True)

    print('V2_FULL_RESET_START seed=',SEED,'output=',out,flush=True)
    reference=None
    results=[]
    env=None
    initial_checkpoint=None
    initial_observation=None
    for branch in ('frozen_original','rpccr_online'):
        E.seed_all(SEED)
        if env is None:
            env=Env()
            env._v629_rpccr_path_lease = False
            env._v629_v8_replan_blocked = 0
            _v629_original_v8_replan = env._phase21_v8_replan
            def _v629_guarded_v8_replan(margin_before):
                if getattr(env, '_v629_rpccr_path_lease', False):
                    env._v629_v8_replan_blocked += 1
                    print('V630_V8_REPLAN_BLOCKED', {
                        'step': int(getattr(env, 'phase21_v8_step', -1)),
                        'margin_before': float(margin_before),
                        'blocked_count': env._v629_v8_replan_blocked
                    }, flush=True)
                    return False
                return _v629_original_v8_replan(margin_before)
            env._phase21_v8_replan = _v629_guarded_v8_replan

            _v344_event_geom_name = 'real_circle_obs_10'
            _v344_base_known_map = MethodType(B.clean_map, env)
            _v344_map_hook_calls = [0]

            def _v344_known_map_without_injected_event(
                _self, *args, **kwargs
            ):
                _result = _v344_base_known_map(*args, **kwargs)
                _model = _self.model

                _gid = mujoco.mj_name2id(
                    _model,
                    mujoco.mjtObj.mjOBJ_GEOM,
                    _v344_event_geom_name
                )

                if _gid < 0:
                    raise RuntimeError(
                        'V344_UNKNOWN_GEOM_NOT_FOUND'
                    )

                _active = (
                    (
                        int(_model.geom_contype[_gid]) != 0
                        or int(_model.geom_conaffinity[_gid]) != 0
                    )
                    and float(_model.geom_rgba[_gid, 3]) > 0.01
                    and float(_model.geom_pos[_gid, 2]) > -1.0
                )

                if not _active:
                    return _result

                if not isinstance(_result, (tuple, list)):
                    raise RuntimeError(
                        'V344_MAP_RETURN_TYPE_UNSUPPORTED:'
                        + type(_result).__name__
                    )

                if len(_result) < 2:
                    raise RuntimeError(
                        'V344_MAP_RETURN_LENGTH_INVALID'
                    )

                _circles = np.asarray(
                    _result[1],
                    dtype=np.float32
                ).reshape(-1, 3)

                _center = np.asarray(
                    _model.geom_pos[_gid, :2],
                    dtype=np.float32
                )

                _radius = float(_model.geom_size[_gid, 0])

                if len(_circles):
                    _matches = (
                        (
                            np.linalg.norm(
                                _circles[:, :2] - _center,
                                axis=1
                            ) < 1e-4
                        )
                        &
                        (
                            np.abs(
                                _circles[:, 2] - _radius
                            ) < 1e-4
                        )
                    )
                else:
                    _matches = np.zeros(0, dtype=bool)

                _base_matches = int(np.count_nonzero(_matches))

                if _base_matches > 1:
                    raise RuntimeError(
                        'V344_UNKNOWN_MAP_MATCH_AMBIGUOUS:'
                        + str(_base_matches)
                    )

                _filtered = _circles[~_matches].copy()

                if len(_filtered):
                    _remaining = (
                        (
                            np.linalg.norm(
                                _filtered[:, :2] - _center,
                                axis=1
                            ) < 1e-4
                        )
                        &
                        (
                            np.abs(
                                _filtered[:, 2] - _radius
                            ) < 1e-4
                        )
                    )
                    _remaining_count = int(
                        np.count_nonzero(_remaining)
                    )
                else:
                    _remaining_count = 0

                if _remaining_count != 0:
                    raise RuntimeError(
                        'V344_UNKNOWN_MAP_EXCLUSION_FAILED'
                    )

                _v344_map_hook_calls[0] += 1

                print(
                    'V344_MAP_EXCLUSION '
                    + json.dumps({
                        'geom': _v344_event_geom_name,
                        'active': True,
                        'base_matches': _base_matches,
                        'removed': _base_matches,
                        'remaining_matches': _remaining_count,
                        'pass': True,
                    }, sort_keys=True),
                    flush=True
                )

                if isinstance(_result, tuple):
                    return (
                        _result[0],
                        _filtered,
                        *_result[2:]
                    )

                _updated = list(_result)
                _updated[1] = _filtered
                return _updated

            env._phase21_v4_known_map_obstacles = MethodType(
                _v344_known_map_without_injected_event,
                env
            )
            if not callable(getattr(env, '_phase21_v3_apply_path', None)):
                raise RuntimeError('V2_RUNTIME_PATH_CONSUMER_MISSING')
            if not callable(getattr(env, '_phase21_sensor_points', None)):
                raise RuntimeError('V2_CAUSAL_SENSOR_API_MISSING')
            if not callable(getattr(H, 'refresh', None)):
                raise RuntimeError('V2_OBSERVATION_REFRESH_API_MISSING')
        cell=out/branch
        cell.mkdir()
        original_mj=mujoco.mj_step
        recorder=None
        physics_count=0
        observer_checks=0
        public_step=[-1]
        try:
            if branch=='frozen_original':
                captured=[]
                original_reset=Env.reset
                @functools.wraps(original_reset)
                def capture_reset(self,*args,**kwargs):
                    result=original_reset(self,*args,**kwargs)
                    captured.append(result)
                    return result
                Env.reset=capture_reset
                try: E.reset_env(env,SEED)
                finally: Env.reset=original_reset
                if len(captured)!=1:
                    raise RuntimeError('UNEXPECTED_RESET_COUNT:'+str(len(captured)))
                observation=captured[0][0] if isinstance(captured[0],tuple) else captured[0]
                obs=np.asarray(observation,dtype=np.float32)
                if obs.ndim!=1 or obs.shape!=model.observation_space.shape or not np.isfinite(obs).all():
                    raise RuntimeError('RESET_OBSERVATION_MISMATCH:'+str(obs.shape))
                initial_observation=obs.copy()
            else:
                # Reuse the genuine initial reset, never a mid-navigation decision snapshot.
                if initial_checkpoint is None or initial_observation is None:
                    raise RuntimeError('INITIAL_RESET_CHECKPOINT_MISSING')
                initial_checkpoint.restore(shift)
                obs=initial_observation.copy()
            xml=out/'assets/isolated_indoor.xml'
            init={'state':A.state_digest(env,shift),'xml':sha(xml),
                  'observation':hashlib.sha256(obs.tobytes()).hexdigest(),
                  'start_xy':np.asarray(env.robot_xy).tolist(),
                  'goal_xy':np.asarray(env.goal_xy).tolist()}
            if reference is None:
                reference=init
                save(out/'paired_reset.json',init)
                initial_checkpoint=B.Snapshot(env,shift)
                if A.state_digest(env,shift)!=init['state']:
                    raise RuntimeError('INITIAL_CHECKPOINT_CAPTURE_MUTATED_STATE')
            elif init!=reference:
                differences={key:{'expected':reference[key],'actual':init[key]}
                             for key in reference if init.get(key)!=reference[key]}
                save(out/'restoration_mismatch.json',differences)
                raise RuntimeError('PAIRED_INITIAL_CHECKPOINT_RESTORE_MISMATCH:'+repr(list(differences)))
            else:
                print('B83_V3_PAIRED_RESET_RESTORED_IDENTICAL=TRUE',flush=True)
            if not B.audit_known_map(env)['known_map_source_gate_pass']:
                raise RuntimeError('KNOWN_MAP_LEAK_OR_AUDIT_FAILED')
            catalog=GeometryCatalog(env.model,mujoco,xml)
            recorder=ContactRecorder(catalog,cell)
            _v648_audit.begin(env,cell,branch)
            from instrumentation import install_physical_contract
            dump_physical = install_physical_contract(env)
            save(cell/'physical_contract.json',dump_physical)
            @functools.wraps(original_mj)
            def observe_mj(m,d,*args,**kwargs):
                nonlocal physics_count,observer_checks
                n=kwargs.get('nstep',args[0] if args else 1)
                if n!=1 or m is not env.model or d is not env.data:
                    raise RuntimeError('B71_MJSTEP_UNCOVERED')
                _v648_audit.before_native(m,d)
                answer=original_mj(m,d,*args,**kwargs)
                _v648_audit.after_native(m,d)
                physics_count+=1
                before=(float(d.time),d.qpos.tobytes(),d.qvel.tobytes(),d.ctrl.tobytes(),
                        d.qacc.tobytes(),d.qacc_warmstart.tobytes(),d.actuator_force.tobytes())
                recorder.record(d,physics_count,public_step[0])
                after=(float(d.time),d.qpos.tobytes(),d.qvel.tobytes(),d.ctrl.tobytes(),
                       d.qacc.tobytes(),d.qacc_warmstart.tobytes(),d.actuator_force.tobytes())
                if before!=after:raise RuntimeError('B71_OBSERVER_MUTATED_PHYSICS')
                observer_checks+=1
                return answer
            mujoco.mj_step=observe_mj
            attempts=0
            accepted=0
            planning_time=0.0
            unavailable_gates=0
            events=[]
            rows=[]
            started=time.monotonic()
            arrived=False
            native_collision=False
            terminated=False
            truncated=False
            _v3_goal_distance_window = []
            _v21_last_accept_step = -1000000
            _v28_last_attempt_step = -1000000
            for step in range(LIMIT):
                public_step[0]=step
                if step == 0:
                    _v66_old_tol = float(env.inner.goal_threshold)

                    if not (0.50 <= _v66_old_tol <= 5.00):
                        raise RuntimeError(
                            'V66_UNEXPECTED_GOAL_THRESHOLD:'
                            + str(_v66_old_tol)
                        )

                    env.inner.goal_threshold = 0.45

                    _v66_new_tol = float(
                        env.inner.goal_threshold
                    )

                    if abs(_v66_new_tol - 0.45) > 1e-7:
                        raise RuntimeError(
                            'V66_GOAL_THRESHOLD_NOT_APPLIED'
                        )

                    print(
                        'V66_NATIVE_GOAL_THRESHOLD',
                        json.dumps({
                            'branch': branch,
                            'step': step,
                            'original': _v66_old_tol,
                            'development': _v66_new_tol,
                            'symmetric_both_branches': True,
                        }),
                        flush=True
                    )
                _v3_goal_distance = float(np.linalg.norm(
                    np.asarray(env.goal_xy, dtype=float).reshape(2)
                    - np.asarray(env.robot_xy, dtype=float).reshape(2)
                ))
                _v3_goal_distance_window.append(_v3_goal_distance)
                if len(_v3_goal_distance_window) > 11:
                    del _v3_goal_distance_window[:-11]
                _v3_progress_stalled = bool(
                    len(_v3_goal_distance_window) >= 11
                    and (
                        _v3_goal_distance_window[0]
                        - _v3_goal_distance_window[-1]
                    ) < 0.03
                )
                try:
                    if branch=='rpccr_online' and step>=31 and getattr(__import__('sys').modules.get('v132_recovery_state'), 'STATE', None) is None and attempts<4 and step-_v28_last_attempt_step>=3 and (accepted==0 or (accepted>=1 and step-_v21_last_accept_step>=25)):
                        print('V344_POST_EVENT_REPLAN_TRIGGER step=', step, flush=True)
                        stage=str(env.inner.recovery_stage)
                        print('V44_GATE_STAGE', {'step':int(step), 'stage':str(stage), 'attempts':int(attempts), 'accepted':int(accepted)}, flush=True)
                        if stage=='NORMAL':
                            state=A.state_digest(env,shift)
                            snapshot=B.Snapshot(env,shift)
                            try:
                                margin = env._phase21_v8_future_sensor_margin()

                                if margin is None and step >= 31:
                                    _v46_fn = env._phase21_v8_future_sensor_margin
                                    _v46_owner = getattr(
                                        _v46_fn, '__self__', None
                                    )
                                    _v46_status = 'NO_VALID_FALLBACK'
                                    _v46_path_count = 0

                                    _v48_module = str(
                                        getattr(
                                            _v46_fn,
                                            '__module__',
                                            ''
                                        )
                                    )

                                    _v48_owner_verified = bool(
                                        _v46_owner is not None
                                        and callable(_v46_fn)
                                        and getattr(
                                            _v46_fn,
                                            '__self__',
                                            None
                                        ) is _v46_owner
                                        and getattr(
                                            _v46_fn,
                                            '__name__',
                                            ''
                                        )
                                        == '_phase21_v8_future_sensor_margin'
                                        and 'phase21' in _v48_module.lower()
                                    )

                                    print(
                                        'V48_BOUND_OWNER_AUDIT',
                                        {
                                            'step': int(step),
                                            'owner_type': type(
                                                _v46_owner
                                            ).__name__,
                                            'function_module':
                                                _v48_module,
                                            'verified':
                                                _v48_owner_verified,
                                            'owner_is_inner':
                                                _v46_owner is env.inner,
                                        },
                                        flush=True
                                    )

                                    if not _v48_owner_verified:
                                        _v46_status = 'PHASE_BOUND_OWNER_UNVERIFIED'

                                    elif getattr(
                                        _v46_owner,
                                        'phase21_v3_active_path',
                                        None
                                    ) is not None:
                                        _v46_status = 'ACTIVE_PATH_ALREADY_EXISTS'

                                    else:
                                        _v46_raw = getattr(
                                            env.inner,
                                            'dense_path',
                                            None
                                        )

                                        if _v46_raw is None:
                                            _v46_status = 'CONSUMER_PATH_MISSING'

                                        else:
                                            _v46_candidate = np.asarray(
                                                _v46_raw,
                                                dtype=float
                                            )

                                            if (
                                                _v46_candidate.ndim != 2
                                                or _v46_candidate.shape[1] < 2
                                                or len(_v46_candidate) < 2
                                                or not np.isfinite(
                                                    _v46_candidate
                                                ).all()
                                            ):
                                                _v46_status = 'INVALID_CONSUMER_PATH'

                                            else:
                                                _v46_xy = np.asarray(
                                                    _v46_candidate[:, :2],
                                                    dtype=float
                                                ).copy()

                                                _v46_goal = np.asarray(
                                                    env.goal_xy,
                                                    dtype=float
                                                ).reshape(2)

                                                _v46_goal_error = float(
                                                    np.linalg.norm(
                                                        _v46_xy[-1]
                                                        - _v46_goal
                                                    )
                                                )

                                                if _v46_goal_error > 1.0:
                                                    _v46_status = 'PATH_GOAL_MISMATCH'

                                                else:
                                                    _v46_path_count = int(
                                                        len(_v46_xy)
                                                    )

                                                    _v46_had_attr = hasattr(
                                                        _v46_owner,
                                                        'phase21_v3_active_path'
                                                    )

                                                    _v46_old_value = getattr(
                                                        _v46_owner,
                                                        'phase21_v3_active_path',
                                                        None
                                                    )

                                                    try:
                                                        setattr(
                                                            _v46_owner,
                                                            'phase21_v3_active_path',
                                                            _v46_xy
                                                        )

                                                        margin = _v46_fn()

                                                        _v46_status = (
                                                            'FALLBACK_RISK_VALID'
                                                            if margin is not None
                                                            and math.isfinite(
                                                                float(margin)
                                                            )
                                                            else 'FALLBACK_RISK_UNAVAILABLE'
                                                        )

                                                    finally:
                                                        if _v46_had_attr:
                                                            setattr(
                                                                _v46_owner,
                                                                'phase21_v3_active_path',
                                                                _v46_old_value
                                                            )
                                                        else:
                                                            delattr(
                                                                _v46_owner,
                                                                'phase21_v3_active_path'
                                                            )

                                    print(
                                        'V46_PATH_FALLBACK',
                                        {
                                            'step': int(step),
                                            'status': _v46_status,
                                            'consumer_path_points':
                                                _v46_path_count,
                                            'risk_margin_m':
                                                repr(margin),
                                            'uses_hidden_obstacle_pose': False,
                                        },
                                        flush=True
                                    )
                            finally:
                                snapshot.restore(shift)
                            if A.state_digest(env,shift)!=state:
                                raise RuntimeError('RISK_QUERY_MUTATED_STATE')
                            print('V44_GATE_MARGIN', {'step':int(step), 'margin':repr(margin)}, flush=True)
                            _v646_lease_active = bool(
                                getattr(env, '_v629_rpccr_path_lease', False)
                            )

                            _v647_margin_valid = bool(
                                margin is not None
                                and math.isfinite(float(margin))
                            )

                            _v647_low_margin = bool(
                                _v647_margin_valid
                                and float(margin) < 0.50
                            )

                            _v647_lease_risk = bool(
                                (not _v647_margin_valid)
                                or _v647_low_margin
                                or _v3_progress_stalled
                            )

                            _v647_replan_trigger = bool(
                                _v647_lease_risk
                                if _v646_lease_active
                                else (
                                    _v647_low_margin
                                    or _v3_progress_stalled
                                )
                            )

                            if (
                                _v646_lease_active
                                and _v647_lease_risk
                            ):
                                _v647_revoke_reason = (
                                    'UNKNOWN_RISK_MARGIN'
                                    if not _v647_margin_valid
                                    else (
                                        'LOW_RISK_MARGIN'
                                        if _v647_low_margin
                                        else 'PROGRESS_STALLED'
                                    )
                                )

                                env._v629_rpccr_path_lease = False

                                print(
                                    'V647_PATH_LEASE_REVOKED',
                                    {
                                        'step': int(step),
                                        'reason': _v647_revoke_reason,
                                        'margin_m': (
                                            float(margin)
                                            if _v647_margin_valid
                                            else None
                                        ),
                                        'progress_stalled':
                                            bool(_v3_progress_stalled),
                                    },
                                    flush=True
                                )

                                _v646_lease_active = False

                            if (
                                _v646_lease_active
                                and int(step) % 10 == 0
                            ):
                                print(
                                    'V647_ACTIVE_PATH_LEASE_SAFE',
                                    {
                                        'step': int(step),
                                        'margin_m': float(margin),
                                    },
                                    flush=True
                                )

                            if _v647_replan_trigger:
                                attempts+=1
                                _v28_last_attempt_step = int(step)
                                event = {
                                    'step': step,
                                    'margin_m': (
                                        float(margin)
                                        if margin is not None
                                        and math.isfinite(float(margin))
                                        else None
                                    ),
                                    'v3_progress_stalled': bool(_v3_progress_stalled),
                                    'v3_goal_distance_m': float(_v3_goal_distance),
                                }
                                state=A.state_digest(env,shift)
                                t=time.monotonic()
                                pool=None
                                try:
                                    pool=C.collect(env,shift,planner,module,Parent)
                                except B.ReplayMismatch as err:
                                    # Only the known non-executable injection boundary is a recoverable case.
                                    if str(err)!='Expected one executable Phase22 search at audited gate':
                                        raise
                                    snapshot.restore(shift)
                                    if A.state_digest(env,shift)!=state:
                                        raise RuntimeError('GATE_DEFER_RESTORE_STATE_MISMATCH')
                                    unavailable_gates+=1
                                    planning_time+=time.monotonic()-t
                                    event['search_status']='deferred_no_executable_gate'
                                    event['rejected']='NO_EXECUTABLE_HANDOFF_GATE'
                                    event['note']='NO_PATH_APPLIED_FROZEN_BASELINE_CONTINUES'
                                _v2_obs_before = np.asarray(obs, dtype=np.float32).copy()
                                _v2_active_before = W.path_hash(env)
                                _v2_dense_before = B.fingerprint(
                                    np.asarray(env.inner.dense_path)
                                )

                                event.pop('rejected', None)
                                event.pop('note', None)

                                if pool is not None:
                                    _v2_sensor_world = pool['request']['sensor_points']
                                    event['handoff_mode'] = 'EXISTING_PHASE22_EXECUTABLE_GATE'
                                    event['native_phase22_gate_unavailable'] = False

                                else:
                                    _v2_sensor_snapshot = B.Snapshot(env, shift)
                                    _v2_sensor_state = A.state_digest(env, shift)

                                    try:
                                        _v2_sensor_world, _ = env._phase21_sensor_points()
                                    finally:
                                        _v2_sensor_snapshot.restore(shift)

                                    if A.state_digest(env, shift) != _v2_sensor_state:
                                        raise RuntimeError('V2_SENSOR_QUERY_MUTATED_STATE')

                                    event['handoff_mode'] = 'V2_DIRECT_RUNTIME_PATH_OWNER'
                                    event['native_phase22_gate_unavailable'] = True

                                world = H.world_input(env, _v2_sensor_world)

                                world['footprint_bounds'] = (
                                    F.extract_self_envelope(env, mujoco)['bounds_xy']
                                )

                                _v333_env_goal = np.asarray(env.goal_xy, dtype=float).reshape(2)
                                _v333_reset_path = out / 'paired_reset.json'
                                if not _v333_reset_path.is_file():
                                    raise RuntimeError('V3_3_3_PAIRED_RESET_GOAL_RECORD_MISSING')
                                _v333_reset_meta = __import__('json').loads(
                                    _v333_reset_path.read_text(encoding='utf-8')
                                )
                                _v333_recorded_goal = np.asarray(
                                    _v333_reset_meta.get('goal_xy', []), dtype=float
                                ).reshape(-1)
                                if (
                                    _v333_recorded_goal.size != 2
                                    or not np.isfinite(_v333_recorded_goal).all()
                                ):
                                    raise RuntimeError('V3_3_3_PAIRED_RESET_GOAL_INVALID')
                                if not np.allclose(
                                    _v333_env_goal, _v333_recorded_goal, atol=1e-6, rtol=0.0
                                ):
                                    raise RuntimeError(
                                        'V3_3_3_ENV_GOAL_NOT_EQUAL_PAIRED_RESET_GOAL:'
                                        + str({
                                            'environment_goal': _v333_env_goal.tolist(),
                                            'paired_reset_goal': _v333_recorded_goal.tolist(),
                                        })
                                    )
                                try:
                                    _v333_world_goal_before = np.asarray(
                                        world.get('goal', []), dtype=float
                                    ).reshape(-1)
                                except Exception:
                                    _v333_world_goal_before = np.asarray([], dtype=float)
                                print('V3_3_3_ENV_GOAL=', _v333_env_goal.tolist(), flush=True)
                                print('V3_3_3_PAIRED_RESET_GOAL=', _v333_recorded_goal.tolist(), flush=True)
                                print('V3_3_3_PLANNER_GOAL_BEFORE=', _v333_world_goal_before.tolist(), flush=True)
                                world['goal'] = _v333_env_goal.copy()
                                _v333_world_goal_after = np.asarray(
                                    world.get('goal', []), dtype=float
                                ).reshape(-1)
                                if (
                                    _v333_world_goal_after.size != 2
                                    or not np.allclose(
                                        _v333_world_goal_after, _v333_env_goal,
                                        atol=1e-8, rtol=0.0
                                    )
                                ):
                                    raise RuntimeError('V3_3_3_PLANNER_GOAL_ASSIGNMENT_FAILED')
                                print('V3_3_3_PLANNER_GOAL_AFTER=', _v333_world_goal_after.tolist(), flush=True)
                                print('V3_3_3_GOAL_ALIGNED=TRUE', flush=True)
                                print('V44_SEARCH_STARTED', {'step':int(step), 'attempts':int(attempts)}, flush=True)
                                if branch == 'rpccr_online' and step in (31, 32, 36, 37):
                                    try:
                                        _v53_start = np.asarray(
                                            world['start'], dtype=float
                                        ).reshape(-1)
                                        _v53_raw = np.asarray(
                                            _v2_sensor_world, dtype=float
                                        )
                                        _v53_record = {
                                            'step': int(step),
                                            'start_pose': _v53_start[:3].tolist(),
                                            'sensor_shape': list(_v53_raw.shape),
                                            'nearest_sensor_xy': None,
                                            'nearest_sensor_range_m': None,
                                            'sensor_count': 0,
                                            'algorithm_input_modified': False,
                                        }
                                        if (
                                            _v53_raw.ndim == 2
                                            and _v53_raw.shape[1] >= 2
                                            and len(_v53_raw) > 0
                                        ):
                                            _v53_xy = _v53_raw[:, :2]
                                            _v53_dist = np.linalg.norm(
                                                _v53_xy - _v53_start[:2],
                                                axis=1
                                            )
                                            _v53_idx = int(np.argmin(_v53_dist))
                                            _v53_record['sensor_count'] = int(
                                                len(_v53_xy)
                                            )
                                            _v53_record['nearest_sensor_xy'] = (
                                                _v53_xy[_v53_idx].tolist()
                                            )
                                            _v53_record['nearest_sensor_range_m'] = (
                                                float(_v53_dist[_v53_idx])
                                            )
                                        print(
                                            'V53_SENSOR_GEOMETRY',
                                            json.dumps(
                                                _v53_record,
                                                ensure_ascii=False,
                                                allow_nan=False
                                            ),
                                            flush=True
                                        )
                                    except Exception as _v53_error:
                                        print(
                                            'V53_DIAGNOSTIC_ERROR',
                                            repr(_v53_error),
                                            flush=True
                                        )

                                # V616: apply the acceptance floor to the actual new map.
                                _v616_original_footprint_map_init = getattr(
                                    F, '_v616_original_footprint_map_init', None
                                )
                                if _v616_original_footprint_map_init is None:
                                    _v616_original_footprint_map_init = F.FootprintMap.__init__
                                    F._v616_original_footprint_map_init = (
                                        _v616_original_footprint_map_init
                                    )
                                    def _v616_guarded_footprint_map_init(self, inputs):
                                        _v616_original_footprint_map_init(self, inputs)

                                        _v616_base_guard = float(self.guard)
                                        _v616_hard_guard = max(_v616_base_guard, 0.15)

                                        _v616_start = np.asarray(
                                            inputs['start'], dtype=float
                                        ).reshape(3)

                                        _v616_start_clearance = float(
                                            self.pose_values([_v616_start])[0]
                                        )

                                        if not np.isfinite(_v616_start_clearance):
                                            raise RuntimeError(
                                                'V616_NONFINITE_START_CLEARANCE'
                                            )

                                        _v616_required = max(
                                            _v616_hard_guard,
                                            min(0.30, _v616_start_clearance) - 0.01,
                                        )

                                        _v616_cfg_copy = (
                                            __import__('copy').copy(self.config)
                                        )

                                        object.__setattr__(
                                            _v616_cfg_copy,
                                            'margin',
                                            float(_v616_hard_guard)
                                        )

                                        self.config = _v616_cfg_copy
                                        self.guard = float(_v616_hard_guard)
                                        print('V619_GUARD_SEMANTICS', {'search_hard_floor_m': float(self.guard), 'final_continuous_floor_m': float(self.config.margin), 'preferred_clearance_m': float(_v616_required)}, flush=True)
                                        print('V616_SEARCH_ACCEPTANCE_GUARD', {
                                            'base_guard_m': _v616_base_guard,
                                            'hard_guard_m': _v616_hard_guard,
                                            'start_clearance_m': _v616_start_clearance,
                                            'target_clearance_m': 0.30,
                                            'preferred_clearance_m': float(_v616_required),
                                            'actual_new_field_guard_m': float(self.guard),
                                            'actual_config_margin_m': float(self.config.margin),
                                            'guard_margin_equal': bool(
                                                abs(float(self.guard) -
                                                    float(self.config.margin)) < 1e-10
                                            ),
                                            'start_above_preferred': bool(
                                                _v616_start_clearance >= _v616_required - 1e-9
                                            ),
                                        }, flush=True)

                                    F.FootprintMap.__init__ = (
                                        _v616_guarded_footprint_map_init
                                    )

                                print('V616_GUARD_WRAPPER_INSTALLED', {
                                    'policy': 'HARD_015_SOFT_030',
                                    'hard_floor_m': 0.15,
                                    'target_m': 0.30,
                                    'start_tolerance_m': 0.01,
                                    'stale_object_mutation': False,
                                }, flush=True)
                                _v600_start = np.asarray(world.get('start', []), dtype=float).reshape(-1)
                                _v600_sensor = np.asarray(world.get('sensor_points', []), dtype=float)
                                _v600_state_obj = getattr(_v132_state, 'STATE', None)
                                _v600_state_mode = _v600_state_obj.get('mode') if isinstance(_v600_state_obj, dict) else None
                                _v600_start_json = _v600_start[:3].tolist() if _v600_start.size >= 3 and np.isfinite(_v600_start[:3]).all() else None
                                print('V600_REPLAN_INPUT', json.dumps({
                                    'step': int(step),
                                    'branch': str(branch),
                                    'start_pose_xy_yaw': _v600_start_json,
                                    'recovery_completed': bool(getattr(_v132_state, 'RECOVERY_COMPLETED', False)),
                                    'recovery_state_mode': _v600_state_mode,
                                    'sensor_shape': list(_v600_sensor.shape),
                                    'sensor_count': int(_v600_sensor.shape[0]) if _v600_sensor.ndim >= 1 else 0,
                                }, allow_nan=False), flush=True)
                                _v648_audit.before_search(world,step)
                                field, path, stats = F.search(world)
                                _v648_audit.after_search(path,stats,field)
                                _v600_path_shape = list(np.asarray(path).shape) if path is not None else None
                                _v600_counters = {str(k): str(v) for k, v in stats.items() if str(k).startswith(('v40_', 'v571_', 'v2_')) and isinstance(v, (int, float, str, bool))}
                                print('V600_REPLAN_OUTPUT', json.dumps({
                                    'step': int(step),
                                    'status': str(stats.get('status')),
                                    'expanded': int(stats.get('expanded', 0)),
                                    'initial_clearance_m': str(stats.get('initial_clearance_m')),
                                    'path_exists': path is not None,
                                    'path_shape': _v600_path_shape,
                                    'gate_counters': _v600_counters,
                                }, allow_nan=False), flush=True)
                                _v520_clearance = float(stats.get('initial_clearance_m', -1.0))
                                _v520_recovery_done = bool(getattr(_v132_state, 'RECOVERY_COMPLETED', False))
                                _v520_geom_admit = bool(stats.get('status') == 'start_occupied_no_teleport' and math.isfinite(_v520_clearance) and 0.025 <= _v520_clearance < 0.15)
                                _v598_points = np.asarray(world.get('sensor_points', []), dtype=float)
                                _v598_guard = float(getattr(field, 'guard', 0.15))
                                _v598_sensor_ok = bool(_v598_points.ndim == 2 and _v598_points.shape[1] >= 2 and len(_v598_points) > 0 and np.isfinite(_v598_points[:, :2]).all())
                                _v598_recovery_geom_admit = bool(branch == 'rpccr_online' and stats.get('status') == 'search_exhausted' and math.isfinite(_v520_clearance) and math.isfinite(_v598_guard) and _v520_clearance >= _v598_guard and _v598_sensor_ok)
                                print('V598_RECOVERY_GEOMETRY_GATE', json.dumps({'status': stats.get('status'), 'clearance_m': _v520_clearance, 'guard_m': _v598_guard, 'sensor_points': len(_v598_points), 'sensor_ok': _v598_sensor_ok, 'admit': _v598_recovery_geom_admit}), flush=True)
                                if branch == 'rpccr_online':
                                    print('V520_RECOVERY_ADMISSION', json.dumps({'seed': int(SEED), 'status': stats.get('status'), 'initial_clearance_m': _v520_clearance, 'admit': _v520_geom_admit, 'recovery_completed': _v520_recovery_done}), flush=True)
                                    if (not _v520_recovery_done and not _v520_geom_admit and path is not None):
                                        stats = dict(stats)
                                        stats['native_search_status'] = stats.get('status')
                                        stats['status'] = 'geometry_deferred_pre_recovery'
                                        path = None
                                        print('V520_PATH_DEFERRED_LOW_CLEARANCE', flush=True)

                                _v599_latch_arm_needed = bool(
                                    branch == 'rpccr_online'
                                    and _v132_state.STATE is None
                                    and _v598_recovery_geom_admit
                                    and not getattr(_v132_state, 'V599_RECOVERY_LATCH_ARMED', False)
                                )
                                if _v599_latch_arm_needed:
                                    _v132_state.V599_RECOVERY_LATCH_ARMED = True
                                    _v599_latch_before = bool(getattr(_v132_state, 'RECOVERY_COMPLETED', False))
                                    if _v599_latch_before:
                                        _v132_state.RECOVERY_COMPLETED = False
                                    print('V599_RECOVERY_LATCH_ARMED', json.dumps({
                                        'branch': branch,
                                        'state_is_none': _v132_state.STATE is None,
                                        'geometry_admit': bool(_v598_recovery_geom_admit),
                                        'latch_before': _v599_latch_before,
                                        'latch_after': bool(getattr(_v132_state, 'RECOVERY_COMPLETED', False)),
                                    }), flush=True)
                                if not getattr(__import__('v132_recovery_state'), 'RECOVERY_COMPLETED', False):
                                    if (branch == 'rpccr_online' and _v132_state.STATE is None and (_v520_geom_admit or _v598_recovery_geom_admit)):
                                        _v132_points = np.asarray(
                                            world.get('sensor_points', []),
                                            dtype=float
                                        )
                                
                                        _v132_start = np.asarray(
                                            world['start'], dtype=float
                                        ).reshape(3)
                                
                                        if (
                                            _v132_points.ndim != 2
                                            or _v132_points.shape[1] < 2
                                            or len(_v132_points) < 1
                                        ):
                                            raise RuntimeError(
                                                'V132_ONLINE_SENSOR_UNAVAILABLE'
                                            )
                                
                                        _v132_heading = np.array([
                                            np.cos(_v132_start[2]),
                                            np.sin(_v132_start[2])
                                        ])
                                
                                        _v132_rel = (
                                            _v132_points[:, :2]
                                            - _v132_start[None, :2]
                                        )
                                
                                        _v132_long = (
                                            _v132_rel @ _v132_heading
                                        )
                                
                                        _v132_lateral = np.abs(
                                            _v132_rel[:, 0] * _v132_heading[1]
                                            - _v132_rel[:, 1] * _v132_heading[0]
                                        )
                                
                                        # 检查预定倒车范围及车尾延伸区域。
                                        # 传感器没有可靠数据时不冒险继续。
                                        _v132_rear_risk = bool(np.any(
                                            (_v132_long >= -1.10)
                                            & (_v132_long <= 0.0)
                                            & (_v132_lateral <= 0.55)
                                        ))
                                
                                        _v132_state.STATE = {
                                            'mode': (
                                                'BLOCKED'
                                                if _v132_rear_risk
                                                else 'BACK'
                                            ),
                                            'initial_xy': _v132_start[:2].copy(),
                                            'heading': _v132_heading.copy(),
                                            'start_step': int(step),
                                            'hold_step': None,
                                            'reverse_m': 0.0,
                                        }
                                
                                        print(
                                            'V132_ONLINE_RECOVERY',
                                            json.dumps({
                                                'step': int(step),
                                                'online_sensor_points':
                                                    int(len(_v132_points)),
                                                'rear_corridor_risk':
                                                    _v132_rear_risk,
                                                'mode': _v132_state.STATE['mode'],
                                                'target_reverse_m': 0.40,
                                                'hidden_truth_used': False,
                                            }),
                                            flush=True
                                        )
                                _v2_start_pose = np.asarray(world['start'], dtype=float).reshape(3)
                                _v2_original_guard = float(field.guard)
                                _v2_start_clearance = float(field.pose_values([_v2_start_pose])[0])
                                _v2_start_deficit = _v2_original_guard - _v2_start_clearance

                                _v23_start_pose = np.asarray(world['start'], dtype=float).reshape(3)
                                _v23_start_c0 = float(field.pose_values([_v23_start_pose])[0])
                                event['start_edge_initial_clearance_m'] = _v23_start_c0
                                event['start_edge_deficit_m'] = float(0.05 - _v23_start_c0)
                                event['start_edge_eligible'] = bool(
                                    0.0 < _v23_start_c0 < 0.05
                                    and 0.05 - _v23_start_c0 <= 0.025 + 1e-9
                                )
                                event['start_edge_plan_certificate'] = bool(
                                    stats.get('start_edge_escape_certified', False)
                                )
                                print('V3_RISK_PROGRESS_SEARCH', json.dumps({
                                    'step': event.get('step'),
                                    'clearance_m': _v23_start_c0,
                                    'eligible': event['start_edge_eligible'],
                                    'plan_certificate': event['start_edge_plan_certificate'],
                                    'search_status': stats.get('status'),
                                    'expanded': stats.get('expanded'),
                                    'candidate_rejections': stats.get('v2_4_edge_candidate_rejections', []),
                                }, ensure_ascii=False, allow_nan=False), flush=True)
                                planning_time += time.monotonic() - t

                                event['search_status'] = stats.get('status')
                                event['expanded'] = stats.get('expanded')
                                event['footprint_search_status'] = stats.get('status')
                                event['footprint_search_wall_seconds'] = stats.get('wall_seconds')

                                if A.state_digest(env, shift) != state:
                                    raise RuntimeError('V2_PLANNER_MUTATED_STATE')

                                if path is not None and stats.get('status') == 'found':

                                    path = np.asarray(path, dtype=float)

                                    if (
                                        path.ndim != 2
                                        or path.shape[1] != 3
                                        or not np.isfinite(path).all()
                                    ):
                                        raise RuntimeError('V2_BAD_PATH_OUTPUT')

                                    if np.linalg.norm(
                                        path[0, :2] - np.asarray(world['start'])[:2]
                                    ) > 0.15:
                                        raise RuntimeError('V2_PATH_START_MISMATCH')

                                    clearance = float(np.min(field.pose_values(path)))
                                    event['clearance_m'] = clearance
                                    event['start_edge_candidate_certificate'] = bool(_v2_escape_certificate(np, field, path, np.asarray(world['start'], dtype=float), 0.05, tolerance=0.025))

                                    _v564_start_clearance = float(field.pose_values([np.asarray(world['start'], dtype=float).reshape(3)])[0])
                                    _v620_hard_clearance_floor = max(0.15, float(field.guard))
                                    _v620_preferred_clearance = max(float(field.guard), min(0.30, _v564_start_clearance) - 0.01)
                                    _v564_required_clearance = float(_v620_hard_clearance_floor)
                                    print('V620_CLEARANCE_POLICY', {
                                        'hard_floor_m': float(_v620_hard_clearance_floor),
                                        'preferred_m': float(_v620_preferred_clearance),
                                        'target_m': 0.30
                                    }, flush=True)
                                    event['start_clearance_m'] = _v564_start_clearance
                                    event['clearance_target_m'] = 0.30
                                    event['required_full_footprint_clearance_m'] = _v564_required_clearance
                                    print('V620_INITIAL_PATH_GATE', {'minimum_clearance_m': float(clearance), 'hard_floor_m': float(_v564_required_clearance)}, flush=True)
                                    if clearance < _v564_required_clearance - 1e-6:
                                        event['rejected'] = 'LOW_FULL_FOOTPRINT_CLEARANCE'
                                        event['accepted'] = False

                                    else:
                                        _v2_sync = None
                                        _v2_applied = None
                                        _v2_owner_count = None

                                        if pool is not None:

                                            obs, _v2_applied = H.apply(
                                                env, obs, shift, path, field, pool, module, Parent
                                            )

                                            _v2_sync = _v2_applied['sync']

                                            if not (
                                                _v2_sync['complete_other_state_equal']
                                                and _v2_sync['all_non_path_observation_equal']
                                                and _v2_sync['no_sensor_queries']
                                            ):
                                                snapshot.restore(shift)
                                                obs = _v2_obs_before.copy()
                                                raise RuntimeError('V2_EXISTING_HANDOFF_SYNC_FAILED')

                                        else:

                                            _v2_owner_count = 0
                                            _v2_owner_target_name = None
                                            _v2_attempt_count = 0
                                            _v2_seen_target_ids = set()
                                            _v2_targets = [
                                                ('env.inner', getattr(env, 'inner', None)),
                                                ('env', env),
                                            ]
                                            for _v2_label, _v2_obj in _v2_targets:
                                                if _v2_obj is None or id(_v2_obj) in _v2_seen_target_ids:
                                                    continue
                                                _v2_seen_target_ids.add(id(_v2_obj))
                                                _v2_candidate_fn = getattr(
                                                    _v2_obj, '_phase21_v3_apply_path', None
                                                )
                                                if not callable(_v2_candidate_fn):
                                                    continue
                                                if _v2_attempt_count > 0:
                                                    snapshot.restore(shift)
                                                    obs = _v2_obs_before.copy()
                                                    if A.state_digest(env, shift) != state:
                                                        raise RuntimeError('V2_OWNER_RETRY_RESTORE_MISMATCH')
                                                _v2_attempt_count += 1
                                                _v2_active_try_before = W.path_hash(env)
                                                _v2_count_try = int(_v2_candidate_fn(path[:, :2]))
                                                _v2_active_try_after = W.path_hash(env)
                                                event.setdefault('runtime_path_owner_attempts', []).append({
                                                    'target': _v2_label,
                                                    'changed_count': _v2_count_try,
                                                    'active_hash_before': _v2_active_try_before,
                                                    'active_hash_after': _v2_active_try_after,
                                                    'active_hash_changed': _v2_active_try_after != _v2_active_try_before,
                                                })
                                                if (
                                                    _v2_count_try > 0
                                                    and _v2_active_try_after != _v2_active_before
                                                ):
                                                    _v2_owner_count = _v2_count_try
                                                    _v2_owner_target_name = _v2_label
                                                    event['runtime_path_owner_target'] = _v2_label
                                                    break
                                                snapshot.restore(shift)
                                                obs = _v2_obs_before.copy()
                                                if A.state_digest(env, shift) != state:
                                                    raise RuntimeError('V2_OWNER_RETRY_RESTORE_MISMATCH')

                                            event['runtime_path_owner_count'] = _v2_owner_count

                                            if _v2_owner_count <= 0:
                                                snapshot.restore(shift)
                                                obs = _v2_obs_before.copy()

                                                if A.state_digest(env, shift) != state:
                                                    raise RuntimeError('V2_NO_OWNER_RESTORE_FAILED')

                                                event['rejected'] = 'NO_RUNTIME_PATH_OWNER'
                                                event['accepted'] = False

                                            else:

                                                obs, _v2_sync = H.refresh(
                                                    env, obs, shift, B
                                                )

                                                if not (
                                                    _v2_sync['complete_other_state_equal']
                                                    and _v2_sync['all_non_path_observation_equal']
                                                    and _v2_sync['no_sensor_queries']
                                                ):
                                                    snapshot.restore(shift)
                                                    obs = _v2_obs_before.copy()

                                                    if A.state_digest(env, shift) != state:
                                                        raise RuntimeError(
                                                            'V2_SYNC_FAILURE_RESTORE_MISMATCH'
                                                        )

                                                    raise RuntimeError('V2_PATH_APPLY_SYNC_FAILED')

                                        if 'rejected' not in event:

                                            _v2_active_after = W.path_hash(env)

                                            _v2_dense, _v2_dense_poses_arr = _v2_dense_poses(
                                                np, env.inner.dense_path
                                            )

                                            _v2_dense_hash = B.fingerprint(_v2_dense)

                                            _v2_dense_clearance = float(
                                                np.min(field.pose_values(_v2_dense_poses_arr))
                                            )

                                            event['consumer_active_path_hash_before'] = (
                                                _v2_active_before
                                            )
                                            event['consumer_active_path_hash_after'] = (
                                                _v2_active_after
                                            )
                                            event['consumer_dense_path_hash'] = _v2_dense_hash
                                            event[
                                                'consumer_dense_min_full_footprint_clearance_m'
                                            ] = _v2_dense_clearance

                                            if (
                                                _v2_active_after == _v2_active_before
                                                or _v2_dense_hash == _v2_dense_before
                                            ):
                                                snapshot.restore(shift)
                                                obs = _v2_obs_before.copy()

                                                if A.state_digest(env, shift) != state:
                                                    raise RuntimeError(
                                                        'V2_PATH_NOT_CONSUMED_RESTORE_MISMATCH'
                                                    )

                                                event['rejected'] = 'PATH_NOT_CONSUMED'
                                                event['accepted'] = False

                                            elif _v2_dense_clearance < _v564_required_clearance - 1e-6:

                                                print('V620_DENSE_GATE_REJECTED', {'minimum_clearance_m': float(_v2_dense_clearance), 'hard_floor_m': float(_v564_required_clearance)}, flush=True)
                                                snapshot.restore(shift)
                                                obs = _v2_obs_before.copy()

                                                if A.state_digest(env, shift) != state:
                                                    raise RuntimeError(
                                                        'V2_DENSE_CLEARANCE_RESTORE_MISMATCH'
                                                    )

                                                event['rejected'] = (
                                                    'LOW_DENSE_FULL_FOOTPRINT_CLEARANCE'
                                                )
                                                event['accepted'] = False

                                            else:
                                                accepted += 1
                                                env._v629_rpccr_path_lease = True
                                                print('V630_RPCCR_PATH_LEASE_ACQUIRED', {
                                                    'step': int(step),
                                                    'v8_blocked': int(env._v629_v8_replan_blocked)
                                                }, flush=True)
                                                event['accepted'] = True

                                                if _v2_applied is not None:
                                                    event['applied'] = _v2_applied
                                                else:
                                                    event['applied'] = {
                                                        'sync': _v2_sync,
                                                        'runtime_path_owner_count': _v2_owner_count,
                                                        'active_path_hash': _v2_active_after,
                                                        'consumer_dense_path_hash': _v2_dense_hash,
                                                        'consumer_dense_min_full_footprint_clearance_m':
                                                            _v2_dense_clearance,
                                                    }

                                else:
                                    event['accepted'] = False
                                    _v590_recovery_state = getattr(_v132_state, 'STATE', None)
                                    _v590_recovery_active = bool(
                                        branch == 'rpccr_online'
                                        and isinstance(_v590_recovery_state, dict)
                                        and _v590_recovery_state.get('mode') in ('BACK', 'HOLD')
                                        and stats.get('status') in ('start_occupied_no_teleport', 'search_exhausted')
                                    )
                                    if _v590_recovery_active:
                                        event['rejected'] = 'RECOVERY_ACTIVE_NO_FINAL_GOAL_PATH'
                                        event['recovery_deferred'] = True
                                        print('V590_RECOVERY_HANDOFF', {
                                            'step': int(step),
                                            'status': stats.get('status'),
                                            'mode': _v590_recovery_state.get('mode'),
                                            'clearance_m': stats.get('initial_clearance_m'),
                                            'next': 'EXECUTE_V132_RECOVERY_THEN_REPLAN',
                                        }, flush=True)
                                    else:
                                        event['rejected'] = 'NO_FINAL_GOAL_PATH'
                                        events.append(event)
                                        print('V571_FAIL_CLOSED_NO_SAFE_PATH', {'step': int(step), 'status': stats.get('status'), 'expanded': stats.get('expanded')}, flush=True)
                                        break
                                events.append(event)
                                if event.get('accepted') is True:
                                    _v21_last_accept_step = int(step)

                                    try:
                                        _v92_geom_model = getattr(env, 'model', None)
                                        if _v92_geom_model is None:
                                            _v92_geom_model = env.inner.model

                                        _v92_gid = mujoco.mj_name2id(
                                            _v92_geom_model,
                                            mujoco.mjtObj.mjOBJ_GEOM,
                                            'real_circle_obs_10'
                                        )

                                        _v92_obstacle = (
                                            np.asarray(
                                                _v92_geom_model.geom_pos[
                                                    _v92_gid, :2
                                                ],
                                                dtype=float
                                            ).tolist()
                                            if _v92_gid >= 0
                                            else None
                                        )

                                        _v92_candidate = np.asarray(
                                            path, dtype=float
                                        ).copy()

                                        _v92_consumer = np.asarray(
                                            env.inner.dense_path,
                                            dtype=float
                                        ).copy()

                                        _v92_snapshot = {
                                            'seed': int(SEED),
                                            'branch': branch,
                                            'step': int(step),
                                            'true_goal_xy':
                                                np.asarray(
                                                    env.goal_xy,
                                                    dtype=float
                                                ).tolist(),
                                            'robot_xy':
                                                np.asarray(
                                                    env.robot_xy,
                                                    dtype=float
                                                ).tolist(),
                                            'planner_world_goal':
                                                np.asarray(
                                                    world.get('goal', []),
                                                    dtype=float
                                                ).reshape(-1).tolist(),
                                            'planner_candidate_path':
                                                _v92_candidate.tolist(),
                                            'consumer_dense_path':
                                                _v92_consumer.tolist(),
                                            'obstacle_runtime_xy':
                                                _v92_obstacle,
                                            'obstacle_radius_m': (
                                                float(
                                                    _v92_geom_model.geom_size[
                                                        _v92_gid, 0
                                                    ]
                                                )
                                                if _v92_gid >= 0
                                                else None
                                            ),
                                            'path_applied_report':
                                                event.get('applied'),
                                            'consumer_path_hash':
                                                event.get(
                                                    'consumer_dense_path_hash'
                                                ),
                                            'accepted': True,
                                        }

                                        _v92_target = (
                                            out / branch /
                                            ('v92_handoff_step_'
                                             + str(int(step))
                                             + '.json')
                                        )

                                        _v92_target.write_text(
                                            json.dumps(
                                                _v92_snapshot,
                                                ensure_ascii=False,
                                                allow_nan=False
                                            ),
                                            encoding='utf-8'
                                        )

                                        print(
                                            'V92_HANDOFF_SNAPSHOT',
                                            json.dumps({
                                                'step': int(step),
                                                'candidate_points':
                                                    len(_v92_candidate),
                                                'consumer_points':
                                                    len(_v92_consumer),
                                                'true_goal_xy':
                                                    _v92_snapshot[
                                                        'true_goal_xy'
                                                    ],
                                                'obstacle_runtime_xy':
                                                    _v92_obstacle,
                                                'saved': str(_v92_target),
                                            }),
                                            flush=True
                                        )

                                    except Exception as _v92_error:
                                        print(
                                            'V92_HANDOFF_CAPTURE_ERROR',
                                            repr(_v92_error),
                                            flush=True
                                        )
                                    print('V21_PATH_ACCEPTED', json.dumps({'step':int(step),'attempts':int(attempts),'accepted_count':int(accepted)}),flush=True)
                                print('V2_PLAN',event,flush=True)
                except RuntimeError as _v335_error:
                    _v335_message = str(_v335_error)
                    if _v335_message in ('Final continuous samples fail map margin', 'Final continuous samples fail start-escape certificate'):
                        print(
                            'V335_CANDIDATE_REJECTED_SAFE_FALLBACK',
                            _v335_message,
                            flush=True,
                        )
                    else:
                        raise
                import phase_v345_runtime as _v345
                if step == 30:
                    _v18_path = getattr(env.inner, 'dense_path', None)
                    _v18_path = np.asarray(
                        _v18_path if _v18_path is not None else [],
                        dtype=float
                    ).copy()
                    _v345.activate(env,branch,step,obs,mujoco)
                    try:
                        _v18_model = getattr(env, 'model', None)
                        if _v18_model is None:
                            _v18_model = getattr(env.inner, 'model', None)
                        if _v18_model is None:
                            raise RuntimeError('MODEL_NOT_AVAILABLE')
                        _v18_gid = mujoco.mj_name2id(
                            _v18_model,
                            mujoco.mjtObj.mjOBJ_GEOM,
                            'real_circle_obs_10'
                        )
                        if _v18_gid < 0:
                            raise RuntimeError('EVENT_GEOM_MISSING')
                        _v18_xy = np.asarray(
                            _v18_model.geom_pos[_v18_gid, :2],
                            dtype=float
                        ).copy()
                        if _v18_path.ndim != 2 or len(_v18_path) < 2:
                            raise RuntimeError('PATH_NOT_AVAILABLE')
                        _v18_pts = _v18_path[:, :2]
                        _v18_a = _v18_pts[:-1]
                        _v18_b = _v18_pts[1:]
                        _v18_ab = _v18_b - _v18_a
                        _v18_t = np.clip(
                            np.sum((_v18_xy - _v18_a) * _v18_ab, axis=1)
                            / np.maximum(np.sum(_v18_ab ** 2, axis=1), 1e-12),
                            0.0, 1.0
                        )
                        _v18_q = _v18_a + _v18_t[:, None] * _v18_ab
                        _v18_d = float(
                            np.min(np.linalg.norm(_v18_q - _v18_xy, axis=1))
                        )
                        _v18_radius = float(
                            _v18_model.geom_size[_v18_gid, 0]
                        )
                        print('V18_ON_PATH_GATE', json.dumps({
                            'branch':branch,
                            'step':int(step),
                            'obstacle_xy':_v18_xy.tolist(),
                            'path_points':int(len(_v18_pts)),
                            'distance_m':_v18_d,
                            'radius_m':_v18_radius,
                            'centerline_blocked':bool(_v18_d <= _v18_radius),
                            'footprint_blocked':bool(
                                _v18_d <= _v18_radius + 0.28
                            )
                        }),flush=True)
                    except Exception as _v18_e:
                        print('V18_ON_PATH_GATE',json.dumps({
                            'branch':branch,
                            'error':repr(_v18_e)
                        }),flush=True)
                elif step >= 31:
                    _v345.audit(env,branch,step,obs,mujoco)
                action,_=model.predict(obs,deterministic=True)
                if branch == 'rpccr_online' and _v132_state.STATE is not None:
                    _v132_s = _v132_state.STATE
                
                    _v132_pos = np.asarray(
                        env.robot_xy,
                        dtype=float
                    ).reshape(-1)[:2]
                
                    _v132_forward_m = float(np.dot(
                        _v132_pos - _v132_s['initial_xy'],
                        _v132_s['heading']
                    ))
                
                    _v132_reverse_m = -_v132_forward_m
                    _v132_s['reverse_m'] = _v132_reverse_m
                
                    _v132_elapsed = (
                        int(step) - _v132_s['start_step']
                    )
                
                    if _v132_s['mode'] == 'BACK':
                
                        if _v132_reverse_m >= 0.40:
                            _v132_s['mode'] = 'HOLD'
                            _v132_s['hold_step'] = int(step)
                
                            print(
                                'V132_BACK_TARGET_REACHED',
                                json.dumps({
                                    'step': int(step),
                                    'reverse_m': _v132_reverse_m
                                }),
                                flush=True
                            )
                
                        elif (
                            _v132_elapsed >= 25
                            and _v132_reverse_m < 0.015
                        ):
                            print(
                                'V132_BACK_BLOCKED=NO_REVERSE_RESPONSE',
                                flush=True
                            )
                            break
                
                        elif (
                            _v132_elapsed >= 15
                            and _v132_forward_m > 0.08
                        ):
                            print(
                                'V132_BACK_BLOCKED=WRONG_DIRECTION',
                                flush=True
                            )
                            break
                
                        elif _v132_elapsed >= 115:
                            print(
                                'V132_BACK_BLOCKED=TIME_BUDGET',
                                'ACTUAL_REVERSE_M=',
                                _v132_reverse_m,
                                flush=True
                            )
                            break
                
                    if (
                        _v132_s['mode'] == 'HOLD'
                        and _v132_s['hold_step'] is not None
                        and int(step) - _v132_s['hold_step'] >= 8
                    ):
                        print(
                            'V132_POSITION_RECOVERY_READY',
                            json.dumps({
                                'step': int(step),
                                'reverse_m': _v132_reverse_m,
                                'next': 'REPLAN_FROM_UPDATED_POSE',
                                'full_navigation_completed': False
                            }),
                            flush=True
                        )
                        _v132_s['mode'] = 'NORMAL'
                        _v132_state.STATE = None
                        setattr(_v132_state, 'RECOVERY_COMPLETED', True)
                        print('V497_RECOVERY_COMPLETED_LATCH=TRUE', flush=True)
                        print('V495_RESUME_ACCEPTED_PATH=TRUE', flush=True)
                
                    if _v132_s['mode'] == 'BLOCKED':
                        print(
                            'V132_BACK_BLOCKED=REAR_CORRIDOR',
                            flush=True
                        )
                        break
                
                    if _v132_s['mode'] == 'BACK':
                        action = np.array(
                            [0.0, -1.0],
                            dtype=np.float32
                        )
                
                    elif _v132_s['mode'] == 'HOLD':
                        action = np.array(
                            [0.0, 0.0],
                            dtype=np.float32
                        )
                
                    if int(step) % 10 == 0:
                        print(
                            'V132_MOTION',
                            json.dumps({
                                'step': int(step),
                                'mode': _v132_s['mode'],
                                'reverse_m': round(
                                    _v132_reverse_m, 5
                                ),
                                'xy': _v132_pos.tolist()
                            }),
                            flush=True
                        )
                _v103_original = None
                _v103_capture = {'calls': 0}

                if (
                    branch == 'rpccr_online'
                    and step >= 31
                    and accepted > 0
                ):
                    import types as _v103_types

                    if '_base_action' in vars(env):
                        raise RuntimeError('V103_EXISTING_BASE_OVERRIDE')

                    _v103_original = env._base_action

                    _v103_ctrl_before = np.asarray(
                        env.data.ctrl[:4], dtype=float
                    ).copy()

                    def _v103_hook(self, raw_obs):
                        _old = np.asarray(
                            _v103_original(raw_obs),
                            dtype=np.float32
                        ).copy()

                        if _old.shape != (2,):
                            raise RuntimeError('V103_BASE_ACTION_SHAPE')

                        # 只读取已经接管的实际消费路径。
                        _v625_path_source = env.inner.dense_path
                        _v625_path_object_id = id(_v625_path_source)
                        _path = np.asarray(
                            _v625_path_source,
                            dtype=float
                        )

                        if (
                            _path.ndim != 2
                            or _path.shape[1] < 2
                            or len(_path) < 3
                            or not np.isfinite(_path).all()
                        ):
                            raise RuntimeError('V103_CONSUMER_PATH_INVALID')

                        _path = _path[:, :2]
                        _v625_path_sha256 = __import__('hashlib').sha256(
                            np.ascontiguousarray(_path).tobytes()
                        ).hexdigest()

                        _xy = np.asarray(
                            env.robot_xy, dtype=float
                        ).reshape(-1)[:2]

                        # 读取真实车体航向。
                        _bid = mujoco.mj_name2id(
                            env.model,
                            mujoco.mjtObj.mjOBJ_BODY,
                            'mkmini_base'
                        )

                        if _bid < 0:
                            raise RuntimeError('V103_ROBOT_BODY_MISSING')

                        _R = np.asarray(
                            env.data.xmat[_bid], dtype=float
                        ).reshape(3, 3)

                        _yaw = float(
                            np.arctan2(_R[1, 0], _R[0, 0])
                        )

                        # 计算当前位置到参考路径的最近投影。
                        _a = _path[:-1]
                        _vec = np.diff(_path, axis=0)

                        _len = np.linalg.norm(
                            _vec, axis=1
                        )

                        _len2 = _len * _len

                        _t = np.divide(
                            np.sum(
                                (_xy[None, :] - _a) * _vec,
                                axis=1
                            ),
                            _len2,
                            out=np.zeros(len(_len2)),
                            where=_len2 > 1e-12
                        )

                        _t = np.clip(_t, 0.0, 1.0)

                        _projection = (
                            _a + _t[:, None] * _vec
                        )

                        _distance = np.linalg.norm(
                            _projection - _xy[None, :],
                            axis=1
                        )

                        _v629_path_hash = hashlib.sha256(
                            np.ascontiguousarray(_path).tobytes()
                        ).hexdigest()
                        _v629_previous_hash = getattr(
                            env, '_v629_tracker_path_hash', None
                        )
                        _v629_previous_index = getattr(
                            env, '_v629_tracker_nearest', None
                        )
                        _v629_tracking_lost = False
                        if _v629_previous_hash != _v629_path_hash:
                            _nearest = int(np.argmin(_distance))
                            _v629_error = float(_distance[_nearest])
                            print('V630_TRACKER_PATH_CHANGE', {
                                'step': int(step),
                                'nearest_error_m': _v629_error,
                                'accepted': bool(_v629_error <= 0.20)
                            }, flush=True)
                            if _v629_error > 0.20:
                                _v629_tracking_lost = True
                        else:
                            if _v629_previous_index is None:
                                _nearest = int(np.argmin(_distance))
                            else:
                                _v629_lo = max(0, int(_v629_previous_index) - 20)
                                _v629_hi = min(len(_distance), int(_v629_previous_index) + 81)
                                _nearest = _v629_lo + int(np.argmin(
                                    _distance[_v629_lo:_v629_hi]
                                ))
                            _v629_error = float(_distance[_nearest])
                            if _v629_error > 0.30:
                                _v629_tracking_lost = True
                                print('V630_TRACKER_LOCAL_LOSS', {
                                    'step': int(step),
                                    'error_m': _v629_error,
                                    'nearest': int(_nearest)
                                }, flush=True)
                        env._v629_tracker_path_hash = _v629_path_hash
                        env._v629_tracker_nearest = int(_nearest)

                        _path_error = float(
                            _distance[_nearest]
                        )

                        _cum = np.concatenate((
                            [0.0],
                            np.cumsum(_len)
                        ))

                        _progress = (
                            _cum[_nearest]
                            + _t[_nearest] * _len[_nearest]
                        )
                        _v625_progress_m = float(_progress)

                        # 前视0.70m，沿真实路径弧长取点。
                        _target_s = min(
                            _progress + 0.70,
                            float(_cum[-1])
                        )

                        _j = int(
                            np.searchsorted(
                                _cum,
                                _target_s,
                                side='right'
                            ) - 1
                        )

                        _j = int(np.clip(
                            _j,
                            0,
                            len(_len) - 1
                        ))

                        _ratio = float(np.clip(
                            (_target_s - _cum[_j])
                            / max(float(_len[_j]), 1e-9),
                            0.0,
                            1.0
                        ))

                        _target = (
                            _path[_j]
                            + _ratio * _vec[_j]
                        )
                        _v625_target_segment = int(_j)
                        _v625_target_s_m = float(_target_s)

                        _desired_yaw = float(np.arctan2(
                            _target[1] - _xy[1],
                            _target[0] - _xy[0]
                        ))

                        _error = float(np.arctan2(
                            np.sin(_desired_yaw - _yaw),
                            np.cos(_desired_yaw - _yaw)
                        ))

                        print(
                            'V625_TRACKING_SAMPLE',
                            json.dumps({
                                'step': int(step),
                                'path_sha256': _v625_path_sha256[:20],
                                'path_object_id': int(_v625_path_object_id),
                                'nearest_segment': int(_nearest),
                                'target_segment': int(_j),
                                'progress_m': float(_progress),
                                'target_s_m': float(_target_s),
                                'nearest_segment_length_m': float(_len[_nearest]),
                                'target_segment_length_m': float(_len[_j]),
                                'target_xy': _target.tolist(),
                                'robot_xy': _xy.tolist(),
                                'path_error_m': float(_path_error),
                                'heading_error_rad': float(_error),
                            }, allow_nan=False),
                            flush=True
                        )

                        # 基础转向层具有V99验证过的控制权。
                        # 保留执行器的原有限幅与斜率限制。
                        _new = _old.copy()

                        _v106_vec = _vec[_nearest]
                        _v106_norm = max(float(_len[_nearest]), 1e-9)
                        _v106_offset = _xy - _projection[_nearest]
                        _v106_signed_cte = float(
                            (_v106_vec[0] * _v106_offset[1]
                             - _v106_vec[1] * _v106_offset[0])
                            / _v106_norm
                        )
                        _v106_signed_cte = float(np.clip(
                            _v106_signed_cte, -0.25, 0.25
                        ))
                        _v106_correction = float(np.arctan(
                            (1.5 * _v106_signed_cte + 5.0 * np.sign(_v106_signed_cte) * max(0.0, abs(_v106_signed_cte) - 0.08))
                        ))
                        _desired_steer = float(np.clip(
                            1.8 * (_error - _v106_correction),
                            -0.70,
                            0.70
                        ))
                        _previous_steer = float(
                            _v103_capture.get('last_steer', _desired_steer)
                        )
                        _new[0] = float(np.clip(
                            _previous_steer + float(np.clip(
                                _desired_steer - _previous_steer,
                                -0.18,
                                0.18
                            )),
                            -0.70,
                            0.70
                        ))
                        _v103_capture['last_steer'] = _new[0]

                        # 航向偏差较大时，降低基础前进命令。
                        # 不直接改动data.ctrl，也不绕过安全层。
                        _speed_cap = (
                            0.10
                            if abs(_error) >= 0.25 or abs(_desired_steer) >= 0.40
                            else 0.24
                        )

                        _new[1] = float(
                            min(
                                float(_old[1]),
                                _speed_cap
                            )
                        )

                        _v103_capture['calls'] += 1

                        _v103_capture['record'] = {
                            'step': int(step),
                            'robot_xy': _xy.tolist(),
                            'robot_yaw': _yaw,
                            'reference_xy': _target.tolist(),
                            'path_error_m': _path_error,
                            'heading_error_rad': _error,
                            'v106_signed_cte_m': _v106_signed_cte,
                            'v106_lateral_correction_rad': _v106_correction,
                            'base_before': _old.tolist(),
                            'base_after': _new.tolist(),
                            'path_points': int(len(_path)),
                            'speed_cap': _speed_cap,
                            'v625_path_sha256': _v625_path_sha256,
                            'v625_path_object_id': int(_v625_path_object_id),
                            'v625_nearest_segment': int(_nearest),
                            'v625_target_segment': int(_j),
                            'v625_progress_m': float(_progress),
                            'v625_target_s_m': float(_target_s),
                            'v625_projection_xy': _projection[_nearest].tolist(),
                            'v625_nearest_segment_length_m': float(_len[_nearest]),
                            'v625_target_segment_length_m': float(_len[_j]),
                        }

                        if branch == 'rpccr_online' and _v132_state.STATE is not None:
                            _v132_mode = _v132_state.STATE['mode']
                        
                            if _v132_mode == 'BACK':
                                _new[0] = 0.0
                                _new[1] = -1.0
                        
                            elif _v132_mode == 'HOLD':
                                _new[0] = 0.0
                                _new[1] = 0.0
                        _v501_ctx = __import__('sys').modules.get('v501_follow_context')
                        if _v501_ctx is not None and getattr(_v132_state, 'RECOVERY_COMPLETED', False):
                            _v501_ctx.path = np.asarray(_path, dtype=float)[:, :2].copy()
                            _v501_ctx.cte = float(_path_error)
                            _v501_ctx.step = int(step)
                        if _v629_tracking_lost:
                            _new[0] = 0.0
                            _new[1] = 0.0
                            print('V630_TRACKER_FAIL_CLOSED', {
                                'step': int(step),
                                'path_error_m': float(_path_error),
                                'nearest_segment': int(_nearest)
                            }, flush=True)
                        return _new

                    env._base_action = _v103_types.MethodType(
                        _v103_hook, env
                    )

                _v104_original_pursuit = None
                _v104_capture = {'calls': 0}

                if (
                    branch == 'rpccr_online'
                    and step >= 31
                    and accepted > 0
                ):
                    import types as _v104_types

                    if '_base_pursuit_action' in vars(env.inner):
                        raise RuntimeError(
                            'V104_EXISTING_PURSUIT_OVERRIDE'
                        )

                    _v104_original_pursuit = (
                        env.inner._base_pursuit_action
                    )

                    def _v104_pursuit_hook(self):
                        result = _v104_original_pursuit()

                        if len(result) != 5:
                            raise RuntimeError(
                                'V104_PURSUIT_RETURN_INVALID'
                            )

                        result = list(result)

                        old_speed = float(result[1])

                        # 仅正常导航时介入。
                        # 恢复状态不修改其原有行为。
                        recovery = str(
                            getattr(self, 'recovery_stage', 'NORMAL')
                        )

                        if recovery == 'NORMAL':
                            new_speed = old_speed
                        else:
                            new_speed = old_speed

                        result[1] = float(new_speed)

                        _v104_capture['calls'] += 1
                        _v104_capture['old_speed'] = old_speed
                        _v104_capture['new_speed'] = new_speed
                        _v104_capture['recovery_stage'] = recovery

                        return tuple(result)

                    env.inner._base_pursuit_action = (
                        _v104_types.MethodType(
                            _v104_pursuit_hook,
                            env.inner
                        )
                    )

                def _v625_snapshot_path():
                    _raw = getattr(env.inner, 'dense_path', None)

                    if _raw is None:
                        return {
                            'object_id': None,
                            'shape': None,
                            'sha256': None
                        }

                    try:
                        _arr = np.asarray(_raw, dtype=float)
                        _digest = __import__('hashlib').sha256(
                            np.ascontiguousarray(_arr).tobytes()
                        ).hexdigest()

                        return {
                            'object_id': int(id(_raw)),
                            'shape': list(_arr.shape),
                            'sha256': _digest
                        }
                    except Exception as _e:
                        return {
                            'object_id': int(id(_raw)),
                            'shape': None,
                            'sha256': None,
                            'error': repr(_e)
                        }

                _v625_before = _v625_snapshot_path()

                try:
                    obs,_,term,trunc,info=B.finish_api(
                        env.step(action)
                    )
                finally:
                    if _v104_original_pursuit is not None:
                        delattr(env.inner, '_base_pursuit_action')

                    if _v103_original is not None:
                        delattr(env, '_base_action')

                _v648_audit.after_public(env,step)
                _v625_after = _v625_snapshot_path()

                if branch == 'rpccr_online':

                    try:
                        _v625_previous = _v625_last_post_rpccr
                    except NameError:
                        _v625_previous = None

                    if (
                        _v625_previous is not None
                        and _v625_previous.get('sha256')
                        != _v625_before.get('sha256')
                    ):
                        print(
                            'V625_PATH_CHANGED_BETWEEN_STEPS',
                            json.dumps({
                                'step': int(step),
                                'previous': _v625_previous,
                                'current': _v625_before
                            }),
                            flush=True
                        )

                    if (
                        _v625_before.get('sha256')
                        != _v625_after.get('sha256')
                    ):
                        print(
                            'V625_PATH_CHANGED_DURING_STEP',
                            json.dumps({
                                'step': int(step),
                                'before': _v625_before,
                                'after': _v625_after
                            }),
                            flush=True
                        )

                    if (
                        _v625_before.get('object_id')
                        != _v625_after.get('object_id')
                        and _v625_before.get('sha256')
                        == _v625_after.get('sha256')
                    ):
                        print(
                            'V625_PATH_OBJECT_REPLACED_SAME_CONTENT',
                            int(step),
                            flush=True
                        )

                    _v625_last_post_rpccr = _v625_after

                if _v104_original_pursuit is not None:

                    if _v104_capture['calls'] < 1:
                        raise RuntimeError(
                            'V104_SPEED_HOOK_NOT_REACHED'
                        )

                    _v104_info = (
                        info if isinstance(info, dict) else {}
                    )

                    _v104_final_wheel = (
                        _v104_info.get('final_wheel_norm')
                    )

                    _v104_row = {
                        'step': int(step),
                        'hook_calls': int(
                            _v104_capture['calls']
                        ),
                        'base_wheel_norm_before': (
                            _v104_capture['old_speed']
                        ),
                        'base_wheel_norm_after': (
                            _v104_capture['new_speed']
                        ),
                        'recovery_stage': (
                            _v104_capture['recovery_stage']
                        ),
                        'phase5_final_wheel_norm': (
                            float(_v104_final_wheel)
                            if _v104_final_wheel is not None
                            else None
                        ),
                        'rear_ctrl': np.asarray(
                            env.data.ctrl[2:4],
                            dtype=float
                        ).tolist(),
                        'robot_xy': np.asarray(
                            env.robot_xy,
                            dtype=float
                        ).reshape(-1)[:2].tolist(),
                    }

                    with (
                        out / branch / 'v104_speed.jsonl'
                    ).open('a', encoding='utf-8') as _v104_f:
                        _v104_f.write(
                            json.dumps(
                                _v104_row,
                                allow_nan=False
                            ) + '\n'
                        )

                    if step <= 55 or step % 10 == 0:
                        print(
                            'V104_SPEED_EFFECT',
                            json.dumps(
                                _v104_row,
                                allow_nan=False
                            ),
                            flush=True
                        )

                if _v103_original is not None:
                    if _v103_capture['calls'] < 1:
                        raise RuntimeError(
                            'V103_BASE_HOOK_NOT_EXECUTED'
                        )

                    _v103_record = dict(
                        _v103_capture['record']
                    )

                    _v103_record['hook_calls'] = int(
                        _v103_capture['calls']
                    )

                    _v103_record['ctrl_before'] = (
                        _v103_ctrl_before.tolist()
                    )

                    _v103_record['ctrl_after'] = (
                        np.asarray(
                            env.data.ctrl[:4],
                            dtype=float
                        ).tolist()
                    )

                    _v103_record['robot_xy_after'] = (
                        np.asarray(
                            env.robot_xy,
                            dtype=float
                        ).reshape(-1)[:2].tolist()
                    )

                    _v103_info = (
                        info if isinstance(info, dict) else {}
                    )

                    _v103_final = _v103_info.get(
                        'final_action',
                        getattr(
                            env,
                            'last_final_action',
                            None
                        )
                    )

                    _v103_record['final_action'] = (
                        np.asarray(
                            _v103_final,
                            dtype=float
                        ).tolist()
                        if _v103_final is not None
                        else None
                    )

                    _v103_record['shield_active'] = str(
                        _v103_info.get(
                            'phase17_shield_active',
                            'UNKNOWN'
                        )
                    )

                    with (
                        out / branch / 'v103_tracking.jsonl'
                    ).open('a', encoding='utf-8') as _f:
                        _f.write(
                            json.dumps(
                                _v103_record,
                                allow_nan=False
                            ) + '\n'
                        )

                    if (
                        step <= 55
                        or step % 15 == 0
                    ):
                        print(
                            'V103_TRACK',
                            json.dumps(
                                _v103_record,
                                allow_nan=False
                            ),
                            flush=True
                        )

                if branch == 'rpccr_online' and 30 <= step <= 130:
                    try:
                        _v92_record = {
                            'step': int(step),
                            'robot_xy': np.asarray(
                                env.robot_xy, dtype=float
                            ).tolist(),
                            'true_goal_xy': np.asarray(
                                env.goal_xy, dtype=float
                            ).tolist(),
                            'action': np.asarray(
                                action, dtype=float
                            ).tolist(),
                            'consumer_path_points': int(
                                len(env.inner.dense_path)
                            ),
                            'terminated': bool(term),
                            'truncated': bool(trunc),
                        }

                        with (
                            out / branch /
                            'v92_execution.jsonl'
                        ).open('a', encoding='utf-8') as _v92_f:
                            _v92_f.write(
                                json.dumps(
                                    _v92_record,
                                    ensure_ascii=False,
                                    allow_nan=False
                                ) + '\n'
                            )

                    except Exception as _v92_error:
                        print(
                            'V92_EXECUTION_CAPTURE_ERROR',
                            repr(_v92_error),
                            flush=True
                        )
                if branch == 'rpccr_online' and (int(step) % 5 == 0 or int(step) == 31):
                    import v115_live_view as _v132_gui
                    _v132_gui.tick(env, branch, step, mujoco)
                audit=G.label_step(env,info)
                hit=bool(audit['primary_collision'])
                success=bool(info.get('reach_goal',False) or info.get('success',False) or info.get('is_success',False))
                arrived|=success
                native_collision|=hit
                terminated|=bool(term)
                truncated|=bool(trunc)
                rows.append({'step':step,'xy':np.asarray(env.robot_xy).tolist(),
                             'action':np.asarray(action).tolist(),
                             'success':success,'collision':hit,
                             'recovery_stage':str(env.inner.recovery_stage),
                             'known_penetration':bool(audit['environment_flags']['phase20_known_penetration']),
                             'unknown_penetration':bool(audit['environment_flags']['phase20_unknown_penetration'])})
                if (step+1)%100==0:print('V2_PROGRESS',branch,step+1,flush=True)
                if term or trunc or hit or recorder.first_anomaly is not None:
                    print(
                        'V66_TERMINATION',
                        json.dumps({
                            'branch': branch,
                            'step': int(step),
                            'terminated': bool(term),
                            'truncated': bool(trunc),
                            'hit': bool(hit),
                            'recorder_anomaly':
                                recorder.first_anomaly is not None,
                            'goal_distance_m': float(
                                np.linalg.norm(
                                    np.asarray(env.robot_xy)
                                    - np.asarray(env.goal_xy)
                                )
                            ),
                            'goal_threshold_m': float(
                                env.inner.goal_threshold
                            ),
                        }),
                        flush=True
                    )
                    break
            mujoco.mj_step=original_mj
            contacts=recorder.summary()
            distance=float(np.linalg.norm(np.asarray(env.robot_xy)-np.asarray(env.goal_xy)))
            tol=float(env.inner.goal_threshold)
            strict=bool(arrived and distance<=tol and not native_collision and
                contacts['robot_obstacle_contact_records']==0 and
                contacts['robot_obstacle_penetration_records']==0 and
                contacts['unknown_contact_records']==0)
            with gzip.open(cell/'public_trace.json.gz','xt') as f:json.dump(rows,f)
            save(cell/'planning_events.json',events)
            record={'branch':branch,'seed':SEED,'scope':'FULL_FROM_RESET_DEVELOPMENT',
                    'steps':len(rows),'physics_steps':physics_count,'observer_checks':observer_checks,
                    'strict_safe_arrival':strict,'native_goal':arrived,
                    'goal_distance_m':distance,'native_collision':native_collision,
                    'terminated':terminated,'truncated':truncated,
                    'censored':len(rows)==LIMIT and not (terminated or truncated or native_collision),
                    'planning_attempts':attempts,'gate_unavailable_events':unavailable_gates,
                    'actual_planner_calls':attempts-unavailable_gates,'new_paths':accepted,
                    'planning_wall_s':planning_time,'contacts':contacts,
                    'elapsed_s':time.monotonic()-started}
            save(cell/'result.json',record)
            results.append(record)
            print('V2_BRANCH_DONE',branch,'strict=',strict,'steps=',len(rows),
                  'contacts=',contacts['robot_obstacle_contact_records'],
                  'attempts=',attempts,'new_paths=',accepted,flush=True)
        finally:
            import phase_v345_runtime as _v345
            if env is not None:
                _v345.restore(env,branch,mujoco)
            mujoco.mj_step=original_mj
            if recorder is not None:recorder.close()
            if branch=='rpccr_online':
                try:
                    import v115_live_view as _v132_gui
                    _v132_gui.close()
                finally:
                    env.close()
    if len(results)!=2:raise RuntimeError('INCOMPLETE_PAIR')
    for p,digest in frozen.items():
        if sha(p)!=digest:raise RuntimeError('FROZEN_FILE_CHANGED:'+p)
    if sha(B.MODEL)!=EXPECTED:raise RuntimeError('SAC_CHANGED')
    a,b=results
    category=('RESCUE' if b['strict_safe_arrival'] and not a['strict_safe_arrival'] else
              'HARM' if a['strict_safe_arrival'] and not b['strict_safe_arrival'] else
              'BOTH_SAFE' if a['strict_safe_arrival'] else 'BOTH_FAIL')
    report={'gate':'V3_RISK_PROGRESS_PAIRED_DEVELOPMENT_PILOT','seed':SEED,'category':category,
            'baseline_strict':a['strict_safe_arrival'],'rpccr_strict':b['strict_safe_arrival'],
            'rpccr_planning_attempts':b['planning_attempts'],'rpccr_new_paths':b['new_paths'],
            'rpccr_gate_unavailable_events':b['gate_unavailable_events'],
            'model_sha256':EXPECTED,'independent_test_seeds_used':0,
            'full_task_start':'FIRST_ENV_RESET_SNAPSHOT_RESTORED_FOR_PAIR',
            'no_statistical_superiority_claim':True}
    save(out/'V2_SUMMARY.json',report)
    print('B85_REPORT',json.dumps(report,ensure_ascii=False),flush=True)
    print('V2_OUTPUT',out,flush=True)

if __name__=='__main__':
    import fcntl,subprocess,signal
    try:
        if Path.cwd().resolve()!=ROOT.resolve():raise RuntimeError('WRONG_CWD')
        ps=subprocess.run(['ps','-eo','pid=,args='],capture_output=True,text=True,timeout=5,check=True)
        active=[line for line in ps.stdout.splitlines() if 'phase_rpccr_' in line and '_worker.py' in line]
        if active:raise RuntimeError('OTHER_PHASE_WORKER_RUNNING:'+repr(active[:2]))
        HERE.mkdir(parents=True,exist_ok=True)
        with (HERE/'single_instance.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            existing=[p for p in (HERE/'runs').glob('pilot_seed_'+str(SEED)+'_*') if (p/'BATCH_LEDGER_COMPLETE').is_file()] if (HERE/'runs').is_dir() else []
            if existing:raise RuntimeError('PILOT_ALREADY_EXISTS_REFUSE_DUPLICATE:'+str(existing[-1]))
            def overtime(*_):raise TimeoutError('B83_1500S_TIME_BUDGET')
            signal.signal(signal.SIGALRM,overtime)
            signal.setitimer(signal.ITIMER_REAL,1500)
            main()
    except Exception as exc:
        print('B83_GATE=BLOCKED',type(exc).__name__,str(exc),flush=True)
        traceback.print_exc(limit=5)
        print('INTERACTIVE_TERMINAL_REMAINS_OPEN=TRUE',flush=True)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
