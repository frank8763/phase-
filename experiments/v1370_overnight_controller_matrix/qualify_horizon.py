"""Finite/all-future audit labels on saved evidence; no prediction or physics."""
import copy
import gzip
from component_context import *
from dynamic_audit import review

def main():
    prior=R/'runs/v858_nav2_verified/v1361/sweep_terminal_dynamic_main'
    events=read(prior/'DYNAMIC_RESERVE_RECORDS.json');commands=read(prior/'ROS_COMMANDS.json');forecasts=read(prior/'FORECAST_RECORDS.json')
    with gzip.open(prior/'physics/SENSORS.json.gz','rt') as f:sensors=json.load(f)
    full=review(events,commands,forecasts,sensors)
    # A saved all-future disk also contains the finite1.5s horizon. Removing
    # that stronger label exercises audit typing only, never an online repair.
    finite=copy.deepcopy(forecasts)
    for item in finite:item.pop('invariant_for_all_future_under_declared_class',None)
    proof=review(events,commands,finite,sensors,forecast_kind='HORIZON');assert full['passed'] and proof['passed']
    for kind in ['short_horizon','false_allfuture']:
        bad=copy.deepcopy(finite)
        if kind=='short_horizon':
            for item in bad:item['horizon_s']=.1
        try:review(events,commands,bad,sensors,forecast_kind='HORIZON' if kind=='short_horizon' else 'NESTED_SWEEP')
        except (AssertionError,KeyError):pass
        else:raise AssertionError('BAD_FORECAST_LABEL_ACCEPTED '+kind)
    dump(O/'HORIZON_AUDIT_QUALIFICATION.json',dict(passed=True,allfuture=full,finite_horizon_type_fixture=proof,negative_cases=2,models=0,physical_native=0,source_evidence_unchanged=True))
    print(json.dumps(dict(passed=True,guard_events=len(events),models=0)))

if __name__=='__main__':main()
