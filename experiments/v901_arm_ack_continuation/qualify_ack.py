"""Execute the exact old/new production send branch on the recorded ARM race."""
import ast,hashlib,json,sys,types
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v901_arm_ack_continuation'
def branch(path):
    tree=ast.parse(path.read_text())
    for n in ast.walk(tree):
        if isinstance(n,ast.If) and ast.unparse(n.test).startswith('now - last_sent >= 0.02'):
            return compile(ast.fix_missing_locations(ast.Module(body=[n],type_ignores=[])),str(path),'exec')
    raise AssertionError('PRODUCTION_SEND_BRANCH_NOT_FOUND')
def run(code,phase,age):
    sent=[];now=100.;env=dict(now=now,last_sent=99.,session=types.SimpleNamespace(phase=phase),sock=None,task={'run_id':'fixture'},vehicle=None,snapshot={},measured_at=now-age,peer='peer')
    env['policy_packet']=lambda run_id,v,snapshot,at,now,phase:dict(phase=phase,scan_measured_at=at,sent_at=now)
    env['send']=lambda sock,packet,peer:sent.append(packet)
    exec(code,env);return sent
def main():
    original=R/'experiments/v882_runtime_evidence_repair/native_loop.py';new=C/'native_loop.py'
    old=branch(original);fixed=branch(new)
    last=json.loads((R/'runs/v858_nav2_verified/v900/main_we/ROS_RESULT.json').read_text())['last_observation'];age=last['sent_at']-last['scan_measured_at']
    assert last['phase']=='RUNNING' and last['native_tick']==0 and age>.25
    checks={'old_real_race_reproduced':bool(run(old,'RUNNING',age)),
            'fixed_never_emits_prearm_running_snapshot':not run(fixed,'RUNNING',age),
            'waiting_initial_snapshot_unchanged':run(old,'WAITING',age)==run(fixed,'WAITING',age),
            'stopping_not_sent_as_initial':not run(fixed,'STOPPING',age)}
    for a in [0.,.05,.25,1.,5.]:checks['arm_interleaving_'+str(a)]=not run(fixed,'RUNNING',a)
    before="if now-last_sent>=.02:send(sock,policy_packet";after="if now-last_sent>=.02 and session.phase=='WAITING':send(sock,policy_packet"
    checks['exact_one_guard_delta']=new.read_text()==original.read_text().replace(before,after)
    text=new.read_text();a=text.index("session.step,vehicle,now)");b=text.index("if k%5==0:snapshot=",a);c=text.index("'observation_send'",b)
    checks['first_running_message_after_actual_k0_scan']=a<b<c and 'k=0;' in text
    science=json.loads((O/'ENTRY_CONTINUATION.json').read_text())['scientific_files_byte_identical_to_v900']
    checks['all_science_exact_v900']=all((C/n).read_bytes()==(R/'experiments/v900_refuge_terminal_set'/n).read_bytes() for n in science)
    for p in C.glob('*.py'):ast.parse(p.read_text())
    result=dict(passed=all(checks.values()),checks=checks,recorded_stale_age_s=age,models=0,integrations=0,
                scope='Exact production branch executed on saved stale packet; native k0 scan order unchanged; not actual navigation success')
    (O/'ACK_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 0 if result['passed'] else 1
if __name__=='__main__':sys.exit(main())
