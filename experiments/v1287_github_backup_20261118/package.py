"""Select closed V1281 evidence plus exact frozen dependencies. No models."""
from pathlib import Path
import collections,fcntl,hashlib,importlib.util,json,os,re,time
C=Path(__file__).resolve().parent;R=C.parents[1]
O=R/'runs'/C.name;D=R/'records/v1281_backup_20261118'
TAG='phase-dynamic-fixed24-v1281-20261118'
def read(p):return json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def walk(root):
    if root.exists():
        for p in root.rglob('*'):
            if p.is_file()and not p.is_symlink()and '__pycache__'not in p.parts and p.suffix not in ['.console','.lock']:yield p
def main():
    assert not(D/'RECORD_INDEX.json').exists(),'ONE_PACKAGE_NO_OVERWRITE'
    os.sched_setaffinity(0,{2,3,4,5});os.nice(19)
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert read(R/'CURRENT_EXPERIMENT.json')['active_run']is None and(R/'REVIEW_PENDING').exists()
    assert read(R/'runs/v1281_partial_reconnection_fixed24/FINALIZED.json')['fixed24_confirmation_passed']
    names=set(read(R/'experiments/v1281_partial_reconnection_fixed24/SOURCE_FREEZE.json')['files'])
    roots=['v1281_partial_reconnection_fixed24','v1278_static_partial_reconnection','v1280_slot24_repeat_clock','v1271_ew_joint_phase_validation','v1286_night_post_verified']
    for name in roots:
        root=R/'runs'/name;final=read(root/'FINALIZED.json');manifest=read(root/'LOCAL_MANIFEST.json')['files']
        assert final['manifest_readback']and len(manifest)==final['files']
        for n,v in manifest.items():
            p=R/n;assert p.stat().st_size==v['bytes']and hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256'],'CHANGED_ARCHIVED_MEMBER '+n
        names.update(manifest)
        names.update(str(p.relative_to(R))for p in walk(root))
    for relative in ['runs/v858_nav2_verified/v1275/main_slot24','runs/v1275_time_window_fixed24','runs/v1279_same_frame_audit','runs/v1282_night_saved_evidence','runs/v1283_night_confirmation_relay','runs/v1284_night_proof_entry','runs/v1285_night_post_confirmation','records/v1281_morning_review_20261118']:
        names.update(str(p.relative_to(R))for p in walk(R/relative))
    for version in range(1277,1287):
        for root in(R/'experiments').glob('v'+str(version)+'_*'):names.update(str(p.relative_to(R))for p in walk(root))
    for n in ['AGENTS.md','MIGRATION.md','RESEARCH_STATUS.md','CURRENT_EXPERIMENT.json','REVIEW_PENDING','docs/STORAGE_POLICY.md','docs/EXPERIMENT_ACCELERATION_POLICY_20261117.md','docs/RAS_AFTER_FIXED24_PLAN_20261117.md']:names.add(n)
    links={}
    for n in list(names):
        p=R/n
        if p.is_symlink():
            target=p.resolve();assert target.is_file()and target.is_relative_to(R),'EXTERNAL_LINK_NOT_ALLOWED '+n
            links[n]=dict(link_target=os.readlink(p),resolved_target=str(target.relative_to(R)))
            names.remove(n);names.add(str(target.relative_to(R)))
    dump(D/'INTERNAL_SYMLINKS.json',links)
    groups=collections.defaultdict(list)
    for n in sorted(names):
        p=R/n;assert p.is_file()and not p.is_symlink()and p.resolve().is_relative_to(R)
        # Never publish common credential files or credential-shaped literals.
        assert p.name not in ['.git-credentials','.env','id_rsa','id_ed25519']
        if p.suffix in ['.py','.json','.md','.yaml','.yml','.sh','.cpp','.hpp','.txt']:
            assert not re.search(rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}',p.read_bytes()),'CREDENTIAL_SHAPED_LITERAL '+n
        prefix='runs/v858_nav2_verified/v1281/'
        if n.startswith(prefix):
            task=n[len(prefix):].split('/')[0];group='v1281-'+task if not task.startswith('t0_')else'v1281-preflights'
        elif n.startswith('runs/'):group='frozen-dependencies-and-provenance'
        else:group='source-reports-and-metadata'
        groups[group].append(p)
    spec=importlib.util.spec_from_file_location('phase_existing_verified_archive',C/'archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc)
    inventory=[];archives=[];begin=time.monotonic();transport=O/'transport';transport.mkdir()
    for number,(group,paths)in enumerate(sorted(groups.items()),1):
        budget=lambda:sum(p.stat().st_size for p in transport.rglob('*')if p.is_file())<2*1024**3
        record,members=arc.package(R,paths,transport/group,group,budget)
        inventory.extend(members);archives.append(record)
        dump(D/'PACKAGE_PROGRESS.json',dict(groups_complete=number,groups_total=len(groups),members=len(inventory),archive_bytes=sum(x['archive_bytes']for x in archives),elapsed_s=time.monotonic()-begin))
        print(json.dumps(dict(event='PACKAGED_AND_DECOMPRESSED_SHA_VERIFIED',group=group,raw_bytes=record['raw_bytes'],archive_bytes=record['archive_bytes'])),flush=True)
    assert len(inventory)==len(names)
    dump(D/'SOURCE_INVENTORY.json',dict(files=inventory))
    index=dict(schema=1,repository='frank8763/phase-',release_tag=TAG,release_url='https://github.com/frank8763/phase-/releases/tag/'+TAG,
        archives=archives,source_files=len(inventory),internal_symlinks_preserved_by_git=links,raw_bytes=sum(x['bytes']for x in inventory),archive_bytes=sum(x['archive_bytes']for x in archives),
        source_and_decompressed_sha_readback=True,maximum_part_bytes=32*1024**2,old_failure_outcomes_preserved=True,raw_local_cleanup_not_yet_authorized_by_readback=True,
        scope='complete V1281 fixed24+t0+three repeats; exact frozen source/input dependency closure; full slot24 and18/19 development pairs; failed V1275 slot24; operational failures and morning review',
        omitted='unrelated older failed candidate pools and repeated earlier success trajectories not required by the selected frozen dependency closure; existing remote historical releases stay unchanged')
    dump(D/'RECORD_INDEX.json',index)
    dump(D/'FINAL_SUMMARY.json',read(R/'records/v1281_morning_review_20261118/VERIFIED_RESULT.json'))
    print(json.dumps(dict(packaged=True,files=len(inventory),raw_bytes=index['raw_bytes'],archive_bytes=index['archive_bytes'],groups=len(archives))),flush=True)
if __name__=='__main__':main()
