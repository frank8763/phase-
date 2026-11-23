"""Compare only saved nominal/actual handoff arrays, without a model call."""
import hashlib,json,math,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v1643_formal_parent_metadata';D=R/'runs/v1742_formal_runtime_recovery/phase_02__full/analysis'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert os.sched_getaffinity(0)=={4}
 import numpy as np
 base=ROOT/'rounds/phase_02__full';assert read(base/'COMPLETION.json')['closed']
 p=base/'actual/CURRENT_GOAL_ENTRY';selected=read(p/'INITIAL_SELECTION.json');onward=read(p/'ONWARD_SELECTION.json');k=selected['prefix_native']
 with np.load(p/'INITIAL_REFERENCE.npz')as z:nominal=z['states'].copy();memory=z['memory'].copy()
 with np.load(p/'EXECUTED.npz')as z:actual=z['states'].copy();actual_memory=z['memory'].copy()
 assert len(actual)==k+1 and len(nominal)>k+1
 delta=actual[-1]-nominal[k];tracking=[float(np.linalg.norm(delta[:2])),abs(math.atan2(math.sin(delta[2]),math.cos(delta[2]))),abs(float(delta[6]))]
 no=read(ROOT/'rounds/phase_02__no_onward/actual/RESULT.json')['model_work'];full=read(base/'actual/RESULT.json')['model_work']
 proof=dict(scope='saved nominal/actual array analysis; not a new prediction, replay or independent audit',full_initial_selection_passed=selected['passed'],selected_refuge=selected['selected_refuge'],prefix_native=k,nominal_full_reference_native=len(nominal)-1,nominal_prefix_initial_state_equal_to_actual=bool(np.array_equal(nominal[0],actual[0])),nominal_handoff_state=nominal[k].tolist(),actual_handoff_state=actual[-1].tolist(),actual_minus_nominal_handoff=delta.tolist(),terminal_position_heading_steering_difference=tracking,tracking_limits_unchanged=[.04,.035,.015],terminal_tracking_differences_inside_limits=bool(np.all(np.asarray(tracking)<=np.asarray([.04,.035,.015]))),actual_minus_nominal_controller_memory=(actual_memory[-1]-memory[k]).tolist(),measured_onward_passed=onward['passed'],finite_search_nodes=onward.get('nodes'),finite_terminal_attempts=onward.get('terminal_attempts'),finite_best_goal_distance_m=(onward.get('best')or{}).get('distance'),full_tracked_recovery_subset=full,no_onward_tracked_recovery_subset=no,additional_tracked_subset_CPP=full['cpp_native']-no['cpp_native'],additional_tracked_subset_Python=full['python_native']-no['python_native'],full_normal_static_otherFFI_and_internal_work_total=None,causal_explanation_not_isolated=['nominal versus actual handoff state and controller memory','observation/source renewal','finite search incompleteness'],no_global_infeasibility_or_unique_cause_claim=True,new_model_or_physical_or_replay_or_planner_calls=0,source_paths_SHA256={str(x.relative_to(R)):sha(x)for x in [p/'INITIAL_SELECTION.json',p/'ONWARD_SELECTION.json',p/'INITIAL_REFERENCE.npz',p/'EXECUTED.npz']})
 target=D/'HANDOFF_BOUNDARY_ANALYSIS.json';assert not target.exists();target.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
