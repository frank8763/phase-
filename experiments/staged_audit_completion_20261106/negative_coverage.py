"""Actual witness/formula seam and exact all-file coverage mutation negatives, no models."""
import ast,hashlib,importlib.abc,importlib.util,json,os,sys
from pathlib import Path
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('NEGATIVES_FORBID_MODELS')
sys.meta_path.insert(0,NoModels())
R=Path(__file__).resolve().parents[2];W=R/'experiments/v842_staged_long_navigation';ROOT=R/'runs/staged_audit_completion_20261106';cell=R/'runs/v842_staged_long_navigation/pilot_main02/paired/geometry_memory'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
for p in [R/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1',R/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1',W]:sys.path.insert(0,str(p))
import numpy as np
from types import SimpleNamespace
from exact_footprint import pose_values
from independent_norm import radial_lower
old=R/'experiments/v802_exact_rejection_global/motion_tracker.py';spec=importlib.util.spec_from_file_location('original_tracked_geometry',old);legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
p=json.loads((cell.parent/'STATIC_PROTOCOL.json').read_text());b=np.asarray(p['footprint_bounds']);base=dict(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=np.asarray(p['known_rectangles']),circles=np.asarray(p['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
original=(W/'audit_reactive.py').read_text();function=next(n for n in ast.parse(original).body if isinstance(n,ast.FunctionDef)and n.name=='values');exec(compile(ast.Module(body=[function],type_ignores=[]),str(W/'audit_reactive.py'),'exec'))
states={s['step']:{k:v for k,v in s.items()if k!='step'}for s in map(json.loads,(cell/'motion_estimate.jsonl').open())};ordinary=[];joint=[]
for row in map(json.loads,(cell/'control_decisions.jsonl').open()):
 if row.get('stage')=='BACKUP_APPEND':ordinary.extend(t for t in row['detail'].get('candidates',[])if t.get('full_minimum_not_evaluated',False))
for event in map(json.loads,(cell/'early_joint_decisions.jsonl').open()):
 for probe in event['probes']:joint.extend(t for t in probe['detail'].get('candidates',[])if t.get('full_minimum_not_evaluated',False))
files={str(x.relative_to(cell))for x in(cell/'rejection_witnesses').glob('*.npz')};refs=[t['early_rejection_witness_file']for t in ordinary+joint]
def complete(refs,files):return len(refs)==len(set(refs))==len(files)and set(refs)==files
assert not complete(refs[:len(ordinary)],files),'ORIGINAL_COUNT_REPRO_MUST_BE_RED'
assert complete(refs,files);negative=0
for wrong,actual in [(refs[:-1],files),(refs+[refs[0]],files),(refs,files|{'unreferenced.npz'}),(refs,files-{refs[0]})]:assert not complete(wrong,actual);negative+=1
def check_witness(data):
 tick=int(data['witness_native_tick']);step=int(data['step']);state=states[step]
 assert str(data['state_sha256'])==hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()
 v=float(values(state,data['poses'][tick-1:tick],np.array([tick*.01]))[0]);assert abs(v-float(data['witness_value']))<=1e-10 and v<.155-1e-8
 return v
selected=[joint[0],joint[len(joint)//2],joint[-1]];verified=[]
for t in selected:
 with np.load(cell/t['early_rejection_witness_file'])as z:data={k:z[k].copy()for k in z.files}
 value=check_witness(data);verified.append(dict(file=t['early_rejection_witness_file'],value=value))
 for key,value in [('witness_value',float(data['witness_value'])+.01),('state_sha256','tampered')]:
  bad=dict(data);bad[key]=np.asarray(value)
  try:check_witness(bad)
  except AssertionError:negative+=1
  else:raise AssertionError('WITNESS_MUTATION_NOT_REJECTED')
out=dict(passed=True,ordinary_witnesses=len(ordinary),joint_witnesses=len(joint),actual_files=len(files),old_count_is_red=True,union_exact=True,original_independent_formula_sample=verified,negative_cases=negative,models=0,integrations=0)
(ROOT/'COMPLETE_COVERAGE_NEGATIVES.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='original_independent_formula_sample'}))
