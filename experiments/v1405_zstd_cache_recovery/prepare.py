"""Exact closed zstd transports and eligible original-inventory offline cache."""
import json
import os
from pathlib import Path
import subprocess
from worker import R,O,h


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));O.mkdir(exist_ok=False)
    protected={}
    for name in ['runs/v1401_model_origin_qualification/SOURCE_FREEZE.json','runs/v1403_current_witness_cli/SOURCE_FREEZE.json','runs/v1404_route_bridge_session/SOURCE_FREEZE.json']:
        for p,sha in h.read(R/name)['files'].items():
            assert p not in protected or protected[p]==sha;protected[p]=sha
    inodes=set()
    for p,sha in protected.items():
        path=R/p;assert h.sha(path)==sha;st=path.stat();inodes.add((st.st_dev,st.st_ino))
    tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0'))
    for p in tracked:
        path=R/p
        if p and path.is_file()and not path.is_symlink():st=path.stat();inodes.add((st.st_dev,st.st_ino))
    def row(path,expected):
        assert not path.is_symlink()and path.is_file();st=path.stat();name=str(path.relative_to(R))
        if name in tracked or(st.st_dev,st.st_ino)in inodes:return None
        assert st.st_size==expected['bytes']and h.sha(path)==expected['sha256'], 'OLD_CACHE_OR_TRANSPORT_CHANGED:'+name
        return dict(path=name,bytes=st.st_size,sha256=expected['sha256'],stat=[st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns])
    groups=[];omitted=[]
    for name in ['v1121_coupled_route_night','v1122_cache_entry_relay']:
        base=R/'runs'/name;assert h.read(base/'FINALIZED.json')['closed']
        index=base/'ARCHIVE.json';z=h.read(index);inventory=base/'cloud'/(z['group']+'.INVENTORY.json');members={x['path']:x for x in h.read(inventory)['files']}
        parts=[row(base/'cloud'/x['name'],x)for x in z['parts']];assert all(parts)
        raw=[]
        if name=='v1122_cache_entry_relay':
            for root,dirs,files in os.walk(base/'offline',followlinks=False):
                dirs[:]=[d for d in dirs if not Path(root,d).is_symlink()]
                for filename in files:
                    p=Path(root)/filename;relative=str(p.relative_to(R))
                    if p.is_symlink()or relative not in members:omitted.append(relative);continue
                    value=row(p,members[relative])
                    if value is None:omitted.append(relative)
                    else:raw.append(value)
        groups.append(dict(name=name,index_path=str(index.relative_to(R)),index_sha256=h.sha(index),inventory_path=str(inventory.relative_to(R)),inventory_sha256=h.sha(inventory),parts=parts,raw_files=raw,archive_bytes=z['archive_bytes']))
    plan=dict(groups=groups,protected_source_hashes=protected,protected_inodes=[list(v)for v in sorted(inodes)],omitted=omitted,
              planned_logical_transport_bytes=sum(g['archive_bytes']for g in groups),planned_obsolete_offline_bytes=sum(x['bytes']for g in groups for x in g['raw_files']),models=0)
    h.dump(O/'PLAN.json',plan);print(json.dumps(dict(groups=len(groups),transport_bytes=plan['planned_logical_transport_bytes'],offline_bytes=plan['planned_obsolete_offline_bytes'],offline_files=sum(len(g['raw_files'])for g in groups),omitted=len(omitted),models=0)))


if __name__=='__main__':main()
