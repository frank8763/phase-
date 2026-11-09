"""Closed V943 and prerequisite evidence: one source push, remote member readback."""
import fcntl
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runs/v944_rpccr_segment_postmortem'
OPS=ROOT/'runs/v943_rpccr_segment_navigation'
REC=ROOT/'records/nav2_v943_20261109'
TAG='phase-rpccr-recovery-v943-20261109'
REPO='frank8763/phase-'
GH=ROOT/'tools/phase_storage_20261107/vendor/gh'
EXPERIMENTS=['v936_rpccr_corridor_search','v937_rpccr_timed_corridor',
             'v938_rpccr_recovery_segments','v939_rpccr_rpp_handoff',
             'v940_rpccr_handoff_entry','v941_rpccr_reference_loss_binding',
             'v942_rpccr_recovery_delivery','v943_rpccr_segment_navigation',
             'v944_rpccr_segment_postmortem']
NAMES=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md',
       'docs/RPCCR_REFERENCE_LOSS_V943_REPORT.md','docs/RPCCR_CERTIFIED_RECOVERY_V943_REPORT.md',
       *['experiments/'+name for name in EXPERIMENTS],'records/nav2_v943_20261109']


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


def whitespace_check():
    # A unified diff's empty context line must contain its leading space.
    # Preserve that exact historical evidence; inspect every ordinary source.
    return run(['git','diff','--cached','--check','--','.',
                ':!experiments/v940_rpccr_handoff_entry/ENTRY_SCOPE.diff'])


