#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import importlib
import inspect
import json
import math
import os
import subprocess
import sys
import time
import traceback
from collections import Counter
from typing import Any

import numpy as np

HOLDOUT_MOD = (
    'training.phase21_risk_switch_fusion_sac.tests.'
    'phase_final_holdout_300_v1_1_resume_safe'
)
FUSION_MOD = (
    'training.phase17_fusion_safety_sac_nav.envs.'
    'mkmini_phase17c_lidar_camera_fusion_env'
)

METHOD_SPECS = {
    'sccr_full': (
        'envs.phase22.mkmini_phase22_v1_continuous_corridor_env',
        'MkMiniPhase22V1ContinuousCorridorEnv',
        'SCCR-Full',
    ),
    'sccr_b162': (
        'envs.g11b.mkmini_g11b_budget162_env',
        'MkMiniG11BBudget162SCCREnv',
        'SCCR-B162',
    ),
    'ra175_full': (
        'envs.g9a.mkmini_g9a_risk_margin_env',
        'MkMiniG9ARisk175Env',
        'RA175-Full',
    ),
    'ra175_b162': (
        'envs.g11b.mkmini_g11b_budget162_env',
        'MkMiniG11BBudget162RA175Env',
        'RA175-B162',
    ),
}
METHODS = tuple(METHOD_SPECS)

FORMAL_SEEDS = list(range(106200, 106400))
SMOKE_SEED = 906200
PLANNED_CELLS = len(FORMAL_SEEDS) * len(METHODS)
HARD_TIMEOUT_S = 120.0

BUDGET = 162
RA_MARGIN = 0.175
SAFE_NONINFERIORITY_MARGIN = -0.05
COLLISION_NONINFERIORITY_MARGIN = 0.05
ALPHA = 0.05

LIDAR_SIGMA_M = 0.02
LIDAR_CLIP_M = 0.06
LIDAR_DROPOUT = 0.05
DEPTH_SIGMA_M = 0.03
DEPTH_CLIP_M = 0.09
DEPTH_DROPOUT = 0.05

EXPECTED_MODEL_SHA = (
    '4072c19e02ba5c7c6b218a268c4ff1d987d2352eada01a3de918854d7173fc9f'
)
EXPECTED_PLANNER_SHA = (
    'd1cdb55220fbf3575401f8a067973fef5b1d0621fa7cc24125e7f60f027ab13a'
)
EXPECTED_PHASE22_SHA = (
    '3f274ed77aa37e52546c915ef6d0e417d99d4b6540c357e12965ed3a4b8094c6'
)
EXPECTED_G9A_ENV_SHA = (
    '756031e362bad102ca23807fa79bb07ec1a1af0eec63bc5c30f8a907f73cc64c'
)

EXPECTED_G11A_FREEZE_SHA = (
    '146a5b39e42b832a63ef646bfe9da121b3e21acc6f463dc2e07aba917bf2f017'
)
EXPECTED_G11B_ENV_SHA = (
    'eee1b5b3bd560394f998b7a52b36698a47dae812147451b3e86ef8aad8c113c1'
)
RUNNER_REVISION = 'V1_3_RESUME_VALIDATION_CONTRACT_FIX'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def atomic_json(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=True),
        encoding='utf-8',
    )
    tmp.replace(path)


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def boolish(x):
    return isinstance(x, (bool, np.bool_))


def classify(row: dict) -> str:
    if bool(row.get('safe_success', False)):
        return 'SAFE'
    if bool(row.get('collision', False)):
        return 'COLLISION'
    if bool(row.get('wall_timeout', False)):
        return 'WALL_TIMEOUT'
    if bool(row.get('env_timeout', False)):
        return 'ENV_TIMEOUT'
    return 'OTHER'


def valid_row(row: Any, seed: int, method: str) -> bool:
    if not isinstance(row, dict):
        return False

    if int(row.get('seed', -1)) != int(seed):
        return False

    if str(row.get('method', '')) != method:
        return False

    for k in ('safe_success', 'collision', 'env_timeout'):
        if k not in row or not boolish(row[k]):
            return False

    if 'wall_timeout' in row and not boolish(row['wall_timeout']):
        return False

    terminal_n = (
        int(bool(row['safe_success']))
        + int(bool(row['collision']))
        + int(bool(row['env_timeout']))
        + int(bool(row.get('wall_timeout', False)))
    )

    if terminal_n > 1:
        return False

    # --------------------------------------------------------------
    # G11B post-processing contract.
    # Prevent partially written worker results from being skipped
    # during resume.
    # --------------------------------------------------------------
    if row.get('g11b_condition') != 'shift':
        return False

    expected_label = METHOD_SPECS[method][2]
    if row.get('g11b_method_label') != expected_label:
        return False

    if 'g11b_selected_budget' not in row:
        return False

    expected_budget = BUDGET if method.endswith('b162') else None
    if row.get('g11b_selected_budget') != expected_budget:
        return False

    if 'g11b_ra_margin_m' not in row:
        return False

    expected_margin = RA_MARGIN if method.startswith('ra175') else None
    observed_margin = row.get('g11b_ra_margin_m')

    if expected_margin is None:
        if observed_margin is not None:
            return False
    else:
        try:
            if abs(float(observed_margin) - float(expected_margin)) > 1e-12:
                return False
        except Exception:
            return False

    # --------------------------------------------------------------
    # Budgeted methods:
    # normal completed cells require complete telemetry.
    #
    # Hard wall-timeout rows may legitimately have no final sidecar
    # if the worker was killed before a search writer flushed.
    # They must carry an explicit infrastructure status instead.
    # --------------------------------------------------------------
    if method.endswith('b162'):
        telemetry = row.get('g11b_budget_telemetry')

        if bool(row.get('wall_timeout', False)) and telemetry is None:
            return (
                row.get('g11b_budget_telemetry_status')
                == 'UNAVAILABLE_HARD_WALL_TIMEOUT'
            )

        if not isinstance(telemetry, dict):
            return False

        required_telemetry = (
            'candidate_budget',
            'search_call_count',
            'candidate_count_total',
            'candidate_count_max',
            'search_time_total_seconds',
            'search_time_max_seconds',
            'budget_overflow_count',
        )

        if any(k not in telemetry for k in required_telemetry):
            return False

        try:
            if int(telemetry['candidate_budget']) != int(BUDGET):
                return False

            checks = (
                ('g11b_budget_overflow_count', 'budget_overflow_count', int),
                ('g11b_search_candidate_count_max', 'candidate_count_max', int),
                ('g11b_search_call_count', 'search_call_count', int),
                (
                    'g11b_search_time_total_seconds',
                    'search_time_total_seconds',
                    float,
                ),
                (
                    'g11b_search_time_max_seconds',
                    'search_time_max_seconds',
                    float,
                ),
            )

            for row_key, tel_key, cast in checks:
                if row_key not in row:
                    return False

                a = cast(row[row_key])
                b = cast(telemetry[tel_key])

                if cast is float:
                    if abs(a - b) > 1e-9:
                        return False
                elif a != b:
                    return False

        except Exception:
            return False

    return True


