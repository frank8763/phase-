"""Actual component certificates and one old t0 schema, zero models."""
import ast,importlib.abc,json,shutil,subprocess,sys
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];own=repo/'experiments/v820_tracked_norm_global'
root=repo/'runs/v820_zero_model_interfaces_02';root.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
for p in own.glob('*.py'):ast.parse(p.read_text())
pair=repo/'runs/v812_soft_global_reference/main_slot01/paired'
view=root/'component_certificate_view';view.mkdir();(view/'geometry_memory').mkdir();(view/'geometry_memory/ordinary_certificates').mkdir()
for n in ['STATIC_PROTOCOL.json','DYNAMIC_PROTOCOL.json']:shutil.copy2(pair/n,view/n)
dump(view/'AUDIT_VIEW_ONLY.json',dict(not_new_navigation=True,source='V819 actual fixed native complete certificates',models=0,integrations=0))
dump(view/'TRACKED_NORM_CONTRACT.json',dict(source='PUBLIC_DECLARED_COURSE',norm_speed_m_s=.08,original_broader_axis_motion_class_claimed=False,threshold_m=.155,native_ticks=328,hidden_world_geometry_used=False))
entries=read(repo/'experiments/v817_tracked_norm_qualification/FIXED_INPUTS.json')
(view/'geometry_memory/motion_estimate.jsonl').write_text(''.join(json.dumps(dict(step=e['step'],**e['state']))+'\n'for e in entries))
for e in entries:
    step=e['step'];z=np.load(repo/f'runs/v819_tracked_norm_native_entry/step{step:04d}/CERTIFICATE.npz')
    np.savez_compressed(view/f'geometry_memory/ordinary_certificates/certificate_{step:04d}.npz',prefix_poses=z['poses'][:8],poses=z['poses'][8:],minimum_causal_clearance=z['causal_values'].min())
def run(script,args,log):
    p=subprocess.run([sys.executable,'-B',str(own/script),*map(str,args)],capture_output=True,text=True,timeout=90)
    (root/log).write_text(p.stdout+p.stderr);assert p.returncode==0,(script,p.stdout[-1200:],p.stderr[-1200:])
run('audit_tracked_norm.py',[view],'actual_component_certificate_adapter.console')
pre=read(repo/'runs/v812_soft_global_reference/development01/PREFLIGHTS.json')[:1]
dump(root/'PREFLIGHTS.json',pre);run('audit_field_preflight.py',[root],'one_original_t0_count_and_noise.console')
out=dict(status='NATIVE_COMPONENT_CERTIFICATE_AND_ONE_TASK_AUDIT_INTERFACES_PASS',component_certificates=2,
    source_component_audit=read(repo/'runs/v819_tracked_norm_native_entry/FINAL_INDEPENDENT_AUDIT.json')['status'],
    norm_audit=read(view/'TRACKED_NORM_INDEPENDENT_AUDIT.json')['status'],one_t0_schema=read(root/'PREFLIGHT_INDEPENDENT_AUDIT.json')['status'],models=0,integrations=0,
    no_old_trajectory_relabeled=True)
dump(root/'RESULT.json',out);print(json.dumps(out))
