"""Full saved sensor-chain evaluation, truth only checked outside policy."""
import gzip
import json
import math
from pathlib import Path
import numpy as np
from causal_occupancy import CausalBall

R=Path(__file__).resolve().parents[2];O=R/'runs/v1342_dynamic_relay_preparation'


def main():
    p=R/'runs/v858_nav2_verified/v1341/rpp_default_dynamic_main'
    setup=json.loads((p/'physics/SETUP.json').read_text());known=setup['known'];actor=setup['actor']
    with gzip.open(p/'physics/SENSORS.json.gz','rt') as stream:scans=json.load(stream)
    tracker=CausalBall(known);errors=[];coverage=[]
    for scan in scans:
        before=len(tracker.records)
        tracker.update(native_tick=scan['native_tick'],sim_time=scan['time'],center_body=[*scan['xy'],scan['yaw']],ranges=scan['ranges'])
        if len(tracker.records)==before:continue
        # This evaluator has the hidden configuration; tracker receives none.
        true=np.array(actor['anchor_xy'])+np.array(actor['axis_xy'])*actor['amplitude_m']*math.sin(actor['omega_rad_s']*scan['time']+actor['phase_rad'])
        errors.append(float(np.linalg.norm(true-tracker.center)))
        for dt in np.linspace(0,tracker.horizon,31):
            future=np.array(actor['anchor_xy'])+np.array(actor['axis_xy'])*actor['amplitude_m']*math.sin(actor['omega_rad_s']*(scan['time']+dt)+actor['phase_rad'])
            center,radius=tracker.occupied_ball(scan['time']);coverage.append(float(np.linalg.norm(future-center))+.1<=radius+1e-8)
    assert errors and max(errors)<=.24 and all(coverage)
    # No-return cannot erase the observed actor; uncertainty grows with age.
    center,r1=tracker.occupied_ball(tracker.last);_,r2=tracker.occupied_ball(tracker.last+3.)
    assert abs(r2-r1-.24)<1e-10
    empty=CausalBall(known);assert empty.occupied_ball(0.) is None
    result=dict(passed=True,causal_updates=len(errors),maximum_observed_surface_to_true_center_m=max(errors),future_evaluator_checks=len(coverage),future_coverage_all=True,no_missing_return_deletes_track=True,truth_inputs_to_policy=False,whole_navigation_qualified=False,models=0,physical_native=0)
    (O/'CAUSAL_OCCUPANCY_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