def stable_seed(seed: int, call_idx: int, tag: str, shape) -> int:
    raw = f'{seed}|{call_idx}|{tag}|{tuple(shape)}'.encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], 'little') & 0x7FFFFFFF


def arrhash(x) -> str:
    return hashlib.sha256(np.asarray(x).tobytes()).hexdigest()


def install_shift_patch(seed: int):
    fm = importlib.import_module(FUSION_MOD)
    orig_lidar = fm.get_lidar_features

    fusion_class = None
    for _, obj in inspect.getmembers(fm, inspect.isclass):
        if obj.__module__ == fm.__name__ and hasattr(obj, '_phase17c_get_depth'):
            fusion_class = obj
            break
    if fusion_class is None:
        raise RuntimeError('PHASE17C_FUSION_CLASS_NOT_FOUND')
    orig_depth = fusion_class._phase17c_get_depth

    state = {
        'lidar_call': 0, 'depth_call': 0,
        'lidar_changed': 0, 'depth_changed': 0,
        'lidar_drop': 0, 'depth_drop': 0,
    }

    def infer_max_range(fn, args, kwargs, default):
        try:
            bound = inspect.signature(fn).bind_partial(*args, **kwargs)
            for k in ('max_range', 'lidar_max_range', 'range_max'):
                if k in bound.arguments:
                    return float(bound.arguments[k])
        except Exception:
            pass
        return float(default)

    def corrupt(out, max_range, sigma, clip, dropout, tag, idx):
        out = np.asarray(out, dtype=np.float32)
        rng = np.random.default_rng(stable_seed(seed, idx, tag, out.shape))
        noise = np.clip(
            rng.normal(0.0, sigma, size=out.shape), -clip, clip
        ).astype(np.float32)
        mask = rng.random(out.shape) < dropout
        meters = np.clip(out, 0.0, 1.0) * max_range
        shifted = np.clip(meters + noise, 0.0, max_range)
        shifted[mask] = max_range
        norm = (shifted / max_range).astype(np.float32)
        if arrhash(norm) != arrhash(out):
            state[tag + '_changed'] += 1
        state[tag + '_drop'] += int(mask.sum())
        return norm

    def lidar(*args, **kwargs):
        out = np.asarray(orig_lidar(*args, **kwargs), dtype=np.float32)
        idx = state['lidar_call']
        state['lidar_call'] += 1
        mr = infer_max_range(orig_lidar, args, kwargs, 3.0)
        return corrupt(
            out, mr, LIDAR_SIGMA_M, LIDAR_CLIP_M,
            LIDAR_DROPOUT, 'lidar', idx
        )

    def depth(self, *args, **kwargs):
        out = np.asarray(orig_depth(self, *args, **kwargs), dtype=np.float32)
        idx = state['depth_call']
        state['depth_call'] += 1
        mr = float(getattr(self, 'phase17c_depth_max_range', 3.0))
        if mr <= 0:
            mr = 3.0
        return corrupt(
            out, mr, DEPTH_SIGMA_M, DEPTH_CLIP_M,
            DEPTH_DROPOUT, 'depth', idx
        )

    fm.get_lidar_features = lidar
    fusion_class._phase17c_get_depth = depth
    return state


