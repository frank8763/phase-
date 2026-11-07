"""Prepared strict saved-evidence audit; no simulator or ROS imports."""
import json,traceback
from pathlib import Path
from handshake import NODES,require
R=Path(__file__).resolve().parents[2]
def startup_checks(native,ros):
    events=native.get('startup_events',[]);armed=[x for x in events if x['event']=='ARMED_AT_T0']
    a=armed[0]if len(armed)==1 else{}
    return dict(one_arm_exactly_at_zero=len(armed)==1 and a['native_tick']==0,
                all_nodes_active=set(a.get('states',{}))==set(NODES)and all(v==3 for v in a.get('states',{}).values()),
                fresh_proof=set(a.get('checked_at',{}))==set(NODES)and all(-.05<=a['at']-t<=1. for t in a.get('checked_at',{}).values()),
                navigation_action_after_arm=ros.get('navigation_action_sent')is True and native.get('armed_at')is not None and ros.get('goal_sent_at',-1)>=native.get('armed_at',float('inf')),
                command_stream_present=ros.get('cmd_vel_messages',0)>0)
def _audit(task):
    out=Path(task['output']);native=json.loads((out/'RESULT.json').read_text())if(out/'RESULT.json').exists()else{}
    ros=json.loads((out/'ROS_RESULT.json').read_text())if(out/'ROS_RESULT.json').exists()else{}
    if not(out/'physics/NATIVE_TRACE.npz').exists()or native.get('status')!='NATIVE_COMPLETE':
        result=dict(passed=False,evidence_passed=False,functional_passed=False,
                    actual_native=native.get('actual_native'),replay_native=native.get('replay_native'),
                    counts_may_be_unknown=native.get('actual_native')is None,
                    reason='NO_COMPLETE_NATIVE_NAVIGATION_EVIDENCE',native_status=native.get('status'))
    else:
        import sys
        sys.path.insert(0,str(R/'experiments/v858_nav2_verified'))
        from audit_navigation import audit as physical_audit
        result=physical_audit(task)
        checks=startup_checks(native,ros);checks['original_physical_evidence']=result['evidence_passed']
        result.update(startup_checks=checks,evidence_passed=all(checks.values()),passed=all(checks.values())and result['functional_passed'])
    result['scope']='One static WE Nav2 nominal baseline only; not dynamic confirmation or RP-CCR acceptance'
    return result
def audit(task):
    try:result=_audit(task)
    except Exception as e:
        result=dict(passed=False,evidence_passed=False,functional_passed=False,
                    actual_native=None,replay_native=None,counts_may_be_unknown=True,
                    reason='UNREADABLE_OR_INCOMPLETE_EVIDENCE_NO_ZERO_INFERENCE',error=repr(e),traceback=traceback.format_exc())
    (Path(task['output'])/'INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');return result
