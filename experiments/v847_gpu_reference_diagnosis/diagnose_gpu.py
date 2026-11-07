"""Observe original V846 failure before its unchanged assertion; one new bounded diagnosis."""
import hashlib
import json
import os
from pathlib import Path
import sys

REPO=Path(__file__).resolve().parents[2]
OWN=Path(__file__).resolve().parent
ROOT=REPO/'runs/v847_gpu_reference_diagnosis'
OLD=REPO/'experiments/v846_parallel_backend_qualification/benchmark.py'
frozen=json.loads((OWN/'FREEZE.json').read_text())
assert all(hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h for p,h in frozen['files'].items())
original=OLD.read_text();source=original;changes=[]
def replace(before,after):
    global source
    assert source.count(before)==1,('DIAG_PATCH_NOT_UNIQUE',before)
    source=source.replace(before,after);changes.append((before,after))
replace("ROOT = REPO / 'runs/v846_parallel_backend_qualification'","ROOT = REPO / 'runs/v847_gpu_reference_diagnosis'")
replace("sys.path.insert(0, str(ROOT / 'deps'))","sys.path.insert(0, str(REPO / 'runs/v846_parallel_backend_qualification/deps'))")
replace("wp.config.kernel_cache_dir = str(ROOT / 'warp_cache')","wp.config.kernel_cache_dir = str(REPO / 'runs/v846_parallel_backend_qualification/warp_cache')")
replace('for nworld in [64,128]:','for nworld in [64]:')
replace("                data.ctrl.assign(command)","                data.ctrl.assign(command)\n                initial_qpos=data.qpos.numpy();initial_qvel=data.qvel.numpy();initial_ctrl=data.ctrl.numpy()\n                np.savez_compressed(ROOT/'INITIAL_64.npz',qpos=initial_qpos,qvel=initial_qvel,ctrl=initial_ctrl)")
anchor="                assert same<=1e-6 and different>1e-6,'PARALLEL_WORLD_IDENTITY_OR_ISOLATION_FAILURE'"
before_assert="""                np.savez_compressed(ROOT/'BEFORE_ORIGINAL_ASSERT_64.npz',qpos=qpos,qvel=qvel,ctrl=command,nefc=nefc,nacon=nacon,latency_ms=np.asarray(samples))
                save('GPU_FAILURE_WITNESS.json',dict(original_assert_same_passed=same<=1e-6,original_assert_different_passed=different>1e-6,
                    same_full_qpos_difference=same,different_full_qpos_difference=different,
                    same_root_xy_difference=float(np.max(abs(qpos[0,:2]-qpos[6,:2]))),
                    same_root_quaternion_difference=float(np.max(abs(qpos[0,3:7]-qpos[6,3:7]))),
                    same_joint_qpos_difference=float(np.max(abs(qpos[0,7:]-qpos[6,7:]))),
                    same_initial_qpos_difference=float(np.max(abs(initial_qpos[0]-initial_qpos[6]))),
                    same_initial_qvel_difference=float(np.max(abs(initial_qvel[0]-initial_qvel[6]))),
                    same_actual_ctrl_difference=float(np.max(abs(initial_ctrl[0]-initial_ctrl[6]))),
                    maximum_constraints=int(np.max(nefc)),total_contacts=int(np.max(nacon)),
                    nworld=nworld,world_steps_per_second=nworld*512/(sum(samples)/1000.),
                    latency_ms=dict(p50=float(np.percentile(samples,50)),p95=float(np.percentile(samples,95)),maximum=max(samples)),
                    current_counts=dict(counts),old_assertion_unchanged=True))
"""
replace(anchor,before_assert+anchor)
restored=source
for before,after in reversed(changes):restored=restored.replace(after,before)
assert restored==original,'DIAG_CHANGED_PHYSICS_OR_ORIGINAL_ASSERTION'
ROOT.mkdir(exist_ok=True)
(ROOT/'SOURCE_PATCH_RECORD.json').write_text(json.dumps(dict(original_sha256=hashlib.sha256(OLD.read_bytes()).hexdigest(),patches=changes,
    reversible=True,original_assert_preserved=True,physical_changes=0),indent=2)+'\n')
namespace=dict(__name__='v847_gpu_diagnostic',__file__=str(OLD))
exec(compile(source,str(OLD),'exec'),namespace)
namespace['main']()