def verify_frozen_inputs(project: Path):
    paths = {
        'model': project / (
            'training/phase20_unknown_obstacle_adaptation/checkpoints/'
            'stage_b_randomized/phase20_stage_b_325000_steps.zip'
        ),
        'planner': project / 'navigation/phase22/continuous_corridor_planner.py',
        'phase22_env': project / 'envs/phase22/mkmini_phase22_v1_continuous_corridor_env.py',
        'g9a_env': project / 'envs/g9a/mkmini_g9a_risk_margin_env.py',
        'g11b_env': project / 'envs/g11b/mkmini_g11b_budget162_env.py',
    }
    for p in paths.values():
        if not p.exists():
            raise RuntimeError(f'G11B_REQUIRED_FILE_MISSING:{p}')

    hashes = {k: sha256(v) for k, v in paths.items()}
    expected = {
        'model': EXPECTED_MODEL_SHA,
        'planner': EXPECTED_PLANNER_SHA,
        'phase22_env': EXPECTED_PHASE22_SHA,
        'g9a_env': EXPECTED_G9A_ENV_SHA,
        'g11b_env': EXPECTED_G11B_ENV_SHA,
    }
    for k, exp in expected.items():
        if hashes[k] != exp:
            raise RuntimeError(
                f'G11B_FROZEN_HASH_MISMATCH:{k}:expected={exp}:got={hashes[k]}'
            )

    g11a_run = Path.home() / 'mkmini_g11a_anytime_compute_budget_v1' / 'run'
    g11a_summary_path = g11a_run / 'G11A_FINAL_SUMMARY_V1.json'
    g11a_report_path = g11a_run / 'G11A_FINAL_REPORT_V1.md'
    if not g11a_summary_path.exists() or not g11a_report_path.exists():
        raise RuntimeError('G11A_FINAL_ARTIFACTS_MISSING')
    g11a = load_json(g11a_summary_path)

    if g11a.get('status') != 'COMPLETE':
        raise RuntimeError('G11A_NOT_COMPLETE')
    if not bool(g11a.get('development_only', False)):
        raise RuntimeError('G11A_NOT_MARKED_DEVELOPMENT')
    if not bool(g11a.get('measurement_valid', False)):
        raise RuntimeError('G11A_MEASUREMENT_NOT_VALID')
    n_events = int(g11a.get('candidate_exhaustion_event_count', 0))
    if n_events < 20:
        raise RuntimeError('G11A_TOO_FEW_EVENTS')
    if int(g11a.get('full_budget_equivalence_pass_count', -1)) != n_events:
        raise RuntimeError('G11A_FULL_EQUIVALENCE_NOT_ALL_PASS')

    selection = (
        g11a.get('pre_registered_selection_rule') or {}
    ).get('selected_budget')
    if int(selection) != BUDGET:
        raise RuntimeError(f'G11A_SELECTED_BUDGET_MISMATCH:{selection}')

    g11a_source = g11a.get('source_contract') or {}
    g11a_hashes = g11a_source.get('hashes') or {}
    # G11A source-contract schema stores the frozen SCCR planner under "sccr".
    # G11B v1 incorrectly queried a non-existent key named "planner".
    if g11a_hashes.get('sccr') != EXPECTED_PLANNER_SHA:
        raise RuntimeError(
            'G11A_SCCR_HASH_MISMATCH:'
            + str(g11a_hashes.get('sccr'))
        )
    if g11a_hashes.get('model') != EXPECTED_MODEL_SHA:
        raise RuntimeError('G11A_MODEL_HASH_MISMATCH')

    g11a_freeze = (
        Path.home()
        / 'mkmini_g11a_anytime_compute_budget_v1'
        / 'G11A_FINAL_FREEZE_20260921.tar.gz'
    )
    if not g11a_freeze.exists():
        raise RuntimeError('G11A_FINAL_FREEZE_ARCHIVE_MISSING')
    g11a_freeze_sha = sha256(g11a_freeze)
    if g11a_freeze_sha != EXPECTED_G11A_FREEZE_SHA:
        raise RuntimeError(
            'G11A_FINAL_FREEZE_HASH_MISMATCH:'
            + g11a_freeze_sha
        )

    # The failed v1 launch aborted before preregistration freeze, smoke, and
    # formal opening. Verify that no confirmatory seed was consumed.
    old_run = (
        Path.home()
        / 'mkmini_g11b_budget162_confirmatory_v1'
        / 'run'
    )
    old_formal_opened = (old_run / 'FORMAL_OPENED.txt').exists()
    old_formal_cells = []
    if (old_run / 'cells').exists():
        old_formal_cells = sorted(
            p.name
            for p in (old_run / 'cells').glob('seed_1062*.json')
        )
    if old_formal_opened or old_formal_cells:
        raise RuntimeError(
            'G11B_V1_FORMAL_DATA_ALREADY_OPENED:'
            f'opened={old_formal_opened}:cells={len(old_formal_cells)}'
        )

    return {
        'runner_revision': RUNNER_REVISION,
        'current_hashes': hashes,
        'g11a_summary_sha256': sha256(g11a_summary_path),
        'g11a_report_sha256': sha256(g11a_report_path),
        'g11a_freeze_sha256': g11a_freeze_sha,
        'g11a_source_hash_key': 'sccr',
        'g11a_selected_budget': int(selection),
        'g11a_event_count': n_events,
        'g11a_full_equivalence': f'{n_events}/{n_events}',
        'g11a_measurement_valid': True,
        'g11b_v1_preformal_abort_verified': True,
        'g11b_v1_formal_opened': False,
        'g11b_v1_formal_cell_count': 0,
    }


def patch_holdout_methods(holdout):
    for key, (module_name, class_name, _) in METHOD_SPECS.items():
        holdout.METHODS[key] = (module_name, class_name)



def ensure_g11b_budget_telemetry(row, telemetry_path: Path, method: str):
    """
    Infrastructure-only telemetry contract repair.

    The G11B environment writes its telemetry sidecar inside _g11b_search().
    Therefore a valid episode with no Phase22/G11B search has no sidecar
    under V1.1 even though all initialized counters are zero.

    This helper synthesizes telemetry only when the completed worker result
    proves the zero-search state. Any ambiguous or non-zero case still fails.
    """
    if telemetry_path.exists():
        return load_json(telemetry_path)

    runtime = row.get('runtime_attrs') or {}

    required = (
        'phase22_v1_attempted',
        'g11b_search_candidate_count_total',
        'g11b_search_candidate_count_max',
    )
    missing = [k for k in required if k not in runtime]
    if missing:
        raise RuntimeError(
            'G11B_BUDGET_TELEMETRY_MISSING_UNPROVEN_ZERO_SEARCH:'
            + ','.join(missing)
        )

    attempted = runtime['phase22_v1_attempted']
    total = int(runtime['g11b_search_candidate_count_total'])
    maximum = int(runtime['g11b_search_candidate_count_max'])

    zero_search_proven = (
        attempted is False
        and total == 0
        and maximum == 0
    )

    if not zero_search_proven:
        raise RuntimeError(
            'G11B_BUDGET_TELEMETRY_MISSING_NONZERO_OR_AMBIGUOUS:'
            f'attempted={attempted}:total={total}:max={maximum}'
        )

    telemetry = {
        'candidate_budget': int(BUDGET),
        'min_sensor_margin': (
            float(RA_MARGIN) if method.startswith('ra175') else None
        ),
        'search_call_count': 0,
        'candidate_count_total': 0,
        'candidate_count_max': 0,
        'search_time_total_seconds': 0.0,
        'search_time_max_seconds': 0.0,
        'search_last_seconds': float('nan'),
        'budget_overflow_count': 0,
        'search_none_count': 0,
        'search_candidate_accept_count': 0,
    }

    atomic_json(telemetry_path, telemetry)
    return telemetry


