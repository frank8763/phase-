"""Inventory immutable local gzip transports; omit every protected inode."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from worker import R,O,h


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    assert not(O/'PLAN.json').exists()
    protected={}
    sources=['experiments/v1383_exact_timed_handoff/SOURCE_FREEZE.json','experiments/v1396_rpp_rpc_retirement/SOURCE_FREEZE.json','runs/v1393_full9390_preparation/ANALYSIS_SOURCE_FREEZE.json','runs/v1397_event_handoff_integration/EVENT_SOURCE_FREEZE.json','runs/v1397_event_handoff_integration/ROUTE_HOOK_SOURCE_FREEZE.json','runs/v1397_event_handoff_integration/BRIDGE_FIELD_SOURCE_FREEZE.json','runs/v1398_current_event_witness/INPUT_PEER_SOURCE_FREEZE.json']
    for name in sources:
        for p,sha in h.read(R/name)['files'].items():
            assert p not in protected or protected[p]==sha, 'FROZEN_SOURCE_HASH_CONFLICT'
            protected[p]=sha
    inodes=set()
    for name,sha in protected.items():
        p=R/name;assert p.is_file() and h.sha(p)==sha, 'PROTECTED_SOURCE_HASH_CHANGED:'+name
        st=p.stat();inodes.add((st.st_dev,st.st_ino))
    tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0'))
    for name in tracked:
        p=R/name
        if name and p.is_file() and not p.is_symlink():
            st=p.stat();inodes.add((st.st_dev,st.st_ino))
    groups=[];skipped=[]
    for d in sorted((R/'runs').iterdir()):
        if not d.is_dir() or d.is_symlink() or not(d/'FINALIZED.json').is_file():continue
        candidates=[d/x for x in ['ARCHIVE_INDEX.json','OFFLINE_ARCHIVE_INDEX.json']if(d/x).is_file()]
        if not candidates:continue
        index=candidates[0];z=h.read(index);parts=z.get('parts',[])
        if not parts or not all('.tar.gz.part'in x.get('name','') for x in parts):continue
        folders=[p for p in [d/'archive',d/'offline_archive',d/'closed_archive'] if all((p/x['name']).is_file() for x in parts)]
        if not folders:continue
        folder=folders[0];rows=[];reasons=[]
        for row in parts:
            p=folder/row['name'];st=p.stat();rel=str(p.relative_to(R))
            if p.is_symlink() or rel in tracked or(st.st_dev,st.st_ino)in inodes:reasons.append(dict(path=rel,reason='PROTECTED_OR_TRACKED_INODE'));continue
            assert st.st_size==row['bytes'] and h.sha(p)==row['sha256'], 'CLOSED_TRANSPORT_SHA_MISMATCH:'+rel
            rows.append(dict(path=rel,bytes=st.st_size,sha256=row['sha256'],stat=[st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns]))
        if reasons:skipped.append(dict(name=d.name,omitted=reasons));continue
        groups.append(dict(name=d.name,index_path=str(index.relative_to(R)),index_sha256=h.sha(index),parts=rows,archive_bytes=z['archive_bytes']))
    assert groups
    plan=dict(groups=groups,skipped=skipped,protected_source_hashes=protected,protected_inodes=[list(x)for x in sorted(inodes)],models=0,only_duplicate_transport=True,physical_raw_deleted=False,planned_logical_recovery_bytes=sum(g['archive_bytes']for g in groups))
    h.dump(O/'PLAN.json',plan);print(json.dumps(dict(groups=len(groups),skipped=len(skipped),transport_bytes=plan['planned_logical_recovery_bytes'],protected_sources=len(protected))))


if __name__=='__main__':main()
