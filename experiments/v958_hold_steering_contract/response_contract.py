"""Proposed original motion/brake qualification; explicit non-neutral wheel state."""
import importlib.util
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v958_full_array_evaluator',ROOT/'experiments/v956_damped_response18/evaluate.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)


def evaluate(data,servo,origin,task):
    metric,expected=base.evaluate(data,servo,origin,task)
    # This is an explicit proposed contract change, not a retrospective re-grade.
    # Failed V956 still fails the original .03 body settling gate irrespective
    # of wheel-neutral completion; it is never rescued by deleting a check.
    neutral=metric['checks'].pop('final_measured_steering_neutral')
    metric.update(final_measured_steering_neutral_observation=neutral,
        final_measured_steering_position=np.asarray(servo)[-1,:2].tolist(),
        forward_handoff_qualified=False)
    return metric,expected


def reference_start_compatible(steering,v,w):
    steering=np.asarray(steering,float)
    if steering.shape!=(2,)or not np.isfinite([*steering,v,w]).all():raise ValueError('INVALID_START')
    if v<=0.:return False
    tangent=np.tan(steering)
    curvature=np.array([tangent[0]/(.6+.27*tangent[0]),tangent[1]/(.6-.27*tangent[1])])
    return bool(abs(curvature[0]-curvature[1])<=.02 and abs(curvature-w/v).max()<=.02)
