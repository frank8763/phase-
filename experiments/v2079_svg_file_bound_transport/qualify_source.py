"""Real output boundary plus full client constructor; zero model/solver calls."""
from context import R,C,O,read,put,sha,load
from pathlib import Path
import ast, hashlib, json, os, subprocess, sys, time, traceback, types

def main():
    os.sched_setaffinity(0,{5})
    os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    assert not(O/'SOURCE_ONCE.json').exists()
    put(O/'SOURCE_ONCE.json',dict(unix=time.time(),pid=os.getpid(),models=0))
    result=dict(passed=False,closed=False,models=0,algorithm_DLLs=0,constructors=0,queries=0,physics=0,replay=0)
    files={}
    try:
        P=R/'runs/v2073_svg_parameter_inheritance_scope'
        assert read(P/'SOURCE_QUALIFICATION.json')['passed']and read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(P/'POST_COMPONENT_STORAGE_BARRIER.json')['passed']
        assert read(P/'COMPLETION.json')['machine_first_error']['error']=="AssertionError('UNBOUND_WRITABLE_DESCRIPTOR')"
        prior=read(P/'SOURCE_FREEZE.json')['files']
        assert all(sha(R/n)==h for n,h in prior.items())
        files=dict(prior)
        old=R/'experiments/v2073_svg_parameter_inheritance_scope'
        same=[]
        excluded={'native_client.py','input_frame.py','software_peer.py','context.py','reservation.py','evidence.py','qualify_source.py'}
        for p in C.glob('*.py'):
            ast.parse(p.read_text())
            if p.name not in excluded:
                assert p.read_bytes()==(old/p.name).read_bytes(),'UNDECLARED_NUMERICAL_CHANGE:'+p.name
                same.append(p.name)
        before=(old/'native_client.py').read_text()
        expected=before.replace("  raw=json.dumps(frame,allow_nan=False).encode()+b'\\n';assert len(raw)<=1024**2", "  from pathlib import Path\n  self.output=Path(read(O/'PILOT_TASK.json')['output']);transport=load('SVG_file_bound_single_frame',C/'input_frame.py')")
        expected=expected.replace("self.p=subprocess.Popen(['taskset','-c','7',*cmd],cwd=R,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)","self.p,self.inputstream=transport.launch(['taskset','-c','7',*cmd],frame,input_path=self.output/'SVG_NATIVE_INPUT.json',cwd=R,env=env)")
        expected=expected.replace(';self.p.stdin.write(raw);self.p.stdin.close()','').replace("   self.save('SVG_NATIVE_CONSOLE.json'","   self.inputstream.close()\n   self.save('SVG_NATIVE_CONSOLE.json'")
        assert expected==(C/'native_client.py').read_text()
        assert(C/'input_frame.py').read_bytes()==(R/'experiments/v2078_svg_bounded_stdin/input_frame.py').read_bytes()
        for name in ['CONFIG.json','NATIVE_DEPENDENCIES.json']:
            assert sha(O/name)==sha(P/name)
        task=read(O/'PILOT_TASK.json');original=read(P/'PILOT_TASK.json')
        for k in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id','maximum_control_native','stop_native']:
            assert task[k]==original[k]
        reserve=load('separate_integration_existing_archive_reservation',C/'reservation.py').admission()
        assert reserve['combined_RPP_archive_subgrants_bytes']<reserve['from_completed_RPP_archive_bytes']
        import context
        assert context.queue_closed()
        # Both genuine production CLIs must refuse before any model/DLL import.
        p=subprocess.run(['taskset','-c','2','/usr/bin/python3','-B',str(C/'pilot_entry.py')],env=dict(os.environ,PHASE_REPO=str(R)),capture_output=True,timeout=10)
        assert p.returncode!=0 and b'SVG_COMPONENT_NOT_ADMITTED'in p.stderr
        ros=load('actual_readonly_ROS_software_fixture',R/'experiments/v856_nav2_foundation/ros_environment.py')
        command=ros.command(['/usr/bin/python3.12','-I','-B','-S',str(C/'native_worker.py')])
        i=command.index('--bind');assert command[i+1:i+3]==[str(R/'runs'),str(R/'runs')];command[i]='--ro-bind'
        p=subprocess.run(['taskset','-c','7',*command],env=ros.environment(),capture_output=True,timeout=15)
        assert p.returncode!=0 and b'PILOT_ADMISSION.json'in p.stderr
        boundary=load('exact_original_output_boundary_in_full_client',R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
        out=O/'software_fixture';out.mkdir(exist_ok=False);charges=[]
        def debit(path,size):
            assert path.is_relative_to(out.resolve())
            charges.append(size);assert sum(charges)<=512*1024,'SOURCE_SOFTWARE_FIXTURE_CAP'
        frame=dict(kind='EXPLICIT_SOFTWARE_NAMESPACE_FIXTURE',values=list(range(128)),no_model=True)
        raw=json.dumps(frame,allow_nan=False).encode()+b'\n'
        saved=[]
        def save(name,value):
            saved.append((name,value));put(out/name,value)
        def client_module(path,name):
            module=load(name,path);original_load=module.load;original_read=module.read
            def software_load(label,path):
                actual=original_load(label,path)
                if label=='SVG_readonly_original_ROS_namespace':
                    def software_command(args):
                        assert args[-1]==str(C/'native_worker.py')
                        return actual.command([*args[:-1],str(C/'software_peer.py')])
                    return types.SimpleNamespace(environment=actual.environment,command=software_command)
                return actual
            module.load=software_load
            def software_read(path):
                value=original_read(path)
                if Path(path)==O/'PILOT_TASK.json':value=dict(value,output=str(out))
                return value
            module.read=software_read
            return module
        old_client=client_module(old/'native_client.py','old_full_client_red_under_original_boundary')
        red=None
        with boundary.OutputBoundary(out,debit):
            try:old_client.Client(save,frame)
            except AssertionError as e:red=str(e)
            assert red=='UNBOUND_WRITABLE_DESCRIPTOR','OLD_FULL_CLIENT_BUG_NOT_REPRODUCED'
            fixed=client_module(C/'native_client.py','new_full_client_green_under_original_boundary')
            obj=fixed.Client(save,frame)
            try:
                answer=obj.query()
                assert answer['explicit_software_fixture']and answer['input_sha256']==hashlib.sha256(raw).hexdigest()
            finally:obj.close()
            assert obj.p.returncode==0 and obj.inputstream.closed
        assert sum(name.startswith('SVG_NATIVE_EVENT_')for name,value in saved)==4
        # Reuse existing negative transport and current-control evidence exactly.
        transport=read(R/'runs/v2078_svg_bounded_stdin/RESULT.json')
        assert transport['software_passed']and len(transport['negative_cases'])==5
        controls=read(R/'runs/v2054_svg_current_control_contract/RESULT.json')
        assert controls['passed']
        proof=dict(passed=True,all_original_numerical_control_capture_auditor_modules_byte_exact=same,
                   native_client_only_regular_readonly_stdin_delivery_changed=True,original_full_client_red=red,
                   repaired_full_client_real_output_boundary_and_readonly_ROS_namespace_passed=True,
                   same_frame_actual_child_SHA256=answer['input_sha256'],four_coalesced_events_reply_close_passed=True,
                   measured_fixture_charged_bytes=sum(charges),input_stream_closed_after_child_exit=True,
                   production_CLIs_refused_before_numerical_imports=True,original_current_control_negatives_reused=True,
                   original_transport_5negatives_reused=True,prior_failed_component_preserved=True,
                   separate_component_grants=reserve['combined_RPP_archive_subgrants_bytes'],joint_peak_bytes=reserve['joint_peak_bytes'],
                   formal_slots_claimed=0,models=0,algorithm_DLLs=0,queries=0)
        put(O/'SOFTWARE_CHECK_PROOF.json',proof)
        for folder in [C,R/'experiments/v2080_svg_file_transport_dispatch']:
            for p in folder.iterdir():
                if p.is_file():
                    if p.suffix=='.py':ast.parse(p.read_text())
                    files[str(p.relative_to(R))]=sha(p)
        for p in [O/name for name in ['PILOT_TASK.json','CONFIG.json','NATIVE_DEPENDENCIES.json','RESERVATION.json','LIMITS_DRAFT.json','AUTHORIZATION.json','SOFTWARE_CHECK_PROOF.json']]+[R/name for name in ['runs/v2078_svg_bounded_stdin/RESULT.json','runs/v2073_svg_parameter_inheritance_scope/COMPLETION.json','runs/v2073_svg_parameter_inheritance_scope/POST_COMPONENT_STORAGE_BARRIER.json','runs/v2070_mppi_final_two_shared_metadata/RESULT.json','runs/v2045_remaining_parallel_source/rounds/common_12__MPPI/POST_ROUND_STORAGE_BARRIER.json']]:files[str(p.relative_to(R))]=sha(p)
        assert all(sha(R/n)==h for n,h in files.items())
        put(O/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
        put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
        result.update(passed=True,source_members=len(files),proof=proof)
    except BaseException as e:
        result.update(first_error=repr(e),traceback=traceback.format_exc())
        put(O/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
    finally:
        result['closed']=True;put(O/'SOURCE_QUALIFICATION.json',result)
        put(O/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,algorithm_DLLs=0,constructors=0,queries=0))
    print(json.dumps(result));return 0 if result['passed']else 1

if __name__=='__main__':raise SystemExit(main())
