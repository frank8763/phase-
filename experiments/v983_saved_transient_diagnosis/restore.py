"""Restore only the19 saved inputs from the original verified V982 archive."""
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v983_saved_transient_diagnosis';GH=R/'tools/phase_storage_20261107/vendor/gh'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    O.mkdir(exist_ok=True);index=json.loads((R/'records/nav2_v982_20261110/RECORD_INDEX.json').read_text());group=index['archives'][0]
    def gh(args):
        job=subprocess.run([str(GH),*args,'--repo',index['repository']],capture_output=True,text=True,timeout=30)
        assert job.returncode==0,job.stderr[-1200:]
    manifest=O/(group['group']+'.INVENTORY.json')
    if not manifest.exists():gh(['release','download',index['release_tag'],'--pattern',manifest.name,'--dir',str(O)])
    catalog={r['path']:r for r in json.loads(manifest.read_text())['files']}
    prefix='runs/v858_nav2_verified/v982/component_0/'
    names=['COMPONENT_REFERENCE.json','ONLINE_TRACKING_FAULT.json','COMMAND_TUBES.json.gz','COMMANDS.json','ROS_RESULT.json','RESULT.json','NATIVE_ACCOUNTING.json','INGRESS.json.gz','physics/NATIVE_TRACE.npz','physics/BODY_COMMANDS.json','physics/SETUP.json','physics/CONTACTS.json.gz','physics/REPLAY.json','physics/PREFIX_RESTORE.json','physics/MODEL_BUILD_CONTRACT.json','physics/EXACT_SENSOR_BINDING.json','physics/SELECTED_NATIVE_BINDING.json']
    wanted={prefix+n:n for n in names}
    for name in ['physics/NATIVE_TRACE.npz','physics/BODY_COMMANDS.json']:wanted['runs/v982_precise_recovery_gate/prior_v974/'+name]='prior/'+name
    rows=[dict(original=name,path=str((O/local).relative_to(R)),sha256=catalog[name]['sha256'],bytes=catalog[name]['bytes'])for name,local in wanted.items()]
    if not all((R/row['path']).is_file()and sha(R/row['path'])==row['sha256']for row in rows):
        assert len(group['parts'])==1;part=group['parts'][0];archive=O/part['name']
        if not archive.exists():gh(['release','download',index['release_tag'],'--pattern',part['name'],'--dir',str(O)])
        assert archive.stat().st_size==part['bytes']and sha(archive)==part['sha256']==group['archive_sha256']
        decoder=subprocess.Popen(['zstd','-q','-dc',str(archive)],stdout=subprocess.PIPE);seen=set()
        with tarfile.open(fileobj=decoder.stdout,mode='r|')as stream:
            for member in stream:
                if member.name not in wanted:continue
                assert member.isfile()and '..'not in Path(member.name).parts
                dest=O/wanted[member.name];dest.parent.mkdir(parents=True,exist_ok=True)
                if dest.exists():assert sha(dest)==catalog[member.name]['sha256']
                else:
                    with stream.extractfile(member)as source,dest.open('xb')as target:shutil.copyfileobj(source,target)
                assert sha(dest)==catalog[member.name]['sha256'];seen.add(member.name)
        assert decoder.wait()==0 and seen==set(wanted);archive.unlink()
    (O/'REMOTE_RESTORE_RECEIPT.json').write_text(json.dumps(dict(passed=True,files=rows,models=0,integrations=0,archive_sha256=group['archive_sha256']),indent=2)+'\n')
    print(json.dumps(dict(restored_inputs=19,models=0,integrations=0,already_saved_physical_data_only=True)))
if __name__=='__main__':main()
