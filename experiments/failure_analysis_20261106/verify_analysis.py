"""Check saved diagnostic provenance; no model initialization or integration."""
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[2]
OUTPUT = REPO / "runs/failure_analysis_20261106"


def read(relative):
    return json.loads((REPO / relative).read_text())


decomposition = read("runs/failure_analysis_20261106/CAUSE_DECOMPOSITION.json")
classification = read("runs/failure_analysis_20261106/TAIL_REJECTION_CLASSIFICATION.json")
assert decomposition["models"] == classification["models"] == 0
assert decomposition["integrations"] == classification["integrations"] == 0
counts = []
inputs = []
for result in classification["records"]:
    step = result["step"]
    source = f"runs/v833_timed_escape_qualification/step{step:04d}/ATTEMPTS.json"
    inputs.append(source)
    attempts = read(source)
    candidates = [
        (attempt["source"]["rank"], candidate)
        for attempt in attempts
        for candidate in attempt["detail"]["candidates"]
        if candidate["library"] == "RETURN_TIMED_ESCAPE"
    ]
    assert len(candidates) == len(result["records"]) == result["new_candidates"]
    expected = Counter((rank, *c["target_command"][:2], c["target_command"][2], c["brake_after_native_ticks"]) for rank, c in candidates)
    actual = Counter((c["rank"], *c["steering"], c["wheel"], c["brake"]) for c in result["records"])
    assert expected == actual
    assert all(c["reason"] == "TIME_CLEARANCE" for _, c in candidates)
    static_failed = sum(c["minimum_static_m"] < .155 for c in result["records"])
    static_passed = len(candidates) - static_failed
    assert static_failed == result["static_geometry_below0155"]
    assert static_passed == result["static_passed_but_time_gate_failed"]
    counts.append({"step": step, "new_tails": len(candidates), "static_failed": static_failed, "static_passed_temporal_rejected": static_passed})

assert sum(x["new_tails"] for x in counts) == 2610
assert sum(x["static_failed"] for x in counts) == 2392
assert sum(x["static_passed_temporal_rejected"] for x in counts) == 218
timeline = {x["step"]: x for x in decomposition["timeline"]}
assert all(timeline[s]["observed_this_frame"] for s in [490, 491, 495, 527, 531])
margin = decomposition["original490_certificate"]["minimum_refined_m"] - .155
assert abs(margin - .00355775799293786) <= 1e-8
assert next(x for x in decomposition["global_plans"] if x["step"] == 531)["nodes"] == 109

start = time.monotonic()
reproduction = subprocess.run(
    [sys.executable, "-B", "experiments/v833_timed_escape_qualification/reproduce_old_rejection.py", "--require-certified"],
    cwd=REPO, capture_output=True, text=True, timeout=20,
)
(OUTPUT / "old_rejection_reproduction.stdout").write_text(reproduction.stdout)
(OUTPUT / "old_rejection_reproduction.stderr").write_text(reproduction.stderr)
assert reproduction.returncode != 0
assert "NO_ORIGINAL_FORWARD_TAIL_HAS_COMPLETE328_CERTIFICATE" in reproduction.stderr
old = json.loads(reproduction.stdout)
assert old["models"] == old["integrations"] == 0
assert [x["step"] for x in old["records"]] == [495, 527]
assert all(x["best_complete328_minimum_m"] < .155 for x in old["records"])

sources = inputs + [
    "runs/v830_ranked_return_development/main_slot01/paired/STATIC_PROTOCOL.json",
    "runs/failure_analysis_20261106/CAUSE_DECOMPOSITION.json",
    "runs/failure_analysis_20261106/TAIL_REJECTION_CLASSIFICATION.json",
    "experiments/failure_analysis_20261106/analyze.py",
    "experiments/failure_analysis_20261106/classify_tails.py",
    "experiments/failure_analysis_20261106/verify_analysis.py",
    "experiments/v834_timed_escape_development/independent_norm.py",
    "experiments/v834_timed_escape_development/exact_footprint.py",
    "experiments/v812_soft_global_reference/motion_tracker.py",
    "experiments/v834_timed_escape_development/run_static.py",
    "experiments/v834_timed_escape_development/recovery_supervisor.py",
    "experiments/v834_timed_escape_development/reserved_recovery.py",
    "experiments/v834_timed_escape_development/rejection_witness.py",
    "docs/RPCCR_FAILURE_CAUSE_AND_PAPER_GAPS_20261106.md",
]
result = {
    "status": "SAVED_ANALYSIS_CONSISTENCY_AND_EXPECTED_OLD_REJECTION_VERIFIED",
    "at": datetime.now().astimezone().isoformat(),
    "tail_counts": counts,
    "old_reproduction_exit_code": reproduction.returncode,
    "old_reproduction_wall_s": time.monotonic() - start,
    "models": 0, "integrations": 0, "new_algorithm_success_claimed": False,
    "source_sha256": {name: hashlib.sha256((REPO / name).read_bytes()).hexdigest() for name in sources},
    "scope": "Diagnostic provenance check; not a new navigation, an algorithm fix, or a full archive audit.",
}
(OUTPUT / "VERIFICATION.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k != "source_sha256"}, ensure_ascii=False))
