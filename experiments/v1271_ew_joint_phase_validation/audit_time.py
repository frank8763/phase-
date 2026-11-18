"""Independent full40 timing recurrence; source generator is never called."""
from audit_chain import *
def verify(x,table,selection):
    if selection['candidate_kind']=='response_reserved_current_goal':
        assert selection['wait_native']==0
        return dict(passed=True,unchanged_success_branch=True,analytical_cpp_native=0)
    assert selection['candidate_kind']=='causal_time_window_reserved_goal'
    import hashlib
    bank=json.loads((C/'PROPOSAL.json').read_text());assert hashlib.sha256((C/'PROPOSAL.json').read_bytes()).hexdigest()==selection['proposal_sha256']
    assert selection['parameters']==bank['parameters']and selection['delta_second']==bank['delta_second']
    assert selection['selection_rule']=='largest_complete_reserve_slack_then_shortest_wait'
    assert not selection['normal_search_refusal']['passed']and len(selection['normal_search_refusal']['parallel_results'])==6
    assert all(a['error']is None and not a['partial_unknown']for a in selection['normal_search_refusal']['parallel_results'])
    wait=selection['wait_native'];rows=selection['rows'];moving_rows=rows[1:]if wait else rows
    if wait:assert rows[0]==[0.,0.,wait,0]
    engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);g=q.Geometry(x,table)
    org=dict(q.initial(x['packet']),steering_load_episode=selection['initial_load']);rho=math.hypot(.44,.375);response=.04+2*rho*math.sin(.035/2)+2e-6
    records=selection['time_window_trials'];assert len(records)==40 and [a['wait_native']for a in records]==list(range(0,2000,50))
    eligible=[]
    for w,saved in zip(range(0,2000,50),records):
        schedule=([[0.,0.,w,0]]if w else[])+moving_rows
        ss,uu,mm=engine.simulate(org,schedule);proof,_=g.final(selection['input'],ss,uu,schedule)
        cursor=0;envelopes=[]
        for t,v,n,mode in schedule:
            if mode:envelopes.append(float(g.cycle(ss[cursor:cursor+1,:3])[0])-.02-rho*.1)
            cursor+=int(n)
        cycle=float(g.cycle(ss[-1:,:3])[0]);minimum=proof['minimum_raw_m']
        okay=proof['passed']and mm.shape==(len(ss),5)and np.array_equal(mm[1:,:4],uu)and minimum>=q.REQUIRED+.022 and min(envelopes)>=q.REQUIRED+response and cycle>=q.REQUIRED+response
        slack=float(min(minimum-(q.REQUIRED+.022),min(envelopes)-(q.REQUIRED+response),cycle-(q.REQUIRED+response)))
        assert bool(okay)==saved['passed']and abs(slack-saved['selection_slack_m'])<=1e-10,'COMPLETE_TIME_WINDOW_RECORD_MISMATCH'
        if okay:eligible.append((-slack,w))
    assert eligible and min(eligible)[1]==wait,'TIME_WINDOW_SELECTION_NOT_FIXED_RULE'
    return dict(passed=True,complete_time_windows=40,passing_windows=len(eligible),selected_wait_native=wait,analytical_cpp_native=engine.native)