def cell_worker(args):
    project = Path(args.project).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(project))

    verified = verify_frozen_inputs(project)
    telemetry_path = out.with_suffix('.g11b_budget_telemetry.json')
    if args.method.endswith('b162'):
        os.environ['G11B_TELEMETRY_PATH'] = str(telemetry_path)
    else:
        os.environ.pop('G11B_TELEMETRY_PATH', None)

    perturb = install_shift_patch(int(args.seed))
    holdout = importlib.import_module(HOLDOUT_MOD)
    patch_holdout_methods(holdout)

    if args.smoke:
        rc = holdout.smoke_worker(args.method, int(args.seed), out, smoke_steps=1)
    else:
        rc = holdout.worker(args.method, int(args.seed), out)

    atomic_json(
        out.with_suffix('.perturb.json'),
        {
            'stage': 'G11B',
            'condition': 'SHIFT',
            'seed': int(args.seed),
            'method': args.method,
            'selected_budget': BUDGET,
            'ra_margin_m': RA_MARGIN,
            **perturb,
        },
    )

    if isinstance(rc, dict) and not out.exists():
        atomic_json(out, rc)
    if not out.exists():
        raise RuntimeError(f'WORKER_DID_NOT_CREATE_RESULT:{out}')
    if rc not in (None, 0):
        raise SystemExit(int(rc))

    if not args.smoke:
        row = load_json(out)
        row['g11b_condition'] = 'shift'
        row['g11b_method_label'] = METHOD_SPECS[args.method][2]
        row['g11b_selected_budget'] = (
            BUDGET if args.method.endswith('b162') else None
        )
        row['g11b_ra_margin_m'] = (
            RA_MARGIN if args.method.startswith('ra175') else None
        )
        row['g11b_freeze_verified'] = verified
        if args.method.endswith('b162'):
            telemetry = ensure_g11b_budget_telemetry(
                row,
                telemetry_path,
                args.method,
            )
            row['g11b_budget_telemetry'] = telemetry
            row['g11b_budget_overflow_count'] = int(telemetry.get('budget_overflow_count', -1))
            row['g11b_search_candidate_count_max'] = int(telemetry.get('candidate_count_max', -1))
            row['g11b_search_call_count'] = int(telemetry.get('search_call_count', 0))
            row['g11b_search_time_total_seconds'] = float(telemetry.get('search_time_total_seconds', 0.0))
            row['g11b_search_time_max_seconds'] = float(telemetry.get('search_time_max_seconds', 0.0))
        atomic_json(out, row)
    return 0


def run_cell(script: Path, project: Path, run: Path, method: str, seed: int, smoke=False):
    sub = run / ('smoke' if smoke else 'cells')
    sub.mkdir(parents=True, exist_ok=True)
    result = sub / f'seed_{seed}_{method}.json'
    log = sub / f'seed_{seed}_{method}.log'

    if not smoke and result.exists():
        try:
            row = load_json(result)
            if valid_row(row, seed, method):
                return row, 'SKIP_VALID'
        except Exception:
            pass

    cmd = [
        sys.executable, str(script),
        '--mode', 'cell-worker',
        '--project', str(project),
        '--out', str(result),
        '--method', method,
        '--seed', str(seed),
    ]
    if smoke:
        cmd.append('--smoke')

    t0 = time.time()
    try:
        with log.open('w') as lf:
            cp = subprocess.run(
                cmd,
                cwd=str(project),
                stdout=lf,
                stderr=subprocess.STDOUT,
                timeout=(180.0 if smoke else HARD_TIMEOUT_S),
                text=True,
            )
        elapsed = time.time() - t0
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        if smoke:
            return None, 'SMOKE_HARD_TIMEOUT'
        row = {
            'seed': int(seed), 'method': method,
            'safe_success': False, 'collision': False,
            'env_timeout': False, 'wall_timeout': True,
            'steps': None, 'error': 'HARD_WALL_TIMEOUT',
            'wall_seconds': float(elapsed),
            'scenario_signature': None,
            'g11b_condition': 'shift',
            'g11b_method_label': METHOD_SPECS[method][2],
            'g11b_selected_budget': (
                BUDGET if method.endswith('b162') else None
            ),
            'g11b_ra_margin_m': (
                RA_MARGIN if method.startswith('ra175') else None
            ),
        }

        row['g11b_freeze_verified'] = verify_frozen_inputs(project)

        if method.endswith('b162'):
            telemetry_path = result.with_suffix(
                '.g11b_budget_telemetry.json'
            )

            if telemetry_path.exists():
                telemetry = load_json(telemetry_path)

                row['g11b_budget_telemetry'] = telemetry
                row['g11b_budget_telemetry_status'] = (
                    'SIDECAR_AVAILABLE_AT_HARD_WALL_TIMEOUT'
                )
                row['g11b_budget_overflow_count'] = int(
                    telemetry.get('budget_overflow_count', -1)
                )
                row['g11b_search_candidate_count_max'] = int(
                    telemetry.get('candidate_count_max', -1)
                )
                row['g11b_search_call_count'] = int(
                    telemetry.get('search_call_count', 0)
                )
                row['g11b_search_time_total_seconds'] = float(
                    telemetry.get('search_time_total_seconds', 0.0)
                )
                row['g11b_search_time_max_seconds'] = float(
                    telemetry.get('search_time_max_seconds', 0.0)
                )
            else:
                row['g11b_budget_telemetry_status'] = (
                    'UNAVAILABLE_HARD_WALL_TIMEOUT'
                )

        atomic_json(result, row)
        return row, 'HARD_WALL_TIMEOUT_VALID'

    if cp.returncode != 0:
        return None, f'WORKER_RC_{cp.returncode}'
    if not result.exists():
        return None, 'RESULT_MISSING'
    try:
        row = load_json(result)
    except Exception as exc:
        return None, f'RESULT_JSON_ERROR:{exc}'
    if smoke:
        return row, 'SMOKE_PASS'
    if not valid_row(row, seed, method):
        return None, 'RESULT_INVALID'
    return row, 'OK'


