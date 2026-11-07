"""Zero-model failed-backend closure, preserving wheels and verified transport parts."""
import sys


class NoModels:
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):
            raise RuntimeError('BACKEND_FINALIZER_FORBIDS_MODELS')


sys.meta_path.insert(0,NoModels())
import fcntl
import hashlib
import json
from pathlib import Path
import zipfile

REPO=Path(__file__).resolve().parents[2]
ROOT=REPO/'runs/v846_parallel_backend_qualification'
OWN=REPO/'experiments/v846_parallel_backend_qualification'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):h.update(block)
    return h.hexdigest()


def main():
    completion=json.loads((ROOT/'COMPLETION.json').read_text())
    outer=json.loads((ROOT/'OUTER_COMPLETION.json').read_text())
    assert completion['closed']and outer['closed']and outer['guard_exact']
    with(REPO/'runs/v648_static_unknown/execution.lock').open('rb')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    target=REPO/'evidence/rpccr_gpu_parallel_v846_20261106'
    assert not target.exists(),'ARCHIVE_EXISTS_NO_OVERWRITE'
    freeze=json.loads((OWN/'FREEZE.json').read_text())
    assert all(sha(REPO/p)==h for p,h in freeze['files'].items())
    error=json.loads((ROOT/'ERROR.json').read_text())
    report=REPO/'docs/RPCCR_GPU_PARALLEL_V846_20261106_REPORT.md'
    summary=dict(status='NOT_PASSED_GPU_WORLD_IDENTITY_CHECK',worlds_physically_advanced=64,
        planned_world_counts=[64,128],world128_unexecuted=True,
        counts=completion['counts'],elapsed_s=completion['elapsed_s'],
        observed_stop=error['message'],same_input_max_difference=None,different_input_difference=None,
        measured_steady_throughput=None,training_updates=0,new_navigation=0,new24=0,
        no_policy_trained=True,shared_environment_changed=False,
        failure_diagnostic_limit='The assertion ran before raw per-world states and latency samples were persisted; the two differences are unknown.',
        no_model_retry=True,source_unchanged=True,raw_deleted=False)
    report.write_text('# V846小场景64/128世界GPU物理资格实际结果\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n已使用机器人本体+支持平地（nq20/nv19/nu11，19body/32geom），没有复制原19静态实体场地或actor，无渲染、奖励、训练更新。依赖只runs私有安装，原环境/模型/网络字节不改。正式资格64世界完成33280原生世界步；CPU原生522步。CUDA首次编译日志保留，不能用总79.45秒（含编译）充当稳态吞吐。\n\n停止于相同输入qpos最大差<=1e-6且不同输入差>1e-6的联合断言。日志未在断言前保存两差值和原始状态，故具体哪部分失败、是否浮点/接触数值差异或真正世界隔离问题未知；不能宣称GPU后端物理不正确，也不能宣称一致性通过。该诊断遗漏保留，不通过放宽容差/修补本冻源重新运行追认。128世界未执行，PPO/SAC和通宵训练未开始。\n\n后续应另做明确有界后端诊断：优先保存各世界输入/末状态、接触容量、root/关节差异与稳态时延，再定义合理数值一致性门；同时保留CPU原车模独立评价。并行吞吐能力不能代替单车在线低延迟，也不能替代原完整动态验收。首失败即停止、执行锁空闲、原REVIEW_PENDING保留。初次依赖选取不匹配及下载完成前安装失败准备日志均保留；不隐藏为只有一次成功安装。\n')
    files={p:REPO/p for p in freeze['files']}
    for base in [OWN,ROOT]:
        for p in base.rglob('*'):
            if p.is_file()and'__pycache__'not in p.parts and'warp_cache'not in p.parts and p.suffix not in ['.lock','.pyc']and p.name!='finalize.console':
                files[str(p.relative_to(REPO))]=p
    files[str(report.relative_to(REPO))]=report
    target.mkdir();archive=target/'RAW.zip';inventory=[]
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True)as z:
        for name,p in sorted(files.items()):
            h=sha(p);z.write(p,name);inventory.append(dict(path=name,bytes=p.stat().st_size,sha256=h))
    with zipfile.ZipFile(archive)as z:
        for row in inventory:
            h=hashlib.sha256();size=0
            with z.open(row['path'])as stream:
                for block in iter(lambda:stream.read(4*1024**2),b''):h.update(block);size+=len(block)
            assert h.hexdigest()==row['sha256']and size==row['bytes']and sha(files[row['path']])==row['sha256']
    manifest=dict(inventory=inventory,zip_sha256=sha(archive),zip_bytes=archive.stat().st_size,
        all_sources_and_decompressed_sha_verified=True,raw_deleted=False,
        derived_compiler_cache_retained_local_but_not_archived=True)
    if archive.stat().st_size>90*1024**2:
        parts=[];h=hashlib.sha256()
        with archive.open('rb')as stream:
            for i,block in enumerate(iter(lambda:stream.read(32*1024**2),b'')):
                p=target/f'RAW.zip.part{i:03d}';p.write_bytes(block);h.update(p.read_bytes())
                parts.append(dict(path=p.name,bytes=len(block),sha256=sha(p)))
        assert h.hexdigest()==sha(archive)
        manifest.update(parts=parts,recombined_sha_verified=True)
        (target/'restore.py').write_text('from pathlib import Path\nimport hashlib,json\nr=Path(__file__).resolve().parent\nm=json.loads((r/"MANIFEST.json").read_text())\np=r/"RESTORED_RAW.zip"\nassert not p.exists()\nh=hashlib.sha256()\nwith p.open("xb")as out:\n for part in m["parts"]:\n  b=(r/part["path"]).read_bytes()\n  assert hashlib.sha256(b).hexdigest()==part["sha256"]\n  h.update(b);out.write(b)\nassert h.hexdigest()==m["zip_sha256"]\nprint(p)\n')
    (target/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    output=dict(**summary,archive=str(target.relative_to(REPO)),report=str(report.relative_to(REPO)),
                 all_sources_and_decompressed_sha_verified=True,models_finalizer=0,integrations_finalizer=0)
    (ROOT/'FINALIZED.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output),flush=True)


if __name__=='__main__':main()
