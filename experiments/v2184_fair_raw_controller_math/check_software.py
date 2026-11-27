"""Pure failure/capacity checks. Never run controller bodies or load a DLL."""
import ast,copy,gzip,hashlib,io,json,os,struct,subprocess,sys,tarfile
from pathlib import Path
from context import R,C,S,source_files,sha
from fixture import build,strict_domain,RECEIPT
from recovery import verify_members,packed,inventory

def main():
    inherited=source_files(R/'runs/v2180_fresh_projection_component/SOURCE_FREEZE.json')
    from readiness import candidate
    old,delta=candidate();source={**old,**delta};common,known=build(source)
    assert common['historical_timestamps_preserved']and common['actual_current_observation_or_physical_authority']is False
    assert len(common['scan']['ranges'])==32 and len(common['local_rear_path'])>=2
    assert strict_domain(.05,0.,1,source)==[.05,0.,False]
    assert strict_domain(-.05,0.,-1,source)==[-.05,0.,False]
    negatives=0
    def rejects(f):
        nonlocal negatives
        try:f()
        except (AssertionError,ValueError,TypeError,KeyError,tarfile.TarError,EOFError):negatives+=1
        else:raise AssertionError('EXPECTED_SOFTWARE_REFUSAL_NOT_OBSERVED')
    for args in [(.101,0.,1),(.05,.1,1),(0.,.01,1),(-.05,0.,1),(float('nan'),0.,1),(float('inf'),0.,1)]:rejects(lambda a=args:strict_domain(*a,source))
    wrong=dict(source);wrong[RECEIPT]='0'*64;rejects(lambda:build(wrong))
    # The real source hierarchy has a 2,141,384-byte inherited freeze; it is
    # allowed only through the bounded4MiB SOURCE_FREEZE parser, not read().
    assert len(inherited)==29655
    rejects(lambda:source_files(C/'context.py'))
    # In-memory exact source archive readback and corruption/omission rejection.
    rows=inventory([C/'fixture.py',C/'entry.py']);raw=packed(rows)
    index=dict(archive_bytes=len(raw),archive_sha256=hashlib.sha256(raw).hexdigest(),files=rows)
    verify_members(raw,index)
    bad=bytearray(raw);bad[len(bad)//2]^=1;rejects(lambda:verify_members(bytes(bad),index))
    other=copy.deepcopy(index);other['files']=other['files'][:-1];rejects(lambda:verify_members(raw,other))
    other=copy.deepcopy(index);other['files'][0]['sha256']='0'*64;rejects(lambda:verify_members(raw,other))
    other=copy.deepcopy(index);other['files'][0]['bytes']+=1;rejects(lambda:verify_members(raw,other))
    # Fixed maximum lossless peer console (cap plus one read chunk) and maximum
    #128x5 trajectory; deterministic high entropy bytes avoid compression credit.
    entropy=b''.join(hashlib.sha256(struct.pack('<I',i)).digest()for i in range(1400))
    evidence=dict(common_historical_input=common,methods=[dict(stdout_lossless_hex=entropy[:36864].hex(),stderr_lossless_hex='',console_complete=False,unknown_counters=True),dict(trajectory_shape=[128,5],trajectory_f64_bytes_hex=entropy[:5120].hex(),failed=True)],first_error={'error':'X'*2048})
    packed_size=len(gzip.compress(json.dumps(evidence,sort_keys=True,separators=(',',':')).encode(),mtime=0));assert packed_size<=56*1024
    # Inspect source contracts without executing native/math bodies.
    trees={p.name:ast.parse(p.read_text())for p in C.glob('*.py')}
    recovery=(C/'recovery.py').read_text();owner=(C/'owner.py').read_text();worker=(C/'rpp_worker.py').read_text()
    assert 'WEEKEND_IO_CLOSED_AFTER09'in recovery and 'OPERATION_ALREADY_CLAIMED_NO_AUTOMATIC_RETRY'in recovery
    assert "st.st_mtime_ns,st.st_dev,st.st_ino"in recovery and "p.unlink()"in recovery
    assert 'CHILD_IDENTITY_CHANGED_NOT_SIGNALED'in owner and 'REVIEW_CHANGED_EXTERNALLY_NOT_OVERWRITTEN'in owner
    assert worker.index('numerical_admission()')<worker.index('import ctypes')<worker.index('ctypes.CDLL(')
    assert worker.index('newmaps=new  # Preserve')<worker.index('categories[name]=scope.classify')
    assert "categories.get(name)=='exact_SHA_ELF'"in worker
    # Actual host CLI refuses before numpy/ctypes imports; no fake admission.
    p=subprocess.run(['/usr/bin/python3','-B',str(C/'entry.py')],cwd=R,capture_output=True,timeout=10)
    assert p.returncode==77 and json.loads(p.stdout)['refused_before_numerical_import']and len(p.stderr)==0
    assert not any((S/n).exists()for n in ['NUMERICAL_ADMISSION.json','SOURCE_ONCE.json','RUNTIME_ONCE.json'])
    print(json.dumps(dict(passed=True,counts=dict(positive=7,negative=negatives,real_host_unadmitted_cli=1,source_AST_files=len(trees)),worst_fixed_console_trajectory_capsule_bytes=packed_size,algorithm_queries_DLL_FFI_models_physics=0,synthetic_evidence_only=True,original_source_parser_bug_preserved_in_preparation_checkpoint=True)))
if __name__=='__main__':main()