def collect(run: Path, method: str):
    rows = []
    for seed in FORMAL_SEEDS:
        p = run / 'cells' / f'seed_{seed}_{method}.json'
        if p.exists():
            try:
                r = load_json(p)
                if valid_row(r, seed, method):
                    rows.append(r)
            except Exception:
                pass
    return rows


def exact_mcnemar(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2.0 * p)


def bootstrap_diff(a, b, reps=100000, seed=20260921):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) == 0:
        return [None, None]
    d = b - a
    rng = np.random.default_rng(seed)
    vals = np.empty(reps, dtype=float)
    for i in range(reps):
        idx = rng.integers(0, len(d), size=len(d))
        vals[i] = float(np.mean(d[idx]))
    lo, hi = np.quantile(vals, [0.025, 0.975])
    return [float(lo), float(hi)]


def num_summary(values):
    a = np.asarray([x for x in values if x is not None and np.isfinite(x)], dtype=float)
    if len(a) == 0:
        return None
    return {
        'n': int(len(a)),
        'mean': float(np.mean(a)),
        'median': float(np.median(a)),
        'q25': float(np.percentile(a, 25)),
        'q75': float(np.percentile(a, 75)),
        'p95': float(np.percentile(a, 95)),
        'max': float(np.max(a)),
    }


def summarize(rows):
    n = len(rows)
    cnt = Counter(classify(r) for r in rows)
    planner_p95 = [r.get('planner_p95_seconds') for r in rows]
    return {
        'n': n,
        'safe_count': cnt['SAFE'],
        'safe_rate': cnt['SAFE'] / n if n else None,
        'collision_count': cnt['COLLISION'],
        'collision_rate': cnt['COLLISION'] / n if n else None,
        'wall_timeout_count': cnt['WALL_TIMEOUT'],
        'wall_timeout_rate': cnt['WALL_TIMEOUT'] / n if n else None,
        'env_timeout_count': cnt['ENV_TIMEOUT'],
        'other_count': cnt['OTHER'],
        'planner_p95_seconds_distribution': num_summary(planner_p95),
    }


def paired(a_rows, b_rows, label_a, label_b):
    a = {int(r['seed']): r for r in a_rows}
    b = {int(r['seed']): r for r in b_rows}
    seeds = sorted(set(a) & set(b))

    A_safe = np.asarray([bool(a[s].get('safe_success', False)) for s in seeds], dtype=int)
    B_safe = np.asarray([bool(b[s].get('safe_success', False)) for s in seeds], dtype=int)
    A_coll = np.asarray([bool(a[s].get('collision', False)) for s in seeds], dtype=int)
    B_coll = np.asarray([bool(b[s].get('collision', False)) for s in seeds], dtype=int)
    A_wt = np.asarray([bool(a[s].get('wall_timeout', False)) for s in seeds], dtype=int)
    B_wt = np.asarray([bool(b[s].get('wall_timeout', False)) for s in seeds], dtype=int)

    sb = int(np.sum((A_safe == 0) & (B_safe == 1)))
    sa = int(np.sum((A_safe == 1) & (B_safe == 0)))
    cb = int(np.sum((A_coll == 0) & (B_coll == 1)))
    ca = int(np.sum((A_coll == 1) & (B_coll == 0)))

    transitions = Counter(f'{classify(a[s])}->{classify(b[s])}' for s in seeds)

    return {
        'n_pairs': len(seeds),
        'a': label_a, 'b': label_b,
        'safe_diff_b_minus_a': float(np.mean(B_safe - A_safe)),
        'safe_95ci': bootstrap_diff(A_safe, B_safe),
        'safe_mcnemar_p': exact_mcnemar(sb, sa),
        'collision_diff_b_minus_a': float(np.mean(B_coll - A_coll)),
        'collision_95ci': bootstrap_diff(A_coll, B_coll),
        'collision_mcnemar_p': exact_mcnemar(cb, ca),
        'wall_timeout_diff_b_minus_a': float(np.mean(B_wt - A_wt)),
        'wall_timeout_95ci': bootstrap_diff(A_wt, B_wt),
        'transitions': dict(sorted(transitions.items())),
    }


def extract_runtime_attr(row, key):
    ra = row.get('runtime_attrs') or {}
    v = ra.get(key, row.get(key))
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def budget_compliance(rows):
    overflow = []
    max_count = []
    calls = []
    total_time = []
    max_time = []
    for r in rows:
        overflow.append(extract_runtime_attr(r, 'g11b_budget_overflow_count'))
        max_count.append(extract_runtime_attr(r, 'g11b_search_candidate_count_max'))
        calls.append(extract_runtime_attr(r, 'g11b_search_call_count'))
        total_time.append(extract_runtime_attr(r, 'g11b_search_time_total_seconds'))
        max_time.append(extract_runtime_attr(r, 'g11b_search_time_max_seconds'))

    observed_overflow = [int(x) for x in overflow if x is not None]
    observed_max = [int(x) for x in max_count if x is not None]
    total_calls = int(sum(int(x) for x in calls if x is not None))

    return {
        'rows_with_overflow_telemetry': len(observed_overflow),
        'overflow_count_sum': int(sum(observed_overflow)),
        'max_candidate_count_observed': max(observed_max) if observed_max else None,
        'total_search_calls_observed': total_calls,
        'search_time_total_seconds_distribution': num_summary(total_time),
        'search_time_max_seconds_distribution': num_summary(max_time),
        'pass': bool(
            len(observed_overflow) == len(rows)
            and sum(observed_overflow) == 0
            and (not observed_max or max(observed_max) <= BUDGET)
        ),
    }


