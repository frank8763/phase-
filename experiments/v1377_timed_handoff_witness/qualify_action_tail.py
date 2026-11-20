"""Tail off-by-one rejection on metadata; raw original audits stay unchanged."""
import copy
import math
import os
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from snapshot_diagnostic import R,O,read,sha,json
from response_membership_contract import audit,rear
from action_tail_contract import audit_with_actions


def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    begin=time.monotonic();frozen=read(O/'ACTION_TAIL_SOURCE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in frozen.items())
    raw=R/'runs/v858_nav2_verified/v1378/steering_response';rows=read(raw/'APPLIED_JOURNAL.json')[32210:];final=read(raw/'FINAL_PACKET.json')
    samples=[dict(native_tick=r['before_native'],sim_time=r['before_native']*.01,relative_time_s=(r['before_native']-32210)*.01,body=r['body'],ctrl=r['last_ctrl'],steering_velocity=r['encoders'][2:],command=r['request'][:2]) for r in rows]
    samples.append(dict(native_tick=32600,sim_time=final['sim_time'],relative_time_s=3.9,body=final['body'],ctrl=final['controller_memory']['last_ctrl'],steering_velocity=final['steering']['velocity'],command=[0.,0.]))
    fixed=rear(rows[0]['body']);reference=[dict(relative_time_s=r['relative_time_s'],rear=fixed) for r in samples]
    actions=[dict(before_native=r['before_native'],request=r['request'][:2],applied=r['applied']) for r in rows]
    args=dict(origin_tick=32210,source_tick=32200,evidence_kind='ACTUAL_SAVED_PREPARATION',stage='PREPARATION')
    good=audit_with_actions(samples,reference,actions,**args)
    assert len(actions)==390 and all(r['phase']=='COMPLETE_STOP_TAIL' for r in rows[-200:])
    # Preserve explicit source-level counterexample: sample-only checker misses
    # the first of200 actions because its final observation carries command0.
    bad=copy.deepcopy(samples);bad_actions=copy.deepcopy(actions)
    bad[-201]['command']=[-.005,.0025];bad_actions[-200]['request']=[-.005,.0025]
    old=audit(bad,reference,**args);assert old['sample_membership_passed']
    rejected=[]
    try:audit_with_actions(bad,reference,bad_actions,**args)
    except AssertionError as e:assert str(e)=='INCOMPLETE_200_APPLIED_ZERO_ACTIONS';rejected.append('199zero_plus_final_state')
    else:raise AssertionError('199_ZERO_ACTIONS_ACCEPTED')
    for name,change in [('unapplied_tail',lambda a:a[-10].__setitem__('applied',False)),('wrong_action_tick',lambda a:a[-10].__setitem__('before_native',0)),('request_binding',lambda a:a[-10].__setitem__('request',[-.005,.0025]))]:
        changed=copy.deepcopy(actions);change(changed)
        try:audit_with_actions(samples,reference,changed,**args)
        except AssertionError:rejected.append(name)
        else:raise AssertionError('BAD_ACTION_METADATA_ACCEPTED '+name)
    try:audit_with_actions(samples,reference,actions[:-1],**args)
    except AssertionError:rejected.append('missing_transition')
    else:raise AssertionError('MISSING_TRANSITION_ACCEPTED')
    result=dict(passed=True,models=0,physical_native=0,private_native=0,replay_native=0,
        original_saved_preparation=good,original_V1378_actual_tail_still_complete=True,
        sample_only_checker_is_insufficient_for_full_action_tail=True,
        retained_counterexample=dict(source='new response_membership_contract only; not original V1378 physical audit',sample_only_accepted=True,earliest_tail_action_index=len(actions)-200,nonzero_request=[-.005,.0025],qualified_actual_response=False),
        negative_cases=rejected,full_action_wrapper_required=True,
        physical_admission=False,actual_moving_response_qualified=False,
        source_authenticity_contact_control_replay_and_continuous_reserves_still_external=True,
        wall_s=time.monotonic()-begin)
    assert all(sha(R/p)==h for p,h in frozen.items())
    p=O/'ACTION_TAIL_QUALIFICATION.json';assert not p.exists();p.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');assert read(p)==result
    print(json.dumps(dict(passed=True,saved_states=len(samples),saved_applied_transitions=len(actions),actual_zero_tail=200,negative_cases=len(rejected),sample_only_gap_retained=True,models=0,physical_native=0,replay_native=0)))


if __name__=='__main__':main()
