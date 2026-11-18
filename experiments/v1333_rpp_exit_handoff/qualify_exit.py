"""Regression at the production supervisor policy seam, no physical imports."""
import ast
import json
from pathlib import Path
import tempfile
from peer_exit import peer_exit_policy

R=Path(__file__).resolve().parents[2]
O=R/'runs/v1333_rpp_exit_handoff'


def main():
    # Extract the exact abort condition that prematurely killed the real worker.
    source=R/'experiments/v1332_common_map_static_campaign/campaign.py'
    tree=ast.parse(source.read_text())
    old=next(n.test for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='any((p.poll() not in (None, 0) for p in jobs))')
    class Job:
        def __init__(self,code):self.code=code
        def poll(self):return self.code
    premature=eval(compile(ast.Expression(old),str(source),'eval'),{'jobs':[Job(1),Job(None)]})
    assert premature is True
    cases=[]
    with tempfile.TemporaryDirectory(dir=O) as folder:
        p=Path(folder)
        functional=dict(action_status=6,error_code=104,public_static_map_receipt={'passed':True})
        scenarios=[('functional_ros_drain',[1,None],functional,None,'DRAIN'),
                   ('unexpected_ros_fault',[1,None],dict(error='UNEXPECTED'),None,'ABORT'),
                   ('missing_ros_result',[1,None],None,None,'ABORT'),
                   ('wrong_exit_even_with_receipt',[2,None],functional,None,'ABORT'),
                   ('map_missing',[1,None],dict(action_status=6,error_code=104),None,'ABORT'),
                   ('native_safety_fail',[0,1],None,dict(error='NATIVE_SAFETY_ANOMALY',evidence_saved=True),'ABORT'),
                   ('native_signal',[None,-15],None,None,'ABORT'),
                   ('native_functional_saved',[None,1],None,dict(evidence_saved=True,replay={'passed':True}),'DRAIN'),
                   ('native_replay_missing',[None,1],None,dict(evidence_saved=True),'ABORT'),
                   ('normal_ros_exit_waits_native',[0,None],None,None,'WAIT'),
                   ('both_running',[None,None],None,None,'WAIT')]
        for name,codes,ros,native,expected in scenarios:
            for namefile,value in [('ROS_RESULT.json',ros),('RESULT.json',native)]:
                path=p/namefile
                if value is None:path.unlink(missing_ok=True)
                else:path.write_text(json.dumps(value))
            actual=peer_exit_policy(codes,p);assert actual==expected,(name,actual,expected)
            cases.append(dict(name=name,passed=True,actual=actual))
    proof=dict(passed=True,original_exact_ast_reproduced_premature_abort=premature,
               cases=cases,tests=len(cases),models=0,physical_native=0,
               original_deadline_and_storage_checks_remain_in_wait_loop=True)
    (O/'EXIT_POLICY_QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='cases'}))


if __name__=='__main__':main()
