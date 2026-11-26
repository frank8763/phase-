"""Source proof redirection only, preserving the original failed sync bytes."""
from pathlib import Path
import ast, hashlib, importlib.util, inspect, json, os, sys

R=Path(__file__).resolve().parents[2]
C=Path(__file__).resolve().parent
S=R/'runs/v2090_svg_persistent_counter_fixture'
D=S/'recovery'

def main():
    os.sched_setaffinity(0,{5})
    proof=json.loads((D/'SOURCE_SYNC_RECOVERED.json').read_text())
    assert proof['remote_verified']and proof['push_executed']is False
    original=D/'SOURCE_SYNC_RESULT.json'
    assert hashlib.sha256(original.read_bytes()).hexdigest()==proof['original_failed_sync_sha256']
    p=R/'experiments/v2090_svg_persistent_counter_fixture/evidence.py'
    spec=importlib.util.spec_from_file_location('frozen_source_transport_proof_recovery',p)
    h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    stage=sys.argv[1]
    if stage=='deliver':
        assert not(D/'remote_delivery').exists()
        source=inspect.getsource(h.deliver)
        needle='text=target.read_text()'
        assert source.count(needle)==1
        old="sync=read(D/'SOURCE_SYNC_RESULT.json')"
        new="sync=read(D/'SOURCE_SYNC_RECOVERED.json')if not runtime else read(D/'SOURCE_SYNC_RESULT.json')"
        source=source.replace(needle,needle+';text=text.replace('+repr(old)+','+repr(new)+')')
        ast.parse(source);scope=dict(h.__dict__);exec(compile(source,str(p),'exec'),scope)
        result=scope['deliver']()
        assert hashlib.sha256(original.read_bytes()).hexdigest()==proof['original_failed_sync_sha256']
        return result
    assert stage=='chain'
    source=inspect.getsource(h.chain).replace('SOURCE_SYNC_RESULT.json','SOURCE_SYNC_RECOVERED.json')
    ast.parse(source);scope=dict(h.__dict__);exec(compile(source,str(p),'exec'),scope)
    scope['chain']()
    return 0

if __name__=='__main__':raise SystemExit(main())
