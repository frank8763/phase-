"""Red-capable saved-evidence loop: actual static arrival gate, without model execution."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=R/'experiments/v864_rpp_static_regression';sys.path.insert(0,str(C));from audit import audit
p=R/'runs/v858_nav2_verified/v864_static/main_ns';task=json.loads((p/'TASK.json').read_text());before=(p/'INDEPENDENT_AUDIT.json').read_bytes()
try:result=audit(task)
finally:(p/'INDEPENDENT_AUDIT.json').write_bytes(before)
summary=dict(functional_passed=result['functional_passed'],evidence_passed=result['evidence_passed'],goal_distance_m=result['goal_distance_m'],native_count=result['native_count'],replay_native=result['replay_native'],case=result['case_id'],scope='Re-evaluate original exact saved execution; does NOT rerun controller or change a result',models=0,integrations=0)
print(json.dumps(summary));sys.exit(0 if result['passed']else 1)
