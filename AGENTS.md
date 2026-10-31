# Phase only

- This is the sole canonical Phase repository, remote `https://github.com/frank8763/phase-.git`.
- Read `RESEARCH_STATUS.md`, `MIGRATION.md`, and `evidence/README.md` first.
- User requested migration and cleanup only on 2026-10-31. Research is PAUSED_PENDING_USER_REVIEW. Do not run simulation, evaluation, training, or overnight jobs until the user explicitly continues after review.
- Stage is an entirely separate research line and repository. Do not import, change, execute, or delete its code, models, outputs, or processes.
- Keep Phase20 SAC SHA256 `4072c19e02ba5c7c6b218a268c4ff1d987d2352eada01a3de918854d7173fc9f` frozen. Phase6 is a required base controller, not a competing current model.
- `current/` is the single V647 handoff snapshot, not a proven best navigation algorithm. Historical rescue evidence is archived in `evidence/` and must not replace the handoff implicitly.
- `runtime/` preserves byte-identical frozen dependencies. Never edit those files or their historical hash contracts. Make new implementations under `experiments/`; save results under `runs/`.
- Use `./run_phase.sh` for verification. `tools/isolate.py` mounts only this repository and the Python environment into the historical paths; Stage and the original workspace are hidden, frozen dependencies are read-only, and only `runs/` is writable. Do not bypass this isolation to run old home-directory experiments.
- After explicit user authorization to continue, update `REVIEW_PENDING`, the research status, and a bounded protocol before an experiment. Preserve same-state pairing, causal observations, full-footprint safety checks, physical-step contact evaluation, and separate native goal/strict arrival outcomes.
- V648 is a proposal for obstacle observability and path consistency. It has not been executed. Do not revive the superseded claim that the current search only considers one turning side.
- No statistical superiority claim is established. Do not merge heterogeneous historical runs into independent trial counts. Do not interpret no-contact, PROCESS_OK, or CELL_PASS as navigation success.

