"""Independent scalar reconstruction of recorded dynamic reserve decisions."""
import math


def clearance(body, ball):
    dx, dy = ball[0]-body[0], ball[1]-body[1]
    c, s = math.cos(body[2]), math.sin(body[2])
    a, b = abs(c*dx+s*dy)-.44, abs(-s*dx+c*dy)-.375
    return (max(a,b) if max(a,b) <= 0 else math.hypot(max(a,0.),max(b,0.)))-ball[2]


def reconstruct(body, ball, v, w):
    current = clearance(body, ball)
    if abs(v) <= 1e-10 and abs(w) <= 1e-10:
        return True, current, None
    if current > .25:
        return True, current, None
    rx, ry = body[0]-.3*math.cos(body[2]), body[1]-.3*math.sin(body[2])
    values=[]
    for i in range(11):
        t=i*.05; a=body[2]+w*t
        if abs(w)>1e-10:
            x=rx+v/w*(math.sin(a)-math.sin(body[2]))
            y=ry-v/w*(math.cos(a)-math.cos(body[2]))
        else:
            x=rx+v*t*math.cos(body[2]);y=ry+v*t*math.sin(body[2])
        values.append(clearance([x+.3*math.cos(a),y+.3*math.sin(a),a],ball))
    return current>=.22 and min(values)>=current-1e-8, current, values


def review(events, commands, forecasts, sensors):
    by_seq={r['sequence']:r for r in commands}
    by_tick={r['native_tick']:r for r in forecasts}
    packets={r['native_tick']:r for r in sensors}
    seen=set(); escape=refused=0; error=0.
    for event in events:
        seq=event['command_sequence'];assert seq not in seen,'DUPLICATE_DYNAMIC_DECISION'
        seen.add(seq);sent=by_seq[seq]
        allowed,current,values=reconstruct(event['body'],event['ball'],*event['requested'])
        assert allowed==event['allowed'],'DYNAMIC_DECISION_MISMATCH'
        proof=event['proof'];error=max(error,abs(current-proof['current_dynamic_clearance_m']))
        assert proof['early_intervention_m']==.25 and proof['unchanged_recovery_margin_m']==.22
        assert proof['empirical_monitor_not_stopping_certificate'] is True
        if values is not None:
            error=max(error,abs(min(values)-proof['command_geometry_minimum_m']),abs(values[-1]-proof['command_geometry_terminal_m']))
            assert proof['preview_s']==.5 and proof['preview_samples']==11 and proof['actual_dynamics_certificate'] is False
            escape+=allowed
        forecast=by_tick[event['native_tick']]
        assert forecast['invariant_for_all_future_under_declared_class'] is True
        assert max(abs(a-b) for a,b in zip(event['ball'],[*forecast['center'],forecast['radius_m']]))<1e-10
        packet=packets[event['native_tick']]
        assert max(abs(a-b) for a,b in zip(event['body'][:2],packet['xy']))<1e-8
        assert abs(event['body'][2]-packet['yaw'])<1e-6 and abs(event['sim_time']-packet['time'])<1e-8
        if not allowed:
            refused+=1
            assert sent['v']==sent['w']==0. and sent['source']!='CONTROLLER','REFUSED_DYNAMIC_COMMAND_APPLIED'
        if sent['source']=='CONTROLLER':
            assert allowed and [sent['v'],sent['w']]==event['requested']
    if forecasts:
        first=min(by_tick)
        assert all(row['sequence'] in seen for row in commands if row['source']=='CONTROLLER' and row['observation_native_tick']>=first),'DYNAMIC_COMMAND_COVERAGE_GAP'
    assert error<=1e-8,'DYNAMIC_GEOMETRY_RECONSTRUCTION_ERROR'
    return dict(passed=True,events=len(events),nondecreasing_escape_decisions=escape,refused=refused,
                maximum_geometry_error_m=error,models=0,physical_native=0)
