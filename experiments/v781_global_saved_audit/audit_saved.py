"""Run one persisted-evidence auditor with all initialization/integration forbidden."""
import argparse,hashlib,json,os,sys,time,signal
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;source=repo/'experiments/v778_global_retained_reentry';out=repo/'runs/v781_global_saved_audit';out.mkdir(exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('script');a=p.parse_args();allowed={'audit_early_scan.py','audit_route_commitment.py','audit_projection_learning.py','audit_all_tail_geometry.py','audit_shadow_mode.py','audit_reentry.py','audit_field_discovery.py'};assert a.script in allowed
freeze=json.loads((own/'INPUT_FREEZE.json').read_text());assert all(hashlib.sha256((repo/n).read_bytes()).hexdigest()==h for n,h in freeze['files'].items())
sys.path.insert(0,str(source));import mujoco
def forbidden(*args,**kwargs):raise RuntimeError('V781_MODELS_AND_INTEGRATION_FORBIDDEN')
for name in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,name,forbidden)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V781_240S_AUDIT_CAP')));signal.alarm(240)
pair=repo/'runs/v778_global_retained_reentry/v780_main01/paired';code=(source/a.script).read_text();changes=[]
if a.script=='audit_early_scan.py':
 old="causal_state_exact=c['forecast_state']==state and state['center']is None";new="causal_state_exact=c['forecast_state']=={k:v for k,v in state.items()if k!='step'} and state['step']==created and state['center']is None";assert code.count(old)==1;code=code.replace(old,new).replace("pair/'EARLY_SCAN_AUDIT.json'","out/'EARLY_SCAN_JOURNAL_METADATA_AUDIT.json'");changes=['exclude and independently check journal-only step in saved payload comparison','preserve original FAIL output']
if a.script=='audit_reentry.py':
 old="assert state==x['forecast_state']";new="assert {k:v for k,v in state.items()if k!='step'}==x['forecast_state'] and state['step']==step";assert code.count(old)==1;code=code.replace(old,new);changes=['exclude and independently check journal-only step in saved payload comparison']
args=[str(source/a.script),str(pair)]
if a.script=='audit_projection_learning.py':args+=['--model',str(repo/'runs/v690_visible_eight_meter/training_8m/proposer.json')]
if a.script=='audit_field_discovery.py':args+=['--output-dir',str(out/'discovery_chain')]
sys.argv=args
(out/(a.script+'.ADAPTER.json')).write_text(json.dumps(dict(source=str((source/a.script).relative_to(repo)),source_sha256=hashlib.sha256((source/a.script).read_bytes()).hexdigest(),changes=changes,model_initializations=0,integrations=0),indent=2)+'\n')
namespace={'__name__':'__main__','__file__':str(source/a.script),'out':out};exec(compile(code,str(source/a.script),'exec'),namespace)
