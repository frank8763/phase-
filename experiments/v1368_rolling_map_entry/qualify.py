"""Two actual saved maps, explicit wrong-map negatives and frozen source reuse."""
import ast
import copy
import sys
from component_context import *
from map_gate import inspect_map
from audit import audit


def main():
    grid=read(C/'COMMON_GRID.json');rows=[]
    for method in ['rpp','mppi']:
        p=R/'runs/v1366_canonical_timed_lattice/software'/('canonical_prefix_'+method)/'DELIVERED_COSTMAP.json'
        actual=read(p);proof=inspect_map(actual,grid);assert proof['passed'];rows.append(dict(method=method,source=str(p.relative_to(R)),sha256=sha(p),proof=proof))
        ix=int((-3.15-actual['origin'][0])/actual['resolution']);iy=int((0.-actual['origin'][1])/actual['resolution'])
        assert not (0<=ix<actual['width'] and 0<=iy<actual['height']),'OLD_SENTINEL_WAS_NOT_OUTSIDE'
        for name in ['empty','unknown','resolution','origin','orientation','frame','missing_one','length']:
            bad=copy.deepcopy(actual)
            if name=='empty':bad['data']=[0]*len(bad['data'])
            elif name=='unknown':bad['data']=[-1]*len(bad['data'])
            elif name=='resolution':bad['resolution']=.10
            elif name=='origin':bad['origin']=[100.,100.]
            elif name=='orientation':bad['orientation']=[0.,0.,.1,.99]
            elif name=='frame':bad['frame_id']='wrong_frame'
            elif name=='length':bad['data'].pop()
            else:
                for i,value in enumerate(bad['data']):
                    if value!=100:continue
                    bad['data'][i]=0
                    if not inspect_map(bad,grid)['passed']:break
                    bad['data'][i]=value
                else:raise AssertionError('NO_REQUIRED_OCCUPIED_CELL_FOUND')
            assert not inspect_map(bad,grid)['passed'],'BAD_MAP_ACCEPTED '+name
    dump(O/'MAP_QUALIFICATION.json',dict(passed=True,actual_saved_maps=rows,negative_cases_per_map=8,old_outside_sentinel_refusal_reproduced=True,models=0,physical_native=0))
    prior=R/'experiments/v1367_shared_recovery_component'
    unchanged=['native_component.py','prefix_restore.py','gear_handoff.py','stamped_contract.py','worker_monitor.py','evidence_io.py','transport.py','rpp_params.json','mppi_params.json','COMMON_GRID.json']
    assert all(sha(C/name)==sha(prior/name) for name in unchanged)
    original=read(R/'experiments/v1367_shared_recovery_component/TASKS.json')[0]
    proof=audit(original);assert proof['passed'] is False
    assert all(proof['checks'][name] for name in ['full_recorded','exact_prefix','actual_clearance','full_self','finite_state','native_clock','legal_ctrl','legal_slew','no_bad_contacts','full_own_replay','complete_tail','gear_reconstruction','independent_allocation','final_measured_rest','final_steering_rest','final_drive_zero'])
    dump(O/'V1367_SUPPLEMENTAL_FAILURE_AUDIT.json',proof)
    assert read(R/'runs/v1367_shared_recovery_component/QUALIFICATION.json')['passed'] and read(R/'runs/v1367_shared_recovery_component/SUPERVISION_QUALIFICATION.json')['passed']
    assert not (O/'USER_WINDOW.json').exists() and not (O/'ROUND_WINDOW.json').exists()
    try:authorize(read(C/'TASKS.json')[0],{})
    except (AssertionError,FileNotFoundError):pass
    else:raise AssertionError('UNAPPROVED_ENTRY_CONTINUATION_ALLOWED')
    tree=ast.parse((C/'start.py').read_text())
    assignment=next(node for node in ast.walk(tree) if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='window' for t in node.targets))
    assert ast.unparse(assignment.value)=="read(R / 'runs/v1367_shared_recovery_component/ROUND_WINDOW.json')",'ENTRY_RESETS_WINDOW'
    assert sources() and not any(name in sys.modules for name in ['mujoco','vehicle','torch'])
    dump(O/'QUALIFICATION.json',dict(passed=True,models=0,physical_native=0,unchanged_control_physics_and_helpers=unchanged,
        prior_full_saved_data_and_exit_qualification_reused=True,old_physical_prefix_and_full_replay_exact=True,
        original_missing_map_and_functional_failure_preserved=True,no_new_physical_authority=True,
        unapproved_entry_refused=True,original_dual_window_reused_without_reset=True))
    print(json.dumps(dict(passed=True,actual_saved_maps=2,map_negatives=16,models=0,physical_native=0)))


if __name__=='__main__':main()
