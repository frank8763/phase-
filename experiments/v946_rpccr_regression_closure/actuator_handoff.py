"""Array-only exact adapter replay and stopped-body/steering-state counterexample.

This does not replay or initialize a vehicle model. Counterfactual controller
outputs below are not counterfactual physical trajectories or repaired arrival.
"""
import importlib.abc
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'runs/v858_nav2_verified/v945/main_we'
OUT=ROOT/'runs/v946_rpccr_regression_closure'


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','factory','physical','vehicle'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel())
sys.path.insert(0,str(ROOT/'experiments/v856_nav2_foundation'))
from vehicle_control import Adapter


def main():
    setup=json.loads((RAW/'physics/SETUP.json').read_text())
    limits=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])

    def adapter(last=None):
        # Exact recorded CommandMap limits; skip only the forbidden model constructor.
        m=Adapter.__new__(Adapter)
        m.dt=.01;m.last=np.zeros(4)if last is None else np.asarray(last).copy();m.integral=0.
        m.wheelbase=.60;m.track=.54;m.radius=.12;m.center_limit=.42722137342572125
        m.max_curvature=np.tan(m.center_limit)/m.wheelbase
        m.commands=SimpleNamespace(lower=limits[:,0],upper=limits[:,1],rate=rates*.08,
            legal=lambda x:bool(np.all(x>=limits[:,0])and np.all(x<=limits[:,1])))
        return m

    commands=json.loads((RAW/'physics/BODY_COMMANDS.json').read_text())
    with np.load(RAW/'physics/NATIVE_TRACE.npz')as trace:
        recorded=trace['ctrl'][:,setup['actuator_ids']].copy()
    m=adapter();maximum=0.
    for i,(_,v,w,mv,mw,stale)in enumerate(commands):
        maximum=max(maximum,float(np.max(abs(m.compute(v,w,mv,mw,stale)-recorded[i]))))
    assert maximum<=1e-8,'ACTUAL_ADAPTER_REPLAY_MISMATCH'
    row=json.loads((RAW/'RECOVERY_CORRIDORS.json').read_text())[0]
    tick=row['install_packet']['native_tick'];act=recorded[tick-1]
    m=adapter(act)
    for _ in range(1000):m.compute(0.,0.,0.,0.)
    held=m.last.copy()
    a=adapter(act).compute(.1,0.,0.,0.)
    b=adapter(np.zeros(4)).compute(.1,0.,0.,0.)
    ending=row['end_packet']['native_tick']
    segment=recorded[tick-1:ending,0]
    signs=np.where(segment>.3,1,np.where(segment<-.3,-1,0))
    nonzero=signs[signs!=0]
    transitions=int(np.count_nonzero(nonzero[1:]!=nonzero[:-1]))
    checks=dict(exact_actual_actuator_control_reconstructed=maximum<=1e-8,
                original_body_stopped_gate_passed=max(abs(row['install_packet']['body'][3]),abs(row['install_packet']['body'][4]))<=.03,
                stopped_body_does_not_imply_neutral_steering=float(np.max(abs(act[:2])))>.5,
                longer_zero_twist_wait_never_centers_steering=np.array_equal(held[:2],act[:2]),
                same_body_twist_different_servo_state_has_different_initial_control=not np.array_equal(a,b),
                mechanical_slew_limit_preserved=bool(np.all(abs(a-act)<=rates*.01+1e-12)))
    result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,
                exact_reconstructed_native_control_rows=len(commands),maximum_actuator_reconstruction_error=maximum,
                actual_install_tick=tick,actual_install_steering_commands_rad=act[:2].tolist(),
                synthetic_10s_zero_twist_final_steering_commands_rad=held[:2].tolist(),
                synthetic_identical_straight_twist_output_from_actual_servo_state=a.tolist(),
                synthetic_identical_straight_twist_output_from_neutral_servo_state=b.tolist(),
                optimistic_minimum_servo_neutralization_s=float(np.max(abs(act[:2])/rates[:2])),
                large_left_steering_sign_transitions_in_recovery=transitions,
                steering_saturation_limit_rad=.52,alignment_alone_not_proven_sufficient=True,
                persistent_feedback_note='Actual steering commands repeatedly switch near both limits during the straight recovery. Adapter adds1.5*(wanted_yaw_rate-measured_yaw_rate) before curvature clipping and slew. Feedback/lag causality requires a controlled response qualification, not another tuned full-route retry.',
                next_mechanism='Recovery handoff must include actual steering state and a legal zero-drive servo-alignment phase, or generate a slew-compatible initial reference. Merely waiting with the existing zero Twist cannot align it.',
                limits=['Exact actual command reconstruction, not a new dynamics replay.',
                        'No unobserved future or obstacle truth used online.',
                        'Neutralization timing is an actuator-rate lower bound, not measured settling time.',
                        'New alignment command and full-body safety qualification not yet implemented or physically tested.'])
    (OUT/'ACTUATOR_HANDOFF.json').write_text(json.dumps(result,indent=2)+'\n')
    (ROOT/'records/nav2_v945_20261109/ACTUATOR_HANDOFF.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));assert result['passed']


if __name__=='__main__':main()
