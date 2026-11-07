"""Register one new bounded candidate; all previous rounds remain immutable."""
import ast
from datetime import datetime
import fcntl
import json
from pathlib import Path
import shutil
import time
from zoneinfo import ZoneInfo

repo = Path(__file__).resolve().parents[1]
common = repo / 'experiments/reference_recovery_20261106'
qual = repo / 'experiments/v835_reference_recovery_qualification'
dev = repo / 'experiments/v836_reference_recovery_development'
confirm = repo / 'experiments/v837_reference_recovery_confirmation'
operation = repo / 'runs/reference_recovery_20261106'
assert all(not p.exists() for p in [common, qual, dev, confirm, operation])
assert (repo / 'REVIEW_PENDING').exists()
with (repo / 'runs/v648_static_unknown/execution.lock').open('rb') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
started = time.time()
deadline = datetime(2026, 11, 6, 23, 0, tzinfo=ZoneInfo('Asia/Shanghai')).timestamp()
assert deadline - started >= 36000
for p in [common, qual, dev, confirm, operation]:
    p.mkdir(parents=True)

def dump(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

auth = dict(
    user_instruction='抓紧时间将动态跑出来', authorized_at=datetime.now().astimezone().isoformat(),
    new_independent_round=True, started_unix=started, absolute_deadline_unix=deadline,
    hard_stop_beijing='2026-11-06T23:00:00+08:00', max_scientific_candidates=1,
    hypothesis='A retained finite stop need not admit the next receding-horizon contract. Certify one more public period with no future observation, and use reference-following native recovery controls instead of a constant-steer escape grid.',
    fixed_component_states=[490, 495], fixed_first_commands_per_state=[1, 4],
    component_cap_s=1800, component_private_native_cap=500000,
    complete_component_native=336, component_actual_cap=672, component_repeat_cap=672,
    old_replay_native=3960, original_complete_gate_native=328, added_continuation_native=8,
    follow_lookahead_m=[.35, .55], follow_wheel_speed=[4., 8., 12.],
    follow_drive_native=[160, 208, 240], follow_candidates=18,
    development_main_max=5, development_repeat_max=5,
    conditional_fresh_confirmation_main_max=24, fixed_confirmation_repeats=[1, 9, 17],
    confirmation_minimum_remaining_s=36000, confirmation_batch_cap_s=36000,
    nav_public_cap=1200, nav_soft_s=1200, nav_hard_s=1500, nav_outer_s=1505,
    t0_internal_s=120, t0_outer_s=125, post_freeze_repairs=0,
    original_prediction_floor_m=.155, original_physical_floor_m=.15,
    self_margin_m=.002, terminal_speed_m_s=.025,
    actual_actor_and_sensor_unchanged=True, before_detection_static_reactive_contract=True,
    norm_speed_m_s=.08, broader_axis_class_claimed=False,
    first_development_functional_or_any_safety_evidence_failure_stops=True,
    confirmation_second_functional_or_first_safety_evidence_failure_stops=True,
    all_models_only_run_phase=True, single_cpu_single_instance=True,
    old_deadlines_and_failures_immutable=True, training_updates=0, SAC=0,
    stage_access=0, real_robot=0, subagents=0, new_chats=0, network_pushes=0,
    automatic_extra_candidates_or_pools=False,
)
dump(repo / 'RPCCR_REFERENCE_RECOVERY_AUTHORIZATION_20261106.json', auth)
dump(operation / 'LEDGER.json', dict(status='PREPARING', closed=False, candidates_started=0,
     active_simulation=False, absolute_deadline_unix=deadline))
replacements = [
    ('timed_escape_night_20261105', 'reference_recovery_20261106'),
    ('v833_timed_escape_qualification', 'v835_reference_recovery_qualification'),
    ('v834_timed_escape_development', 'v836_reference_recovery_development'),
    ('RPCCR_TIMED_ESCAPE_NIGHT_AUTHORIZATION_20261105.json', 'RPCCR_REFERENCE_RECOVERY_AUTHORIZATION_20261106.json'),
    ('RPCCR_TIMED_ESCAPE_NIGHT_20261105', 'RPCCR_REFERENCE_RECOVERY_20261106'),
    ('RPCCR_TIMED_ESCAPE_V833', 'RPCCR_REFERENCE_RECOVERY_V835'),
    ('RPCCR_TIMED_ESCAPE_V834', 'RPCCR_REFERENCE_RECOVERY_V836'),
    ('V833', 'V835'), ('V834', 'V836'),
]
for source, destination in [
    (repo/'experiments/timed_escape_night_20261105', common),
    (repo/'experiments/v833_timed_escape_qualification', qual),
    (repo/'experiments/v834_timed_escape_development', dev),
]:
    for path in source.iterdir():
        if not path.is_file() or path.suffix not in ['.py', '.md', '.json'] or path.name in ['INPUT_FREEZE.json', 'CANDIDATE_FREEZE.json', 'prepare.py', 'freeze.py', 'register.py', 'launch.py', 'verify_ops.py']:
            continue
        text = path.read_text()
        for old, new in replacements:
            text = text.replace(old, new)
        (destination/path.name).write_text(text)

# New scientific modules and their audits are installed before the freeze.
config = json.loads((dev/'BATCH.json').read_text())
config.update(label=dev.name, output='runs/'+dev.name, archive='evidence/rpccr_reference_recovery_v836_20261106',
              absolute_deadline_unix=deadline, batch_cap_s=18000, minimum_start_budget_s=7200,
              reference_view='runs/reference_recovery_20261106/qualification/reference/paired')
dump(dev/'BATCH.json', config)
(repo/config['output']).mkdir()
dump(operation/'REGISTRATION.json', auth)
for path in common.glob('*.py'):
    ast.parse(path.read_text(), filename=str(path))
print(json.dumps(dict(status='REGISTERED_ONE_NEW_REFERENCE_RECOVERY_CANDIDATE',
                     root_deadline=auth['hard_stop_beijing'], models=0, integrations=0)))
