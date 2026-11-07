"""Exercise the shared ordinary/return callsite and prepared batch API; no models."""
import argparse,ast,copy,hashlib,json
from pathlib import Path
import numpy as np
from coordinator import Coordinator
from qualify import certificate,qpos

R=Path(__file__).resolve().parents[2];OUT=R/'runs/v852_maneuver_contract';C=Path(__file__).parent


def main():
    global OUT
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=OUT/'coordinator_final01');args=parser.parse_args();OUT=args.output.resolve();assert OUT.is_relative_to(R/'runs/v852_maneuver_contract');OUT.mkdir(parents=True,exist_ok=False)
    path=np.array([[0.,0.,0.,1.],[-.5,0.,0.,-1.],[-1.,0.,0.,-1.],[-.5,0.,0.,1.],[2.,0.,0.,1.]])
    c=certificate(-.06,-.3,x8=-.01);before=copy.deepcopy(c);decisions=[]
    for role in ['ORDINARY','BACKUP_RETURN']:
        controller=Coordinator();controller.install_reference(path,[2.,0.],0)
        answer=controller.try_certificate(c,qpos(0.),np.zeros(6),0.,role=role);assert answer['accepted'];decisions.append(answer['decision'])
        old_reference=controller.reference.reference_id
        for i in range(4):
            suppressed=controller.try_certificate(c,qpos(0.),np.zeros(6),0.,role='BACKUP_RETURN')
            assert suppressed['status']=='CONTINUE_COMMITTED32'and not suppressed['accepted']and not suppressed['heavy_candidate_search_required']
            n=8*(i+1);q=c['initial_qpos']if n==8 else c['qpos'][n-9];v=c['initial_qvel']if n==8 else c['qvel'][n-9]
            receipt=controller.actual_public_receipt(q,v,suppressed['command']);assert receipt['complete']==(i==3)
        assert controller.last_accepted['maneuver_contract']['role']==role
        # The rest of the complete original 328-tick certificate stays owned.
        for n in range(40,329,8):
            receipt=controller.actual_public_receipt(c['qpos'][n-9],c['qvel'][n-9],controller.retained_command());assert receipt['complete']==(n==328)
        assert controller.backup_finished()['reference_id']==old_reference and controller.reference.path is not None
    assert decisions[0]==decisions[1],'ORDINARY_AND_RETURN_MERIT_MUST_BE_IDENTICAL'
    for key in ['qpos','qvel','controls','initial_qpos','initial_qvel','prefix_command']:assert np.array_equal(c[key],before[key])
    # Current installed API is read from source, not imported or instantiated.
    installed=Path('/home/linghu/miniconda3/envs/mk_mujoco/lib/python3.10/site-packages/mujoco/rollout.py');tree=ast.parse(installed.read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='rollout');allowed={a.arg for a in function.args.args+function.args.kwonlyargs}
    adapter=C/'native_batch.py';parsed=ast.parse(adapter.read_text());call=next(n for n in ast.walk(parsed)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='rollout')
    assert all(k.arg in allowed for k in call.keywords)
    assert 'nthread'not in [k.arg for k in call.keywords]
    # API presence never qualifies MuJoCo batch dynamics or performance.
    value=dict(status='COORDINATED_CALLSITE_ZERO_MODEL_PASS',passed=True,ordinary_return_decisions_identical=True,unfinished32_commitment_suppresses_replacement=True,actual_state_ctrl_receipts_checked=True,original328_remainder_not_discarded_at32=True,reference_survives_backup=True,input_certificate_not_mutated=True,native_batch_keywords_match_installed_source=True,installed_rollout_sha256=hashlib.sha256(installed.read_bytes()).hexdigest(),source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in C.glob('*.py')},new_models=0,new_integrations=0,actual_native_batch_invoked=False,closed_loop_worker_integration_qualified=False,real_time_qualified=False)
    (OUT/'COORDINATOR_QUALIFICATION.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
