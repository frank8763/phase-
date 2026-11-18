"""Independent finite proposal-membership audit; no dynamics propagation."""
from pathlib import Path
import copy,hashlib,json
C=Path(__file__).resolve().parent;R=C.parents[1]

def verify(selection):
 assert selection['passed'] and selection['prefix_rows'] is None
 assert selection['proposal_method']=='whole_route_fine_single_primitive_duration_reconnection'
 assert selection['proposals']<=3200 and selection['admissions']<=8
 old=selection['retained_exhaustion']
 assert not old['passed'] and old['bounded_total_expansions']==6000
 assert len(old['search_trials'])==2 and all(not t['passed']and sum(t['phase_expanded'])==3000 for t in old['search_trials'])
 rows=copy.deepcopy(selection['rows']);assert rows[-1]==[0.,0.,2200,0]
 assert all(not r[3]and r[1]in[0.,.12]and type(r[2])is int and r[2]>0 for r in rows)
 wait=0
 if rows[0][1]==0.:wait=rows.pop(0)[2]
 assert 0<=wait<=2000 and wait%10==0 and wait==selection['initial_wait']
 rows.pop();assert sum(r[2]for r in rows)<=6000
 identifier=selection['proposal_id'];source_name,variant=identifier.split('/')
 source=next(s for s in json.loads((C/'PROPOSAL_BANK.json').read_text())['items']if s['id']==source_name)
 assert hashlib.sha256((R/source['source']).read_bytes()).hexdigest()==source['sha256']
 expected=copy.deepcopy(source['moving_rows'])
 if variant!='original':
  index,delta=variant.removeprefix('segment').split('_');index=int(index);delta=int(delta)
  assert 0<=index<len(expected)and delta in[-50,-25,25,50]
  expected[index][2]+=delta
 assert rows==expected,'ACTION_PROPOSAL_NOT_PREREGISTERED'
 a=selection['admission'];assert a['passed']and a['required_nominal_reserve_m']==.022 and a['nominal_execution_reserve_m']>=.022
 return dict(passed=True,proposal_id=identifier,initial_wait_native=wait,changed_motion_segments=0 if variant=='original'else 1,
             no_old_certificate_reused=True,original_task_phase_unchanged=True,models=0,physical_native=0,analytical_propagations=0)

if __name__=='__main__':
 import sys
 p=Path(sys.argv[1]);selection=json.loads(p.read_text());result=verify(selection);bad=copy.deepcopy(selection);bad['rows'][1][2]+=1
 try:verify(bad)
 except AssertionError:result['modified_action_rejected']=True
 else:raise AssertionError('MODIFIED_ACTION_ACCEPTED')
 target=R/'runs/v1241_fine_route_reconnection/PROPOSAL_INDEPENDENT_AUDIT.json';target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
