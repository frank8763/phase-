"""Pure policy/control-map qualification on locked saved records and negatives."""
import argparse,ast,copy,gzip,hashlib,importlib.abc,json,signal,sys
from pathlib import Path
from types import SimpleNamespace
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('USER_REQUESTED_NO_NEW_MODELS')
sys.meta_path.insert(0,NoModels())
import numpy as np
from maneuver import ReferenceOwner,evaluate,CommittedPrefix,poses
from command_batch import sequences,deduplicate_full_sequences
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v852_maneuver_contract'


def qpos(x,y=0.,yaw=0.):return np.array([x,y,.2,np.cos(yaw/2),0.,0.,np.sin(yaw/2)])


def certificate(x32,xend,x8=0.,entry=None):
    entry=qpos(0.)if entry is None else entry
    q=np.repeat(qpos(xend)[None],320,axis=0);q[:24]=np.linspace(qpos(x8),qpos(x32),24);q[24:]=np.linspace(qpos(x32),qpos(xend),296)
    return dict(qpos=q,qvel=np.zeros((320,6)),controls=np.zeros((320,4)),prefix_initial_qpos=entry.copy(),initial_qpos=qpos(x8),initial_qvel=np.zeros(6),prefix_command=np.zeros(4),prefix_poses=np.repeat(poses(entry[None]),8,axis=0),created_time=0.,start_time=.08,minimum_causal_predicted_clearance_m=.16,minimum_predicted_self_domain_margin_m=.003,terminal_speed_m_s=0.)


