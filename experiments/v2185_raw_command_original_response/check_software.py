"""Pure static/configuration/authority negatives; no original numeric import."""
import ast,copy,hashlib,json,subprocess,sys
from pathlib import Path
from context import R,C,S,PARENT,files,read,sha
from fixture import fixed,RECEIPT,SETUP,EVIDENCE,RESULT,CLOSURE
from profiles import plans,shadow_refused,METHODS

def main():
    source=files(PARENT/'SOURCE_FREEZE.json')
    for n in [RECEIPT,SETUP,EVIDENCE,RESULT,CLOSURE]:source[n]=sha(R/n)
    input=fixed(source);p=plans(input['cases']);assert [(r['method'],r['profile'],r['command_native'])for r in p]==[(METHODS[0],'shadow',10),(METHODS[0],'admission',5),(METHODS[1],'shadow',10),(METHODS[1],'admission',5)]
    blocked=set();shadow_refused(p[0],False,blocked);assert p[1]['method']in blocked and p[2]['method']not in blocked
    shadow_refused(p[2],True,blocked);assert p[3]['method']not in blocked
    negative=[]
    def no(name,f):
        try:f()
        except(AssertionError,KeyError,ValueError):negative.append(name)
        else:raise AssertionError('EXPECTED_REFUSAL:'+name)
    no('reordered_methods',lambda:plans(input['cases'][::-1]))
    no('missing_method',lambda:plans(input['cases'][:1]))
    no('nonboolean_gate',lambda:shadow_refused(p[0],1,set()))
    bad=dict(p[0],command_native=5);no('shortened_shadow',lambda:shadow_refused(bad,False,set()))
    bad=dict(p[1],command_native=10);no('changed_admission',lambda:shadow_refused(bad,True,set()))
    bad=dict(source);bad[EVIDENCE]='0'*64;no('altered_raw_output',lambda:fixed(bad))
    bad=dict(source);bad[RECEIPT]='0'*64;no('foreign_initial_packet',lambda:fixed(bad))
    # Entry guard actually executes and refuses before NumPy/model/ctypes.
    child=subprocess.run(['/usr/bin/python3','-B',str(C/'entry.py')],cwd=R,capture_output=True,timeout=10);assert child.returncode==77 and json.loads(child.stdout)['refused_before_numerical_import']and not child.stderr
    assert not any(n in sys.modules for n in ['numpy','ctypes','backend','numeric','mujoco','torch'])
    required=['owner.py','run_phase.py','recovery.py','readiness.py','qualify.py']
    assert all((C/n).exists()for n in required),'ALL_IMPLEMENTATION_MUST_EXIST_BEFORE_READY'
    for path in C.glob('*.py'):ast.parse(path.read_text())
    # Owner/isolation/once/error source checks, not execution with fake authority.
    o=(C/'owner.py').read_text();ns=(C/'run_phase.py').read_text();b=(C/'backend.py').read_text()
    assert "'RUNTIME_ONCE.json','COMPLETION.json','OWNED_CHILD.json'"in o and 'CHILD_IDENTITY_CHANGED_NOT_SIGNALED'in o
    assert "--unshare-all"in ns and "str(S/'RUNTIME')"in ns
    assert b.index('require_admission()')<b.index('import numpy as np')<b.index("q=load(")
    assert 'source.get(name)==sha(path)'in b and 'ANALYTIC_ALIAS_MISMATCH'in b
    assert read(S/'REQUIRED_ARRAY_FORMAT_PREFLIGHT.json')['total_stored_bytes']==1417240
    print(json.dumps(dict(passed=True,negatives=negative,positive_fixtures=4,real_host_refusal=77,original_q_model_imports_constructors_steps=0,fixed_profile_denominator=4,shadow_refusal_never_rescued=True)))
if __name__=='__main__':main()
