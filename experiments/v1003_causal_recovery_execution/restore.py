"""Bounded selected-member restoration; SHA before use; zero models."""
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1003_causal_recovery_execution';GH=R/'tools/phase_storage_20261107/vendor/gh'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def restore(index,group,prefix,wanted,destination,expected=None):
    record=next(x for x in index['archives']if x['group']==group);assert len(record['parts'])==1
    folder=O/('download_'+destination.name);folder.mkdir(exist_ok=False)
    def fetch(name):
        a=subprocess.run([str(GH),'release','download',index['release_tag'],'--repo',index['repository'],'--pattern',name,'--dir',str(folder)],capture_output=True,text=True,timeout=30)
        assert a.returncode==0,a.stderr[-1000:]
    fetch(group+'.INVENTORY.json');part=record['parts'][0];fetch(part['name']);archive=folder/part['name']
    assert archive.stat().st_size==part['bytes']and sha(archive)==part['sha256']==record['archive_sha256']
    catalog={x['path']:x for x in read(folder/(group+'.INVENTORY.json'))['files']};destination.mkdir(exist_ok=False);rows=[]
    proc=subprocess.Popen(['zstd','-q','-dc',str(archive)],stdout=subprocess.PIPE)
    with tarfile.open(fileobj=proc.stdout,mode='r|')as stream:
        for member in stream:
            if not member.name.startswith(prefix)or member.name[len(prefix):]not in wanted:continue
            rel=member.name[len(prefix):];assert member.isfile()and '..'not in Path(rel).parts
            p=destination/rel;p.parent.mkdir(parents=True,exist_ok=True)
            with stream.extractfile(member)as source,p.open('xb')as target:shutil.copyfileobj(source,target)
            row=catalog[member.name];assert p.stat().st_size==row['bytes']and sha(p)==row['sha256']
            if expected is not None:assert row['sha256']==expected[member.name]['sha256']and row['bytes']==expected[member.name]['bytes']
            rows.append(dict(original=member.name,path=str(p.relative_to(R)),bytes=row['bytes'],sha256=row['sha256']))
    assert proc.wait(timeout=30)==0 and len(rows)==len(wanted)
    shutil.rmtree(folder);return rows
if __name__=='__main__':
    old=read(R/'experiments/v991_coordinated_components/RESTORE_REQUIREMENTS.json')
    expected={x['original']:x for x in old['files']};prefix='runs/v858_nav2_verified/v974/main_we/'
    wanted={x[len(prefix):]for x in expected}
    rows=restore(read(R/'records/nav2_v974_20261110/RECORD_INDEX.json'),'v974-single-day-dynamic-gate',prefix,wanted,O/'prior_v974',expected)
    (O/'RESTORE_RECEIPT.json').write_text(json.dumps(dict(passed=True,models=0,integrations=0,files=rows),indent=2)+'\n')
    print(json.dumps(dict(restored=len(rows),bytes=sum(x['bytes']for x in rows),models=0)))
