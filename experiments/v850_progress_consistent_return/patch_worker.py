"""Install the single progress/commitment mechanism in the new worker, before freezing."""
import ast
import difflib
import json
from pathlib import Path

R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
OLD=R/'experiments/v848_goal_first_worker';W=R/'experiments/v850_progress_consistent_worker'
OUT=R/'runs/v850_progress_consistent_return'
STAGED={}


def replace(p,before,after):
    source=STAGED.get(p,p.read_text());assert source.count(before)==1,(p.name,before[:90])
    STAGED[p]=source.replace(before,after)


def main():
    p=W/'reserved_recovery.py'
    replace(p,'from self_geometry import containment_margin','from self_geometry import containment_margin\nfrom progress_contract import context as progress_context,assess as assess_progress,summarize as summarize_progress')
    replace(p,'self.last_attempt=None;self.handovers=0;self.expected_ctrl=None;self.allow_forward_escape=False;self.escape_goal_xy=None','self.last_attempt=None;self.handovers=0;self.expected_ctrl=None;self.allow_forward_escape=False;self.escape_goal_xy=None;self.progress_pending=False')
    replace(p,"assert not proactive or active,'PROACTIVE_REQUIRES_TRACKED_FORWARD_REFERENCE'", "assert not proactive or active,'PROACTIVE_REQUIRES_TRACKED_FORWARD_REFERENCE'\n        progress=getattr(self,'progress_context_override',None)\n        if progress is None:progress=progress_context(real,state,reference,self.cache,self.cursor,step)")
    replace(p,"'reference_successor_active':active,'reference':reference}","'reference_successor_active':active,'reference':reference,'progress_context':progress}")
    replace(p,'best=None;safe_count=0','best=None;best_recovery=None;recovery_detail=None;safe_count=0')
    marker="                detail={'kind':kind,'library':library"
    replace(p,marker,"                safety_reason=reason;decision=assess_progress(progress,trajectory[-1,:2])if reason is None else None\n                recovery_only=bool(decision is not None and decision['recovery_only']and not proactive and progress['role']!='BACKUP_RETURN')\n                if decision is not None and not decision['normal_allowed']:reason='RECOVERY_ONLY'if recovery_only else decision['reason']\n"+marker)
    replace(p,"'minimum_static_m':float(__import__('exact_footprint').pose_values(getattr(field,'nominal_static_geometry',field),complete).min())}","'minimum_static_m':float(__import__('exact_footprint').pose_values(getattr(field,'nominal_static_geometry',field),complete).min()),'safety_reason':safety_reason,'progress_assessment':decision}")
    replace(p,'                if reason is not None:continue\n                safe_count+=1','                if reason is not None and not recovery_only:continue\n                safe_count+=int(not recovery_only)')
    replace(p,"                if best is not None and score<=best['score']:continue\n                controls=", "                if not recovery_only and best is not None and score<=best['score']:continue\n                if recovery_only and best_recovery is not None and (best_recovery['recovery_library']=='ORIGINAL'and library!='ORIGINAL'or score<=best_recovery['score']):continue\n                controls=")
    replace(p,"                best={'proactive_joint':proactive", "                offer={'proactive_joint':proactive")
    replace(p,"                    best['one_cycle_continuation']=", "                    offer['one_cycle_continuation']=")
    replace(p,"                if following:best['reference_following']=", "                if following:offer['reference_following']=")
    replace(p,"                if not following and brake_only:break", "                mode='RECOVERY_ENTRY'if recovery_only else'PROGRESS'if progress['active']else'LEGACY_PHASE'\n                summarize_progress(offer,progress,decision,mode);offer['recovery_library']=library\n                if recovery_only:\n                    best_recovery=offer;recovery_detail=detail;continue\n                best=offer\n                if not following and brake_only:break")
    replace(p,"        self.last_attempt['status']='APPENDABLE_BACKUP_FOUND'if best is not None else'NO_APPENDABLE_BACKUP'", "        if best is None and best_recovery is not None:\n            best=best_recovery;recovery_detail['reason']=None;recovery_detail['accepted_mode']='RECOVERY_ENTRY';safe_count=1\n        self.last_attempt['status']='APPENDABLE_BACKUP_FOUND'if best is not None else'NO_APPENDABLE_BACKUP'\n        self.last_attempt['progress_mode']=None if best is None else best['progress_contract']['mode']")
    replace(p,"        self.cache=best;self.cursor=0;self.expected=(initial_q,initial_v);self.expected_ctrl=np.asarray(proposal).copy();self.finish_pending=False", "        self.cache=best;self.cursor=0;self.expected=(initial_q,initial_v);self.expected_ctrl=np.asarray(proposal).copy();self.finish_pending=False\n        self.progress_pending=best['progress_contract']['mode']=='RECOVERY_ENTRY'")
    replace(p,"'successor_certificate':best.get('one_cycle_continuation')}","'successor_certificate':best.get('one_cycle_continuation'),'progress_contract':best['progress_contract']}")
    replace(p,"        summary=candidate.admit_nominal(real,proposal,field,state,step)", "        candidate.progress_context_override=progress_context(real,state,candidate.reference,old,old_cursor,step,role='BACKUP_RETURN')\n        summary=candidate.admit_nominal(real,proposal,field,state,step)")
    replace(p,"        self.last_prefix_qpos=candidate.last_prefix_qpos;self.last_prefix_qvel=candidate.last_prefix_qvel", "        self.last_prefix_qpos=candidate.last_prefix_qpos;self.last_prefix_qvel=candidate.last_prefix_qvel;self.progress_pending=False")
    replace(p,"    def start(self,real,step):\n        assert", "    def _begin_contract(self,real,step):\n        assert")
    replace(p,"        return self.command(real)\n    def command(self,real):", "    def start(self,real,step):\n        self._begin_contract(real,step)\n        return self.command(real)\n    def begin_pending_recovery(self,real,step):\n        assert self.progress_pending and not self.executing\n        assert self.cache['progress_contract']['mode']=='RECOVERY_ENTRY'\n        self.progress_pending=False;self._begin_contract(real,step)\n    def command(self,real):")
    # When a valid retained contract exists, failure of the bounded early search
    # commits that contract instead of repeating the old unrestricted fallback.
    p=W/'joint_admission.py'
    replace(p,"        if result is not None:return result", "        if result is not None:return result\n        if reserved.cache is not None:return proposal,gate,None")
    replace(p,"        selected.update(score=float(score)", "        selected.update(progress_contract=reserved.cache.get('progress_contract'),recovery_entry_pending=reserved.progress_pending,score=float(score)")
    # A recovery entry first executes its original certified 8-tick prefix.
    # Only after the exact public match is its remaining 320-tick tail committed.
    p=W/'run_static.py'
    replace(p,"'v848_goal_first_worker'/a.name", "'v850_progress_consistent_worker'/a.name")
    replace(p,"'V848_GOAL_REFERENCE_AND_FIRST_CERTIFIED_NOMINAL'", "'V850_PROGRESS_CONSISTENT_RETURN_AND_COMMITMENT'")
    replace(p,'install(outer)','profile_finish=install(outer)')
    replace(p,"                recovery_finished=reserved.after_public(env.data)\n                reentry.after_public(env.data,reserved)", "                recovery_finished=reserved.after_public(env.data)\n                if reserved.progress_pending:\n                    supervisor.remember(path,index,step+1)\n                    reserved.begin_pending_recovery(env.data,step+1);backup_attempts+=1\n                    emit(cell,'gear_transitions.jsonl',{'step':step+1,'status':'PROGRESS_GUARDED_RECOVERY_COMMIT','from_gear':None,'to_gear':None,'actual_xy_speed_m_s':float(np.linalg.norm(env.data.qvel[:2]))})\n                    path=None;index=0;active_reference_kind=None\n                reentry.after_public(env.data,reserved)")
    replace(p,"    dump(target,{'status':status", "    profile_finish()\n    dump(target,{'status':status")
    # Explicit profile flush survives arbitrary legacy atexit behavior.
    p=W/'operation_profile.py';replace(p,' atexit.register(finish)',' atexit.register(finish)\n return finish')
    for p,source in STAGED.items():ast.parse(source,filename=str(p))
    for p,source in STAGED.items():p.write_text(source)
    changes=[]
    for p in W.glob('*.py'):
        ast.parse(p.read_text(),filename=str(p))
        previous=(OLD/p.name).read_text()if(OLD/p.name).exists()else''
        if previous!=p.read_text():changes.append(dict(path=str(p.relative_to(R)),diff=''.join(difflib.unified_diff(previous.splitlines(True),p.read_text().splitlines(True),fromfile=str((OLD/p.name).relative_to(R)),tofile=str(p.relative_to(R))))))
    (OUT/'SOURCE_CHANGE_RECORD.json').write_text(json.dumps(changes,indent=2)+'\n')
    print(json.dumps(dict(changed_files=[x['path']for x in changes],models=0,integrations=0)))


if __name__=='__main__':main()
