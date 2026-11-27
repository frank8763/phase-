"""Production Service with saved-array byte fixtures; no analytical model run."""
import sys,json,copy,types,time
from pathlib import Path
import numpy as np
from context import R,C,SOURCE as S,load,read,put,sha
svc=load('prospective_exact_recipe_service',C/'evidence_service.py');pack=load('source_bound_pack_reader',R/'experiments/v1903_dwa_durable_proof_pack/proof_pack.py');codec=load('source_bound_direct_bits',C/'direct_bits.py')
old=R/'runs/v2137_psf_progress_control/components/PSF/actual';proof=read(old/'cycle_000000_shadow.json')
with(old/'DWA_PREDICTIONS.pack').open('rb')as f:raw,end=pack.read_record(f,proof['hybrid_evidence']['offset'],proof['arrays'])
arrays=pack.read_arrays(raw,codec.decode);proof=svc.Service.clean_proof(None,proof);fixture=arrays
class ToySavedArrayReader:
 def __init__(self,*_):self.i=0;self.state=fixture['states'][0].copy();self.adapter=types.SimpleNamespace(last=fixture['memory'][0,:4].copy(),integral=fixture['memory'][0,4])
 def step(self,*_):
  ledger.before('python',1);ledger.python+=1;self.i+=1;self.state=fixture['states'][self.i].copy();self.adapter.last=fixture['memory'][self.i,:4].copy();self.adapter.integral=fixture['memory'][self.i,4];return self.state.copy(),fixture['controls'][self.i-1].copy()
class Ledger:
 limits={'python_native_cap':25000000};python=0
 def before(self,kind,count):assert kind=='python'and count==1
ledger=Ledger();q=types.SimpleNamespace(np=np,model=types.SimpleNamespace(Predictor=ToySavedArrayReader),initial=lambda p:{})
quota=types.SimpleNamespace(admit=lambda *_:None);out=S/'recipe_software';out.mkdir();previous=sys.modules.get('kernel');sys.modules['kernel']=types.SimpleNamespace()
try:
 service=svc.Service(q,setup={},task={'software':True},source={'experiments/v1863_remaining_routes_dwa/response.py':sha(R/'experiments/v1863_remaining_routes_dwa/response.py')},out=out,quota=quota,ledger=ledger,window={})
 p=copy.deepcopy(proof);receipt=service.persist(p,arrays);p['hybrid_evidence']=receipt;assert receipt['mode']=='RECIPE'and service.live_canary_passed and ledger.python==2210
 with service.load_full(p)as z:
  for k in arrays:assert np.array_equal(z[k].view(np.uint64),arrays[k].view(np.uint64))
 assert ledger.python==4420 and not service.escrow.holds
 service.confirm_full_geometry(p)
 with service.load_prefix_after_full(p)as z:assert len(z['states'])==6 and len(z['requests'])==5
 # Stored full goal bytes, no reconstruct/physical integration.
 goal=read(old/'cycle_000250_segment_stop.json')
 with(old/'DWA_PREDICTIONS.pack').open('rb')as f:raw,_=pack.read_record(f,goal['hybrid_evidence']['offset'],goal['arrays'])
 aa=pack.read_arrays(raw,codec.decode);goal=svc.Service.clean_proof(None,goal);goal['arrays']='cycle_001250_goal_stop.npz';goal['hybrid_evidence']=service.persist(goal,aa);assert goal['hybrid_evidence']['mode']=='FULL_ARRAYS'
 with service.load_full(goal)as z:
  for k in aa:assert np.array_equal(z[k].view(np.uint64),aa[k].view(np.uint64))
 neg=[]
 def reject(name,fn):
  try:fn()
  except AssertionError:neg.append(name)
  else:raise AssertionError('RECIPE_NEGATIVE_ACCEPTED:'+name)
 reject('duplicate_prediction_key',lambda:service.persist(proof,arrays))
 # New service with no spent hold rejects source/proof changes before reading.
 d=S/'recipe_negative';d.mkdir();ledger=Ledger();badservice=svc.Service(q,setup={},task={'software':True},source={'experiments/v1863_remaining_routes_dwa/response.py':sha(R/'experiments/v1863_remaining_routes_dwa/response.py')},out=d,quota=quota,ledger=ledger,window={})
 bad=copy.deepcopy(proof);fixture={k:v.copy()for k,v in arrays.items()};fixture['states'][1,0]=np.nextafter(fixture['states'][1,0],np.inf)
 reject('first_live_canary_array_bit_mismatch',lambda:badservice.persist(bad,arrays));assert badservice.poisoned and not(d/'DWA_PREDICTIONS.pack').exists()
 put(S/'EXACT_RECIPE_SOFTWARE_PROOF.json',dict(passed=True,production_service_and_original_AST_loop_executed_on_saved_array_fixture=True,models=0,physical_native=0,replay_native=0,analytical_dynamics_integrations=0,fixture_rows_read=4420,actual_work_counter_is_mock_not_scientific=True,reconstruction_escrow_empty_after_full_audit=True,original_subset_python_cap=25000000,max_rebuild_native=11100000,worst_reserved_rebuild_native=11063900,worst_double_plus_canary_and_goal=22132210,negative_cases=neg,bitwise_uint64_equal=True));print(json.dumps(dict(passed=True,models=0,fixture_rows=4420)))
finally:
 if previous is None:sys.modules.pop('kernel',None)
 else:sys.modules['kernel']=previous
