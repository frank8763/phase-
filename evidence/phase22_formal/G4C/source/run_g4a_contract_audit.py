from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROJECT = Path(os.environ.get("MKMINI_PROJECT", Path.cwd())).resolve()
EXP = PROJECT / "experiments/phase_paper_stageG4_external_baseline_v1"
RESULTS = EXP / "g4a_contract_audit"
RESULTS.mkdir(parents=True, exist_ok=True)

CORE = [
    PROJECT / "envs/phase21/mkmini_phase21_v11_candidate_recovery_env.py",
    PROJECT / "envs/phase22/mkmini_phase22_v1_continuous_corridor_env.py",
    PROJECT / "navigation/phase22/continuous_corridor_planner.py",
    PROJECT / "training/phase21_risk_switch_fusion_sac/tests/eval_phase21_v3_exact_pair_5ep.py",
    PROJECT / "training/phase20_unknown_obstacle_adaptation/checkpoints/stage_b_randomized/phase20_stage_b_325000_steps.zip",
]
MODEL_SHA = "4072c19e02ba5c7c6b218a268c4ff1d987d2352eada01a3de918854d7173fc9f"
AUDIT_SEED = 22751  # already-opened diagnostic seed; no formal outcome is generated.


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def safe(v: Any):
    if isinstance(v, dict):
        return {str(k): safe(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [safe(x) for x in v]
    if isinstance(v, np.ndarray):
        return {"type": "ndarray", "shape": list(v.shape), "dtype": str(v.dtype)}
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return repr(v)


def summarize_attr(obj, name: str):
    try:
        v = getattr(obj, name)
    except Exception as e:
        return {"name": name, "error": repr(e)}
    row = {"name": name, "type": type(v).__name__}
    if isinstance(v, np.ndarray):
        row.update(shape=list(v.shape), dtype=str(v.dtype))
        if v.size and np.issubdtype(v.dtype, np.number):
            a = v.astype(float, copy=False)
            finite = a[np.isfinite(a)]
            if finite.size:
                row.update(min=float(finite.min()), max=float(finite.max()))
    elif isinstance(v, (list, tuple)):
        row["len"] = len(v)
        if len(v) <= 8:
            row["value"] = safe(v)
    elif isinstance(v, (str, int, float, bool)) or v is None:
        row["value"] = safe(v)
    return row


def source_of(obj, name: str):
    try:
        member = getattr(obj, name)
        return inspect.getsource(member)
    except Exception as e:
        return f"# SOURCE_UNAVAILABLE {name}: {e!r}\n"


def scan_source_baselines():
    pats = re.compile(r"\b(dwa|dynamic[_ -]?window|teb|timed[_ -]?elastic|mpc)\b", re.I)
    roots = [PROJECT / "navigation", PROJECT / "envs", PROJECT / "training"]
    hits = []
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*.py"):
            try:
                if p.stat().st_size > 2_000_000:
                    continue
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if pats.search(line):
                    hits.append({"file": str(p.relative_to(PROJECT)), "line": i, "text": line.strip()[:300]})
                    if len(hits) >= 300:
                        return hits
    return hits


def seed_exposure_audit():
    roots = [
        PROJECT / "experiments",
        PROJECT / "training/phase21_risk_switch_fusion_sac",
        PROJECT / "training/phase20_unknown_obstacle_adaptation",
    ]
    exts = {".json", ".jsonl", ".csv", ".txt", ".log", ".py", ".sh", ".md", ".yaml", ".yml"}
    # Paper-series seed range only; avoids unrelated large training seeds.
    seed_token = re.compile(r"(?i)(?:seed|seeds|random_seed)[^\n\r0-9]{0,24}([2][2-9][0-9]{3})")
    range_token = re.compile(r"\b(2[2-9][0-9]{3})\s*(?:\.\.|-|to|至)\s*(2[2-9][0-9]{3})\b", re.I)
    used = set()
    evidence = []
    scanned = 0
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in exts:
                continue
            try:
                size = p.stat().st_size
                if size > 20_000_000:
                    continue
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            scanned += 1
            local = set()
            for m in seed_token.finditer(text):
                local.add(int(m.group(1)))
            for m in range_token.finditer(text):
                a, b = int(m.group(1)), int(m.group(2))
                if a <= b and b-a <= 2000:
                    local.update(range(a, b+1))
            if local:
                used.update(local)
                evidence.append({
                    "file": str(p.relative_to(PROJECT)),
                    "seeds": sorted(local)[:250],
                    "count": len(local),
                })
    candidate_ranges = []
    start = None
    prev = None
    for s in range(22000, 30000):
        if s not in used:
            if start is None:
                start = s
            prev = s
        else:
            if start is not None and prev-start+1 >= 120:
                candidate_ranges.append([start, prev])
            start = prev = None
    if start is not None and prev-start+1 >= 120:
        candidate_ranges.append([start, prev])
    return {
        "scanned_files": scanned,
        "used_seed_count": len(used),
        "used_seeds": sorted(used),
        "evidence_files": evidence,
        "unused_contiguous_ranges_ge_120": candidate_ranges,
        "warning": "This is a repository-text audit, not proof of global non-exposure outside the project tree.",
    }


def main():
    print("="*100)
    print("G4A EXTERNAL BASELINE SOURCE / SEED CONTRACT AUDIT")
    print("="*100)
    missing = [str(p) for p in CORE if not p.exists()]
    if missing:
        raise SystemExit("MISSING_CORE_FILES=" + json.dumps(missing, ensure_ascii=False))
    core_sha = {str(p.relative_to(PROJECT)): sha256(p) for p in CORE}
    model_rel = "training/phase20_unknown_obstacle_adaptation/checkpoints/stage_b_randomized/phase20_stage_b_325000_steps.zip"
    if core_sha[model_rel] != MODEL_SHA:
        raise SystemExit("MODEL_SHA_MISMATCH")

    # Imports are intentionally read-only; no source files are patched.
    p21m = importlib.import_module("envs.phase21.mkmini_phase21_v11_candidate_recovery_env")
    p22m = importlib.import_module("envs.phase22.mkmini_phase22_v1_continuous_corridor_env")
    em = importlib.import_module("training.phase21_risk_switch_fusion_sac.tests.eval_phase21_v3_exact_pair_5ep")
    P21 = getattr(p21m, "MkMiniPhase21V11CandidateRecoveryEnv")
    P22 = getattr(p22m, "MkMiniPhase22V1ContinuousCorridorEnv")

    report = {
        "audit_seed": AUDIT_SEED,
        "training_enabled": False,
        "formal_rollouts_enabled": False,
        "algorithm_changed": False,
        "core_sha256": core_sha,
        "classes": {
            "phase21_mro": [f"{c.__module__}.{c.__name__}" for c in P21.mro()],
            "phase22_mro": [f"{c.__module__}.{c.__name__}" for c in P22.mro()],
        },
        "existing_external_baseline_source_hits": scan_source_baselines(),
        "seed_exposure": seed_exposure_audit(),
        "evaluator": {
            "rollout_source_evidence": [
                x for x in ("robot_sample_points", "robot_obstacle_contact", "check_map_penetration", "collision")
                if x in inspect.getsource(em.rollout)
            ],
            "scenario_signature_available": hasattr(em, "scenario_signature"),
            "synchronize_rngs_available": hasattr(em, "synchronize_rngs"),
        },
    }

    env = None
    try:
        env = P21(
            randomized=True,
            random_seed=AUDIT_SEED,
            terminate_on_collision=True,
            penetration_margin=0.02,
            safe_clearance=0.35,
        )
        if hasattr(env, "phase17_enable_domain_randomization"):
            env.phase17_enable_domain_randomization = False
        if hasattr(em, "synchronize_rngs"):
            em.synchronize_rngs(env, AUDIT_SEED)
        if hasattr(em, "reset_env"):
            obs, info = em.reset_env(env, AUDIT_SEED)
        else:
            out = env.reset(seed=AUDIT_SEED)
            obs, info = out if isinstance(out, tuple) and len(out)==2 else (out,{})

        keywords = ("path", "route", "target", "goal", "lidar", "depth", "sensor", "obstacle", "robot", "steer", "wheel", "speed", "velocity", "clearance", "local", "global")
        attrs = []
        for name in sorted(set(dir(env))):
            low = name.lower()
            if any(k in low for k in keywords) and not name.startswith("__"):
                try:
                    v = getattr(env, name)
                except Exception:
                    continue
                if callable(v):
                    continue
                attrs.append(summarize_attr(env, name))
        report["runtime_contract"] = {
            "observation_shape": list(np.asarray(obs).shape),
            "action_space": repr(getattr(env, "action_space", None)),
            "scenario_signature": safe(em.scenario_signature(env)) if hasattr(em,"scenario_signature") else None,
            "selected_attributes": attrs,
        }

        method_names = [
            "_phase21_v3_build_detour",
            "_phase21_v8_replan",
            "_phase21_v8_apply_active_path",
            "_phase21_v4_apply_path",
            "step",
            "reset",
        ]
        src = []
        for name in method_names:
            if hasattr(P21, name):
                src.append(f"\n# ===== Phase21 {name} =====\n" + source_of(P21, name))
            if hasattr(P22, name):
                src.append(f"\n# ===== Phase22 {name} =====\n" + source_of(P22, name))
        (RESULTS / "planner_hook_sources.py.txt").write_text("\n".join(src), encoding="utf-8")
    finally:
        if env is not None:
            try: env.close()
            except Exception: pass

    (RESULTS / "g4a_contract_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    prereg = {
        "status": "PRE_REGISTERED_PROTOCOL_ONLY",
        "external_baseline": "Ackermann-adapted Dynamic Window Approach (DWA)",
        "reference": "Fox, Burgard, Thrun, IEEE Robotics & Automation Magazine 4(1):23-33, 1997, DOI 10.1109/100.580977",
        "fairness_contract": [
            "same precomputed global A* route and same scenario signature",
            "unknown obstacle introduced after global planning",
            "no global A* rerun after unknown obstacle insertion",
            "runtime control uses only permitted sensor/local state; no unknown-obstacle ground truth",
            "same frozen SAC checkpoint for methods that retain the residual-control stack",
            "same strict collision adjudication, max steps, and wall-time limits",
            "external-baseline tuning restricted to fresh development seeds; formal seeds remain unopened until freeze",
        ],
        "planned_methods": ["DWA external baseline", "Phase21-v11", "Phase22-v1"],
        "primary_endpoint": "collision-free task success",
        "secondary_endpoints": ["collision", "wall timeout", "environment timeout", "planning latency", "activation/replan count"],
        "statistics": ["paired exact McNemar for binary paired outcomes", "Wilson 95% CI", "paired bootstrap 95% CI for success-rate difference"],
        "seed_policy": "Do not assign G4 dev/formal seed ranges until repository exposure audit is reviewed.",
    }
    (RESULTS / "g4_preregistration.json").write_text(json.dumps(prereg, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"SOURCE_HITS={len(report['existing_external_baseline_source_hits'])}")
    print(f"SEED_AUDIT_USED_N={report['seed_exposure']['used_seed_count']}")
    print("UNUSED_RANGES_GE_120=" + json.dumps(report['seed_exposure']['unused_contiguous_ranges_ge_120']))
    print(f"OBS_SHAPE={report.get('runtime_contract',{}).get('observation_shape')}")
    print("TRAINING_ENABLED=FALSE")
    print("FORMAL_ROLLOUTS_ENABLED=FALSE")
    print("ALGORITHM_CHANGED=FALSE")
    print("EXTERNAL_BASELINE_SELECTED=ACKERMANN_DWA")
    print("NEXT=G4B_DWA_INTEGRATION_ON_FRESH_DEV_SEEDS_AFTER_CONTRACT_REVIEW")
    print("G4A_EXTERNAL_BASELINE_CONTRACT_AUDIT=PASS")


if __name__ == "__main__":
    main()
