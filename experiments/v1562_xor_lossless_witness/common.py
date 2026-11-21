"""Immutable source composition and small-scope bounded metadata; no model work."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
BASE=R/'runs/v1559_causal_source_record/SOURCE_FREEZE.json'
INPUT=R/'runs/v1532_observer_epoch_origin/source_target/METHOD_INPUT.json'
SETUP=R/'runs/v1479_retirement_scope_binding/first_event/bridge_events/event0000/SETUP.json'
read=lambda p:json.loads(p.read_text())
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as stream:
        for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
    return h.hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def put(path,value,maximum=65536):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n';assert len(raw)<=maximum
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_bytes(raw);tmp.replace(path)
def limits():return read(C/'LIMITS.json')
def sources():
    spec=read(O/'SOURCE_FREEZE.json');assert spec['base_manifest_sha256']==sha(BASE)
    values=read(BASE)['files'].copy()
    for name,identity in spec['files'].items():
        assert name not in values or values[name]==identity;values[name]=identity
    assert all(sha(R/name)==identity for name,identity in values.items()),'STOP_COMPONENT_FROZEN_SOURCE_CHANGED'
    return values
def inputs():
    path=R/'runs/v1550_canonical_observer_policy/source_target/RESPONSE_METHOD.json'
    fixed=read(O/'FIXED_INPUTS.json')
    assert sha(path)==fixed['response_method_file_sha256']and sha(SETUP)==fixed['setup_sha256']
    current=read(path);clean=dict(current);identity=clean.pop('response_method_sha256')
    assert digest(clean)==identity==fixed['response_method_sha256']
    return current,read(SETUP)
def guard():return load('v1532_original_immutable_guard_only',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
def bootstrap():
    import sys
    source=R/'experiments/v1067_causal_replan_brake_reserve/resource_policy.py';assert sha(source)==read(BASE)['files'][str(source.relative_to(R))]
    sys.path.insert(0,str(source.parent));import resource_policy
    assert Path(resource_policy.__file__).resolve()==source
    return resource_policy.apply()
def usage():
    seen=set();total=0
    for root,ds,fs in os.walk(R/'runs',followlinks=False):
        for p in [Path(root)]+[Path(root)/name for name in fs]:
            st=p.lstat();key=st.st_dev,st.st_ino
            if key not in seen:seen.add(key);total+=st.st_blocks*512
    return total
