"""Restore selected V974 evidence after exact archive and member SHA verification."""
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v987_bounded_startup_components';GH=R/'tools/phase_storage_20261107/vendor/gh'
PREFIX='runs/v858_nav2_verified/v974/main_we/'
WANTED={'TASK.json','RECOVERY_CORRIDORS.json','MOTION_ENVELOPE.json.gz','RESULT.json',
        'physics/BODY_COMMANDS.json','physics/NATIVE_TRACE.npz','physics/INITIAL_STATE.npz','physics/SETUP.json',
        'physics/CONTACTS.json.gz','physics/SENSORS.json.gz','physics/MODEL_BUILD_CONTRACT.json',
        'physics/EXACT_SENSOR_BINDING.json','physics/SELECTED_NATIVE_BINDING.json'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    if not(O/'USER_APPROVAL.json').exists():raise PermissionError('V987_RESTORE_WAITS_FOR_REVIEWABLE_GATE_APPROVAL')
    assert not(O/'ROUND_WINDOW.json').exists(),'RESTORE_MUST_PRECEDE_MODEL_WINDOW'
    index=json.loads((R/'records/nav2_v974_20261110/RECORD_INDEX.json').read_text())
    record=next(x for x in index['archives']if x['group']=='v974-single-day-dynamic-gate')
    manifest=O/(record['group']+'.INVENTORY.json');catalog={x['path']:x for x in json.loads(manifest.read_text())['files']}
    part=record['parts'][0];assert len(record['parts'])==1
    archive=O/part['name']
    result=subprocess.run([str(GH),'release','download',index['release_tag'],'--repo',index['repository'],'--pattern',part['name'],'--dir',str(O)],capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr[-1000:]
    assert archive.stat().st_size==part['bytes']and sha(archive)==part['sha256']==record['archive_sha256']
    out=O/'prior_v974';out.mkdir(exist_ok=False);restored=[]
    decoder=subprocess.Popen(['zstd','-q','-dc',str(archive)],stdout=subprocess.PIPE)
    with tarfile.open(fileobj=decoder.stdout,mode='r|')as stream:
        for member in stream:
            if not member.name.startswith(PREFIX)or member.name[len(PREFIX):]not in WANTED:continue
            relative=member.name[len(PREFIX):];assert member.isfile()and '..'not in Path(relative).parts
            target=out/relative;target.parent.mkdir(parents=True,exist_ok=True)
            with stream.extractfile(member)as source,target.open('xb')as destination:shutil.copyfileobj(source,destination)
            expected=catalog[member.name];assert sha(target)==expected['sha256']and target.stat().st_size==expected['bytes']
            restored.append(dict(original=member.name,path=str(target.relative_to(R)),sha256=expected['sha256'],bytes=expected['bytes']))
    assert decoder.wait()==0 and len(restored)==len(WANTED)
    required=json.loads((Path(__file__).parent/'RESTORE_REQUIREMENTS.json').read_text())
    assert required['archive_sha256']==record['archive_sha256']
    assert sorted(restored,key=lambda x:x['path'])==sorted(required['files'],key=lambda x:x['path'])
    restored=required['files']
    (O/'RESTORE_RECEIPT.json').write_text(json.dumps(dict(passed=True,files=restored,models=0,integrations=0),indent=2)+'\n')
    archive.unlink()
    print(json.dumps(dict(restored=len(restored),bytes=sum(x['bytes']for x in restored),models=0)))
if __name__=='__main__':main()
