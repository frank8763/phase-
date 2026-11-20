"""Explicit old/new link-text verification and conflicting-schema rejection."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
from resume import R,C,O,old,verify_stream


class Reader(io.BytesIO):
    def __init__(self,data):super().__init__(data);self.digest=hashlib.sha256()
    def read(self,n=-1):
        b=super().read(n);self.digest.update(b);return b


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));O.mkdir(exist_ok=False)
    memory=io.BytesIO();data=b'archive fixture'
    with tarfile.open(fileobj=memory,mode='w:gz')as t:
        m=tarfile.TarInfo('member');m.size=len(data);t.addfile(m,io.BytesIO(data))
        m=tarfile.TarInfo('link');m.type=tarfile.SYMTYPE;m.linkname='member';t.addfile(m)
    payload=memory.getvalue();common=dict(path='member',bytes=len(data),sha256=hashlib.sha256(data).hexdigest());cases=[]
    for row in [dict(path='link',symlink='member'),dict(path='link',kind='symlink',target='member',bytes=6)]:
        index=dict(files=[common,row],archive_sha256=hashlib.sha256(payload).hexdigest());assert verify_stream(Reader(payload),index)==2;cases.append(row)
    negative=[]
    for label,row in [('conflicting_schema',dict(path='link',symlink='member',kind='symlink',target='other',bytes=5)),('changed_target',dict(path='link',kind='symlink',target='other',bytes=5)),('wrong_target_length',dict(path='link',kind='symlink',target='member',bytes=7))]:
        try:verify_stream(Reader(payload),dict(files=[common,row],archive_sha256=hashlib.sha256(payload).hexdigest()))
        except AssertionError:negative.append(label)
        else:raise AssertionError('BAD_LINK_ACCEPTED')
    # PLAN is the same protected 7-group source plan, not an expanded cleanup.
    old_plan=R/'runs/v1399_closed_transport_recovery/PLAN.json';os.link(old_plan,O/'PLAN.json')
    q=dict(passed=True,modern_and_legacy_explicit_link_schemas=True,negative_cases=negative,models=0,old_claim_error_freeze_preserved=True)
    old.h.dump(O/'LINK_SCHEMA_QUALIFICATION.json',q);old.h.dump(O/'QUALIFICATION.json',q)
    files=[C/'resume.py',C/'qualify.py',old_plan,R/'experiments/v1399_closed_transport_recovery/worker.py',R/'experiments/v1389_idempotent_storage_transfer/resume.py',R/'experiments/v1382_weekend_campaign/deliver_full9390_preparation.py',R/'experiments/v1382_weekend_campaign/storage_preserve.py']
    old.h.dump(O/'SOURCE_FREEZE.json',dict(files={str(p.relative_to(R)):old.h.sha(p)for p in files},models=0));print(json.dumps(q))


if __name__=='__main__':main()
