"""Production relay boundary counterexamples; no models or dynamics."""
import sys,json,copy
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1121_coupled_route_night';sys.path.insert(0,str(C));from policy import classify

def main():
 r={'new_actual_native':2200,'own_replay_native':2200,'passed':False,'functional_refusal_safely_stopped':True,'replay':{'passed':True,'maximum_qpos_qvel_ctrl_mocap_error':0.,'contact_mismatched_ticks':0},'physical':{'bad_contacts':0,'minimum_actual_clearance_m':.25}};a={'passed':False,'evidence_passed':True,'functional_passed':False};assert classify(1,r,a)=='FUNCTIONAL_STOPPED';neg=[]
 for key,value in [('new_actual_native',None),('own_replay_native',2199),('functional_refusal_safely_stopped',False)]:
  bad=copy.deepcopy(r);bad[key]=value;assert classify(1,bad,a)=='HARD';neg.append(key)
 for key,value in [('passed',False),('maximum_qpos_qvel_ctrl_mocap_error',1e-6),('contact_mismatched_ticks',1)]:
  bad=copy.deepcopy(r);bad['replay'][key]=value;assert classify(1,bad,a)=='HARD';neg.append('replay_'+key)
 for key,value in [('bad_contacts',1),('minimum_actual_clearance_m',.149)]:
  bad=copy.deepcopy(r);bad['physical'][key]=value;assert classify(1,bad,a)=='HARD';neg.append('physical_'+key)
 bad=copy.deepcopy(a);bad['evidence_passed']=False;assert classify(1,r,bad)=='HARD';neg.append('audit')
 good=copy.deepcopy(r);good['passed']=True;assert classify(0,good,{'passed':True})=='PASSED'
 from source import deterministic_admission
 assert deterministic_admission({'status':'TARGET_FEASIBLE_STOP'},100)and deterministic_admission({'status':'FIXED_BUDGET_STOP'},1700)and not deterministic_admission({'status':'FIXED_BUDGET_STOP'},1699)
 x={'passed':True,'negative_cases':neg,'production_function_exercised':True,'wall_time_dependent_source_acceptance_refused':True,'models':0,'physical_integrations':0,'new_analytical_dynamics':0};(O/'POLICY_QUALIFICATION.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x))
if __name__=='__main__':main()
