"""Zero-model closure and lossless evidence archive for V844/V845 components."""
import sys


class NoModels:
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):
            raise RuntimeError('COMPONENT_ARCHIVE_FORBIDS_MODELS')


sys.meta_path.insert(0,NoModels())
import fcntl
import hashlib
import json
from pathlib import Path
import zipfile

REPO=Path(__file__).resolve().parents[2]


def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as stream:
        for data in iter(lambda:stream.read(4*1024**2),b''):
            h.update(data)
    return h.hexdigest()


def main():
    roots=[REPO/'runs/v844_gpu_proposal_qualification',REPO/'runs/v845_gpu_native_qualification']
    target=REPO/'evidence/rpccr_gpu_components_v844_v845_20261106'
    assert not target.exists(),'EXISTING_ARCHIVE_NO_OVERWRITE'
    a=json.loads((roots[0]/'QUALIFICATION.json').read_text())
    b=json.loads((roots[1]/'native01/RESULT.json').read_text())
    audit=json.loads((roots[1]/'native01/INDEPENDENT_AUDIT.json').read_text())
    assert a['component_passed']and audit['evidence_passed']
    assert (REPO/'REVIEW_PENDING').read_bytes()==(roots[1]/'REVIEW_PENDING.before').read_bytes()
    with(REPO/'runs/v648_static_unknown/execution.lock').open('rb')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    files={}
    for stage in ['v844_gpu_proposal_qualification','v845_gpu_native_qualification']:
        c=REPO/'experiments'/stage
        freeze=json.loads((c/'FREEZE.json').read_text())
        assert all(sha(REPO/name)==h for name,h in freeze['files'].items())
        for name in freeze['files']:
            files[name]=REPO/name
        for path in c.iterdir():
            if path.is_file():files[str(path.relative_to(REPO))]=path
    for root in roots:
        for path in root.rglob('*'):
            if path.is_file()and path.suffix not in ['.lock','.pyc']and'__pycache__'not in path.parts:
                files[str(path.relative_to(REPO))]=path
    report=REPO/'docs/RPCCR_GPU_COMPONENTS_V844_V845_20261106_REPORT.md'
    math_errors=[max(row['maximum_pose_error'],row['maximum_control_error'],row['maximum_cost_error'])for row in a['details']]
    safe=sum(all(x['checks'][k]for k in ['causal_clearance','full_self','terminal328','terminal336','amplitude_slew'])for row in b['records']for x in row['candidates'])
    summary=dict(gpu_proposal_component_passed=True,gpu_p95_ms=[x['end_to_end']['p95_ms']for x in a['details']],
        maximum_numpy_formula_error=max(math_errors),gpu_peak_allocator_bytes=a['peak_allocator_bytes'],
        native_fixed_states=4,native_candidate_sequences=16,original_safety_gate_passed_sequences=safe,
        candidates_meeting_all_native_and_progress_gates=0,
        candidates_meeting_first8_progress_gate_only=sum(x['checks']['positive_first_public']for row in b['records']for x in row['candidates']),
        all_states_native_development_passed=False,
        native_compute_ms=[x['native_computation_ms']for x in b['records']],
        maximum_ideal_native_xy_error_m=max(x['maximum_ideal_native_xy_error_m']for row in b['records']for x in row['candidates']),
        counts=b['counts'],model_initializations=None,approximate_gpu_counted_steps=a['counted_ideal_proposal_steps'],
        approximate_setup_work=a['additional_setup_ideal_model_work'],full_closed_loop_realtime_passed=False,
        dynamic_acceptance_passed=False,new_policy_trained=False,source_unchanged=True)
    report.write_text('# V844 GPU提案与V845原生资格实际结果\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\nGPU提案512条/42公开段，四例数学和20ms p95门通过；仅为理想模型计算，非完整车模。原生16尾中8条原安全门合格，另8条净空不足；原安全合格的8条均不满足新增首8原生目标增益>=.001的开发资格，不能将它们称为安全失败。全部16末速、自体和控制幅值/速率过门、整尾目标进展为正。无实际分支接管/新导航/确认/训练，旧9584原生重放误差0，5376私有。新增673半步规划查询包括原329/657子集，不是新增实际积分或连续时间保证。候选未达到资格即停止该批，无改阈值/增加候选/重跑。\n\n四候选原生认证150.5–171.5ms，端到端GPU与CPU实联闭环延迟未测，不称80ms实时通过。GPU理想/原生位置偏差最大.677m，直接移植便宜运动模型不够。两个阶段原冻结SHA与原始来源、零模型独立公式回读保留；后端并行物理测试另立协议，不混本批成功。\n')
    files[str(report.relative_to(REPO))]=report
    for name in ['docs/RPCCR_REALTIME_AND_PAPER_RECOVERY_20261106.md','docs/RPCCR_GPU_PARALLEL_TRAINING_20261106_PLAN.md']:
        files[name]=REPO/name
    target.mkdir()
    inventory=[]
    archive=target/'RAW.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True)as z:
        for name,path in sorted(files.items()):
            h=sha(path);z.write(path,name);inventory.append(dict(path=name,bytes=path.stat().st_size,sha256=h))
    with zipfile.ZipFile(archive)as z:
        for row in inventory:
            h=hashlib.sha256();size=0
            with z.open(row['path'])as stream:
                for block in iter(lambda:stream.read(4*1024**2),b''):h.update(block);size+=len(block)
            assert h.hexdigest()==row['sha256']and size==row['bytes']and sha(files[row['path']])==row['sha256']
    manifest=dict(status='ALL_SOURCE_AND_DECOMPRESSED_SHA_VERIFIED',inventory=inventory,
                  zip_bytes=archive.stat().st_size,zip_sha256=sha(archive),raw_deleted=False,
                  models_in_finalizer=0,integrations_in_finalizer=0)
    if archive.stat().st_size>90*1024**2:
        parts=[];recombined=hashlib.sha256()
        with archive.open('rb')as stream:
            for index,block in enumerate(iter(lambda:stream.read(32*1024**2),b'')):
                part=target/f'RAW.zip.part{index:03d}';part.write_bytes(block);recombined.update(part.read_bytes())
                parts.append(dict(path=part.name,bytes=len(block),sha256=sha(part)))
        assert recombined.hexdigest()==sha(archive)
        manifest.update(parts=parts,recombined_sha_verified=True)
    (target/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    output=dict(status='COMPONENTS_CLOSED_GPU_MATH_PASS_NATIVE_DEVELOPMENT_NOT_PASSED',
                report=str(report.relative_to(REPO)),archive=str(target.relative_to(REPO)),
                all_source_and_decompressed_sha_verified=True,files=len(inventory),**summary)
    for root in roots:(root/'FINALIZED.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items()if k not in ['counts']}),flush=True)


if __name__=='__main__':
    main()
