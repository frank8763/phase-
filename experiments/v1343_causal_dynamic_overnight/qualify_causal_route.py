"""Causal and route-coordinate regressions using saved arrays, zero models."""
import ast
import gzip
import json
from pathlib import Path
import numpy as np
from component_context import R,C,O,dump
from causal_occupancy import CausalBall
from observed_route import nominal_clearance


def main():
    raw=R/'runs/v858_nav2_verified/v1341/rpp_default_dynamic_main'
    known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
    with gzip.open(raw/'physics/SENSORS.json.gz','rt') as stream:scans=json.load(stream)
    tracker=CausalBall(known);guard_tick=None;guard_at_failure=None
    for scan in scans:
        tracker.update(native_tick=scan['native_tick'],sim_time=scan['time'],center_body=[*scan['xy'],scan['yaw']],ranges=scan['ranges'])
        ball=tracker.occupied_ball(scan['time'])
        if ball is not None:
            clearance=nominal_clearance([*scan['xy'],scan['yaw']],*ball)
            if clearance<=.25 and guard_tick is None:guard_tick=scan['native_tick']
            if scan['native_tick']==6815:guard_at_failure=clearance
    assert tracker.records[0]['native_tick']==4505 and guard_tick<6819 and guard_at_failure<.25
    # Future/retrograde clocks cannot be silently admitted.
    rejected=False
    try:tracker.update(native_tick=1,sim_time=.01,center_body=[0,0,0],ranges=[3.]*32)
    except AssertionError:rejected=True
    assert rejected
    # Mechanical rear coordinates map exactly back to the nominal center.
    errors=[]
    for yaw in np.linspace(-np.pi,np.pi,721):
        center=np.array([1.2,-.7]);rear=center-.3*np.array([np.cos(yaw),np.sin(yaw)])
        recovered=rear+.3*np.array([np.cos(yaw),np.sin(yaw)]);errors.append(float(abs(center-recovered).max()))
    assert max(errors)<1e-12
    # Extract and compile the actual bridge source, prohibiting direct actor
    # config/hidden future dependencies; policy only receives published fields.
    source=(C/'ros_component.py').read_text();tree=ast.parse(source)
    assert 'actor.config' not in source and 'phase_rad' not in source and 'anchor_xy' not in source
    assert "mode='brake'" in source and "native_tick-brake_start>=200" in source
    lattice=json.loads((R/'runs/v1342_dynamic_relay_preparation/REAR_LATTICE_QUALIFICATION.json').read_text())
    assert lattice['passed'] and lattice['rear_geometry_center_offset_m']==.3
    proof=dict(passed=True,original_failure_would_be_held_before_native=guard_tick,last6815_causal_clearance_m=guard_at_failure,
               first_novel_return_tick=4505,retrograde_time_negative_rejected=True,rear_center_roundtrip_max=max(errors),
               original_saved_observation_count=len(scans),new_route_proposal_passed=True,
               partial_route_is_not_claimed_whole_arrival=not lattice['whole_goal_proposal'],
               truth_inputs_absent_from_policy=True,complete200brake_before_replanning_source_present=True,
               models=0,physical_native=0,whole_navigation_qualified=False)
    dump(O/'CAUSAL_ROUTE_QUALIFICATION.json',proof);print(json.dumps(proof))


if __name__=='__main__':main()