def hierarchical_decision(comparisons, compliance):
    c1 = comparisons['B162_SCCR_vs_Full_SCCR']
    c2 = comparisons['B162_RA175_vs_Full_RA175']

    gate1_safe = (
        c1['safe_95ci'][0] is not None
        and c1['safe_95ci'][0] >= SAFE_NONINFERIORITY_MARGIN
    )

    gate2_safe = (
        gate1_safe
        and c2['safe_95ci'][0] is not None
        and c2['safe_95ci'][0] >= SAFE_NONINFERIORITY_MARGIN
    )
    gate2_collision = (
        gate1_safe
        and c2['collision_95ci'][1] is not None
        and c2['collision_95ci'][1] <= COLLISION_NONINFERIORITY_MARGIN
    )

    if not compliance['sccr_b162']['pass'] or not compliance['ra175_b162']['pass']:
        status = 'FAIL_BUDGET_COMPLIANCE'
    elif not gate1_safe:
        status = 'FAIL_BASE_SAFE_NONINFERIORITY'
    elif not gate2_safe:
        status = 'FAIL_FINAL_SAFE_NONINFERIORITY'
    elif not gate2_collision:
        status = 'FAIL_FINAL_COLLISION_NONINFERIORITY'
    else:
        status = 'CONFIRMATORY_PASS'

    return {
        'status': status,
        'hierarchical_gate_order': [
            'B162 SCCR safe noninferiority vs Full SCCR',
            'B162 RA175 safe noninferiority vs Full RA175',
            'B162 RA175 collision noninferiority vs Full RA175',
        ],
        'gate1_base_safe_noninferiority': bool(gate1_safe),
        'gate2_final_safe_noninferiority': bool(gate2_safe),
        'gate3_final_collision_noninferiority': bool(gate2_collision),
        'safe_noninferiority_margin': SAFE_NONINFERIORITY_MARGIN,
        'collision_noninferiority_margin': COLLISION_NONINFERIORITY_MARGIN,
        'alpha': ALPHA,
        'no_tuning_after_opening': True,
    }


def freeze_raw_manifest(run: Path):
    files = []
    for seed in FORMAL_SEEDS:
        for method in METHODS:
            p = run / 'cells' / f'seed_{seed}_{method}.json'
            if not p.exists():
                raise RuntimeError(f'RAW_CELL_MISSING:{p}')
            files.append({
                'seed': seed,
                'method': method,
                'relative_path': str(p.relative_to(run)),
                'sha256': sha256(p),
                'size_bytes': p.stat().st_size,
            })
    atomic_json(
        run / 'G11B_RAW_800_FREEZE_MANIFEST.json',
        {
            'stage': 'G11B_BUDGET162_CONFIRMATORY_V1',
            'formal_cells': len(files),
            'raw_cells_rerun_during_aggregation': 0,
            'raw_cells_modified': 0,
            'files': files,
        },
    )


