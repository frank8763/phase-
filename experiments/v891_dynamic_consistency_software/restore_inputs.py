"""Read selected verified V890 members; never retry its completed delivery."""
import hashlib,json,pathlib,shutil,subprocess,tarfile
R=pathlib.Path(__file__).resolve().parents[2]
O=R/'runs/v891_dynamic_consistency_software';REC=R/'records/nav2_v891_20261108'
GH=R/'tools/phase_storage_20261107/vendor/gh'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    O.mkdir(exist_ok=True);REC.mkdir(exist_ok=True)
    index=json.loads((R/'records/nav2_v890_20261108/RECORD_INDEX.json').read_text())
    group=index['archives'][0];cache=O/'readback';cache.mkdir(exist_ok=False)
    target=O/'inputs';target.mkdir(exist_ok=False)
    for name in [p['name']for p in group['parts']]+[group['group']+'.INVENTORY.json']:
        p=subprocess.run([str(GH),'release','download',index['release_tag'],'--repo',index['repository'],'--pattern',name,'--dir',str(cache)],cwd=R,capture_output=True,text=True,timeout=40)
        assert p.returncode==0,p.stderr[-400:]
    for p in group['parts']:assert sha(cache/p['name'])==p['sha256']
    inventory=json.loads((cache/(group['group']+'.INVENTORY.json')).read_text())
    expected={x['path']:x for x in inventory['files']}
    names=['physics/SENSORS.json.gz','physics/SETUP.json','RESULT.json','PLANS.json','ROUTER_REQUESTS.json','physics/NATIVE_TRACE.npz','MOTION_ENVELOPE.json.gz']
    selected={f'runs/v858_nav2_verified/v890/main_we/{n}':n.replace('/','__')for n in names}
    archive=cache/'joined.tar.zst'
    with archive.open('xb')as f:
        for part in group['parts']:
            with(cache/part['name']).open('rb')as s:shutil.copyfileobj(s,f)
    assert sha(archive)==group['archive_sha256'];seen=[]
    proc=subprocess.Popen(['zstd','-q','-dc',str(archive)],stdout=subprocess.PIPE)
    with tarfile.open(fileobj=proc.stdout,mode='r|')as tf:
        for member in tf:
            if member.name not in selected:continue
            assert member.isfile();p=target/selected[member.name]
            with p.open('xb')as f:shutil.copyfileobj(tf.extractfile(member),f)
            assert sha(p)==expected[member.name]['sha256']
            seen.append(dict(source=member.name,restored=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size))
    assert proc.wait(timeout=15)==0 and len(seen)==len(selected)
    shutil.rmtree(cache)
    proof=dict(passed=True,selected_files=seen,remote_readback_only=True,old_upload_or_sync_retried=False,models=0,integrations=0)
    for p in [O/'INPUT_READBACK.json',REC/'INPUT_READBACK.json']:p.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(dict(passed=True,files=len(seen),bytes=sum(x['bytes']for x in seen))),flush=True)
if __name__=='__main__':main()
