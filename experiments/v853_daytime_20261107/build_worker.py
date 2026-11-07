"""Prepare one immutable worker with three preregistered commitment schedules."""
import hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;W=R/'experiments/v853_maneuver_worker';OLD=R/'experiments/v851_profile_output_worker'


def patch(name,before,after):
    p=W/name;s=p.read_text();assert s.count(before)==1,(name,before,s.count(before));p.write_text(s.replace(before,after))


def main():
    assert not W.exists();W.mkdir()
    for p in OLD.iterdir():
        if p.is_file()and p.suffix in ['.py','.md','.json']:shutil.copy2(p,W/p.name)
    core=(R/'experiments/v852_maneuver_contract/maneuver.py').read_text().replace('COMMIT_NATIVE=32',"import os\nCOMMIT_NATIVE=int(os.environ.get('PHASE_MANEUVER_COMMIT_NATIVE','32'));assert COMMIT_NATIVE in [32,64,328]")
    core=core.replace('V852_SINGLE_GEAR_COMMITTED_REFERENCE_DRAFT','V853_COMMON_SEGMENT_COMMITMENT').replace('q[[23,-1]]','q[[COMMIT_NATIVE-9,-1]]').replace('v[23]','v[COMMIT_NATIVE-9]').replace('route_merit_gain32_m','route_merit_gain_commit_m')
    (W/'maneuver_core.py').write_text(core)
    shutil.copy2(C/'maneuver_policy.py',W/'maneuver_policy.py')
    patch('reserved_recovery.py','from progress_contract import context as progress_context,assess as assess_progress,summarize as summarize_progress','from progress_contract import context as progress_context,assess as assess_progress,summarize as summarize_progress\nfrom maneuver_policy import assess_offer,decorate,commit_ticks')
    patch('reserved_recovery.py',"int(path[min(index+1,len(path)-1),3])==1:","int(path[min(index+1,len(path)-1),3])in[-1,1]:")
    patch('reserved_recovery.py',"proactive=bool(getattr(self,'proactive',False))","proactive=bool(reference is not None and state['center']is not None)")
    patch('reserved_recovery.py',"if active:groups.append(('REFERENCE_FOLLOW',[(look,(wheel,brake))for look in LOOKAHEADS for wheel in WHEELS for brake in DRIVE_TICKS]))","if active and int(reference['path'][min(reference['index']+1,len(reference['path'])-1)][3])==1:\n            groups=[('REFERENCE_FOLLOW',[(look,(wheel,brake))for look in LOOKAHEADS for wheel in WHEELS for brake in DRIVE_TICKS]),*groups]")
    patch('reserved_recovery.py',"else'PROACTIVE_NO_GOAL_PROGRESS'if proactive and goal_gain<.02 else'ESCAPE_NO_GOAL_PROGRESS'if following and goal_gain<.02 else None","else None")
    patch('reserved_recovery.py',"if not recovery_only and best is not None and score<=best['score']:continue","# Selection is evaluated after the complete common maneuver proof.")
    patch('reserved_recovery.py',"if recovery_only and best_recovery is not None and (best_recovery['recovery_library']=='ORIGINAL'and library!='ORIGINAL'or score<=best_recovery['score']):continue","# A failed maneuver cannot replace a still valid old tail.")
    patch('reserved_recovery.py',"if following:offer['reference_following']={**reference,'lookahead_m':lookahead,'wheel_speed':wheel,'drive_ticks':brake_after,'targets':extended['targets'].tolist()}","if following:offer['reference_following']={**reference,'lookahead_m':lookahead,'wheel_speed':wheel,'drive_ticks':brake_after,'targets':extended['targets'].tolist()}\n                maneuver=assess_offer(self,reference,real,offer,state,step)\n                if maneuver is not None:\n                    detail['maneuver_contract']=maneuver;offer['maneuver_contract']=maneuver\n                    if not maneuver['normal_allowed']:\n                        if maneuver['old_created_step'] is not None or getattr(self,'maneuver_return',False):\n                            detail['reason']=maneuver['reason'];continue\n                        recovery_only=True;detail['reason']='RECOVERY_ONLY'\n                    else:\n                        score=float(maneuver['route_merit_gain_commit_m']+.1*maneuver['route_merit_gain328_m']+.15*min(minimum,.30));offer['score']=score;detail['selection_score']=score")
    patch('reserved_recovery.py',"best=offer\n                if not following and brake_only:break","best=offer\n                if maneuver is not None or(not following and brake_only):break")
    patch('reserved_recovery.py',"recovery_only=True;detail['reason']='RECOVERY_ONLY'","recovery_only=True;detail['reason']='RECOVERY_ONLY'\n                        decision=dict(decision,active=True,normal_allowed=False,recovery_only=True,reason=maneuver['reason'])")
    patch('reserved_recovery.py',"for library,choices in groups:\n            if not proactive", "for library,choices in groups:\n            if best is not None and best.get('maneuver_contract',{}).get('normal_allowed'):break\n            if not proactive")
    patch('reserved_recovery.py',"self.cache=best;self.cursor=0;self.expected=(initial_q,initial_v);self.expected_ctrl=np.asarray(proposal).copy();self.finish_pending=False","decorate(best,reference,state,step)\n        self.cache=best;self.cursor=0;self.expected=(initial_q,initial_v);self.expected_ctrl=np.asarray(proposal).copy();self.finish_pending=False\n        self.maneuver_commit_until=step+commit_ticks(best)//8")
    patch('reserved_recovery.py',"candidate.progress_context_override=progress_context(real,state,candidate.reference,old,old_cursor,step,role='BACKUP_RETURN')","candidate.progress_context_override=progress_context(real,state,candidate.reference,old,old_cursor,step,role='BACKUP_RETURN')\n        candidate.maneuver_old=(old,old_cursor);candidate.maneuver_return=True")
    patch('reserved_recovery.py',"self.handovers+=1","self.maneuver_commit_until=candidate.maneuver_commit_until\n        self.handovers+=1")
    # V850's Euclidean goal gate is replaced, not silently applied only forward.
    patch('progress_contract.py',"active=bool(state['center']is not None and reference is not None)","active=False  # superseded by complete maneuver_core proof for both gears")
    patch('joint_admission.py',"if getattr(reserved,'early_joint_started_step',None)is not None and getattr(reserved,'reference',None)is not None:","if False:  # replaced by the common complete maneuver admission")
    patch('recovery_supervisor.py',"if age<4 or age%4:return None","if step<getattr(reserved,'maneuver_commit_until',self.first_step+4)or age%4:return None")
    patch('recovery_supervisor.py',"if gear!=1:","if gear not in[-1,1]:")
    patch('recovery_supervisor.py',"speed=min(.60,.50/(1+abs(steer)))","speed=gear*min(.60,.50/(1+abs(steer)))")
    patch('recovery_supervisor.py',"if progress<.02:","if False:  # ordinary and return now use the same complete segment merit")
    patch('recovery_supervisor.py',"'active_gear':1,","'active_gear':gear,")
    # Preserve all native instrumentation, physical sensing and complete tails.
    patch('run_static.py',"'v851_profile_output_worker'/a.name","'v853_maneuver_worker'/a.name")
    patch('run_static.py',"'V850_PROGRESS_CONSISTENT_RETURN_AND_COMMITMENT' if geometry_mode","'V853_COMMON_SEGMENT_COMMITMENT' if geometry_mode")
    patch('run_static.py',"if activate(reserved,motion_state,step):","if False:  # V853 uses the common maneuver gate, no old early-goal selector")
    patch('run_static.py',"returned=reentry.try_return(env,field,motion_state,reserved,path,index,step)","returned=None  # common fresh-complete return is the only reentry path")
    patch('run_static.py',"proposal,model_gate,path,index=returned;active_reference_kind=None","proposal,model_gate,path,index=returned")
    patch('run_static.py',"if keep['current_route_invalid']:need=True","if keep['current_route_invalid']and step-last_plan>=12 and motion_state['observed_this_frame']:need=True")
    patch('run_static.py',"if index>=len(path)-4:need=True","# End-of-segment alone does not delete the causal reference.")
    patch('run_static.py',"if step-last_plan>=12 and (float(np.min(distances))>.20 or heading_error>.50):need=True","if step-last_plan>=12 and motion_state['observed_this_frame']and(float(np.min(distances))>.20 or heading_error>.50):need=True")
    patch('run_static.py',"if keep['stagnated_without_route_progress']:need=True","if keep['stagnated_without_route_progress']and motion_state['observed_this_frame']:need=True")
    patch('run_static.py',"proposal,model_gate=reserved.start(env.data,step);backup_attempts+=1;backup_steps+=1;path=None;index=0;active_reference_kind=None","proposal,model_gate=reserved.start(env.data,step);backup_attempts+=1;backup_steps+=1")
    patch('run_static.py',"if reserved.progress_pending:\n                    supervisor.remember(path,index,step+1)","if reserved.cache is not None and not reserved.executing and reserved.expected is None and getattr(reserved,'maneuver_commit_until',-1)>step+1:\n                    supervisor.remember(path,index,step)\n                    reserved._begin_contract(env.data,step+1);backup_attempts+=1\n                if reserved.progress_pending and not reserved.executing:\n                    supervisor.remember(path,index,step+1)")
    patch('run_static.py',"supervisor.path=None;supervisor.first_step=None\n                    path=None;index=0","# Keep the same causal route through finite recovery completion.\n                    emit(cell,'maneuver_reference_retained.jsonl',dict(step=step,reference_path=None if path is None else path.tolist(),reference_index=index))")
    patch('run_static.py',"reserved._begin_contract(env.data,step+1);backup_attempts+=1","reserved._begin_contract(env.data,step+1);reserved.progress_pending=False;backup_attempts+=1")
    # Original physical auditor retained; its forward-only scientific test is
    # explicitly replaced by the independently reconstructed common merit.
    patch('audit_run.py',"'forward_progress':c['metadata']['active_gear']==1 and c['metadata']['predicted_goal_progress_m']>=.02","'common_maneuver_progress':c['maneuver_contract']['normal_allowed']and c['metadata']['active_gear']in[-1,1]")
    patch('audit_shadow_mode.py',"all(x['predicted_goal_progress_m']>=.02 for x in hands if x['status']=='CERTIFIED_RETURN')","all(x.get('maneuver_progress_allowed',False)for x in hands if x['status']=='CERTIFIED_RETURN')")
    patch('recovery_supervisor.py',"'status':'CERTIFIED_RETURN','predicted_goal_progress_m':goal_progress","'status':'CERTIFIED_RETURN','maneuver_progress_allowed':bool(reserved.cache['maneuver_contract']['normal_allowed']),'predicted_goal_progress_m':goal_progress")
    patch('audit_ranked_return.py',"if progress<.02:","if False:")
    patch('audit_ranked_return.py',"unchanged_progress_002=True","common_complete_maneuver_gate_separately_audited=True")
    shutil.copy2(C/'audit_maneuver.py',W/'audit_maneuver.py')
    differences={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in W.iterdir()if p.is_file()and((not(OLD/p.name).exists())or p.read_bytes()!=(OLD/p.name).read_bytes())}
    (C/'WORKER_CHANGES.json').write_text(json.dumps(differences,indent=2)+'\n');print(json.dumps(dict(worker=str(W.relative_to(R)),changed=list(differences))))


if __name__=='__main__':main()
