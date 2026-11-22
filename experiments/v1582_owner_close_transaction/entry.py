"""Once new production owner-close/unknown-counter target; no simulation."""
import ast
import copy
import fcntl
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1582_entry_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)


def main():
    start=time.monotonic();resources=c.bootstrap();c.guard()
    lock=(c.R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models_authorized=False),f)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,
        Allocator_recomputations=0,optimizer_calls=0,replay_native=0,
        complete_actual_source_target_passed=False,actual_runtime_qualified=False,whole_route_passed=False)
    def profile(frame,event,arg):
        if event=='call':
            path=Path(frame.f_code.co_filename)
            if path.is_absolute()and path.is_relative_to(c.R):
                assert not(path.name in {'model.py','coupled_model.py','prediction.py','engine.py','coupled_control.py'}and frame.f_code.co_name in {'__init__','step','simulate','compute'}),'SOURCE_MODEL_OR_ALLOCATOR_FORBIDDEN'
                assert frame.f_code.co_name not in {'physical_binding','load_definitions','initial','all_future'},'SOURCE_NUMERICAL_BINDING_FORBIDDEN'
                assert not('gear_handoff.py'in str(path)and frame.f_code.co_name=='select'),'SOURCE_GEAR_FORBIDDEN'
    sys.setprofile(profile)
    try:
        source=c.draft_sources();assert all(c.sha(c.R/n)==h for n,h in source.items())
        closer=c.load('v1582_actual_close_helper',C/'close.py')
        accounting=c.load('v1582_actual_close_counters',C/'accounting.py')
        owner=c.load('v1582_actual_source_supervisor',C/'supervisor.py')
        writers=c.load('v1582_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
        io=c.load('v1582_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
        target=c.O/'source_target';target.mkdir()
        writer=writers.WriterBudget(target,role='PLANNER',maximum_bytes=2*1024**2,source_identity=c.sha(C/'entry.py'))
        cases=[]
        with io.OutputBoundary(target,writer.reserve):
            # These dictionaries are explicit SOFTWARE closure states. They
            # contain no fake physical arrays, sensor packets or certificates.
            for name,fault in [('clean',''),('first_and_secondary','close_native'),
                               ('drain_error','drain'),('logs_error','logs'),
                               ('child_unproven','child'),('lock_busy','lock'),
                               ('review_save_error','review'),('machine_error','machine'),
                               ('prepared_save_error','prepared'),('parent_save_error','parent'),
                               ('final_save_error','final')]:
                folder=target/name;folder.mkdir();events=[];parent_updates=[]
                children={'native':{'closed':False},'ros':{'closed':False}}
                primary={'error':'SOFTWARE_ORIGINAL_FIRST','stage':'ORIGINAL'}if fault else None
                def fail(stage):raise OSError('SOFTWARE_CLOSE_FAILURE:'+stage)
                def close_child(child):
                    child['closed']=True;events.append('child_close')
                    if fault=='close_native'and child is children['native']:fail('close_native')
                def exited(child):return child['closed']and not(fault=='child'and child is children['native'])
                def drain():
                    events.append('drain')
                    if fault=='drain':fail('drain')
                def logs():
                    events.append('logs')
                    if fault=='logs':fail('logs')
                def idle():events.append('lock');return fault!='lock'
                def restore():
                    events.append('restore')
                    if fault=='review':fail('review')
                    (folder/'SOFTWARE_REVIEW').write_bytes(b'SOFTWARE_REVIEW_NOT_ROOT')
                def verify():return(folder/'SOFTWARE_REVIEW').read_bytes()==b'SOFTWARE_REVIEW_NOT_ROOT'
                def machine():
                    if fault=='machine':fail('machine')
                    return dict(actual_native=0,actual_inflight_unknown=False,own_replay_native=0,
                        own_replay_inflight_unknown=False,canonical_vehicle_initializations=0,
                        software_metadata_not_model=True)
                def save(kind,value):
                    if fault==kind.lower():fail(kind)
                    c.put(folder/(kind+'.json'),dict(software_only=True,close=value),maximum=128*1024)
                def parent(snapshot):
                    events.append('parent')
                    if fault=='parent':fail('parent')
                    before=dict(active_round='SOFTWARE_ROUND',active_math_round=None,models_now_authorized=True,
                        scientific_revisions=12,actual_total_native=0,own_replay_native=0,rounds=[{'id':'SOFTWARE_ROUND'}])
                    after,counts=accounting.apply_closed(before,round_id='SOFTWARE_ROUND',machine=snapshot['machine'],
                        result_path='SOFTWARE_RESULT_NOT_PHYSICAL',close_errors=snapshot['errors'])
                    assert after['active_round']is None and after['actual_total_native']==after['own_replay_native']==0
                    c.put(folder/'SOFTWARE_PARENT.json',after);parent_updates.append(after);return True
                closed=closer.close_owner(children=children,close_child=close_child,child_closed=exited,
                    drain=drain,close_logs=logs,read_machine=machine,restore_review=restore,
                    verify_review=verify,verify_lock_idle=idle,save_receipt=save,close_parent=parent,first_error=primary)
                assert events.count('child_close')==2 and 'drain'in events and 'logs'in events
                if primary is not None:assert closed['first_error']==primary
                if fault in {'child','lock'}:
                    assert not closed['close_complete']and not parent_updates and 'restore'not in events
                    assert closed['close_refusals']and not(folder/'SOFTWARE_REVIEW').exists()
                elif fault in {'review','parent','prepared','final'}:
                    assert not closed['close_complete']
                else:assert closed['close_complete']
                if fault=='machine':assert closed['machine']is None and closed['machine_counts_unknown']
                if fault=='review':assert not parent_updates
                if fault in {'close_native','drain','logs','review','machine','prepared','parent','final'}:assert closed['errors']
                c.put(folder/'TARGET_OBSERVED.json',dict(software_only=True,result=closed,events=events),maximum=128*1024)
                cases.append(dict(name=name,primary_preserved=True,close_complete=closed['close_complete'],errors=len(closed['errors'])))
            # Exact-or-unknown counters: absence, bool, negative, cap overflow,
            # and inflight must never become a completed integer or zero.
            for candidate in [None,{}, {'actual_native':True,'actual_inflight_unknown':False},
                              {'actual_native':-1,'actual_inflight_unknown':False},
                              {'actual_native':40001,'actual_inflight_unknown':False},
                              {'actual_native':7,'actual_inflight_unknown':True}]:
                assert accounting.summary(candidate)['actual_native']is None
            known=dict(actual_native=7,actual_inflight_unknown=False,own_replay_native=6,
                own_replay_inflight_unknown=False,canonical_vehicle_initializations=1,
                independent_allocation=dict(allocator_recomputations=7,allocator_recomputation_inflight_unknown=False))
            counters=accounting.summary(known)
            assert counters['actual_native']==7 and counters['own_replay_native']==6
            assert counters['independent_Allocator_recomputations']==7 and counters['internal_factory_model_constructions']is None
            # Import the production owner only; do not invoke launch or any
            # old process/namespace/ROS/model target. Native acceptance stays
            # separate from successful resource cleanup.
            assert owner.runtime_passed(0,{'passed':True,'closed':True},[])is False
            assert owner.runtime_passed(1,None,[])is False
            c.put(target/'QUALIFICATION.json',dict(passed=True,software_only=True,cases=cases,
                new_owner_close_and_accounting_only=True,actual_parent_or_review_touched=False,
                numerical_array_fixtures=0,OS_process_or_ROS_tests_reexecuted=0))
        # No old model/codec/policy source suite: compare unmodified modules
        # by normalized AST, and retain the original frozen qualification SHA.
        reused=[]
        for name in ['tracker.py','carrier.py','witness.py','gates.py','current_reserve.py','reference.py',
                     'actual_sink.py','scoped_output.py','transaction.py','components.py']:
            before=(c.R/'experiments/v1580_bounded_task_handoff'/name).read_text()
            after=(C/name).read_text().replace('v1582_owner_close_transaction','v1580_bounded_task_handoff').replace('v1582','v1580')
            assert ast.dump(ast.parse(before))==ast.dump(ast.parse(after)),name
            reused.append(dict(path=name,prior_sha256=c.sha(c.R/'experiments/v1580_bounded_task_handoff'/name)))
        assert all(c.sha(c.R/n)==h for n,h in source.items())
        c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),source_only=True,
            owner_close_source_qualified=True,models_authorized=False,complete_actual_source_target_passed=False),maximum=4*1024**2)
        result.update(passed=True,source_members=len(source),resources=resources,cases=len(cases),
            writer_charged_bytes=writer._read()['charged_bytes'],source_reuse=reused,
            source_gates=dict(owner_close_first_secondary=True,unknown_counter_accounting=True,
                complete_actual_source_target=False))
    except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None);result.update(closed=True,wall_s=time.monotonic()-start)
        c.put(c.O/'ENTRY_QUALIFICATION.json',result);lock.close()
    print(json.dumps({k:result.get(k)for k in ['passed','closed','first_error','models','physical_native']}))
    return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
