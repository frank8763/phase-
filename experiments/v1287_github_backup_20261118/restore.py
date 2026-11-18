"""Restore selected verified Release groups; source comes from Git."""
from pathlib import Path
import argparse,fcntl,hashlib,json,os,subprocess,tarfile,threading,urllib.request
R=Path(__file__).resolve().parents[2];D=R/'records/v1281_backup_20261118'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--list',action='store_true');p.add_argument('--group',action='append');p.add_argument('--all',action='store_true');p.add_argument('--prefix',default='runs/');p.add_argument('--verify-only',action='store_true');a=p.parse_args()
    index=json.loads((D/'RECORD_INDEX.json').read_text());inventory={x['path']:x for x in json.loads((D/'SOURCE_INVENTORY.json').read_text())['files']}
    if a.list:
        for g in index['archives']:print(g['group'],g['source_files'],g['raw_bytes'],g['archive_bytes'])
        return
    assert a.all or a.group,'Select --group NAME (repeatable), or --all'
    groups=[x for x in index['archives']if a.all or x['group']in a.group];assert groups
    if a.group:assert set(a.group)<={x['group']for x in groups}
    assert a.prefix.startswith('runs/')and '..'not in Path(a.prefix).parts,'Only saved run data is restored; get source/metadata from Git'
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert(R/'REVIEW_PENDING').exists(),'No restore during active experiments'
    base='https://github.com/frank8763/phase-/releases/download/'+index['release_tag']+'/'
    for group in groups:
        error=[];archive_hash=hashlib.sha256();process=subprocess.Popen(['zstd','-q','-dc'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        def feed():
            try:
                for part in group['parts']:
                    h=hashlib.sha256();n=0
                    with urllib.request.urlopen(base+part['name'],timeout=90)as src:
                        for block in iter(lambda:src.read(1048576),b''):
                            h.update(block);archive_hash.update(block);n+=len(block);process.stdin.write(block)
                    assert n==part['bytes']and h.hexdigest()==part['sha256'],'TRANSPORT_PART_SHA'
            except BaseException as e:error.append(e)
            finally:process.stdin.close()
        thread=threading.Thread(target=feed,daemon=True);thread.start();seen=set();restored=0
        try:
            with tarfile.open(fileobj=process.stdout,mode='r|')as tar:
                for member in tar:
                    assert member.isfile()and member.name in inventory and member.name not in seen
                    row=inventory[member.name];target=R/member.name;assert target.resolve().is_relative_to(R)
                    selected=not a.verify_only and member.name.startswith(a.prefix)
                    if selected:
                        assert not any(p.is_symlink()for p in [target,*target.parents]if p.is_relative_to(R)),'SYMLINK_TARGET'
                        if target.exists():assert target.stat().st_size==row['bytes']and sha(target)==row['sha256'],'EXISTING_DIFFERENT_FILE '+member.name
                    temporary=target.with_name(target.name+'.restore.tmp')if selected and not target.exists()else None
                    if temporary:target.parent.mkdir(parents=True,exist_ok=True)
                    out=temporary.open('xb')if temporary else None;h=hashlib.sha256()
                    try:
                        stream=tar.extractfile(member)
                        for block in iter(lambda:stream.read(1048576),b''):
                            h.update(block)
                            if out:out.write(block)
                        assert member.size==row['bytes']and h.hexdigest()==row['sha256'],'MEMBER_SHA '+member.name
                    finally:
                        if out:out.close()
                    if temporary:temporary.replace(target);restored+=1
                    seen.add(member.name)
            while process.stdout.read(1048576):pass
            thread.join(timeout=120);assert not thread.is_alive()and not error,repr(error)
            assert process.wait(timeout=10)==0 and archive_hash.hexdigest()==group['archive_sha256']and len(seen)==group['source_files']
        finally:
            if process.poll()is None:process.kill();process.wait()
        print(json.dumps(dict(group=group['group'],verified_members=len(seen),restored_files=restored)))
if __name__=='__main__':main()
