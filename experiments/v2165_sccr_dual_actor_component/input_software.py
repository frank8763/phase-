from common import *
import numpy as np
from saved_inputs import packet,observation
assert os.sched_getaffinity(0)=={0}and not(S/'SAVED_INPUT_SOFTWARE_PROOF.json').exists()
rows=[]
for i in range(3):
 p=packet(np,i);calls=[]
 def explicit_stub(x):assert x.shape==(107,);calls.append(x.copy());return np.array([.2,-.1],np.float32)
 obs,parts=observation(np,p,explicit_stub);assert len(calls)==1 and obs.shape==(186,)and np.array_equal(obs[127:129],np.array([.2,-.1],np.float32));assert p['previous_body_command']==[0.,0.]
 rows.append(dict(native=5*i,dimensions=[len(calls[0]),len(obs)],original107_before186=True,nonzero_stub_marker_in_baseblock=True,saved_fixture_not_live=True))
v=dict(passed=True,closed=True,fixtures=rows,explicit_network_constructors=0,weight_deserializations=0,forward_calls=0,physics=0,replay=0,stub_provider_only=True,actual_phase6_provider_pending=True);dump(S/'SAVED_INPUT_SOFTWARE_PROOF.json',v);print(json.dumps(v))
