"""Run persisted-evidence checks with redirected outputs, preserving V724 failure."""
import argparse,hashlib,json,os,sys
from pathlib import Path
import numpy as np
import mujoco
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;source=repo/'experiments/v724_progress_observation_recovery';root=repo/'runs/v726_saved_evidence_completion'
p=argparse.ArgumentParser();p.add_argument('script');a=p.parse_args()
allowed={'audit_recovery_selection.py':'RECOVERY_SELECTION_AUDIT.json','audit_route_commitment.py':'ROUTE_COMMITMENT_AUDIT.json','audit_projection_learning.py':'PROJECTION_LEARNING_AUDIT.json','audit_all_tail_geometry.py':'SAVED_TAIL_GEOMETRY_AUDIT.json','audit_shadow_mode.py':'SHADOW_MODE_AUDIT.json','audit_field_discovery.py':'DISCOVERY_CHAIN_AUDIT_V699.json'}
assert a.script in allowed and (repo/'REVIEW_PENDING').exists()
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
assert read(repo/'runs/v724_progress_observation_recovery/ROUND_WINDOW.json')['round_closed']
assert read(repo/'runs/v724_progress_observation_recovery/FINALIZED.json')['status']=='PROGRESS_OBSERVATION_PILOT_NOT_PASSED'
def reject(*args,**kwargs):raise RuntimeError('V726_FORBIDS_MODEL_INITIALIZATION_OR_INTEGRATION')
class ForbiddenModel:
 from_binary_path=staticmethod(reject)
 from_xml_path=staticmethod(reject)
 from_xml_string=staticmethod(reject)
 def __init__(self,*args,**kwargs):reject()
mujoco.MjModel=ForbiddenModel;mujoco.MjData=reject
for n in ['mj_step','mj_step1','mj_step2']:setattr(mujoco,n,reject)
root.mkdir(exist_ok=True);output=root/a.script.removesuffix('.py');output.mkdir(exist_ok=False)
path=source/a.script;code=path.read_text();before=sha(path)
if a.script=='audit_field_discovery.py':argv=[str(path),str(repo/'runs/v724_progress_observation_recovery/main01/paired'),'--output-dir',str(output)]
else:
 name=allowed[a.script];variable='pair'if a.script in ['audit_recovery_selection.py','audit_shadow_mode.py']else'root';old="("+variable+"/'"+name+"')";new="(supplement_output/'"+name+"')"
 assert code.count(old)==1;code=code.replace(old,new)
 argv=[str(path),str(repo/'runs/v724_progress_observation_recovery/main01/paired')]
 if a.script=='audit_projection_learning.py':argv+=['--model',str(repo/'runs/v690_visible_eight_meter/training_8m/proposer.json')]
if a.script=='audit_recovery_selection.py':
 old='json.dumps(out,indent=2)';assert code.count(old)==1
 code=code.replace(old,'json.dumps(out,indent=2,default=lambda value: value.item() if isinstance(value,np.generic) else value)')
provenance=dict(original_source=str(path.relative_to(repo)),sha256=before,original_v724_failure_unchanged=True,only_output_path_redirected=True,only_numpy_scalar_serialization_adapted=a.script=='audit_recovery_selection.py',model_and_integration_functions_rejected=True,new_integrations=0)
(output/'PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n')
sys.path.insert(0,str(source));os.environ['PHASE_REPO']=str(repo);sys.argv=argv
try:exec(compile(code,str(path),'exec'),dict(__name__='__main__',__file__=str(path),supplement_output=output))
finally:assert sha(path)==before and all(sha(repo/n)==h for n,h in freeze['files'].items())