def packer():
    spec=importlib.util.spec_from_file_location('closed_archive',ROOT/'experiments/v856_nav2_closure/package_records.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.OUT=OUT/'cloud'
    return module


def prepare():
    with(OUT/'PREPARE_CLAIM.json').open('x') as f:json.dump(dict(at=time.time(),models=0),f)
    assert json.loads((OPS/'COMPLETION.json').read_text())['closed']
    assert json.loads((OPS/'FINALIZED.json').read_text())['all_sources_and_decompressed_sha_verified']
    frozen=json.loads((ROOT/'experiments/v943_rpccr_segment_navigation/SOURCE_FREEZE.json').read_text())['files']
    assert all(sha(ROOT/p)==h for p,h in frozen.items())
    assert not run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
    module=packer();module.OUT.mkdir(exist_ok=False);files=[]
    for name in EXPERIMENTS:
        files.extend(module.walk(ROOT/'experiments'/name))
    for name in EXPERIMENTS[:-1]:
        base=ROOT/'runs'/name
        files.extend(p for p in module.walk(base) if not any(
            part in {'download','cloud','receipt_readback'} for part in p.relative_to(base).parts))
    files.extend(p for p in module.walk(OUT) if p.suffix in {'.json','.md'})
    files.extend(module.walk(ROOT/'runs/v943_startup_fixture02'))
    files.extend(module.walk(REC))
    for name in NAMES[:4]:files.append(ROOT/name)
    for name in ['v938_qualification.console','v941_qualification.console','v942_supervisor.console',
                 'v942_supervisor_corrected.console','v943_corridor_qualification.console',
                 'v943_zero_qualification.console','v944_analysis.console']:
        if(ROOT/'runs'/name).exists():files.append(ROOT/'runs'/name)
    supplement=module.archive('v936-v944-closed-recovery-preparation',files)
    index=json.loads((REC/'RECORD_INDEX.json').read_text())
    index.update(release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',
                 status='LOCAL_ALL_SOURCES_AND_DECOMPRESSED_SHA_VERIFIED_REMOTE_PENDING',
                 restore_order='archives in listed order; supplement contains the later report/metadata snapshot',
                 scientific_status='V943_NOT_PASSED',models_during_packaging=0)
    index['archives'].append({k:v for k,v in supplement.items() if k!='files'})
    dump(REC/'RECORD_INDEX.json',index)
    run(['git','add','--',*NAMES]);whitespace_check()
    staged=run(['git','diff','--cached','--name-only']).splitlines()
    assert all((ROOT/p).stat().st_size<90*1024**2 for p in staged)
    dump(OUT/'PREPARED.json',dict(staged=len(staged),models=0))
    print('PREPARED',len(staged),flush=True)


def publish():
    assert(OUT/'PREPARED.json').exists()
    with(OUT/'PUBLISH_CLAIM.json').open('x') as f:json.dump(dict(at=time.time(),models=0),f)
    whitespace_check()
    run(['git','commit','-m','Validate RP-CCR reference-loss recovery and preserve V943 freshness stop'])
    head=run(['git','rev-parse','HEAD']).strip()
    sync=dict(commit=head,one_attempt=True,push_budget_s=30,verify_budget_s=5)
    with(OUT/'GIT_SYNC_CLAIM.json').open('x') as f:json.dump(sync,f)
    try:run(['git','push','origin','main'],30);sync['push_succeeded']=True
    except Exception as error:sync['push_error']=repr(error)
    try:
        sync['remote_head']=run(['git','ls-remote','origin','refs/heads/main'],5).split()[0]
        sync['remote_head_verified']=sync['remote_head']==head
    except Exception as error:sync['verify_error']=repr(error)
    dump(REC/'GIT_SYNC_RESULT.json',sync)
    assert sync.get('remote_head_verified'),'REMOTE_SOURCE_UNKNOWN_KEEP_REQUIRED_RAW'
    gh(['release','create',TAG,'--title','RP-CCR reference-loss corridor V943: actual recovery prefix, freshness stop',
        '--notes','V943 original WE dynamic development NOT_PASSED: new RP-CCR reference-loss corridor actually handed to frozen FeasibleRPP and advanced0.580617m; supervisory STALE_BODY stop before segment/goal completion.6455 actual and6455 own replay, min clearance0.269041872m, bad contacts0, state error0. Repeat/new24 unexecuted. Includes original zero-model failures and source-bound qualifications. Not dynamic acceptance or a formal safety guarantee.',
        '--target',head,'--draft'])
    clouds=[OPS/'cloud',OUT/'cloud']
    assets=[p for folder in clouds for p in folder.iterdir() if '.part' in p.name or p.name.endswith('.INVENTORY.json')]
    assets.append(REC/'RECORD_INDEX.json')
    assert len({p.name for p in assets})==len(assets)
    gh(['release','upload',TAG,*map(str,assets)],180)
    destination=OUT/'download';destination.mkdir(exist_ok=False)
    gh(['release','download',TAG,'--dir',str(destination)],180)
    for path in assets:assert sha(path)==sha(destination/path.name)
    index=json.loads((REC/'RECORD_INDEX.json').read_text());originals={};members=0
    for group in index['archives']:
        inventory=json.loads((destination/(group['group']+'.INVENTORY.json')).read_text())
        catalog={row['path']:row for row in inventory['files']}
        combined=destination/'reassembled.tar.zst';whole=hashlib.sha256()
        with combined.open('xb') as stream:
            for part in group['parts']:
                path=destination/part['name']
                assert path.stat().st_size==part['bytes'] and sha(path)==part['sha256']
                with path.open('rb') as input_stream:
                    for block in iter(lambda:input_stream.read(1048576),b''):whole.update(block);stream.write(block)
        assert whole.hexdigest()==group['archive_sha256']
        process=subprocess.Popen(['zstd','-q','-dc',str(combined)],stdout=subprocess.PIPE)
        seen=set()
        with tarfile.open(fileobj=process.stdout,mode='r|') as archive:
            for member in archive:
                assert member.name in catalog and member.name not in seen and member.isfile()
                row=catalog[member.name];h=hashlib.sha256();size=0
                stream=archive.extractfile(member)
                for block in iter(lambda:stream.read(1048576),b''):h.update(block);size+=len(block)
                assert size==row['bytes'] and h.hexdigest()==row['sha256']
                seen.add(member.name);originals[member.name]=row['sha256'];members+=1
        assert process.wait()==0 and seen==set(catalog)
        combined.unlink()
    gh(['release','edit',TAG,'--draft=false'])
    proof=dict(passed=True,source_commit=head,downloaded_decompressed_members=members,
               all_source_and_part_and_decompressed_sha_verified=True,
               release_url=index['release_url'],scientific_status='NOT_PASSED',models=0,at=time.time())
    dump(REC/'REMOTE_VERIFIED.json',proof)
    receipts=OUT/'receipt_readback';receipts.mkdir(exist_ok=False)
    for path in [REC/'REMOTE_VERIFIED.json',REC/'GIT_SYNC_RESULT.json']:
        gh(['release','upload',TAG,str(path)])
        gh(['release','download',TAG,'--pattern',path.name,'--dir',str(receipts)],30)
        assert sha(path)==sha(receipts/path.name)
    deleted=0;cleaned=[]

    def verified_remove(folder):
        nonlocal deleted
        assert folder.resolve().is_relative_to(ROOT/'runs') and not folder.is_symlink()
        assert not any(p.is_symlink() for p in folder.rglob('*'))
        for path in packer().walk(folder):
            assert originals.get(str(path.relative_to(ROOT)))==sha(path),'UNVERIFIED_REQUIRED_RAW '+str(path)
            deleted+=path.stat().st_size
        shutil.rmtree(folder);cleaned.append(str(folder.relative_to(ROOT)))

    for folder in [ROOT/'runs/v858_nav2_verified/v943',ROOT/'runs/v943_startup_fixture02',
                   ROOT/'runs/v936_rpccr_corridor_search/saved']:
        verified_remove(folder)
    # Duplicate downloaded archive and new verified compressed/readback copies.
    # Selected original inputs are now preserved and verified in the supplement.
    prior=ROOT/'runs/v936_rpccr_corridor_search'
    assert json.loads((prior/'RESTORE_VERIFIED.json').read_text())['passed']
    for folder in [prior/'download',*clouds,destination]:
        assert folder.resolve().is_relative_to(ROOT/'runs') and not folder.is_symlink()
        assert not any(p.is_symlink() for p in folder.rglob('*'))
        deleted+=sum(p.stat().st_size for p in packer().walk(folder))
        shutil.rmtree(folder);cleaned.append(str(folder.relative_to(ROOT)))
    delivery=dict(status='REMOTE_VERIFIED_REQUIRED_RAW_AND_DUPLICATE_ARCHIVE_CACHE_CLEANED',
                  deleted_bytes=deleted,cleaned_paths=cleaned,models=0,
                  metadata_and_qualifications_retained=True,release_url=index['release_url'])
    dump(REC/'DELIVERY_RESULT.json',delivery)
    gh(['release','upload',TAG,str(REC/'DELIVERY_RESULT.json')])
    gh(['release','download',TAG,'--pattern','DELIVERY_RESULT.json','--dir',str(receipts)],30)
    assert sha(REC/'DELIVERY_RESULT.json')==sha(receipts/'DELIVERY_RESULT.json')
    shutil.rmtree(receipts)
    run(['git','add','--',str(REC.relative_to(ROOT))])
    run(['git','commit','-m','Record verified V943 remote evidence and bounded raw cleanup'])
    print(json.dumps(dict(remote=proof,cleanup=delivery)),flush=True)


if __name__=='__main__':
    lock=(ROOT/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(ROOT/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    {'prepare':prepare,'publish':publish}[sys.argv[1]]()
