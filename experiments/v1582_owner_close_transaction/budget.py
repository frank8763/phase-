"""Exact new fixed-cap scope; allruns include history and transport peaks."""
import hashlib
import json
import os
from pathlib import Path
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def limits():
    v=read(C/'LIMITS.json')
    assert v['scientific_revision']==12 and v['maximum_task_wall_s']==5400
    assert v['maximum_actual_native']==v['maximum_own_replay_native']==v['maximum_allocator_recomputations']==40000
    assert v['maximum_current_reserve_native']==8200*2200
    assert v['maximum_private_native_all_categories']==8200+2*5300800+8200*2200
    assert sum(v['writer_scope_caps_MiB'].values())==224
    assert v['full_scope_additional_bytes']==(224+2+240+32+512)*1024**2
    return v


def usage():
    seen=set();total=0
    for root,ds,fs in os.walk(R/'runs',followlinks=False):
        for p in [Path(root)]+[Path(root)/name for name in fs]:
            s=p.lstat();key=s.st_dev,s.st_ino
            if key not in seen:seen.add(key);total+=s.st_blocks*512
    return total


def preflight():
    v=limits();used=usage();peak=used+v['full_scope_additional_bytes']
    assert peak<10*1024**3,'GOAL_BOUND_FULL_SCOPE_EVIDENCE_ARCHIVE_DOWNLOAD_ROOT_PEAK'
    return dict(allruns_inode_allocated_bytes=used,full_reserved_peak_bytes=peak,limit_bytes=10*1024**3,
        models=0,old_scope_not_reused_as_admission=True)
