"""New zero-model transfer continuation; closed V1399 remains immutable."""
import fcntl
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tarfile
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
spec=importlib.util.spec_from_file_location('v1400_original_bounded_recovery',R/'experiments/v1399_closed_transport_recovery/worker.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)


def link_target(row):
    modern=row.get('symlink');legacy=row.get('target')if row.get('kind')=='symlink'else None
    assert modern is None or isinstance(modern,str)
    assert legacy is None or isinstance(legacy,str)
    assert modern is None or legacy is None or modern==legacy, 'ARCHIVE_LINK_SCHEMA_CONFLICT'
    return modern if modern is not None else legacy


def verify_stream(reader,index):
    wanted={r['path']:r for r in index['files']};assert len(wanted)==len(index['files']);seen=set()
    with tarfile.open(fileobj=reader,mode='r|gz')as archive:
        for member in archive:
            assert member.name in wanted and member.name not in seen, 'ARCHIVE_UNKNOWN_OR_DUPLICATE_MEMBER'
            row=wanted[member.name];target=link_target(row)
            if target is not None:
                assert member.issym() and member.linkname==target, 'ARCHIVE_LINK_CHANGED'
                if row.get('kind')=='symlink':assert row['bytes']==len(target.encode()), 'ARCHIVE_LINK_TEXT_LENGTH'
            else:
                assert member.isfile() and member.size==row['bytes'], 'ARCHIVE_MEMBER_SIZE'
                digest=hashlib.sha256();stream=archive.extractfile(member)
                for block in iter(lambda:stream.read(1024**2),b''):digest.update(block)
                assert digest.hexdigest()==row['sha256'], 'ARCHIVE_MEMBER_SHA'
            seen.add(member.name)
    while reader.read(1024**2):pass
    assert seen==set(wanted) and reader.digest.hexdigest()==index['archive_sha256'], 'ARCHIVE_REASSEMBLY_SHA_OR_MEMBERS'
    return len(seen)


def main():
    assert old.h.read(O/'LINK_SCHEMA_QUALIFICATION.json')['passed']
    assert old.h.read(R/'runs/v1399_closed_transport_recovery/ERROR.json')['completed']==[]
    old.O=O;old.h.O=O;old.h.W=O;old.verify_stream=verify_stream
    old.main()
    # V1399's failed first group left hardlinks, which are duplicate transport
    # paths too. They may be removed only after the new COMPLETE proof/index.
    removed=[]
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);parent=old.h.read(R/'runs/v1382_weekend_campaign/LEDGER.json')
        assert parent['active_round']is None and old.h.sha(R/'REVIEW_PENDING')==parent['review_pending_original_bytes_sha256']
        for group in old.h.read(O/'PLAN.json')['groups']:
            assert old.h.read(O/group['name']/'FINALIZED.json')['passed']
            for row in group['parts']:
                p=R/'runs/v1399_closed_transport_recovery'/group['name']/'upload'/(group['name']+'__'+Path(row['path']).name)
                if p.exists():
                    st=p.stat();assert not p.is_symlink() and [st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns]==row['stat'] and old.h.sha(p)==row['sha256']
                    p.unlink();removed.append(str(p.relative_to(R)))
    old.h.dump(O/'PRIOR_FAILED_TRANSPORT_LINK_CLEANUP.json',dict(passed=True,removed=removed,only_fully_remote_verified_duplicate_links=True,models=0))


if __name__=='__main__':main()
