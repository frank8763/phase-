"""Independent saved selection order/objective and admitted native certificates."""
import gzip,json
from pathlib import Path
import numpy as np

def check(cell,event,candidates,protocol,deep=False,source_cell=None):
    cell=Path(cell);source=cell if source_cell is None else Path(source_cell)
    goal=np.asarray(protocol['goal_xy']);assert np.array_equal(event['public_goal_xy'],goal)
    safe=sorted([c for c in candidates if c['reason']is None],key=lambda c:c['score'],reverse=True)
    unique=[];seen=set()
    for c in safe:
        key=tuple(c['first_command'])
        if key not in seen:seen.add(key);unique.append(c)
    eligible=[];distance=float(np.linalg.norm(np.asarray(event['real_qpos'])[:2]-goal))
    for i,c in enumerate(unique):
        z=np.load(source/'nominal_forecasts'/c['nominal_saved_forecast'])
        gain=distance-float(np.linalg.norm(z['poses'][-1,:2]-goal))
        if np.mean(c['first_command'][2:])>=0. and gain>=.02:eligible.append(i)
    expected=[]
    if eligible:
        indexes=[eligible[0],max(eligible,key=lambda i:(np.mean(unique[i]['first_command'][:2]),-i)),min(eligible,key=lambda i:(np.mean(unique[i]['first_command'][:2]),i)),max(eligible,key=lambda i:(np.mean(unique[i]['first_command'][2:]),-i))]
        expected=list(dict.fromkeys(indexes))
    first=event.get('selection_policy')=='FIRST_FEASIBLE_IN_NOMINAL_ORDER_V848'
    if first:expected=sorted(expected)
    assert expected==event['representative_ranks']and len(expected)<=4 and event['original_unique_commands']==len(unique)
    assert event['hidden_world_geometry_used']is False
    if first:
        assert 0<len(event['probes'])<=len(expected)
        assert [p['rank']for p in event['probes']]==expected[:len(event['probes'])]
        good=[p for p in event['probes']if p['summary']is not None]
        assert (len(good)==1 and good[0]is event['probes'][-1])if event['selected_rank']is not None else(not good and len(event['probes'])==len(expected))
    else:assert len(event['probes'])==len(expected)
    contract=json.loads((source/'ACTUATOR_COMMAND_CONTRACT.json').read_text())
    limits=np.asarray(contract['limits']);rate=np.asarray(contract['rate']);admitted=[]
    for rank,probe in zip(expected,event['probes']):
        assert probe['rank']==rank and np.array_equal(probe['first_command'],unique[rank]['first_command'])and abs(probe['nominal_score']-unique[rank]['score'])<=1e-10
        detail=probe['detail'];assert detail['reference_successor_active']and detail['reference']['path']==event['reference_path']
        cs=detail['candidates'];old=[c for c in cs if c['library']=='ORIGINAL'];forward=[c for c in cs if c['library']=='FORWARD_EXTENSION'];new=[c for c in cs if c['library']=='REFERENCE_FOLLOW']
        if detail['status']=='PREFIX_SELF_DOMAIN_REJECTED':assert detail['prefix_self_domain_margin_m']<.002 and not cs;continue
        assert len(old)in[1,16]and len(forward)==5 and len(new)==18
        for c,(look,wheel,brake)in zip(new,[(l,w,b)for l in[.35,.55]for w in[4.,8.,12.]for b in[160,208,240]]):
            assert c['lookahead_m']==look and c['wheel_speed']==wheel and c['brake_after_native_ticks']==brake
        valid=[c for c in cs if c['reason']is None]
        if probe['summary']is None:assert detail['status']=='NO_APPENDABLE_BACKUP'and not valid and probe['certificate']is None;continue
        assert valid and detail['status']=='APPENDABLE_BACKUP_FOUND'
        with gzip.open(cell/probe['certificate'],'rt')as stream:cache=json.load(stream)
        assert cache['proactive_joint']and cache['reference_following']['path']==event['reference_path']if 'reference_following'in cache else cache['proactive_joint']
        gain=float(np.linalg.norm(np.asarray(cache['prefix_initial_qpos'])[:2]-goal)-np.linalg.norm(np.asarray(cache['qpos'])[-1,:2]-goal))
        value=cache['minimum_causal_predicted_clearance_m']+.5*gain
        assert gain>=.02 and abs(gain-probe['goal_gain_m'])<=1e-10 and abs(value-probe['joint_score'])<=1e-10 and abs(cache['score']-value)<=1e-10
        assert abs(value-max(c['selection_score']for c in valid))<=1e-10
        assert np.array_equal(cache['prefix_command'],unique[rank]['first_command'])and np.array_equal(cache['prefix_initial_qpos'],event['real_qpos'])
        assert cache['minimum_causal_predicted_clearance_m']>=.155 and cache['minimum_predicted_self_domain_margin_m']>=.002 and cache['terminal_speed_m_s']<=.025
        if deep:
            from reference_certificate_audit import check_successor,independent_values
            check_successor(cache,protocol,limits,rate)
            for c in valid:
                z=np.load(cell/c['full_forecast_file']);v=independent_values(z['poses'],cache['forecast_state'],protocol)
                progress=distance-float(np.linalg.norm(z['poses'][327,:2]-goal));score=float(v[:328].min()+.5*progress)
                assert v.min()>=.155 and progress>=.02 and abs(score-c['selection_score'])<=1e-8
        admitted.append((value,probe['nominal_score'],-rank,rank))
    selected=(admitted[0][-1]if first else max(admitted,key=lambda x:x[:3])[-1])if admitted else None
    assert event['selected_rank']==selected
    return True
