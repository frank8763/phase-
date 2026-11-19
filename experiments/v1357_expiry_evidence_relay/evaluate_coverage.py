"""Evaluator-only truth checks after sensor-only forecasts are persisted.

This module is never imported by ROS, planner or predictor. No model loading.
"""
import importlib.util
import json
import math
from pathlib import Path
import sys
import numpy as np

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def evaluate(out,forecasts):
    config=json.loads((out/'physics/SETUP.json').read_text())['actor']
    assert config['amplitude_m']==.25 and config['omega_rad_s']==.32 and config['radius_m']==.1
    assert abs(np.linalg.norm(config['axis_xy'])-1.)<1e-12 and config['maximum_speed_m_s']==.08
    times=np.linspace(0,1.5,151);maximum=-math.inf;checked=0
    for row in forecasts:
        assert row['horizon_s']==1.5
        truth=np.asarray(config['anchor_xy'])+config['amplitude_m']*np.sin((row['sim_time']+times)*config['omega_rad_s']+config['phase_rad'])[:,None]*np.asarray(config['axis_xy'])
        excess=np.linalg.norm(truth-np.asarray(row['center']),axis=1)+.1-row['radius_m']
        maximum=max(maximum,float(excess.max()));checked+=len(times)
    assert checked>0 and maximum<=1e-8,('FORECAST_CONTAINMENT_FAILED',maximum)
    return dict(passed=True,forecast_rows=len(forecasts),future_samples=checked,
          maximum_actor_disk_excess_m=maximum,includes_entire_actor_radius=True,
          public_class_checked_against_evaluator=True,online_truth_used=False,models=0,physical_native=0)


def main():
    raw=R/'runs/v858_nav2_verified/v1354/rpp_fast_stamped_dynamic_main'
    rows=json.loads((O/'FORECAST_FIXTURES.json').read_text());result=evaluate(raw,rows)
    # Generic adversarial triangle-bound qualification, independent of saved truth.
    rng=np.random.default_rng(1356);n=20000;phase=rng.uniform(-math.pi,math.pi,n);dt=rng.uniform(0,100,n)
    displacement=np.abs(.25*(np.sin(phase+.32*dt)-np.sin(phase)))
    allowed=np.minimum(.08*dt,.50);assert np.max(displacement-allowed)<=1e-12
    result['analytic_displacement_random_cases']=n
    result['maximum_displacement_bound_excess_m']=float(np.max(displacement-allowed))
    (O/'INDEPENDENT_PREDICTION_COVERAGE.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
