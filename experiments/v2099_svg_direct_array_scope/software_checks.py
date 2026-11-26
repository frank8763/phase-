"""Actual future full-array service and boundary, zero numerical constructors."""
import ast,copy,hashlib,importlib.abc,json,os,subprocess,sys,time,traceback,types
from pathlib import Path
from context import R,C,SOURCE,STUDY,O,read,put,sha,load,predecessors_closed
P=R/'runs/v2095_svg_common_full_route'
def main():
 assert not(SOURCE/'SOURCE_ONCE.json').exists();out=SOURCE/'software_fixture_v2';out.mkdir(exist_ok=False);result=dict(passed=False,models=0,DLLs=0,constructors=0,solver_queries=0,physics=0,replay=0,new_old_case_audit=False)
 try:
  os.sched_setaffinity(0,{4})
  class Ban(importlib.abc.MetaPathFinder):
   def find_spec(self,n,*a):
    if n.split('.')[0]in{'mujoco','torch','jax','kernel','factory','vehicle','fast_predict','OpenGL'}:raise AssertionError('SOFTWARE_NO_MODEL_IMPORT:'+n)
  sys.meta_path.insert(0,Ban());import numpy as np
  predecessors_closed();prior=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in prior.items())
  measured=R/'runs/v2098_svg_direct_array_evidence/RESULT.json';assert read(measured)['passed']and read(measured)['old_actual_deadline_red']
  input=R/'runs/v1672_svg_direct_live_component/actual/CURRENT_SHADOW.npz'
  with np.load(input)as z:arrays={k:z[k][:2211 if k in ['states','memory']else 2210].copy()for k in z.files}
  boundary=load('unchanged_original_output_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');charges=[]
  def debit(p,n):assert p.is_relative_to(out.resolve());charges.append(n);assert sum(charges)<4*1024**2,'SOFTWARE_FIXTURE_4MIB_STOP'
  class Quota:
   def admit(self,n,stage):assert 0<=n<=4*1024**2
  ledger=types.SimpleNamespace(limits=dict(python_native_cap=25000000),python=0,before=lambda *a:(_ for _ in()).throw(AssertionError('MODEL_CALL_DURING_FULL_ARRAY_EVIDENCE')))
  service=load('actual_future_full_array_service',C/'evidence_service.py');q=types.SimpleNamespace(np=np)
  s=service.Service(q,setup=dict(explicit_software_only=True),task=dict(explicit_software_only=True),source=prior,out=out,quota=Quota(),ledger=ledger,window={})
  proof=dict(native=2210,arrays='software_shadow.npz',origin_packet=dict(software_fixture=True))
  with boundary.OutputBoundary(out,debit):
   proof['hybrid_evidence']=s.persist(proof,arrays)
   assert proof['hybrid_evidence']['mode']=='FULL_ARRAYS'and s.recipe_records==s.recipe_native==0
   with s.load_full(proof)as decoded:assert all(decoded[k].tobytes()==a.tobytes()for k,a in arrays.items())
  assert s.rebuilt_native==0 and not s.escrow.holds and not s.poisoned
  negatives=[]
  def reject(label,fn):
   try:fn()
   except (AssertionError,ValueError,KeyError):negatives.append(label)
   else:raise AssertionError('BAD_INPUT_ACCEPTED:'+label)
  reject('cached_prefix_before_full_geometry',lambda:s.load_prefix_after_full(proof));s.confirm_full_geometry(proof)
  with s.load_prefix_after_full(proof)as z:assert z['states'].tobytes()==arrays['states'][:6].tobytes()
  bad=copy.deepcopy(proof);bad['hybrid_evidence']['mode']='RECIPE';reject('old_reconstruction_mode_forbidden',lambda:s.load_full(bad));assert s.poisoned
  direct=load('exact_vectorized_uint64_codec',C/'direct_bits.py');words=np.random.default_rng(2099).integers(0,2**64,size=(2211,8),dtype=np.uint64);words[:6,0]=[0,2**63,1,0x7ff0000000000000,0x7ff8000000000051,0xfff0000000000000];x=words.view(np.float64);header,payload=direct.encode(x);assert direct.decode(header,payload).tobytes()==x.tobytes();corrupt=bytearray(payload);corrupt[23]^=1;reject('corrupt_array_bits',lambda:direct.decode(header,bytes(corrupt)))
  budget=load('actual_next_audit_budget',C/'audit_budget.py');assert budget.seconds(1200)==1000 and budget.seconds(650)==590;reject('closure_exhausted',lambda:budget.seconds(100))
  writer=load('actual_compact_json_writer',C/'compact_json.py');value=read(P/'rounds/common_01__SVGMPPI/actual/cycle_000811_shadow.json')
  with boundary.OutputBoundary(out,debit):writer.atomic(out/'compact_roundtrip.json',value)
  assert read(out/'compact_roundtrip.json')==value
  original=R/'experiments/v2095_svg_common_full_route';unchanged=[]
  changed={'context.py','pilot_entry.py','run_phase.py','queue_storage.py','evidence.py','evidence_service.py','driver.py','reserved_census.py','reservation.py','software_checks.py','qualify_source.py'}
  for p in original.glob('*.py'):
   if p.name not in changed and (C/p.name).exists():assert p.read_bytes()==(C/p.name).read_bytes(),p.name;unchanged.append(p.name)
  for n in ['CONFIG.json','NATIVE_DEPENDENCIES.json']:assert sha(SOURCE/n)==sha(P/n)
  assert not(O/'PILOT_ONCE_CLAIM.json').exists()and not(O/'COMPLETION.json').exists()and not(O/'actual').exists()
  assert read(STUDY/'RETENTION_STATE.json')['last']=='common_01__SVGMPPI'
  for name in ['pilot_entry.py','run_phase.py']:
   p=subprocess.run(['taskset','-c','2','/usr/bin/python3','-B',str(C/name)],env=dict(os.environ,PHASE_REPO=str(R)),capture_output=True,timeout=10);assert p.returncode!=0 and b'NOT_ADMITTED'in p.stderr
  ros=load('readonly_native_no_admission',R/'experiments/v856_nav2_foundation/ros_environment.py');cmd=ros.command(['/usr/bin/python3.12','-I','-B','-S',str(C/'native_worker.py')]);idx=cmd.index('--bind');cmd[idx]='--ro-bind';p=subprocess.run(['taskset','-c','7',*cmd],env=ros.environment(),capture_output=True,timeout=15);assert p.returncode!=0 and b'PILOT_ADMISSION.json'in p.stderr
  # Source scope/output binding is separate: common02 original byte SHA remains
  # the immutable registered template; original source/round01 not overwritten.
  task=read(O/'PILOT_TASK.json');assert task['task_id']=='common_02__SVGMPPI'and task['run_id'].startswith('v2095_')and O.parent==STUDY/'rounds'
  from reserved_census import admission
  reserve=admission();pins={}
  for folder in [C,R/'experiments/v2100_svg_second_formal_dispatch',R/'experiments/v2098_svg_direct_array_evidence']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     pins[str(p.relative_to(R))]=sha(p)
  for p in [input,measured,O/'PILOT_TASK.json',P/'rounds/common_01__SVGMPPI/POST_ROUND_STORAGE_BARRIER.json']:pins[str(p.relative_to(R))]=sha(p)
  result.update(passed=True,full_array_service_mode='FULL_ARRAYS',actual_production_service_OutputBoundary_roundtrip=True,no_model_reconstruction_calls=True,bit_exact_all_arrays=True,arbitrary_IEEE754_bits_exact=True,compact_JSON_values_order_preserved=True,negative_cases=negatives,unchanged_modules=unchanged,original_algorithm_CABI_and_parameters_unchanged=True,old_common01_preserved_closed=True,source_study_output_roots_distinct=True,budget_maximum_audit_s=1000,budget_original_root_reserve_s=60,source_pins=pins,reservation=reserve,software_fixture_bytes_charged=sum(charges),packed_profile_bytes=proof['hybrid_evidence']['frame_bytes'])
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:result['closed']=True;put(SOURCE/'SOFTWARE_CHECK_PROOF.json',result)
 print(json.dumps({k:result.get(k)for k in ['passed','first_error','models','packed_profile_bytes']}));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
