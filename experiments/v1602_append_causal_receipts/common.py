"""Source target composition only; no numerical authority."""
import hashlib
import importlib.util
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
BASE=R/'runs/v1599_readonly_context_durability/SOURCE_FREEZE.json'
read=lambda p:json.loads(Path(p).read_text())

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as stream:
        for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
    return h.hexdigest()

def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def put(path,value,maximum=65536):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'
    assert len(raw)<=maximum
    t=path.with_name(path.name+'.tmp');t.write_bytes(raw);t.replace(path)

def bootstrap():
    import sys
    path=R/'experiments/v1067_causal_replan_brake_reserve/resource_policy.py'
    assert sha(path)==read(BASE)['files'][str(path.relative_to(R))]
    sys.path.insert(0,str(path.parent));import resource_policy
    assert Path(resource_policy.__file__).resolve()==path
    return resource_policy.apply()

def guard():return load('v1602_original_immutable_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)


def draft_sources():
    values=read(BASE)['files'].copy()
    asset=read(C/'MESA_BINDING.json')
    assert sha(R/asset['real_path'])==asset['real_sha256']
    values[asset['real_path']]=asset['real_sha256']
    for n,h in read(C/'REUSE_INPUTS.json').items():
        assert sha(R/n)==h
        if n in values:assert values[n]==h
        values[n]=h
    for p in C.iterdir():
        if p.is_file():values[str(p.relative_to(R))]=sha(p)
    p=R/'runs/v1577_goal_bound_segment_bridge/SCIENTIFIC_REVISION_REGISTRATION.json'
    values[str(p.relative_to(R))]=sha(p)
    p=R/'runs/v1382_weekend_campaign/STORAGE_AUTHORIZATION_15GIB_20261122.json'
    values[str(p.relative_to(R))]=sha(p)
    return values

def sources():
    value=read(O/'SOURCE_FREEZE.json')
    assert value['base_manifest_sha256']==sha(BASE)
    assert all(sha(R/n)==h for n,h in value['files'].items())
    return value['files']


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
