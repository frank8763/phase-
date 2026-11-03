"""Pure array adapter checks of already saved predictions; no MuJoCo import."""
import ast,copy,gzip,json,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(own));sys.path.insert(1,str(repo/'experiments/v735_scan_differential_navigation'))
from retained_coupled import prepare_retained
from renewal_state import decode,encode
read=lambda p:json.loads(p.read_text())
root=repo/'runs/v764_prelaunch';root.mkdir(exist_ok=False)
contract=read(repo/'runs/v735_scan_differential_navigation/main01/paired/geometry_memory/ACTUATOR_COMMAND_CONTRACT.json');ids=contract['ids'];limits=np.asarray(contract['limits']);rate=np.asarray(contract['rate'])
def sequence(target,last,count,brake):
 out=[];command=np.asarray(last).copy()
 for tick in range(0,count,8):
  target_now=np.asarray(target).copy()
  if tick>=brake:target_now[2:]=0.
  command=np.clip(np.clip(target_now,limits[:,0],limits[:,1]),command-rate,command+rate);out.extend([command.copy()for _ in range(min(8,count-tick))])
 return np.asarray(out)
node=next(n for n in ast.walk(ast.parse((own/'probe.py').read_text()))if isinstance(n,ast.FunctionDef)and n.name=='make_proof');scope=dict(encode=encode,np=np);exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'make_proof','exec'),scope);make_proof=scope['make_proof'];checked=neg=0
raw=repo/'runs/v757_state_feedback_qualification';result=read(raw/'RESULT.json')
for state in result['states']:
 domain=decode(read(raw/(state['profile']+'_INITIAL_DOMAIN.json')))
 for rec in state['candidates']:
  if not rec['admissible']:continue
  z=np.load(raw/(rec['label']+'_PRIVATE.npz'));proof=make_proof(rec,z,domain);ctrl=np.zeros(11);ctrl[ids]=z['initial_ctrl'];real=SimpleNamespace(qpos=z['qpos'][7].copy(),qvel=z['qvel'][7].copy(),ctrl=ctrl,time=float(z['initial_time'])+.08);command_map=SimpleNamespace(ids=ids,sequence=sequence)
  cache,_=prepare_retained(proof,real,command_map);assert all(np.array_equal(cache[k],z[k][8:])for k in ['qpos','qvel','controls','poses']);checked+=1
  for mode in ['qpos','qvel','time','ctrl','schedule','target']:
   test=copy.deepcopy(real);bad=copy.deepcopy(proof)
   if mode in ['qpos','qvel']:getattr(test,mode)[0]+=.001
   elif mode=='time':test.time+=.01
   elif mode=='ctrl':test.ctrl[ids[0]]+=.01
   elif mode=='target':bad['target']=[0,0,9,9]
   else:bad['controls'][8][2]+=.001
   try:prepare_retained(bad,test,command_map)
   except AssertionError:neg+=1
   else:raise AssertionError('MALFORMED_CONTRACT_ACCEPTED')
assert checked==27 and neg==162
(root/'RESULT.json').write_text(json.dumps(dict(status='ALL_SAVED_QUALIFIED_TARGET_HANDOVERS_AND_NEGATIVES_PASS',positive_cases=checked,negative_cases=neg,new_initializations=0,new_integrations=0),indent=2)+'\n')
print(checked,neg)
