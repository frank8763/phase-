"""Causal temporal admission of one frozen course proposal after normal search."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys,time
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path.insert(0,str(C))
import ew_retained_parallel as base
assert Path(base.__file__).resolve()==C/'ew_retained_parallel.py','WRONG_PARALLEL_SOURCE_BINDING'
q=base.q;np=base.np
def read_bank():
    path=C/'PROPOSAL.json';record=json.loads(path.read_text());assert record['scope']=='exposed_EW_course_control_proposal_not_certificate'
    assert record['delta_second']in[-200,-250,-300]and len(record['parameters'])==4
    return record
def generate(x,table,load,deadline,checkpoint=lambda _:None):
    retained=base.generate(x,table,load,deadline,checkpoint)
    if retained['passed']:return retained
    assert len(retained['parallel_results'])==6 and all(a['error']is None and not a['partial_unknown']for a in retained['parallel_results']),'ONLY_COMPLETE_NORMAL_REFUSAL_ALLOWS_TIME_WINDOWS'
    assert time.monotonic()<deadline-10,'TIME_WINDOW_RESERVE'
    bank=read_bank();origin=base.live.component.entry.bind_current(x,x['packet'],load);g=q.Geometry(x,table)
    rows0=base.schedule(base.groups_of(),bank['delta_second'],bank['parameters'])
    target=np.r_[np.asarray(x['goal'])+np.asarray(bank['target_offset_xy']),bank['target_yaw']]
    proposal=copy.deepcopy(x);proposal['safe_terminal_pose']=target.tolist()
    engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);records=[];selected=None;rank=None
    for wait in range(0,2000,50):
        assert time.monotonic()<deadline,'TIME_WINDOW_ROOT_DEADLINE'
        rows=([(0.,0.,wait,0)]if wait else[])+rows0;ss,uu,mm=engine.simulate(origin,rows)
        proof,_=g.final(proposal,ss,uu,rows);env,cycle=base.reserves(g,ss,rows)
        checks=dict(proof['checks']);checks.update(complete_memory=bool(mm.shape==(len(ss),5)and np.array_equal(mm[1:,:4],uu)),extra22mm=proof['minimum_raw_m']>=q.REQUIRED+.022,park_response_reserve=min(env)>=q.REQUIRED+base.RESPONSE,terminal_response_reserve=cycle>=q.REQUIRED+base.RESPONSE)
        passed=bool(all(checks.values()));slack=float(min(proof['minimum_raw_m']-(q.REQUIRED+.022),min(env)-(q.REQUIRED+base.RESPONSE),cycle-(q.REQUIRED+base.RESPONSE)))
        record=dict(wait_native=wait,passed=passed,checks=checks,minimum_raw_m=proof['minimum_raw_m'],mode_envelopes=env,terminal_cycle_m=cycle,selection_slack_m=slack)
        records.append(record)
        if passed and(rank is None or(-slack,wait)<rank):
            rank=(-slack,wait);proof['checks']=checks;proof['passed']=True
            selected=dict(passed=True,rows=rows,states=ss,controls=uu,memory=mm,proof=proof,input=proposal,origin=origin,initial_load=load,wait_native=wait,
                candidate_kind='causal_time_window_reserved_goal',parameters=bank['parameters'],delta_second=bank['delta_second'],terminal_target=target.tolist(),response_reserve_m=base.RESPONSE,
                selection_slack_m=slack,proposal_sha256=hashlib.sha256((C/'PROPOSAL.json').read_bytes()).hexdigest())
    summary=dict(time_window_trials=records,normal_search_refusal=retained,analytical_cpp_native=retained['analytical_cpp_native']+engine.native,
        selection_rule='largest_complete_reserve_slack_then_shortest_wait',physical_eligible=False)
    checkpoint(dict(stage='causal_time_window_complete',passing=len([a for a in records if a['passed']]),selected_wait_native=selected['wait_native']if selected else None,cpp_native=summary['analytical_cpp_native']))
    if selected is None:return dict(summary,passed=False)
    selected.update(summary);return selected
