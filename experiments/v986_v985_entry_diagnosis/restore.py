"""Restore closed V985 startup metadata only, with archive and member SHA."""
import fcntl,hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v986_v985_entry_diagnosis';GH=R/'tools/phase_storage_20261107/vendor/gh'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert json.loads((R/'records/nav2_v985_20261110/FINALIZED.json').read_text())['remote_verified']
    ix=json.loads((R/'records/nav2_v985_20261110/RECORD_INDEX.json').read_text());g=ix['archives'][0];O.mkdir(exist_ok=True)
    def download(name):
        p=O/name
        if not p.exists():
            x=subprocess.run([str(GH),'release','download',ix['release_tag'],'--repo',ix['repository'],'--pattern',name,'--dir',str(O)],capture_output=True,text=True,timeout=30)
            assert x.returncode==0,x.stderr[-1200:]
        return p
    inventory=download(g['group']+'.INVENTORY.json');catalog={v['path']:v for v in json.loads(inventory.read_text())['files']}
    prefix='runs/v858_nav2_verified/v985/component_0/'
    names=['RESULT.json','COMPLETION.json','ACTUATION_AUDIT.json','INGRESS.json.gz','NATIVE_ACCOUNTING.json','NATIVE_READY.json',
        'PARENT_STOP_REQUEST.json','RUNTIME_TIMING.json','TASK.json','WORKER_CLOSURE.json','WORKER_FAILURE.json','native.console',
        'physics/ACTIVE_ADAPTER_BINDING.json','physics/PREFIX_RESTORE.json','physics/REPLAY.json','physics/SETUP.json','physics/YAW_FEEDBACK.json.gz']
    wanted={prefix+n:n for n in names};assert set(wanted)<=catalog.keys()
    assert len(g['parts'])==1;part=g['parts'][0];archive=download(part['name'])
    assert sha(archive)==part['sha256']==g['archive_sha256']and archive.stat().st_size==part['bytes']
    decoder=subprocess.Popen(['zstd','-q','-dc',str(archive)],stdout=subprocess.PIPE);seen=set();rows=[]
    with tarfile.open(fileobj=decoder.stdout,mode='r|')as stream:
        for member in stream:
            if member.name not in wanted:continue
            assert member.isfile()and '..'not in Path(member.name).parts
            dest=O/wanted[member.name];dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():
                with stream.extractfile(member)as src,dest.open('xb')as out:shutil.copyfileobj(src,out)
            row=catalog[member.name];assert sha(dest)==row['sha256']and dest.stat().st_size==row['bytes']
            seen.add(member.name);rows.append(dict(original=member.name,path=str(dest.relative_to(R)),sha256=row['sha256'],bytes=row['bytes']))
    assert decoder.wait()==0 and seen==set(wanted);archive.unlink()
    receipt=dict(passed=True,models=0,integrations=0,archive_sha256=g['archive_sha256'],files=rows,
        original_release_url=ix['release_url'],ros_console_in_original_archive=prefix+'ros.console'in catalog)
    (O/'RESTORE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(restored_files=len(rows),bytes=sum(v['bytes']for v in rows),models=0,integrations=0)))
if __name__=='__main__':main()
