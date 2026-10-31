
from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(os.environ["MKMINI_PROJECT"]).resolve()
G2A_SCRIPT = (
    ROOT
    / "experiments/phase_paper_stageG2A_randomized_unknown_generalization_80_v1/"
      "run_g2a.py"
)

def load_g2a():
    spec = importlib.util.spec_from_file_location("g2a_lh_worker_base", G2A_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("FAILED_TO_LOAD_G2A_BASE")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["g2a_lh_worker_base"] = mod
    spec.loader.exec_module(mod)
    return mod

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--method", choices=["baseline", "proposed"], required=True)
    ap.add_argument("--ready", required=True)
    ap.add_argument("--result", required=True)
    args = ap.parse_args()

    G = load_g2a()

    if G.sha256(G.MODEL) != G.MODEL_SHA:
        raise RuntimeError("MODEL_SHA_MISMATCH")
    if int(G.METHOD_WALL) != 120:
        raise RuntimeError(f"METHOD_WALL_CHANGED={G.METHOD_WALL}")

    E, pinfo = G.load_eval()
    C = G.env_class(
        G.BASE_MOD if args.method == "baseline" else G.PROP_MOD,
        G.BASE_CLS if args.method == "baseline" else G.PROP_CLS,
    )

    env = None
    try:
        # Deliberately use the exact G2A preparation protocol.
        env, obs, info, sig = G.prepare(E, C, args.seed)

        from stable_baselines3 import SAC
        model = SAC.load(str(G.MODEL), device="cpu")

        G.dump(Path(args.ready), {
            "seed": args.seed,
            "method": args.method,
            "scenario_signature": sig,
            "protocol_info": pinfo,
            "model_sha256": G.MODEL_SHA,
            "method_wall_seconds": int(G.METHOD_WALL),
            "ready_for_rollout": True,
        })
        print(f"METHOD_READY seed={args.seed} method={args.method}", flush=True)

        row = G.run_method(E, env, obs, info, model, args.method)

        # Persist the scientific result BEFORE cleanup.
        G.dump(Path(args.result), {
            "seed": args.seed,
            "method": args.method,
            "scenario_signature": sig,
            "protocol_info": pinfo,
            "row": row,
        })
        print(
            f"METHOD_DONE seed={args.seed} method={args.method} "
            f"class={row.get('final_class')}",
            flush=True,
        )
        return 0
    finally:
        if env is not None:
            try:
                env.close()
            except Exception:
                pass

if __name__ == "__main__":
    raise SystemExit(main())
