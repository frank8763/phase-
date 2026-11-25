"""One runtime proof reuse, at most two same-package transport episodes."""
import importlib.util,json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs/v1923_dwa_five_checked_queue'
read=lambda p:json.loads(p.read_text())
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def main():
    rid=os.environ['PHASE_EVENING_ASSIGNMENT'];assert rid in [f'common_{i:02d}__DWA'for i in range(8,13)]
    D=S/'runtime_archives'/rid
    if '--source-sync'in sys.argv:
        p=R/'experiments/v1924_dwa_checked_source_recovery/deliver.py';s=importlib.util.spec_from_file_location('exact_reused_source_proof',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m.main(runtime=True)
    claim=D/'TRANSPORT_SUPERVISOR_ONCE.json';assert not claim.exists()and not(D/'FULL_REMOTE_VERIFIED.json').exists()
    put(claim,dict(pid=os.getpid(),started_unix=time.time(),maximum_episodes=2,per_episode_s=600,same_archive_only=True,no_owner_audit_replay_archive_push_ref_repeat=True))
    for episode in [1,2]:
        output=D/('transport_episode_'+str(episode));assert not output.exists()
        env=dict(os.environ,PHASE_TRANSPORT_SOURCE_ROOT=str(S),PHASE_TRANSPORT_OUTPUT=str(output))
        p=subprocess.run([sys.executable,'-B',str(C/'episode.py')],cwd=R,env=env,timeout=610)
        value=read(output/'RESULT.json')if(output/'RESULT.json').exists()else None
        if p.returncode==0 and value and value['passed']:
            put(D/'TRANSPORT_SUPERVISOR_CLOSED.json',dict(passed=True,closed=True,episodes=episode,models=0));return 0
        assert value is not None,'TRANSPORT_RESULT_MISSING_REQUIRES_REVIEW'
        error=value.get('first_error','')
        assert 'GITHUB_TRANSFER_FAILED'in error or 'TRANSIENT'in error or 'BOUNDED_FULL_ASSET_SHA_MISMATCH_OR_INCOMPLETE'in error,'NONTRANSIENT_TRANSPORT_STOP'
        if episode==1:time.sleep(15)
    put(D/'TRANSPORT_SUPERVISOR_CLOSED.json',dict(passed=False,closed=True,episodes=2,models=0));return 1
if __name__=='__main__':raise SystemExit(main())
