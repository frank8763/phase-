"""Verify immutable already-uploaded V1014 archive, then remove verified cache only."""
import fcntl,json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];ROOT=R/'runs/atomic_handoff_night_20261110';REC=R/'records/nav2_v1014_20261110'
sys.path.insert(0,str(C));from archive import verify,walk,sha

def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    read=lambda p:json.loads(Path(p).read_text())
    assert read(ROOT/'COMPLETION.json')['closed']and not read(ROOT/'APPROVAL.json')['models_authorized']
    index=read(REC/'RECORD_INDEX.json');record=index['archives'][0];tag=index['release_tag'];gh=R/'tools/phase_storage_20261107/vendor/gh'
    inventory=ROOT/'cloud'/(record['group']+'.INVENTORY.json');catalog=read(inventory)['files']
    with tempfile.TemporaryDirectory(prefix='verify-existing-',dir=ROOT)as td:
        back=Path(td)
        def fetch(name):
            p=subprocess.run([str(gh),'release','download',tag,'--repo','frank8763/phase-','--pattern',name,'--dir',str(back)],capture_output=True,text=True,timeout=30)
            assert p.returncode==0,(p.stdout+p.stderr)[-1000:];return back/name
        assert sha(fetch(inventory.name))==sha(inventory)
        verify(record,catalog,lambda part:(fetch(part['name']),True))
    mapping={x['path']:x for x in catalog};links=read(REC/'RESOURCE_LINKS.json');deleted=[]
    roots=[R/'runs/v1014_atomic_handoff_navigation',R/'runs/v858_nav2_verified/v1014']
    for folder in roots:
        files=list(walk(folder))
        for p in files:
            if p.suffix=='.lock':assert p.stat().st_size==0;continue
            row=mapping[str(p.relative_to(R))];assert p.stat().st_size==row['bytes']and sha(p)==row['sha256'],str(p)
        for base,dirs,names in os.walk(folder,followlinks=False):
            for name in dirs+names:
                p=Path(base,name)
                if p.is_symlink():assert any(x['path']==str(p.relative_to(R))and x['target']==os.readlink(p)for x in links);p.unlink()
        deleted.append(dict(path=str(folder.relative_to(R)),bytes=sum(p.stat().st_size for p in files)));shutil.rmtree(folder)
    for folder in [ROOT/'cloud',ROOT/'readback']:
        if folder.exists():shutil.rmtree(folder)
    final=dict(closed=True,status='NOT_PASSED',remote_verified=True,all_remote_decompressed_member_sha_verified=True,models=0,integrations=0,
        original_zero_model_cleanup_KeyError_preserved=True,existing_archive_not_overwritten=True,no_git_push_retry=True,deleted=deleted)
    for p in [REC/'FINALIZED.json',ROOT/'FINALIZED.json']:p.write_text(json.dumps(final,indent=2)+'\n')
    print(json.dumps(final))
if __name__=='__main__':main()
