"""Closed V945 only: one bounded source sync and verified, link-safe raw cleanup."""
import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runs/v946_rpccr_regression_closure'
OPS=ROOT/'runs/v945_rpccr_observation_liveness'
REC=ROOT/'records/nav2_v945_20261109'
TAG='phase-rpccr-regression-v945-20261109'
REPO='frank8763/phase-'
GH=ROOT/'tools/phase_storage_20261107/vendor/gh'
NAMES=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md',
       'docs/RPCCR_REGRESSION_RECOVERY_V945_REPORT.md','docs/RPCCR_CERTIFIED_RECOVERY_V945_REPORT.md',
       'experiments/v945_rpccr_observation_liveness','experiments/v946_rpccr_regression_closure',
       'records/nav2_v945_20261109']
FOLDERS=[ROOT/'runs/v858_nav2_verified/v945',ROOT/'runs/v945_startup_fixture02',
         ROOT/'runs/v945_startup_fixture03',ROOT/'runs/v936_rpccr_corridor_search/saved']


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def run(args,timeout=30):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=timeout)
    assert p.returncode==0,(p.stderr or p.stdout)[-1200:]
    return p.stdout


def gh(args,timeout=90):return run([str(GH),*args,'--repo',REPO],timeout)


def packer():
    spec=importlib.util.spec_from_file_location('v945_archive',ROOT/'experiments/v856_nav2_closure/package_records.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.OUT=OUT/'cloud'
    return module


def prepare():
    assert json.loads((OPS/'COMPLETION.json').read_text())['closed']
    assert json.loads((OPS/'FINALIZED.json').read_text())['all_sources_and_decompressed_sha_verified']
    with(OUT/'PREPARE_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
    assert all(sha(ROOT/p)==h for p,h in json.loads((ROOT/'experiments/v945_rpccr_observation_liveness/SOURCE_FREEZE.json').read_text())['files'].items())
    assert not run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
    module=packer();module.OUT.mkdir(exist_ok=False)
    links=[]
    for folder in FOLDERS:
        for current,dirs,files in os.walk(folder,followlinks=False):
            for name in dirs+files:
                path=Path(current)/name
                if path.is_symlink():links.append(dict(path=str(path.relative_to(ROOT)),target=os.readlink(path)))
    dump(REC/'GENERATED_LINKS.json',dict(links=links,target_accessed=False,target_deleted=False,
                                     scope='Generated mesh directory pointers; compiled MJB and regular evidence retained.'))
    files=[]
    for folder in [*FOLDERS[1:],ROOT/'experiments/v946_rpccr_regression_closure']:
        files.extend(module.walk(folder))
    base_catalog={}
    for inventory in (OPS/'cloud').glob('*.INVENTORY.json'):
        base_catalog.update({item['path']:item.get('sha256')for item in json.loads(inventory.read_text())['files']})
    files.extend(p for p in module.walk(FOLDERS[0])if base_catalog.get(str(p.relative_to(ROOT)))!=sha(p))
    files.extend(p for p in module.walk(OPS)if 'cloud' not in p.relative_to(OPS).parts)
    files.extend(p for p in module.walk(OUT)if p.parent==OUT and p.suffix=='.json')
    files.extend(module.walk(REC))
    files.extend(ROOT/name for name in NAMES[:4])
    supplement=module.archive('v945-closed-regression-supplement',files)
    index=json.loads((REC/'RECORD_INDEX.json').read_text())
    index.update(release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',
                 restore_order='Listed archives in order; supplement has closed reports and operation snapshots.',models_during_packaging=0)
    index['archives'].append({k:v for k,v in supplement.items()if k!='files'})
    dump(REC/'RECORD_INDEX.json',index)
    run(['git','add','--',*NAMES]);run(['git','diff','--cached','--check'])
    staged=run(['git','diff','--cached','--name-only']).splitlines()
    assert all((ROOT/p).stat().st_size<90*1024**2 for p in staged)
    dump(OUT/'PREPARED.json',dict(staged=len(staged),models=0))
    print('PREPARED',len(staged),flush=True)


def publish():
    assert(OUT/'PREPARED.json').exists()
    with(OUT/'PUBLISH_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
    run(['git','diff','--cached','--check'])
    run(['git','commit','-m','Separate RP-CCR supervision liveness and audit fixed dynamic regression'])
    head=run(['git','rev-parse','HEAD']).strip()
    sync=dict(commit=head,one_attempt=True,push_budget_s=30,verify_budget_s=5)
    with(OUT/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
    try:run(['git','push','origin','main'],30);sync['push_succeeded']=True
    except Exception as error:sync['push_error']=repr(error)
    try:
        sync['remote_head']=run(['git','ls-remote','origin','refs/heads/main'],5).split()[0]
        sync['remote_head_verified']=sync['remote_head']==head
    except Exception as error:sync['verify_error']=repr(error)
    dump(REC/'GIT_SYNC_RESULT.json',sync)
    assert sync.get('remote_head_verified'),'REMOTE_SOURCE_UNKNOWN_KEEP_REQUIRED_RAW'
    summary=json.loads((REC/'RESULT_SUMMARY.json').read_text())
    gh(['release','create',TAG,'--title','RP-CCR V945 fixed WE regression and observation liveness',
        '--notes','Frozen original WE main and success-only repeat. Scientific outcome: '+summary['status']+'. Historical V827/V828 successes are preserved separately. Full native/control replay, source, causal and recovery audits included. Narrow periodic course; no new24 acceptance or formal safety claim.',
        '--target',head,'--draft'])
    assets=[p for folder in [OPS/'cloud',OUT/'cloud']for p in folder.iterdir()if '.part'in p.name or p.name.endswith('.INVENTORY.json')]
    assets.append(REC/'RECORD_INDEX.json');assert len({p.name for p in assets})==len(assets)
    gh(['release','upload',TAG,*map(str,assets)],180)
    destination=OUT/'download';destination.mkdir(exist_ok=False)
    gh(['release','download',TAG,'--dir',str(destination)],180)
    for path in assets:assert sha(path)==sha(destination/path.name)
    index=json.loads((REC/'RECORD_INDEX.json').read_text());originals={};members=0
    for group in index['archives']:
        catalog={row['path']:row for row in json.loads((destination/(group['group']+'.INVENTORY.json')).read_text())['files']}
        combined=destination/'reassembled.tar.zst';whole=hashlib.sha256()
        with combined.open('xb')as output:
            for part in group['parts']:
                path=destination/part['name'];assert path.stat().st_size==part['bytes']and sha(path)==part['sha256']
                with path.open('rb')as source:
                    for block in iter(lambda:source.read(1048576),b''):whole.update(block);output.write(block)
        assert whole.hexdigest()==group['archive_sha256']
        process=subprocess.Popen(['zstd','-q','-dc',str(combined)],stdout=subprocess.PIPE);seen=set()
        with tarfile.open(fileobj=process.stdout,mode='r|')as archive:
            for member in archive:
                assert member.name in catalog and member.name not in seen and member.isfile()
                row=catalog[member.name];h=hashlib.sha256();size=0
                source=archive.extractfile(member)
                for block in iter(lambda:source.read(1048576),b''):h.update(block);size+=len(block)
                assert size==row['bytes']and h.hexdigest()==row['sha256']
                originals[member.name]=row['sha256'];seen.add(member.name);members+=1
        assert process.wait()==0 and seen==set(catalog);combined.unlink()
    gh(['release','edit',TAG,'--draft=false'])
    proof=dict(passed=True,source_commit=head,downloaded_decompressed_members=members,
               all_source_and_part_and_decompressed_sha_verified=True,release_url=index['release_url'],
               scientific_status=summary['status'],models=0,at=time.time())
    dump(REC/'REMOTE_VERIFIED.json',proof)
    receipts=OUT/'receipt_readback';receipts.mkdir(exist_ok=False)
    for path in [REC/'REMOTE_VERIFIED.json',REC/'GIT_SYNC_RESULT.json']:
        gh(['release','upload',TAG,str(path)])
        gh(['release','download',TAG,'--pattern',path.name,'--dir',str(receipts)],30)
        assert sha(path)==sha(receipts/path.name)
    # Check every regular source before deleting anything; never follow mesh links.
    for folder in FOLDERS:
        assert folder.resolve().is_relative_to(ROOT/'runs')and not folder.is_symlink()
        for path in packer().walk(folder):assert originals.get(str(path.relative_to(ROOT)))==sha(path),'UNVERIFIED_REQUIRED_RAW '+str(path)
    deleted=0;cleaned=[]
    for folder in FOLDERS:
        deleted+=sum(p.stat().st_size for p in packer().walk(folder))
        shutil.rmtree(folder);cleaned.append(str(folder.relative_to(ROOT)))
    for folder in [OPS/'cloud',OUT/'cloud',destination]:
        assert folder.resolve().is_relative_to(ROOT/'runs')and not folder.is_symlink()
        deleted+=sum(p.stat().st_size for p in packer().walk(folder))
        shutil.rmtree(folder);cleaned.append(str(folder.relative_to(ROOT)))
    delivery=dict(status='REMOTE_VERIFIED_REQUIRED_RAW_AND_DUPLICATE_CACHE_CLEANED',deleted_bytes=deleted,
                  cleaned_paths=cleaned,models=0,link_targets_untouched=True,release_url=index['release_url'])
    dump(REC/'DELIVERY_RESULT.json',delivery)
    gh(['release','upload',TAG,str(REC/'DELIVERY_RESULT.json')])
    gh(['release','download',TAG,'--pattern','DELIVERY_RESULT.json','--dir',str(receipts)],30)
    assert sha(REC/'DELIVERY_RESULT.json')==sha(receipts/'DELIVERY_RESULT.json');shutil.rmtree(receipts)
    run(['git','add','--',str(REC.relative_to(ROOT))])
    run(['git','commit','-m','Record V945 downloaded evidence verification and raw cleanup'])
    print(json.dumps(dict(remote=proof,cleanup=delivery)),flush=True)


if __name__=='__main__':
    lock=(ROOT/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(ROOT/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    {'prepare':prepare,'publish':publish}[sys.argv[1]]()
