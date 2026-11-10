"""Read saved command/encoder witnesses only after closed V979; zero models."""
import gzip,hashlib,importlib.abc,json,math,shutil,subprocess,sys,tarfile
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v980_recovery_actuation_postmortem';GH=R/'tools/phase_storage_20261107/vendor/gh'
PREFIX='runs/v858_nav2_verified/v979/component_0/'
WANTED={'ONLINE_TRACKING_FAULT.json','COMPONENT_REFERENCE.json','COMMAND_TUBES.json.gz','ROS_RESULT.json','COMMANDS.json',
        'physics/PREFIX_RESTORE.json','physics/SETUP.json','PARTIAL.json','NATIVE_READY.json','COMPLETION.json'}
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    index=json.loads((R/'records/nav2_v979_20261110/RECORD_INDEX.json').read_text());group=index['archives'][0]
    inventory=json.loads((O/(group['group']+'.INVENTORY.json')).read_text());catalog={x['path']:x for x in inventory['files']}
    part=group['parts'][0];assert len(group['parts'])==1
    expected_selected=[name for name in WANTED if PREFIX+name in catalog]
    restored=[dict(path=name,sha256=catalog[PREFIX+name]['sha256'])for name in expected_selected]
    already=all((O/name).is_file() and sha(O/name)==catalog[PREFIX+name]['sha256']for name in expected_selected)
    if not already:
        path=O/part['name'];job=subprocess.run([str(GH),'release','download',index['release_tag'],'--repo',index['repository'],'--pattern',part['name'],'--dir',str(O)],capture_output=True,text=True,timeout=30)
        assert job.returncode==0,job.stderr[-1200:]
        assert path.stat().st_size==part['bytes']and sha(path)==part['sha256']==group['archive_sha256']
        decoder=subprocess.Popen(['zstd','-q','-dc',str(path)],stdout=subprocess.PIPE);restored=[]
        with tarfile.open(fileobj=decoder.stdout,mode='r|')as stream:
            for member in stream:
                if not member.name.startswith(PREFIX)or member.name[len(PREFIX):]not in WANTED:continue
                name=member.name[len(PREFIX):];assert member.isfile()and '..'not in Path(name).parts
                target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
                with stream.extractfile(member)as source,target.open('xb')as output:shutil.copyfileobj(source,output)
                assert sha(target)==catalog[member.name]['sha256'];restored.append(dict(path=name,sha256=sha(target)))
        assert decoder.wait()==0;path.unlink()
    fault=json.loads((O/'ONLINE_TRACKING_FAULT.json').read_text());plan=json.loads((O/'COMPONENT_REFERENCE.json').read_text())
    rows=json.loads(gzip.decompress((O/'COMMAND_TUBES.json.gz').read_bytes()));body=fault['packet']['body'];reference=np.asarray(plan['proposal']['path'])
    distance=np.linalg.norm(reference[:,:2]-body[:2],axis=1);closest=int(np.argmin(distance));angle=math.atan2(math.sin(body[2]-reference[closest,2]),math.cos(body[2]-reference[closest,2]))
    witnesses=[]
    for row in rows:
        packet=row['packet'];q=np.asarray(packet['steering']['position']);t=np.tan(q);k=[t[0]/(.6+.27*t[0]),t[1]/(.6-.27*t[1])]
        proof=row['proof'];selected=row.get('selected_shaping',{}).get('selected')
        witnesses.append(dict(native_tick=packet['native_tick'],body=packet['body'],measured_curvatures=k,
                              raw_nominal=row['raw_wanted'],shaped=row['wanted'],dispatched=[proof['v'],proof['w']],
                              admitted=proof['passed'],alternative_motion_selected=row.get('recovery') is not None,
                              shaping_mode=row['selected_shaping']['mode']))
    origin=json.loads((O/'physics/PREFIX_RESTORE.json').read_text())
    observed_ticks=[x['native_tick']for x in witnesses]+[fault['packet']['native_tick']]
    trace_names=[PREFIX+'physics/'+x for x in ['NATIVE_TRACE.npz','BODY_COMMANDS.json','CONTACTS.json.gz','REPLAY.json']]
    report=dict(models=0,integrations=0,new_predictions=0,old_outcome_unchanged='V979_NOT_PASSED',
                historical_restore_native=origin['historical_prefix_replay_native'],historical_all_state_control_error=origin['maximum_all_state_control_error'],
                new_branch_native_exact=None,new_branch_native_observed_lower_bound=max(observed_ticks)-origin['global_native_tick'],
                complete_native_trace_saved=trace_names[0]in catalog,own_control_replay_saved=trace_names[-1]in catalog,
                first_reported_error=json.loads((O/'ROS_RESULT.json').read_text())['error'],
                captured_fault_tick=fault['packet']['native_tick'],captured_body=body,nearest_reference_pose=reference[closest].tolist(),
                captured_position_error_m=float(distance[closest]),captured_heading_error_rad=abs(angle),
                original_heading_limit_rad=.035,online_sampling_allowance_rad=.758770385*.00625,
                measured_steering_at_fault=fault['packet']['steering'],
                admitted_decisions=len(witnesses),alternative_motion_decisions=sum(x['alternative_motion_selected']for x in witnesses),
                first_commands=witnesses[:12],last_commands=witnesses[-12:],
                missing_full_native_evidence=[name for name in trace_names if name not in catalog],
                evidence_stop_issue='Parent FIRST_WORKER_FAILURE terminated the native process group, including isolate/bwrap die-with-parent, before full native finally records were saved. Exact new/replay counts and full contact/safety verdict unavailable; no inferred zeros.',
                limits='Body/steering/command witnesses distinguish physical tracking from software-peer result, but do not isolate unique actuator/transmission cause; no fresh model or rerun.',
                restored=restored)
    import importlib.util,sys
    sys.path.insert(0,str(R/'experiments/v977_state_consistent_recovery'))
    spec=importlib.util.spec_from_file_location('v980_saved_curve_only',R/'experiments/v977_state_consistent_recovery/saved_qualification.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    proposal=plan['proposal'];fine=module.reconstruct(proposal['initial_state'],proposal['edge_targets'])
    j=int(np.argmin(np.linalg.norm(fine[:,:2]-np.asarray(body[:2]),axis=1)))
    refined=abs(math.atan2(math.sin(body[2]-fine[j,2]),math.cos(body[2]-fine[j,2])))
    report['refined_captured_pose_check']=dict(reference_step_m=.0005,heading_error_rad=refined,
         sampling_allowance_rad=.758770385*.00025,conservative_upper_rad=refined+.758770385*.00025,
         original_limit_rad=.035,captured_pose_within_original_heading_envelope=refined+.758770385*.00025<=.035,
         not_full_native_trajectory=True)
    report['online_conservative_upper_rad']=report['captured_heading_error_rad']+report['online_sampling_allowance_rad']
    report['positive_turn_request_with_negative_measured_body_yaw']=[x for x in witnesses if x['dispatched'][1]>0 and x['body'][4]<-.03]
    report['no_unique_cause_claim']='Coarse-reference sampling allowance explains this observed guard rejection without proving actual2degree violation. Measured yaw lag also exists; future full-path success cannot be inferred from one refined saved pose.'
    (O/'DIAGNOSIS.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items()if k not in {'first_commands','last_commands','restored','measured_steering_at_fault'}}),flush=True)
if __name__=='__main__':main()
