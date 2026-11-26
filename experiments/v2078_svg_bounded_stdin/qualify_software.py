from pathlib import Path
import hashlib, importlib.util, json, os, subprocess

R=Path(__file__).resolve().parents[2]
C=Path(__file__).resolve().parent
O=R/'runs'/C.name
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    assert json.loads((O/'ORIGINAL_RED_REPRO.json').read_text())['error']=='UNBOUND_WRITABLE_DESCRIPTOR'
    assert not(O/'RESULT.json').exists()
    boundary_path=R/'experiments/v1436_pathlib_control_rename/bounded_io.py'
    before=sha(boundary_path);boundary=load('unmodified_actual_output_boundary',boundary_path)
    helper=load('regular_stdin_frame_fix',C/'input_frame.py')
    output=O/'fixture';charges=[]
    def reserve(path,size):
        assert path.is_relative_to(output.resolve())
        charges.append(size);assert sum(charges)<=256*1024
    frame=dict(kind='EXPLICIT_SOFTWARE_FRAME_NOT_SOLVER_INPUT',values=list(range(128)),unicode='Phase数据')
    expected=hashlib.sha256(json.dumps(frame,allow_nan=False).encode()+b'\n').hexdigest()
    argv=['/usr/bin/python3','-I','-B','-S','-c','import sys,hashlib;print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())']
    rejected=[]
    def reject(name,fn):
        try:fn()
        except(AssertionError,FileExistsError):rejected.append(name)
        else:raise AssertionError('EXPECTED_TRANSPORT_REFUSAL:'+name)
    with boundary.OutputBoundary(output,reserve):
        reject('original_anonymous_writable_stdin',lambda:subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE))
        peer,stream=helper.launch(argv,frame,input_path=output/'frame.json',cwd=R,env=dict(os.environ))
        try:
            stdout,stderr=peer.communicate(timeout=10)
            assert peer.returncode==0 and not stderr and stdout.decode().strip()==expected
        finally:
            if peer.poll()is None:peer.terminate();peer.wait(timeout=5)
            stream.close()
        reject('outside_output',lambda:helper.launch(argv,frame,input_path=O/'outside.json',cwd=R,env=dict(os.environ)))
        reject('oversize_before_write',lambda:helper.launch(argv,{'data':'x'*(1024**2)},input_path=output/'oversize.json',cwd=R,env=dict(os.environ)))
        reject('existing_input_no_overwrite',lambda:helper.launch(argv,frame,input_path=output/'frame.json',cwd=R,env=dict(os.environ)))
        reject('raw_writable_descriptor_still_forbidden',lambda:__import__('io').open(1234567,'wb'))
    assert not(O/'outside.json').exists()and not(output/'oversize.json').exists()
    assert sha(boundary_path)==before
    result=dict(closed=True,software_passed=True,original_red_reproduced=True,exact_child_frame_SHA256=expected,negative_cases=rejected,
                charged_open_and_write_bytes=sum(charges),input_held_readonly_until_child_exit=True,original_output_boundary_unchanged=True,
                source_SHA256={str(p.relative_to(R)):sha(p)for p in [boundary_path,C/'input_frame.py',C/'qualify_software.py']},
                vehicle_source_qualified=False,vehicle_retry_started=False,models=0,optimizer_calls=0,physics=0,replay=0,formal_slots=0)
    (O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
