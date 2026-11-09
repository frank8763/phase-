"""Read-only diagnosis of the actual V953 failure; no counterfactual physics."""
import ast
import hashlib
import importlib.abc
import json
import sys
from pathlib import Path
import numpy as np


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','torch','factory','vehicle','physical'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoModel())
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runs/v954_stop_align_closure';OUT.mkdir(exist_ok=True)
CASE=ROOT/'runs/v858_nav2_verified/v953/response_01'
with np.load(CASE/'BODY_AND_STEERING.npz') as data:
    body=data['body'];steering=data['steering'];phases=data['phases']
with np.load(CASE/'physics/NATIVE_TRACE.npz') as data:
    setup=json.loads((CASE/'physics/SETUP.json').read_text())
    ctrl=data['ctrl'][:,setup['actuator_ids']]
commands=np.asarray(json.loads((CASE/'physics/BODY_COMMANDS.json').read_text()),float)
active=np.flatnonzero(phases=='ALIGNING')
events=[]
for i in active:
    events.append(dict(tick=int(i),phase_before=str(phases[i-1]),phase_after=str(phases[i+1]),
        measured_v_before=float(commands[i,3]),measured_w_before=float(commands[i,4]),
        measured_v_next=float(commands[i+1,3]),measured_w_next=float(commands[i+1,4]),
        steering_command_before=ctrl[i-1,:2].tolist(),steering_command_after=ctrl[i,:2].tolist(),
        steering_encoder_after=steering[i,:2].tolist()))

# Execute the original frozen handoff array-expression itself, with model imports
# blocked. It is unreachable after case1 failed, but preparation must report it.
worker=ROOT/'experiments/v953_stop_align_components/worker.py'
source=worker.read_text();tree=ast.parse(source)
expression=next(node for node in ast.walk(tree) if isinstance(node,ast.Assign) and
    any(isinstance(t,ast.Name) and t.id=='expected' for t in node.targets) and
    isinstance(node.value,ast.Subscript))
error=None
try:
    exec(compile(ast.fix_missing_locations(ast.Module(body=[expression],type_ignores=[])),str(worker),'exec'),
         dict(np=np,origin=np.zeros(5),t=np.arange(1,201)*.01,math=__import__('math')))
except ValueError as exception:error=str(exception)
assert error is not None,'EXPECTED_FROZEN_HANDOFF_ARRAY_LENGTH_DEFECT'

checks=dict(
    real_case_failed_only_final_alignment=not json.loads((CASE/'QUALIFICATION.json').read_text())['checks']['final_measured_steering_neutral'],
    nine_alignment_ticks=len(active)==9,
    every_alignment_one_tick=all(phases[i-1]=='BRAKING' and phases[i+1]=='BRAKING' for i in active),
    every_next_yaw_breaks_internal_gate=all(abs(commands[i+1,4])>.005 for i in active),
    every_entry_satisfies_internal_gate=all(max(abs(commands[i,3:5]))<=.005 for i in active),
    original_body_settle_gate_still_passes=float(abs(body[269:,3:5]).max())<=.03,
    original_encoder_failure_reproduced=float(abs(steering[-1,:2]).max())>.01,
    latent_handoff_array_length_failure_reproduced=error is not None)
assert all(checks.values())
result=dict(diagnosis_verified=True,component_passed=False,checks=checks,
    observed_chain='Measured stop enters ALIGNING; a steering slew step coincides with body yaw crossing internal .005rad/s gate; next tick re-locks steering and resets ten-tick gate. All nine episodes are one tick. This identifies the interlock liveness failure on the actual trace, not a counterfactual physical guarantee.',
    alignment_ticks=active.tolist(),events=events,
    commanded_right_steering_at_brake_rad=float(ctrl[199,1]),
    final_commanded_steering_rad=ctrl[-1,:2].tolist(),
    final_measured_steering_rad=steering[-1,:2].tolist(),
    final_measured_steering_velocity_rad_s=steering[-1,2:].tolist(),
    cumulative_alignment_time_s=float(len(active)*.01),
    body_after_half_second_max_speed_or_yaw=float(abs(body[269:,3:5]).max()),
    maximum_abs_yaw_during_straight_warmup_rad_s=float(abs(body[:200,4]).max()),
    moving_controller_warning='Straight warmup already has nonzero oscillatory steering under the unchanged yaw-feedback adapter. Stop-phase repair alone does not establish a stable moving controller.',
    hypotheses=dict(encoder_recording_error='Rejected by exact native joint reconstruction in independent audit.',
        missing_steering_actuation='Rejected: encoder motion follows each recorded steering command change; no claim of calibrated servo dynamics.',
        stop_alignment_chattering='Supported by all nine exact transitions and original controller reconstruction.'),
    latent_unexecuted_handoff_defect=dict(source=str(worker.relative_to(ROOT)),source_sha256=hashlib.sha256(worker.read_bytes()).hexdigest(),
        source_line=expression.lineno,position_samples=200,heading_samples=1200,error=error,
        evaluated_actual_slice='data[400:600]',required_actual_slice='data[400:1600]',
        physically_executed=False,old_30_preparation_checks_did_not_cover_composed_array_expression=True),
    next_design_requirements=['Qualify complete moving yaw/steering response rather than stop phase alone.',
        'Use a bounded continuous alignment phase with explicit body displacement/yaw envelope and encoder completion; validate without relaxing original physical gates.',
        'Run the exact full 1200-sample handoff evaluation with model imports blocked before any new physical authority.'],
    new_models=0,new_integrations=0,new_physical_authority=False)
(OUT/'FAILURE_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in {'events','hypotheses','next_design_requirements'}},indent=2))
