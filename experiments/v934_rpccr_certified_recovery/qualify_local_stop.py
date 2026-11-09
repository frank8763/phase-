"""Constructed exact ingress phase/command seam, including local deadline stop."""
import copy,json,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v934_rpccr_certified_recovery';sys.path.insert(0,str(C));from ingress_audit import check
proof=dict(passed=True,v=0.,w=0.,body_native_tick=0,body=[0.,0.,0.,0.,0.],body_age_s=.001,issued_at=100.,residual_position_m=.02,terminal_cycle_qualified=True,terminal_cycle_lower_m=.2,source_native_tick=0)
p=dict(run_id='test',kind='command',sequence=1,issued_at=100.,v=0.,w=0.,tube=proof)
receipts=[dict(native_tick=0,packet=dict(run_id='test',kind='arm'),prior_sequence=None,retained_sequence=None,decision='CONTROL_EVENT'),dict(native_tick=0,packet=p,received_at=100.01,prior_sequence=None,retained_sequence=1,decision='ACCEPTED')]
steps=[dict(native_tick=1,phase='RUNNING',sequence=1,at=100.02,controls=[0.,0.,False],completed=True),dict(native_tick=2,phase='STOPPING',sequence=1,at=100.03,controls=[0.,0.,True],completed=True)]
data=dict(receipts=receipts,execution=steps,local_stop_events=[dict(native_tick=1)])
a=check(data,[proof],np.zeros((2,5)),'test');checks=dict(local_stop_reconstructed=a['passed'])
bad=copy.deepcopy(data);bad['local_stop_events']=[];checks['missing_local_stop_rejected']=not check(bad,[proof],np.zeros((2,5)),'test')['passed']
bad=copy.deepcopy(data);bad['execution'][1]['controls']=[.1,0.,False];checks['moving_after_local_stop_rejected']=not check(bad,[proof],np.zeros((2,5)),'test')['passed']
post=copy.deepcopy(data);post['receipts'].append(dict(native_tick=1,packet=dict(p,sequence=2,issued_at=100.021,tube=dict(proof,issued_at=100.021)),received_at=100.025,prior_sequence=1,retained_sequence=1,decision='POST_STOP_COMMAND_IGNORED'))
checks['poststop_no_anchor_reset']=check(post,[proof,post['receipts'][-1]['packet']['tube']],np.zeros((2,5)),'test')['passed']
x=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0);(O/'LOCAL_STOP_AUDIT_QUALIFICATION.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x));assert x['passed']
