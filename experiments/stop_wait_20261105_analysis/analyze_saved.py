"""Finite geometric diagnosis of saved stopping locations. Zero models/steps."""
import copy,gzip,importlib.abc,importlib.util,json,sys
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2]
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):
            raise RuntimeError('SAVED_DIAGNOSIS_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
for p in ['runtime/mk-mini/experiments/phase_rpccr_p0b68_v1','experiments/v812_soft_global_reference']:
    sys.path.insert(0,str(repo/p))
from exact_footprint import build
from motion_tracker import install_time_gate
from current_guide import route_world,attach
root=repo/'runs/v814_stop_wait_entry_continuation/physical';read=lambda p:json.loads(p.read_text())
spec=importlib.util.spec_from_file_location('F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
cell=repo/'runs/v812_soft_global_reference/main_slot01/paired/geometry_memory';world=read(cell/'planning_0303.json')['causal_input']
protocol=read(cell.parent/'STATIC_PROTOCOL.json');result=read(root/'RESULT.json');out=[]
for branch in result['records']:
    checkpoint=branch['checkpoint'];directory=root/f'checkpoint_{checkpoint}'
    with gzip.open(directory/'OBSERVATIONS.json.gz','rt')as f:observations=json.load(f)
    rows=[]
    for label,index in [('AFTER_RETAINED_BRAKE',40),('END_OF_BRANCH',len(observations)-1)]:
        item=observations[index];state=item['state'];p=item['packet'];pose=np.r_[p['xy'],p['yaw']]
        w=copy.deepcopy(world);w['sensor_points']=[];w['circles']=protocol['known_circles'];w['rectangles']=[*protocol['known_rectangles'],state['current_outer_rectangle']]
        field=build(F,w);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
        actual_pose_values=field.trajectory_values(np.repeat([pose],328,axis=0),.01)
        rows.append(dict(label=label,step=p['step'],pose=pose.tolist(),current_causal_clearance_m=float(field.pose_values([pose])[0]),
                         ideal_fixed_pose_3_28s_causal_minimum_m=float(actual_pose_values.min()),
                         ideal_fixed_pose_passed_original_gate=bool(actual_pose_values.min()>=.155),
                         actual_new_sensor_hit=state['observed_this_frame'],measurement_age_s=state['age_s'],
                         scope='Geometric diagnostic only. Fixed pose is not an actuator trajectory or physical waiting proof.'))
    search=branch['searches'][-1];state=search['state'];path=np.asarray(search['path'])
    w=copy.deepcopy(world);w['sensor_points']=[];w['circles']=protocol['known_circles'];w['rectangles']=[*protocol['known_rectangles'],state['current_outer_rectangle']]
    field=build(F,w);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
    rw,_=route_world(w,state);guide=build(F,rw);attach(guide,state)
    hold_values=[float(field.trajectory_values(np.repeat([pose[:3]],328,axis=0),.01).min())for pose in path]
    out.append(dict(checkpoint=checkpoint,stopping_locations=rows,current_reference_minimum_m=float(guide.pose_values(path[:,:3]).min()),
                    forward_reference_nodes=len(path),reference_nodes_with_3_28s_geometric_hold_below_gate=sum(v<.155 for v in hold_values),
                    minimum_geometric_hold_on_reference_m=min(hold_values),no_new_path_constructed=True))
dest=repo/'runs/v814_stop_wait_entry_continuation/SAVED_STOP_LOCATION_DIAGNOSIS.json';assert not dest.exists()
report=dict(status='FINITE_SAVED_STOP_LOCATION_DIAGNOSIS_COMPLETE',records=out,models=0,integrations=0,new_control_candidates=0,
            cannot_conclude_no_physical_control_or_longer_wait_solution=True)
dest.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
