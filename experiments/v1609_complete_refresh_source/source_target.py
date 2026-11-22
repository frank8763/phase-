"""One append/current-source continuation under immutable guard and ROS cap."""
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1609_target_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)

def main():
    start=time.monotonic();resources=c.bootstrap();c.guard()
    assert sorted(os.sched_getaffinity(0))==[2]and os.environ['PHASE_REPO']==str(c.R)
    lock=(c.R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as stream:json.dump(dict(unix=time.time(),models_authorized=False),stream)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,
        Allocator_recomputations=0,optimizer_calls=0,phase_FFI_loads=0,OS_library_loads=0,
        original_tracker_updates=0,actual_capture_qualified=False,actual_runtime_qualified=False,
        complete_actual_source_target_passed=False,whole_route_passed=False)
    class NoNumerics(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0]in {'numpy','mujoco','OpenGL','torch','jax','jaxlib','rclpy','factory','vehicle','kernel','runtime'}:
                raise AssertionError('APPEND_SOURCE_NO_NUMERICS:'+name)
    finder=NoNumerics();sys.meta_path.insert(0,finder)
    def profile(frame,event,arg):
        if event=='call':
            p=Path(frame.f_code.co_filename)
            if p.is_absolute()and p.is_relative_to(c.R):
                assert frame.f_code.co_name not in {'physical_binding','load_definitions','initial','all_future','create_vehicle','step','simulate','predict','compute','advance'}
                assert not(p.name=='causal_occupancy.py'and frame.f_code.co_name in {'__init__','update','snapshot','raster','occupied_ball'})
            assert time.monotonic()-start<120
    sys.setprofile(profile)
    try:
        parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json')
        assert parent['scientific_revisions']==12 and parent['active_round']is None and not parent['models_now_authorized']
        source=c.draft_sources();assert all(c.sha(c.R/n)==h for n,h in source.items())
        prior=c.read(c.R/'runs/v1603_capture_close_source/ENTRY_QUALIFICATION.json')
        recovery=c.read(c.R/'runs/v1603_capture_close_source/CURRENT_SOURCE_REMOTE_RECOVERY.json')
        assert prior['passed']and prior['complete_actual_source_target_passed']and recovery['all_frozen_members_remote_chain_covered']
        assert recovery['source_freeze_sha256']==c.sha(c.BASE)
        wm=c.load('v1609_original_actual_ROS_writer',c.R/'experiments/v1479_retirement_scope_binding/writer_budget.py')
        io=c.load('v1609_original_actual_ROS_boundary',c.R/'experiments/v1479_retirement_scope_binding/bounded_io.py')
        cases=c.load('v1609_new_append_cases',C/'source_cases_new.py');reused=cases.reuse(c)
        coverage=c.load('v1609_new_writer_coverage',C/'writer_coverage.py').coverage(source)
        target=c.O/'source_target';target.mkdir()
        writer=wm.WriterBudget(target,role='ACTUAL_ROS',maximum_bytes=24*1024**2,source_identity=c.digest(source));negative=[]
        def save(path,value):c.put(path,value,maximum=512*1024)
        def refused(name,fn):
            try:fn()
            except(AssertionError,KeyError,ValueError,RuntimeError,OSError,TypeError)as error:
                negative.append(dict(name=name,error=repr(error)));save(target/('REFUSAL_'+name+'.json'),negative[-1]);return
            raise AssertionError('APPEND_NEGATIVE_ACCEPTED:'+name)
        with io.OutputBoundary(target,writer.reserve):
            outcome=cases.run(c,source,target,save,refused)
            barrier=c.load('v1609_previous_round_barrier',C/'round_barrier.py').before_next(parent,current_round=C.name)
            assert 'v1603_capture_close_source'in barrier['reviewed_new_authority_rounds']
            save(target/'QUALIFICATION.json',dict(passed=True,source_only=True,software_and_saved_bytes=True,
                outcome=outcome,source_reuse=reused,negative_cases=negative,writer_coverage=coverage,
                previous_round_barrier=barrier,models=0,actual_runtime_qualified=False))
        assert all(c.sha(c.R/n)==h for n,h in source.items())
        c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),source_only=True,
            models_authorized=False,complete_actual_source_target_passed=True,actual_runtime_qualified=False,whole_route_passed=False),maximum=4*1024**2)
        result.update(passed=True,complete_actual_source_target_passed=True,source_gates=dict(prior['source_gates'],stopped_history_preparation=True,one_current_source_refresh=True,closure_grant_before_metadata=True),
            writer_source_coverage={k:v['source_hook_coverage_qualified']for k,v in coverage.items()},
            outcome=outcome,source_members=len(source),negative_cases=len(negative),writer_charged_bytes=writer._read()['charged_bytes'],
            resources=resources,old_suites_reused_not_rerun=True)
    except BaseException as error:
        result.update(first_error=repr(error),traceback=traceback.format_exc())
        if 'source'in locals():c.put(c.O/'FAILED_SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False),maximum=4*1024**2)
    finally:
        sys.setprofile(None);sys.meta_path.remove(finder);result.update(closed=True,wall_s=time.monotonic()-start)
        c.put(c.O/'ENTRY_QUALIFICATION.json',result);lock.close()
    print(json.dumps({k:result.get(k)for k in ['passed','closed','first_error','models','physical_native']}))
    return 0 if result['passed']else 1

if __name__=='__main__':raise SystemExit(main())
