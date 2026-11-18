"""One common exposed static geometric path; no loaded vehicle models."""
import copy
import math
from component_context import *


def main():
    assert not(C/'SOURCE_FREEZE.json').exists(),'ALREADY_FROZEN'
    source=read(R/'runs/v1281_partial_reconnection_fixed24/WEST_EAST_STATIC_SOURCE.json');plan=source['plan']
    assert source['passed']and plan['passed']and all(plan['checks'].values())and plan['full_goal_route_required']
    poses=plan['state_path'];selected=[poses[0][:3]]
    for row in poses[1:]:
        p=row[:3]
        if math.hypot(p[0]-selected[-1][0],p[1]-selected[-1][1])>=.01 or abs(math.atan2(math.sin(p[2]-selected[-1][2]),math.cos(p[2]-selected[-1][2])))>=.02:
            selected.append(p)
    if selected[-1]!=poses[-1][:3]:selected.append(poses[-1][:3])
    assert len(selected)>100 and math.hypot(selected[-1][0]-4,selected[-1][1]+2)<=.45
    dump(C/'SHARED_PATH.json',dict(poses=selected,source='runs/v1281_partial_reconnection_fixed24/WEST_EAST_STATIC_SOURCE.json',source_sha256=sha(R/'runs/v1281_partial_reconnection_fixed24/WEST_EAST_STATIC_SOURCE.json'),same_course_guidance_for_both=True,no_saved_body_or_wheel_controls_used=True,not_unseen_global_planner_test=True))
    rpp=read(R/'experiments/v1294_rpp_output_scope/params.json')
    mppi=copy.deepcopy(rpp)
    ctrl=copy.deepcopy(read(R/'experiments/v929_executable_mppi/params.yaml')['controller_server']['ros__parameters']['FollowPath'])
    ctrl['PathFollowCritic']['threshold_to_consider']=.1
    mppi['controller_server']['ros__parameters']['controller_plugins']=['MPPI']
    mppi['controller_server']['ros__parameters'].pop('RPP');mppi['controller_server']['ros__parameters']['MPPI']=ctrl
    dump(C/'rpp_params.json',rpp);dump(C/'mppi_params.json',mppi)
    original=read(R/'experiments/v1281_partial_reconnection_fixed24/TASK_main_slot01.json');tasks=[]
    for algorithm,plugin in [('rpp','RPP'),('mppi','MPPI')]:
        for role in ['main','repeat']:
            name=algorithm+'_'+role
            tasks.append(dict(original,task_id=name,run_id='v1300-'+name,role=role,algorithm=algorithm,controller_plugin=plugin,
                              dynamic=False,output=str(RAW/name),run_root=str(O),scope='same_static_guidance_current_vehicle_comparison',component_goal_xy=[4.,-2.],native_limit=60000,nav2_params=str(C/(algorithm+'_params.json'))))
    dump(C/'TASKS.json',tasks);dump(C/'TASKS_entry.json',tasks[0])
    parent=read(R/'experiments/v1294_rpp_output_scope/SOURCE_FREEZE.json')['files']
    paths=[R/p for p in parent if(R/p).is_file()]
    paths += [*C.glob('*.py'),*C.glob('*.json'),C/'PROTOCOL.md',O/'OUTPUT_SCOPE_QUALIFICATION.json',R/'runs/v1281_partial_reconnection_fixed24/WEST_EAST_STATIC_SOURCE.json']
    legacy=read(R/'experiments/v929_executable_mppi/SOURCE_FREEZE.json')['files']
    for p in (R/'runs/v929_executable_mppi/install').rglob('*'):
        if p.is_file():assert sha(p)==legacy[str(p.relative_to(R))];paths.append(p)
    dump(C/'SOURCE_FREEZE.json',dict(files={str(p.relative_to(R)):sha(p)for p in sorted(set(paths))},physical_models_before_freeze=0,tasks=4))
    print(json.dumps(dict(prepared=True,reference_poses=len(selected),tasks=4,source_files=len(set(paths)),models=0)))


if __name__=='__main__':main()
