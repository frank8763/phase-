"""Archive the exact saved inputs actually read and all new offline evidence."""
import gzip,hashlib,json,signal,time,zipfile
from pathlib import Path

R=Path(__file__).resolve().parents[2];O=R/'runs/v852_maneuver_contract';E=R/'evidence/rpccr_v852_offline_core_20261107'


def digest(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def main():
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('ZERO_MODEL_ARCHIVE_180S')));signal.alarm(180)
    assert not E.exists();E.mkdir();inputs=json.loads((O/'VERIFIED_INPUT_SHA256.json').read_text());paths={R/p for p in inputs}
    for folder in ['experiments/v851_outcome_analysis','runs/v851_outcome_analysis','experiments/v852_maneuver_contract','runs/v852_maneuver_contract']:
        paths.update(p for p in(R/folder).rglob('*')if p.is_file())
    paths.update(R/p for p in ['docs/RPCCR_V851_TIME_CAUSE_AND_V852_OFFLINE_REVISION_20261107.md','CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','REVIEW_PENDING','experiments/v851_profile_output_continuation/CANDIDATE_FREEZE.json'])
    rows=[]
    for p in sorted(paths):
        assert p.resolve().is_relative_to(R)and p.is_file()
        relative=str(p.relative_to(R));value=digest(p)
        if relative in inputs:assert inputs[relative]==value
        rows.append(dict(path=relative,sha256=value,bytes=p.stat().st_size))
    target=E/'RAW.zip'
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True)as z:
        for row in rows:z.write(R/row['path'],row['path'])
    with zipfile.ZipFile(target)as z:
        assert len(z.namelist())==len(rows)
        for row in rows:
            h=hashlib.sha256();size=0
            with z.open(row['path'])as stream:
                for b in iter(lambda:stream.read(1048576),b''):h.update(b);size+=len(b)
            assert h.hexdigest()==row['sha256']and size==row['bytes']and digest(R/row['path'])==row['sha256']
    with gzip.open(E/'MANIFEST.jsonl.gz','wt')as f:
        for row in rows:f.write(json.dumps(row)+'\n')
    transport=[]
    if target.stat().st_size>90*1024**2:
        with target.open('rb')as f:
            for i in range((target.stat().st_size+32*1024**2-1)//(32*1024**2)):
                p=E/f'RAW.zip.part{i:03d}';p.write_bytes(f.read(32*1024**2));transport.append(dict(path=p.name,bytes=p.stat().st_size,sha256=digest(p)))
        h=hashlib.sha256()
        for row in transport:
            with(E/row['path']).open('rb')as f:
                for b in iter(lambda:f.read(1048576),b''):h.update(b)
        assert h.hexdigest()==digest(target)
    result=dict(status='OFFLINE_ARCHIVE_ALL_SAVED_SOURCE_AND_DECOMPRESSED_SHA_VERIFIED',verified_unix=time.time(),files=len(rows),raw_bytes=sum(x['bytes']for x in rows),zip_bytes=target.stat().st_size,zip_sha256=digest(target),all_source_and_decompressed_sha_verified=True,originals_retained=True,transport_chunks=transport,new_models=0,new_integrations=0,not_physical_acceptance=True)
    (E/'VERIFIED.json').write_text(json.dumps(result,indent=2)+'\n')
    (E/'README.md').write_text('# V852 零模型控制核心与 V851 原因分解\n\nRAW.zip 包含本次实际读取的旧保存输入、全部新源码、失败与准备快照、资格结果及状态元数据。MANIFEST.jsonl.gz 对每个来源及解压文件逐字节SHA256回读；VERIFIED.json 记录核验结果。原始runs与旧归档均保留。\n\n11正/13负例、1600原控制序列、10旧证书分类、共享入口及14边界检查通过。没有新模型、积分、训练或导航，不是物理资格、提速或动态验收通过。实际工作器接线和原生批物理等价仍未执行。没有物理窗口或自动后续运行。\n')
    print(json.dumps(result))


if __name__=='__main__':main()
