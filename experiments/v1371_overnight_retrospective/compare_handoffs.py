"""Single-variable saved-input handoff diagnosis; not future trajectory proof."""
import json
import os
from pathlib import Path
import sys
from reproduce import NoModel

R=Path(__file__).resolve().parents[2];O=R/'runs/v1371_overnight_retrospective'
sys.path.insert(0,str(R/'experiments/v1370_overnight_controller_matrix'))
from segments import validate
def read(p):return json.loads(p.read_text())
def main():
    os.sched_setaffinity(0,{5});rows=[]
    for name in ['rpp_default_horizon_m1_s01_main','rpp_local_horizon_m1_s01_main']:
        d=R/'runs/v858_nav2_verified/v1370'/name;events=read(d/'SEGMENT_RECORDS.json');forecasts=read(d/'FORECAST_RECORDS.json');by_tick={f['native_tick']:f for f in forecasts};ticks=sorted(by_tick);known=read(d/'physics/SETUP.json')['known'];queue=[];plan=0;initial=None
        def ball(tick):
            assert tick in by_tick,'EXACT_HANDOFF_FORECAST_MISSING '+str(tick)
            f=by_tick[tick];return (f['center'],f['radius_m'])
        for event in events:
            if event['event']=='INSTALL_ORDERED_ROUTE':queue=event['segments'][1:];plan=event['plan_index'];initial=ball(event['native_tick'])
            elif event['event']=='CUSP_NEXT_SEGMENT_CHECK':
                assert queue;segment=queue[0];latest=ball(event['native_tick'])
                actual,p=validate(segment,event['body'],known,latest);assert actual==event['accepted']
                for k,v in event['geometry'].items():
                    if isinstance(v,(float,int)) and not isinstance(v,bool):assert abs(p[k]-v)<=1e-8
                    else:assert p[k]==v
                prior,q=validate(segment,event['body'],known,initial);static,s=validate(segment,event['body'],known,None)
                if not actual:rows.append(dict(task=name,plan_index=plan,native_tick=event['native_tick'],actual_latest_passed=actual,actual_latest=p,same_pose_path_with_install_ball_passed=prior,install_ball_result=q,static_only_diagnostic_passed=static,static_only=s,install_ball=initial,latest_ball=latest,cause='HEADING_CAPTURE' if p['reason']=='CUSP_CAPTURE_OUTSIDE_REGISTERED_BOUND' else 'LATEST_DYNAMIC_FIELD_CHANGE' if prior and static else 'OTHER_OR_COMBINED'))
                if event['accepted']:queue.pop(0)
                else:queue=[]
    result=dict(rejected_handoffs=rows,models=0,physical_native=0,scope='fixed same pose/path, only occupied field changed; static-only diagnostic never executed')
    (O/'HANDOFF_ATTRIBUTION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(total_rejections=len(rows),heading_capture=sum(r['cause']=='HEADING_CAPTURE' for r in rows),changed_dynamic_field=sum(r['cause']=='LATEST_DYNAMIC_FIELD_CHANGE' for r in rows),other=sum(r['cause']=='OTHER_OR_COMBINED' for r in rows),rows=[dict(task=r['task'],plan=r['plan_index'],tick=r['native_tick'],cause=r['cause'],current_min=r['actual_latest'].get('minimum_clearance_m'),same_initial_ball_min=r['install_ball_result'].get('minimum_clearance_m')) for r in rows],models=0)))

if __name__=='__main__':main()
