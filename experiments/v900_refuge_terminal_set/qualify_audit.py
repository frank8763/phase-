"""Exercise independent audit on a real recorded prefix and falsified evidence."""
import copy,gzip,json,math,shutil,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v900_refuge_terminal_set'
sys.path.insert(0,str(C))
from refuge_audit import audit_refuge
def main():
    old=R/'runs/v858_nav2_verified/v897/main_we';fixture=O/'audit_fixture';fixture.mkdir(exist_ok=False);(fixture/'physics').mkdir()
    for name in ['MOTION_ENVELOPE.json.gz','physics/NATIVE_TRACE.npz','physics/SETUP.json']:
        shutil.copyfile(old/name,fixture/name)
    saved=json.loads((old/'REFUGE_SUPERVISION.json').read_text());request=saved['events'][0]
    candidate=json.loads((O/'SAVED_DIAGNOSIS.json').read_text())['first_saved_terminal_region'];tick=candidate['native_tick']
    states=json.loads(gzip.decompress((old/'MOTION_ENVELOPE.json.gz').read_bytes()))['states'];state=next(s for s in states if s['native_tick']==tick)
    with np.load(old/'physics/NATIVE_TRACE.npz')as z:
        q=z['qpos'][tick-1];v=z['qvel'][tick-1];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
        body=[q[0],q[1],yaw,v[0]*math.cos(yaw)+v[1]*math.sin(yaw),v[5]]
    source=dict(source_native_tick=tick,source_scan_sim_time=state['time'],source_age_s=.1,support_bounds=state['support_bounds'],last_hit_time=state['last_hit_time'])
    entry=dict(event='REFUGE_SET_ENTERED',native_tick=tick,body=body,source=source,region=candidate['region'],start_body=request['body'],selected_goal=request['selection']['goal'])
    checks={}
    def run(name,events,expected):
        value=dict(saved,events=events);(fixture/'REFUGE_SUPERVISION.json').write_text(json.dumps(value)+'\n')
        try:result=audit_refuge(fixture);accepted=result['passed']
        except AssertionError:accepted=False
        checks[name]=accepted==expected
    run('real_failed_prefix_is_not_navigation_success',[request],True)
    run('saved_actual_region_reconstructs',[request,entry],True)
    bad=copy.deepcopy(entry);bad['body'][0]+=.01;run('reject_forged_actual_pose',[request,bad],False)
    bad=copy.deepcopy(entry);bad['source']['support_bounds'][0]+=.01;run('reject_changed_source',[request,bad],False)
    bad=copy.deepcopy(entry);bad['source']['source_age_s']=.21;run('reject_stale_region',[request,bad],False)
    bad=copy.deepcopy(entry);bad['region']['projected_retreat_m']+=.1;run('reject_changed_progress',[request,bad],False)
    bad=copy.deepcopy(entry);bad.update(event='REFUGE_STOP_CONFIRMED',brake_elapsed_s=.5);run('reject_cancel_without_actual_stop',[request,entry,bad],False)
    result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,scope='Actual old prefix plus synthetic region event; not counterfactual physical execution')
    (O/'AUDIT_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 0 if result['passed'] else 1
if __name__=='__main__':sys.exit(main())