def main():
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('ZERO_MODEL_QUALIFICATION_180S')));signal.alarm(180)
    global OUT
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=OUT/'qualification_final01');args=parser.parse_args();OUT=args.output.resolve();assert OUT.is_relative_to(R/'runs/v852_maneuver_contract');OUT.mkdir(parents=True,exist_ok=False);sources={};negative=[];positive=[]
    for path in C.glob('*.py'):sources[str(path.relative_to(R))]=hashlib.sha256(path.read_bytes()).hexdigest()
    def reject(label,call):
        try:call()
        except (AssertionError,ValueError,RuntimeError):negative.append(label);return
        raise AssertionError('NEGATIVE_NOT_REJECTED:'+label)
    def read(path):
        raw=path.read_bytes();sources[str(path.relative_to(R))]=hashlib.sha256(raw).hexdigest();return json.loads(gzip.decompress(raw)if path.suffix=='.gz'else raw)
    path=np.array([[0.,0.,0.,1.],[-.5,0.,0.,-1.],[-1.,0.,0.,-1.],[-.5,0.,0.,1.],[2.,0.,0.,1.]])
    owner=ReferenceOwner();owner.install(path,[2.,0.],0);segment=owner.segment();assert segment.gear==-1 and segment.end==2
    backward=certificate(-.06,-.3,x8=-.01);decision=evaluate(segment,backward,qpos(0.),np.zeros(6),0.)
    assert decision['normal_allowed']and decision['goal_distance_gain_m']<0 and decision['route_merit_gain32_m']>=.02
    positive.append('necessary_reverse_accepted_as_route_progress')
    bad=certificate(-.001,-.3,x8=-.0001);assert evaluate(segment,bad,qpos(0.),np.zeros(6),0.)['reason']=='NO_COMMITTED32_PROGRESS';positive.append('terminal_only_promise_rejected')
    drift=copy.deepcopy(backward);drift['qpos'][-1,1]=.3;assert evaluate(segment,drift,qpos(0.),np.zeros(6),0.)['reason']=='OUTSIDE_ACTIVE_SEGMENT_TUBE'
    positive.append('off_reference_full_tail_rejected')
    prefix=CommittedPrefix(segment,backward,decision,qpos(0.));assert not prefix.replacement_allowed
    before=[backward['qpos'].copy(),backward['qvel'].copy(),backward['controls'].copy()]
    for tick in range(4):
        n=(tick+1)*8;q=backward['initial_qpos']if n==8 else backward['qpos'][n-9];v=backward['initial_qvel']if n==8 else backward['qvel'][n-9]
        result=prefix.receipt(q,v,prefix.next_command());assert result['complete']==(tick==3)
    assert prefix.replacement_allowed and all(np.array_equal(backward[k],v)for k,v in zip(['qpos','qvel','controls'],before));positive.append('four_public_state_matched_commitment_no_mutation')
    badprefix=CommittedPrefix(segment,backward,decision,qpos(0.));reject('wrong_actual_qpos',lambda:badprefix.receipt(backward['initial_qpos']+.001,backward['initial_qvel'],badprefix.next_command()))
    reject('wrong_actual_control',lambda:badprefix.receipt(backward['initial_qpos'],backward['initial_qvel'],np.ones(4)))
    old=certificate(-.05,-.4);old.update(initial_qpos=qpos(0.),initial_qvel=np.zeros(6),start_time=0.,maneuver_contract=dict(segment_key=segment.key))
    dominated=evaluate(segment,backward,qpos(0.),np.zeros(6),0.,old=old,old_cursor=0);assert dominated['reason']=='NO_IMPROVEMENT_OVER_RETAINED';positive.append('same_segment_old_remaining_dominance')
    wrong=copy.deepcopy(old);wrong['maneuver_contract']['segment_key']='another_reference';reject('old_from_different_reference',lambda:evaluate(segment,backward,qpos(0.),np.zeros(6),0.,old=wrong,old_cursor=0))
    reject('forged_old_join_time',lambda:evaluate(segment,backward,qpos(0.),np.zeros(6),0.,old=old,old_cursor=1))
    for key,value in [('minimum_causal_predicted_clearance_m',.154),('minimum_predicted_self_domain_margin_m',.001),('terminal_speed_m_s',.026)]:
        broken=copy.deepcopy(backward);broken[key]=value;reject('original_gate_'+key,lambda broken=broken:evaluate(segment,broken,qpos(0.),np.zeros(6),0.))
    broken=copy.deepcopy(backward);broken['qpos']=broken['qpos'][:-1];reject('truncated_original320_tail',lambda:evaluate(segment,broken,qpos(0.),np.zeros(6),0.))
    broken=copy.deepcopy(backward);broken['qpos'][-1,0]=np.nan;reject('nan_full_trajectory',lambda:evaluate(segment,broken,qpos(0.),np.zeros(6),0.))
    reject('moving_cusp_switch',lambda:owner.advance_cusp(np.array([-1.,0.,0.]),np.array([.06,0.,0.,0.,0.,0.])))
    reject('skip_cusp_index',lambda:owner.update_index(3))
    saved_id=owner.reference_id;assert owner.after_backup_finished()['reference_id']==saved_id and owner.path is not None
    reject('renew_on_backup_finish',lambda:owner.install(path,[2.,0.],20,cause='BACKUP_FINISHED',observed_this_frame=True,evidence_id='fake'))
    reject('renew_without_fresh_observation',lambda:owner.install(path,[2.,0.],20,cause='CURRENT_GEOMETRY_INVALID',observed_this_frame=False,evidence_id='x'))
    owner.advance_cusp(np.array([-1.,0.,0.]),np.zeros(6));assert owner.segment().gear==1 and owner.index==2;positive.append('actual_settled_cusp_advances_phase')
    assert owner.segment().key!=segment.key
    owner.install(path,[2.,0.],20,cause='CURRENT_GEOMETRY_INVALID',observed_this_frame=True,evidence_id='logged_causal_field_check');positive.append('explicit_causal_reference_renewal')
    # Reproduce the old reference-drop callsite without executing a model.
    source=R/'experiments/v851_profile_output_worker/run_static.py';sources[str(source.relative_to(R))]=hashlib.sha256(source.read_bytes()).hexdigest();tree=ast.parse(source.read_text());node=next(n for n in ast.walk(tree)if isinstance(n,ast.If)and isinstance(n.test,ast.Name)and n.test.id=='recovery_finished')
    ns=dict(supervisor=SimpleNamespace(path=path.copy(),first_step=0),path=path.copy(),index=2)
    exec(compile(ast.Module(body=node.body[:4],type_ignores=[]),str(source),'exec'),ns)
    assert ns['path']is None and owner.path is not None;positive.append('old_actual_reference_drop_reproduced_new_owner_retains')
    # Actual old geometric projection and control map, no constructor invoked.
    sys.path.insert(0,str(R/'experiments/v851_profile_output_worker'))
    from serial_predictor import project_to_segment_path
    from actuator_commands import CommandMap
    rng=np.random.default_rng(852);points=np.c_[rng.uniform(-1.2,.2,256),rng.uniform(-.3,.3,256),rng.uniform(-.5,.5,256)]
    arc,contour,heading=project_to_segment_path(points,segment.points);p=segment.project(points)
    assert np.max(abs(arc-p['arc']))<=1e-12 and np.max(abs(contour-p['contour']))<=1e-12 and np.max(abs(np.abs((points[:,2]-heading+np.pi)%(2*np.pi)-np.pi)-p['heading_error']))<=1e-12
    positive.append('single_gear_projection_matches_original_256cases')
    command=CommandMap.__new__(CommandMap);command.lower=np.array([-.6,-.6,-24.,-24.]);command.upper=-command.lower;command.rate=np.array([.1,.1,.7,.7]);batch_cases=0
    for i in range(64):
        targets=rng.uniform([-1.,-1.,-40.,-40.],[1.,1.,40.,40.],size=(25,4));targets[-1]=targets[0];last=rng.uniform(command.lower,command.upper);horizon=240 if i%2==0 else 320;brake=80 if horizon==240 else 160
        original=np.asarray([command.sequence(target,last,horizon,brake)for target in targets]);batch=sequences(targets,last,command.lower,command.upper,command.rate,horizon,brake);assert np.array_equal(batch,original)
        unique,inverse,first=deduplicate_full_sequences(batch);assert len(unique)<len(batch)and np.array_equal(unique[inverse],original);batch_cases+=len(targets)
    positive.append('1600_original_full_control_sequences_batch_bit_exact')
    assert len(deduplicate_full_sequences(np.array([[[0.,0.,0.,0.],[0.,0.,1.,1.]],[[0.,0.,0.,0.],[0.,0.,2.,2.]]]))[0])==2
    positive.append('same_first_command_different_future_not_deduplicated')
    # Fixed saved actual contracts are classified; refusal is retained rather
    # than manufacturing a new admissible physical branch.
    pair=R/'runs/v851_profile_output_worker/v851_main_slot01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');plans=[read(p)for p in sorted(cell.glob('planning_*.json'))];trace=read(cell/'trace.json');execution={r['step']:r for r in map(json.loads,(cell/'v648_execution.jsonl').open())};saved=[]
    for step in [374,399,619,734,865,932,982,1073,1120,1148]:
        c=read(cell/'progress_certificates'/f'certificate_{step:04d}.json.gz');route=max((p for p in plans if p['step']<=step),key=lambda x:x['step']);owned=ReferenceOwner();owned.install(route['path'],protocol['goal_xy'],0);owned.index=trace[step]['path_index'];seg=owned.segment();before=execution[step-1]
        decision=evaluate(seg,c,before['qpos_full'],before['qvel_full'],c['created_time']);saved.append(dict(step=step,gear=seg.gear,decision=decision))
    result=dict(status='ZERO_MODEL_MANEUVER_AND_BATCH_LOGIC_QUALIFICATION_PASS',passed=True,positive_checks=positive,negative_cases=negative,saved_fixed_contract_classifications=saved,control_sequences_exact=batch_cases,reference_scope='single active gear; old stop thresholds unchanged',new_models=0,new_integrations=0,new_navigation=0,training_updates=0,native_batch_rollout_qualified=False,new_physical_closed_loop_qualified=False,three_route_passed=False,real_time_qualified=False,limitations='Synthetic logic/state receipt cases and saved previously audited contract classification; no new physical prediction, search, speed benchmark or arrival evidence.')
    (OUT/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'INPUT_SHA256.json').write_text(json.dumps(sources,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='saved_fixed_contract_classifications'}),flush=True)


if __name__=='__main__':main()
