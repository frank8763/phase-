"""Real complete entry imports and CPU rendering backend, zero vehicle models."""
import importlib.util
import subprocess
import sys
from component_context import *
from campaign import native_environment,peer_environment
def main():
    spec=importlib.util.spec_from_file_location('phase_sampling_isolation',R/'tools/isolate.py');isolation=importlib.util.module_from_spec(spec);spec.loader.exec_module(isolation)
    commands=[('backend',isolation.command(C/'backend_check.py',writable=True),native_environment()),
        ('native',[sys.executable,'-B',str(C/'native_component.py'),str(C/'ENTRY.json'),'--entry-check'],native_environment())]
    ros,env=peer_environment();commands.append(('peer',ros.command(['/usr/bin/python3.12','-B',str(C/'fault_peer.py'),str(C/'ENTRY.json'),'--entry-check']),env))
    # Audit dependencies are checked in the same runtime that will produce the peer receipt.
    commands.append(('audit_import',ros.command(['/usr/bin/python3.12','-B',str(C/'qualify_entry.py'),'--audit-import']),env))
    proofs=[]
    for name,command,env in commands:
        p=subprocess.run(command,cwd=R,env=env,capture_output=True,text=True,timeout=45)
        (O/(name+'_entry.console')).write_text(p.stdout+p.stderr)
        assert p.returncode==0,'ENTRY_FAILED '+name
        proof=json.loads(p.stdout.strip().splitlines()[-1]);assert proof['passed'];proofs.append(dict(entry=name,proof=proof))
    assert sources();dump(O/'FULL_ENTRY_QUALIFICATION.json',dict(passed=True,entries=proofs,models=0,physical_native=0,
        tested_source_hashes={str(p.relative_to(R)):sha(p) for p in C.glob('*.py')}))
    print(json.dumps(dict(passed=True,entries=len(proofs),models=0)))
if __name__=='__main__':
    if '--audit-import' in sys.argv:
        import audit_entry
        import sampling_audit
        print(json.dumps(dict(passed=True,models=0,physical_native=0,python=sys.version,numpy=__import__('numpy').__version__)))
    else:main()