def finalize(run: Path):
    rows = {m: collect(run, m) for m in METHODS}
    if any(len(rows[m]) != len(FORMAL_SEEDS) for m in METHODS):
        raise RuntimeError('G11B_INCOMPLETE_FORMAL_CELLS')

    freeze_raw_manifest(run)

    summaries = {m: summarize(rows[m]) for m in METHODS}
    comparisons = {
        'B162_SCCR_vs_Full_SCCR': paired(
            rows['sccr_full'], rows['sccr_b162'], 'SCCR-Full', 'SCCR-B162'
        ),
        'B162_RA175_vs_Full_RA175': paired(
            rows['ra175_full'], rows['ra175_b162'], 'RA175-Full', 'RA175-B162'
        ),
        'B162_RA175_vs_B162_SCCR': paired(
            rows['sccr_b162'], rows['ra175_b162'], 'SCCR-B162', 'RA175-B162'
        ),
    }

    compliance = {
        'sccr_b162': budget_compliance(rows['sccr_b162']),
        'ra175_b162': budget_compliance(rows['ra175_b162']),
    }
    decision = hierarchical_decision(comparisons, compliance)

    secondary_risk = comparisons['B162_RA175_vs_B162_SCCR']
    secondary_risk_interpretation = {
        'collision_direction_improved': (
            secondary_risk['collision_diff_b_minus_a'] < 0
        ),
        'collision_mcnemar_p': secondary_risk['collision_mcnemar_p'],
        'safe_noninferiority_descriptive': (
            secondary_risk['safe_95ci'][0] is not None
            and secondary_risk['safe_95ci'][0] >= SAFE_NONINFERIORITY_MARGIN
        ),
        'confirmatory_status': 'SECONDARY_SUPPORTIVE_ONLY',
    }

    final = {
        'stage': 'G11B_BUDGET162_CONFIRMATORY_V1',
        'status': 'COMPLETE',
        'condition': 'SHIFT_ONLY',
        'formal_seeds': [FORMAL_SEEDS[0], FORMAL_SEEDS[-1]],
        'n_seeds': len(FORMAL_SEEDS),
        'planned_cells': PLANNED_CELLS,
        'selected_budget': BUDGET,
        'frozen_ra_margin_m': RA_MARGIN,
        'summaries': summaries,
        'paired_comparisons': comparisons,
        'budget_compliance': compliance,
        'confirmatory_decision': decision,
        'secondary_budgeted_risk_replication': secondary_risk_interpretation,
        'interpretation_boundary': [
            'Fresh simulation holdout under deployment-like sensor degradation.',
            'G11B confirms the operating point selected in development G11A; no tuning after opening.',
            'Candidate-count budget is the primary compute control; wall-clock telemetry is secondary.',
            'Not physical-robot validation and not a general safety guarantee.',
        ],
    }
    atomic_json(run / 'G11B_FINAL_SUMMARY_V1.json', final)

    report = [
        '# G11B Budget-162 Fresh Confirmatory Holdout',
        '',
        '- Fresh seeds: 106200–106399 (n=200)',
        '- Condition: SHIFT only',
        '- Selected in G11A before formal opening: candidate budget = 162',
        '- Frozen RA sensor-margin floor: 0.175 m',
        '- Methods: SCCR-Full, SCCR-B162, RA175-Full, RA175-B162',
        '- Formal cells: 800/800',
        '- No tuning after formal opening.',
        '',
        '| Method | Safe | Collision | Wall timeout | Env timeout | Planner-P95 median |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for m in METHODS:
        s = summaries[m]
        pp = s.get('planner_p95_seconds_distribution') or {}
        ppm = pp.get('median')
        pptext = 'NA' if ppm is None else f'{ppm:.4f}s'
        report.append(
            f"| {METHOD_SPECS[m][2]} | "
            f"{s['safe_count']}/200 ({100*s['safe_rate']:.2f}%) | "
            f"{s['collision_count']}/200 ({100*s['collision_rate']:.2f}%) | "
            f"{s['wall_timeout_count']}/200 ({100*s['wall_timeout_rate']:.2f}%) | "
            f"{s['env_timeout_count']}/200 | {pptext} |"
        )

    def add_comp(title, c):
        report.extend([
            '',
            f'## {title}',
            '',
            f"- Safe Δ {c['b']}−{c['a']}: {100*c['safe_diff_b_minus_a']:.2f} pp",
            f"- Safe paired bootstrap 95% CI: [{100*c['safe_95ci'][0]:.2f}, {100*c['safe_95ci'][1]:.2f}] pp",
            f"- Safe exact McNemar p: {c['safe_mcnemar_p']}",
            f"- Collision Δ {c['b']}−{c['a']}: {100*c['collision_diff_b_minus_a']:.2f} pp",
            f"- Collision paired bootstrap 95% CI: [{100*c['collision_95ci'][0]:.2f}, {100*c['collision_95ci'][1]:.2f}] pp",
            f"- Collision exact McNemar p: {c['collision_mcnemar_p']}",
            f"- Wall-timeout Δ {c['b']}−{c['a']}: {100*c['wall_timeout_diff_b_minus_a']:.2f} pp",
        ])

    add_comp('Primary gate 1: SCCR-B162 vs SCCR-Full', comparisons['B162_SCCR_vs_Full_SCCR'])
    add_comp('Primary gates 2–3: RA175-B162 vs RA175-Full', comparisons['B162_RA175_vs_Full_RA175'])
    add_comp('Secondary supportive replication: RA175-B162 vs SCCR-B162', comparisons['B162_RA175_vs_B162_SCCR'])

    report.extend([
        '',
        '## Budget compliance',
        '',
        f"- SCCR-B162: {compliance['sccr_b162']}",
        f"- RA175-B162: {compliance['ra175_b162']}",
        '',
        '## Confirmatory decision',
        '',
        f"- Status: {decision['status']}",
        f"- Gate 1 base safe noninferiority: {decision['gate1_base_safe_noninferiority']}",
        f"- Gate 2 final safe noninferiority: {decision['gate2_final_safe_noninferiority']}",
        f"- Gate 3 final collision noninferiority: {decision['gate3_final_collision_noninferiority']}",
        '',
        '## Boundary',
        '',
        'This is a fresh simulation confirmatory holdout under deployment-like sensor degradation.',
        'The candidate-count budget is the primary compute control. Wall-clock timing is secondary.',
        'This is not physical-robot validation and does not establish a general safety guarantee.',
    ])
    (run / 'G11B_FINAL_REPORT_V1.md').write_text(
        '\n'.join(report) + '\n', encoding='utf-8'
    )
    return final


def write_progress(run: Path, completed: int, current=None, status='RUNNING'):
    atomic_json(
        run / 'progress.json',
        {
            'stage': 'G11B_BUDGET162_CONFIRMATORY_V1',
            'status': status,
            'completed_cells': completed,
            'planned_cells': PLANNED_CELLS,
            'fraction': completed / PLANNED_CELLS,
            'formal_seeds_opened': (run / 'FORMAL_OPENED.txt').exists(),
            'current': current,
            'updated_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
        },
    )


def master(args):
    project = Path(args.project).expanduser().resolve()
    run = Path(args.out).expanduser().resolve()
    run.mkdir(parents=True, exist_ok=True)
    script = Path(__file__).resolve()
    sys.path.insert(0, str(project))

    print('=' * 96, flush=True)
    print('G11B BUDGET-162 FRESH CONFIRMATORY HOLDOUT V1.1', flush=True)
    print('RUNNER_REVISION=' + RUNNER_REVISION, flush=True)
    print('=' * 96, flush=True)
    print('FORMAL_SEEDS=106200-106399', flush=True)
    print('N_SEEDS=200', flush=True)
    print('CONDITION=SHIFT_ONLY', flush=True)
    print('METHODS=SCCR-Full,SCCR-B162,RA175-Full,RA175-B162', flush=True)
    print('PLANNED_CELLS=800', flush=True)
    print('SELECTED_BUDGET_FROZEN_FROM_G11A=162', flush=True)
    print('RA175_MARGIN_FROZEN=0.175', flush=True)
    print('SAFE_NONINFERIORITY_MARGIN=-0.05', flush=True)
    print('COLLISION_NONINFERIORITY_MARGIN=+0.05', flush=True)
    print('TRAINING=FALSE', flush=True)
    print('MODEL_SAVING=FALSE', flush=True)
    print('G11A_SEEDS_REUSED=FALSE', flush=True)
    print('G9B_SEEDS_REUSED=FALSE', flush=True)
    print('NO_TUNING_AFTER_OPENING=TRUE', flush=True)

    verified = verify_frozen_inputs(project)

    if not (run / 'FORMAL_OPENED.txt').exists():
        atomic_json(
            run / 'G11B_PREREGISTRATION_FREEZE.json',
            {
                'stage': 'G11B_BUDGET162_CONFIRMATORY_V1',
                'created_before_formal_opening': True,
                'formal_seed_range': [FORMAL_SEEDS[0], FORMAL_SEEDS[-1]],
                'n_seeds': len(FORMAL_SEEDS),
                'methods': list(METHODS),
                'selected_budget': BUDGET,
                'frozen_ra_margin_m': RA_MARGIN,
                'safe_noninferiority_margin': SAFE_NONINFERIORITY_MARGIN,
                'collision_noninferiority_margin': COLLISION_NONINFERIORITY_MARGIN,
                'hierarchical_gate_order': [
                    'B162 SCCR safe noninferiority vs Full SCCR',
                    'B162 RA175 safe noninferiority vs Full RA175',
                    'B162 RA175 collision noninferiority vs Full RA175',
                ],
                'alpha': ALPHA,
                'runner_sha256': sha256(script),
                'verified_frozen_inputs': verified,
            },
        )
        print('[1/3] prereg freeze + smoke', flush=True)
        for method in METHODS:
            _, status = run_cell(
                script, project, run, method, SMOKE_SEED, smoke=True
            )
            print(f'SMOKE {METHOD_SPECS[method][2]} = {status}', flush=True)
            if status != 'SMOKE_PASS':
                print('G11B_FORMAL_OPENING=BLOCKED_BY_SMOKE', flush=True)
                raise SystemExit(2)
        (run / 'SMOKE_PASS.txt').write_text('PASS\n', encoding='utf-8')
        (run / 'FORMAL_OPENED.txt').write_text(
            'Formal seeds opened only after preregistration freeze and smoke PASS.\n',
            encoding='utf-8',
        )
        print('G11B_SMOKE=PASS', flush=True)
        print('G11B_FORMAL_OPENED=TRUE', flush=True)
    else:
        print('G11B_FORMAL_ALREADY_OPENED=TRUE', flush=True)
        print('RESUME_VALID_CELLS_ONLY=TRUE', flush=True)

    completed = sum(len(collect(run, m)) for m in METHODS)
    write_progress(run, completed)
    print('[2/3] formal 800 cells', flush=True)

    for seed in FORMAL_SEEDS:
        order = list(METHODS)
        shift = seed % len(order)
        order = order[shift:] + order[:shift]
        for method in order:
            p = run / 'cells' / f'seed_{seed}_{method}.json'
            if p.exists():
                try:
                    if valid_row(load_json(p), seed, method):
                        continue
                except Exception:
                    pass

            current = {
                'seed': seed,
                'method': method,
                'label': METHOD_SPECS[method][2],
            }
            write_progress(run, completed, current)
            print(
                f'CELL_START completed={completed}/{PLANNED_CELLS} '
                f'seed={seed} method={METHOD_SPECS[method][2]}',
                flush=True,
            )
            row, status = run_cell(
                script, project, run, method, seed, smoke=False
            )
            print(
                f'CELL_DONE seed={seed} method={METHOD_SPECS[method][2]} '
                f'status={status}',
                flush=True,
            )
            if row is None:
                write_progress(
                    run, completed, current, status='BLOCKED_INFRASTRUCTURE'
                )
                print('G11B_INFRASTRUCTURE_FAILURE=TRUE', flush=True)
                print('VALID_FORMAL_CELLS_WILL_NOT_BE_RERUN=TRUE', flush=True)
                raise SystemExit(3)
            completed += 1
            write_progress(run, completed, current)

    print('[3/3] raw freeze + aggregate', flush=True)
    final = finalize(run)
    write_progress(run, PLANNED_CELLS, None, status='COMPLETE')

    print('G11B_COMPLETE=TRUE', flush=True)
    print('VALID_CELLS=800/800', flush=True)
    print('CONFIRMATORY_STATUS=' + final['confirmatory_decision']['status'], flush=True)
    print(
        'GATE1_BASE_SAFE_NI=' +
        str(final['confirmatory_decision']['gate1_base_safe_noninferiority']),
        flush=True,
    )
    print(
        'GATE2_FINAL_SAFE_NI=' +
        str(final['confirmatory_decision']['gate2_final_safe_noninferiority']),
        flush=True,
    )
    print(
        'GATE3_FINAL_COLLISION_NI=' +
        str(final['confirmatory_decision']['gate3_final_collision_noninferiority']),
        flush=True,
    )
    print(
        'BUDGET_COMPLIANCE_SCCR=' +
        str(final['budget_compliance']['sccr_b162']['pass']),
        flush=True,
    )
    print(
        'BUDGET_COMPLIANCE_RA175=' +
        str(final['budget_compliance']['ra175_b162']['pass']),
        flush=True,
    )
    print('REPORT=' + str(run / 'G11B_FINAL_REPORT_V1.md'), flush=True)
    return 0



def preflight(args):
    project = Path(args.project).expanduser().resolve()
    run = Path(args.out).expanduser().resolve()
    run.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(project))

    print('=' * 96, flush=True)
    print('G11B V1.1 READ-ONLY PREFLIGHT', flush=True)
    print('=' * 96, flush=True)
    print('RUNNER_REVISION=' + RUNNER_REVISION, flush=True)
    print('FORMAL_SEEDS=106200-106399', flush=True)
    print('SCIENTIFIC_PROTOCOL_CHANGED=FALSE', flush=True)

    verified = verify_frozen_inputs(project)

    atomic_json(
        run / 'G11B_V1_1_PREFLIGHT.json',
        {
            'stage': 'G11B_BUDGET162_CONFIRMATORY_V1_1',
            'status': 'PASS',
            'read_only_preflight': True,
            'formal_seeds_opened': False,
            'verified_frozen_inputs': verified,
        },
    )

    print('G11B_PREFLIGHT=PASS', flush=True)
    print('G11A_SCCR_HASH_KEY_FIX=PASS', flush=True)
    print('G11A_FINAL_FREEZE_HASH=PASS', flush=True)
    print('G11B_V1_PREOPEN_ABORT_VERIFIED=TRUE', flush=True)
    print('FORMAL_SEEDS_REMAIN_UNOPENED=TRUE', flush=True)
    return 0


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=['run', 'cell-worker', 'preflight'], required=True)
    p.add_argument('--project', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--method', choices=METHODS)
    p.add_argument('--seed', type=int)
    p.add_argument('--smoke', action='store_true')
    return p.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if args.mode == 'preflight':
        raise SystemExit(preflight(args))
    if args.mode == 'cell-worker':
        if args.seed is None or args.method is None:
            raise SystemExit('G11B_CELL_ARGS_MISSING')
        try:
            raise SystemExit(cell_worker(args))
        except SystemExit:
            raise
        except Exception:
            err = Path(args.out).with_suffix('.exception.txt')
            err.parent.mkdir(parents=True, exist_ok=True)
            err.write_text(traceback.format_exc(), encoding='utf-8')
            raise
    raise SystemExit(master(args))
