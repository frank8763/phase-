"""Download exact verified V1337 archive, extract only saved diagnostic inputs."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

R=Path(__file__).resolve().parents[2];O=R/'runs/v1340_overnight_preparation';GH=R/'tools/phase_storage_20261107/vendor/gh'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    index=json.loads((R/'records/v1337_margin_route_20261118/RECORD_INDEX.json').read_text())
    inventory=json.loads((R/'records/v1337_margin_route_20261118/SOURCE_INVENTORY.json').read_text())['files']
    folder=O/'saved_input_restore';folder.mkdir(exist_ok=False)
    release=json.loads(subprocess.check_output([str(GH),'api','repos/frank8763/phase-/releases/tags/'+index['release_tag']],cwd=R,text=True,timeout=20))
    assets={a['name']:a for a in release['assets']}
    def get(part):
        dest=folder/part['name'];asset=assets[part['name']]
        with dest.open('xb') as stream:
            result=subprocess.run([str(GH),'api',f'repos/frank8763/phase-/releases/assets/{asset["id"]}','-H','Accept: application/octet-stream'],cwd=R,stdout=stream,stderr=subprocess.PIPE,timeout=40)
        assert result.returncode==0 and dest.stat().st_size==part['bytes'] and sha(dest)==part['sha256']
        return part['name']
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(get,index['parts']))
    archive=folder/index['archive_name']
    with archive.open('xb') as stream:
        for part in index['parts']:stream.write((folder/part['name']).read_bytes())
    assert sha(archive)==index['archive_sha256']
    wanted={x['path']:x for x in inventory};seen=set();selected=[]
    names={'ROS_COMMANDS.json','INITIAL_PACKET.json','FINAL_PACKET.json','NATIVE_TRACE.npz','SENSORS.json.gz','SETUP.json'}
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            item=wanted[member.name];seen.add(member.name)
            if item.get('kind')=='symlink':assert member.issym() and member.linkname==item['target'];continue
            data=tar.extractfile(member).read();assert hashlib.sha256(data).hexdigest()==item['sha256']
            if Path(member.name).name in names:
                dest=folder/Path(member.name).name;dest.write_bytes(data);selected.append(dict(path=str(dest.relative_to(R)),sha256=item['sha256'],bytes=len(data)))
    assert len(seen)==32 and len(selected)==6
    proof=dict(passed=True,all_archive_members_verified=32,selected=selected,models=0)
    (O/'SAVED_INPUT_RESTORE.json').write_text(json.dumps(proof,indent=2)+'\n')
    for part in index['parts']:(folder/part['name']).unlink()
    archive.unlink();print(json.dumps(dict(passed=True,selected=6,models=0)))


if __name__=='__main__':main()
