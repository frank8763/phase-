"""Complete branch first, attempted native row, then actual applied receipt."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

R=Path(__file__).resolve().parents[2]


def encode(value):
    def native(v):
        if hasattr(v,'tolist'):return v.tolist()
        if hasattr(v,'item'):return v.item()
        raise TypeError(type(v).__name__)
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False,default=native)


class EvidenceSink:
    def __init__(self,folder,*,identity,np,atomic,maximum_branches,quota):
        self.folder=Path(folder);assert self.folder.is_relative_to(R/'runs') and not self.folder.exists()
        self.quota=quota;quota.admit(32768,"OPEN_ACTUAL_RECEIPT_SINK")
        self.folder.mkdir();self.identity=identity;self.atomic=atomic;self.closed=False;self.pending=None
        self.before_count=0;self.after_count=0;self.last_native=None
        p=Path(__file__).with_name('branch_store.py')
        spec=importlib.util.spec_from_file_location('v1415_original_full_branch_stream',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        self.store=m.BranchStore(self.folder/'branches',input_sha256=identity,np=np,atomic=atomic,maximum_branches=maximum_branches,quota=quota)
        self.journal=(self.folder/'APPLIED_JOURNAL.jsonl').open('x',buffering=1)

    def reserve_complete(self,proof,states,ctrl):
        assert not self.closed and self.pending is None
        assert proof['complete_native']==200 and type(proof['passed'])is bool
        bound=copy.deepcopy(proof);bound['input_sha256']=self.identity
        self.store.append(bound,states,ctrl)

    def reserve_partial(self,proof,states,ctrl):
        assert not self.closed
        index=len(self.store.rows);path=self.folder/('PARTIAL_RESERVE_%06d.npz'%index)
        assert not path.exists()
        self.quota.save_npz(path.with_suffix('.npz.pending'),dict(states=states,ctrl=ctrl),self.store.np)
        path.with_suffix('.npz.pending').replace(path)
        self.atomic(self.folder/('PARTIAL_RESERVE_%06d.json'%index),dict(proof,arrays_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),states_shape=list(states.shape),ctrl_shape=list(ctrl.shape),not_complete_certificate=True))

    def before(self,row,proof,states,ctrl):
        assert not self.closed and self.pending is None and row['applied'] is False
        assert self.last_native is None or row['before_native']==self.last_native+1
        assert proof['before_native']==row['before_native'] and proof['source_packet_sha256']==row['source_packet_sha256']
        assert proof['passed'] is True and proof['complete_native']==200
        assert self.store.rows and self.store.rows[-1]['proof']['before_native']==row['before_native']
        assert self.store.rows[-1]['proof']['source_packet_sha256']==row['source_packet_sha256'],'ADMITTED_RESERVE_NOT_ALREADY_PERSISTED'
        value=copy.deepcopy(row);raw=encode(value);self.quota.admit(2*len(raw.encode())+16384,'BEFORE_ACTUAL_RECEIPT');self.pending=(row['before_native'],hashlib.sha256(raw.encode()).hexdigest(),value)
        self.journal.write(encode(dict(kind='BEFORE_NATIVE',row=value,source_row_sha256=self.pending[1]))+'\n');self.journal.flush();self.before_count+=1

    def after(self,row):
        assert not self.closed and self.pending is not None and row['applied'] is True
        tick,identity,before=self.pending
        assert row['before_native']==tick
        for key,value in before.items():
            if key!='applied':assert row[key]==value,'APPLIED_RECEIPT_SOURCE_ROW_CHANGED'
        self.quota.admit(2*len(encode(row).encode())+16384,'AFTER_ACTUAL_RECEIPT')
        self.journal.write(encode(dict(kind='AFTER_NATIVE',row=copy.deepcopy(row),source_row_sha256=identity))+'\n');self.journal.flush()
        self.after_count+=1;self.last_native=tick;self.pending=None

    def close(self,accounting):
        if self.closed:return
        self.store.close();self.journal.close();self.closed=True
        self.atomic(self.folder/'EVIDENCE_INDEX.json',dict(closed=True,input_sha256=self.identity,before_native_rows=self.before_count,after_native_rows=self.after_count,
                    incomplete_receipt_native=None if self.pending is None else self.pending[0],complete_reserved_branches=len(self.store.rows),reserved_without_before_native_rows=len(self.store.rows)-self.before_count,accounting=copy.deepcopy(accounting),
                    journal_sha256=hashlib.sha256((self.folder/'APPLIED_JOURNAL.jsonl').read_bytes()).hexdigest(),physical_admission=False))
