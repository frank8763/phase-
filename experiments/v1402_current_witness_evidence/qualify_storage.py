"""Branch evidence transaction/negative boundary qualification, zero models."""
import copy
import hashlib
import importlib.abc
import json
import os
from pathlib import Path
import sys

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','coupled_model','factory','physical','rclpy'}:raise AssertionError('ZERO_MODEL_EVIDENCE_QUALIFICATION:'+name)
sys.meta_path.insert(0,NoModel())
from branch_store import BranchStore,verified_branch
import independent_audit


def atomic(path,value):
    p=Path(path);temporary=p.with_suffix(p.suffix+'.tmp');temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temporary.replace(p)


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));O.mkdir(exist_ok=False)
    import numpy as np
    atomic(O/'QUALIFICATION_CLAIM.json',dict(models=0,analytical_native=0,physical_native=0,synthetic_zero_arrays_not_model_output=True))
    store=BranchStore(O/'branch_fixture',input_sha256='0'*64,np=np,atomic=atomic)
    states=np.zeros((201,8));ctrl=np.zeros((200,4));proof=dict(input_sha256='0'*64,complete_native=200,before_native=17)
    negative=[]
    def reject(name,fn):
        try:fn()
        except AssertionError:negative.append(name)
        else:raise AssertionError('INVALID_EVIDENCE_ACCEPTED:'+name)
    reject('incomplete200_branch',lambda:store.append(proof,states[:-1],ctrl))
    reject('wrong_input_identity',lambda:store.append(dict(proof,input_sha256='1'*64),states,ctrl))
    store.append(proof,states,ctrl);a,b=verified_branch(store.folder,store.rows[0],np);assert np.array_equal(a,states)and np.array_equal(b,ctrl)
    reject('origin_gap',lambda:store.append(dict(proof,before_native=19),states,ctrl))
    altered=copy.deepcopy(store.rows[0]);altered['sha256']='f'*64;reject('changed_branch_SHA',lambda:verified_branch(store.folder,altered,np))
    store.close();reject('append_after_close',lambda:store.append(dict(proof,before_native=18),states,ctrl))
    reject('unregistered_model_audit',lambda:independent_audit.audit({}, {}, {}, None,authority={'mode':'DISABLED'},lock=None))
    index=json.loads((store.folder/'INDEX.json').read_text());assert index['closed']and len(index['branches'])==1 and index['complete_branch_native_saved']==200
    result=dict(passed=True,transactional_npz_and_SHA_index_roundtrip=True,negative_cases=negative,complete_native_count_is_software_fixture_only=True,
                models=0,analytical_native=0,physical_native=0,replay_native=0,model_audit_not_qualified=True,physical_admission=False)
    atomic(O/'EVIDENCE_STORAGE_QUALIFICATION.json',result)
    files=[C/'branch_store.py',C/'independent_audit.py',C/'production_entry.py',C/'qualify_storage.py',C/'PROTOCOL.md']
    atomic(O/'EVIDENCE_SOURCE_FREEZE.json',dict(files={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files},qualification='runs/v1402_current_witness_evidence/EVIDENCE_STORAGE_QUALIFICATION.json',numerical_model_audit_not_qualified=True,physical_admission=False))
    print(json.dumps(result))


if __name__=='__main__':main()
