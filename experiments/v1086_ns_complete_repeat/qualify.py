"""Real isolated entry import, matched pose contracts and repeat-gate negatives."""
import sys, json, ast, types, importlib.abc, gzip
from pathlib import Path

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R/'runs/v1086_ns_complete_repeat'

class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *_):
        if name.split('.')[0] in {'mujoco', 'physical', 'vehicle', 'rclpy', 'torch'}:
            raise AssertionError('NO_MODEL_QUALIFICATION '+name)

sys.meta_path.insert(0, NoModel())
sys.path.insert(0, str(R/'experiments/v1085_pose_entry_relay'))
import worker_relay as w
module = w.load_worker()
sys.path.insert(0, str(C))
import audit
source = audit.patched_source()
assert source.replace(audit.NEW, audit.OLD) == audit.ORIGINAL.read_text()
audit.load_audit()
import numpy as np
from campaign import same_complete

task = json.loads((O/'repeat_fresh_ns.json').read_text())
t, root, cfg, out = module.entry(str(O/'repeat_fresh_ns.json'))
assert t == task and root == O and not out.exists()
assert t['kind'] == 'repeat' and t['historical_prefix_native'] == 0
f = module.factory(O)
owner = module.pipeline.configure(O)
assert callable(f.create_vehicle) and callable(f.replay) and callable(owner.navigate)
assert Path(__import__('planner').library()._name).is_file()
meta = json.loads((O/'NORTH_SOUTH_T0_METADATA.json').read_text())
actual = json.loads((R/'runs/v858_nav2_verified/v1085/main_fresh_ns/RESULT.json').read_text())['physical']['final_body']
worker_node = next(n for n in ast.walk(ast.parse(w.patched_source())) if isinstance(n, ast.Assert) and isinstance(n.msg, ast.Constant) and n.msg.value == 'CANONICAL_POSE_TOLERANCE')
worker_test = compile(ast.Expression(worker_node.test), '<worker-pose-contract>', 'eval')
audit_test = compile(ast.parse(audit.NEW, mode='eval'), '<audit-pose-contract>', 'eval')
def evaluate(body):
    return (bool(eval(worker_test, dict(np=np, v=types.SimpleNamespace(body=lambda:body), meta=meta))),
            bool(eval(audit_test, dict(np=np, p=dict(body=body), task=task))))
assert evaluate(actual) == (True, True)
pose_negatives = []
for axis in range(3):
    for sign in [-1, 1]:
        body = list(meta['packet']['body'])
        body[axis] += sign*1.01e-8
        pose_negatives.append(evaluate(body) == (False, False))
assert all(pose_negatives)

baseline = json.loads((O/'BASELINE_TASK.json').read_text())
self_pair = same_complete(baseline, baseline)
assert self_pair['passed'] and self_pair['complete_length'] == 21351
tests = O/'comparison_cases'
tests.mkdir(exist_ok=True)
def fixture(name, *, delta=0., length=2, model='same', initial_delta=0., detection=1, contact='none'):
    base = tests/name
    ph = base/'physics'
    ph.mkdir(parents=True, exist_ok=True)
    arrays = {k:np.zeros((length, 2)) for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
    arrays['qpos'][0,0] = delta
    np.savez(ph/'NATIVE_TRACE.npz', **arrays)
    np.savez(ph/'INITIAL_STATE.npz', state=np.array([initial_delta]))
    (ph/'SETUP.json').write_text(json.dumps(dict(model_sha256=model)))
    (base/'RESULT.json').write_text(json.dumps(dict(physical=dict(first_actor_detection=dict(native_tick=detection)))))
    with gzip.open(ph/'CONTACTS.json.gz', 'wt') as f:
        json.dump([[[0, 1, contact, 0.]]] * (length+1), f)
    return dict(output=str(base))
a = fixture('baseline')
assert same_complete(a, fixture('equal'))['passed']
rejects = {}
for label, options in dict(state=dict(delta=1.1e-8), length=dict(length=3), model=dict(model='wrong'), initial=dict(initial_delta=1e-8), discovery=dict(detection=2), contact=dict(contact='robot_obstacle_contact')).items():
    try:
        same_complete(a, fixture(label, **options))
        rejects[label] = False
    except AssertionError:
        rejects[label] = True
assert all(rejects.values())
for p in C.glob('*.py'):
    compile(p.read_text(), str(p), 'exec')

# Last, install the real history-read guard; imports and comparator above are offline.
module.install_history_guard(out)
try:
    (Path(baseline['output'])/'physics/NATIVE_TRACE.npz').open('rb')
    history_rejected = False
except AssertionError:
    history_rejected = True
assert history_rejected
answer = dict(passed=True, real_isolated_production_entry=True,
    scientific_worker_reused_exactly=True, audit_only_t0_tolerance_changed=True,
    actual_saved_t0_both_entries_passed=True, over_tolerance_both_entries_rejected=pose_negatives,
    repeat_comparator_real_baseline_self_check=self_pair,
    repeat_comparator_negative_cases=rejects, old_navigation_history_read_rejected=True,
    navigation_tasks=1, new_main_samples=0, models=0, integrations=0)
(O/'QUALIFICATION.json').write_text(json.dumps(answer, indent=2)+'\n')
print(json.dumps(answer), flush=True)
