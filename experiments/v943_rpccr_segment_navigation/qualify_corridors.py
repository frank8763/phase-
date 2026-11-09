"""Pre-model old-command and independent-source negative gates on fixed saved paths."""
import copy
import importlib.abc
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent
OUT=ROOT/'runs/v943_rpccr_segment_navigation'


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','torch','vehicle','factory','physical','rclpy'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel());sys.path[:0]=[str(CODE),str(ROOT/'experiments/v938_rpccr_recovery_segments')]
from command_tube import admit
from recovery import dense_path
from corridor_audit import check_source,tracking


def main():
    saved=ROOT/'runs/v936_rpccr_corridor_search'
    first=json.loads((saved/'ENTRY_QUALIFICATION.json').read_text())['first_actual_trigger']
    known=json.loads((saved/'saved/SETUP.json').read_text())['known']
    paths=json.loads((ROOT/'runs/v938_rpccr_recovery_segments/CORRIDORS.json').read_text())
    checks={};summaries=[]
    for index,row in enumerate(paths):
        packet=copy.deepcopy(first['packet'])
        if index:
            item=json.loads((saved/f'CASE_{[7000,11000,17000][index-1]}.json').read_text())
            packet=copy.deepcopy(item['actual_packet']);source=copy.deepcopy(item['original_source'])
        else:source=copy.deepcopy(first['source'])
        dense=dense_path(row['proposal']['path']);accepted=0;lowest=math.inf
        for j,pose in enumerate(dense):
            p=copy.deepcopy(packet);s=copy.deepcopy(source)
            p['body']=[*pose,0.,0.]
            # Explicit analytic-arrival fixture: not a fresh actual scan or state.
            now=1000.;p['body_measured_at']=now-.05;p['sent_at']=now
            s['decision_at']=now;s['source_age_s']=0.
            s['source_scan_sim_time']+=j*.0125/.1
            if j+1<len(dense):
                angle=math.atan2(math.sin(dense[j+1,2]-pose[2]),math.cos(dense[j+1,2]-pose[2]))
                direction=1 if (dense[j+1,:2]-pose[:2]) @ [math.cos(pose[2]),math.sin(pose[2])] >= 0 else -1
                v=.1*direction;w=v*angle/(direction*.0125)
            else:v=w=0.
            result=admit(p,s,v,w,known,now)
            accepted+=int(result['passed'])
            lowest=min(lowest,result['static_lower_m'],result['dynamic_lower_m'],result['terminal_cycle_lower_m'])
        checks[f'all_original_admissions_fixed_{index}']=accepted==len(dense)
        summaries.append(dict(index=index,analytical_fixture_commands=len(dense),passed=accepted,minimum_lower_m=lowest))
    p=first['packet'];s=first['source'];recorded=np.zeros((p['native_tick'],5));recorded[-1]=p['body']
    stamp=s['source_native_tick'];states={stamp:dict(support_bounds=s['support_bounds'])};priors={stamp:s['periodic']}
    check_source(p,s,recorded,states,priors);checks['exact_native_body_and_source_positive']=True
    for name,modify in [('body',lambda p,s:p['body'].__setitem__(0,p['body'][0]+.01)),('support',lambda p,s:s['support_bounds'].__setitem__(0,s['support_bounds'][0]+.01)),('periodic',lambda p,s:s['periodic']['vertices'][0][0].__setitem__(0,s['periodic']['vertices'][0][0][0]+.01)),('future',lambda p,s:s.update(source_native_tick=p['native_tick']+1))]:
        a,b=copy.deepcopy(p),copy.deepcopy(s);modify(a,b)
        try:check_source(a,b,recorded,states,priors)
        except AssertionError:checks[name+'_tamper_rejected']=True
        else:checks[name+'_tamper_rejected']=False
    path=paths[0]['proposal']['path'];reference=dense_path(path,samples=200)
    checks['reference_tracking_positive']=tracking(path,reference)['passed']
    changed=reference.copy();changed[len(changed)//2,1]+=.1
    checks['out_of_corridor_actual_pose_rejected']=not tracking(path,changed)['passed']
    changed=reference.copy();changed[len(changed)//2,2]+=.1
    checks['out_of_corridor_actual_heading_rejected']=not tracking(path,changed)['passed']
    result=dict(passed=all(checks.values()),checks=checks,cases=summaries,models=0,integrations=0,
                synthetic_analytic_arrival_fixture=True,
                scope='Original admit function on frozen causal-set/analytic-pose fixtures and independent native-source/tracking negatives, not new actual states or observations.')
    (OUT/'CORRIDOR_AUDIT_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));assert result['passed']


if __name__=='__main__':main()
