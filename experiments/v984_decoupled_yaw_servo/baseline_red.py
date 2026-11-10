"""Original rear driving targets do not respond to measured yaw; saved-data red seam."""
import json,math
from pathlib import Path
import numpy as np
from control_fixture import R,frozen,make,copy_state
C=Path(__file__).parent;O=R/'runs/v984_decoupled_yaw_servo'
def main():
    O.mkdir(exist_ok=True)
    saved=R/'runs/v983_saved_transient_diagnosis';setup=json.loads((saved/'physics/SETUP.json').read_text())
    commands=json.loads((saved/'physics/BODY_COMMANDS.json').read_text());adapter=make(frozen.Adapter);maximum=0.;checkpoint=None
    with np.load(saved/'physics/NATIVE_TRACE.npz')as data:
        for i,row in enumerate(commands):
            if i+1==6175:checkpoint=copy_state(adapter,frozen.Adapter)
            control=adapter.compute(row[1],row[2],row[3],row[4],row[5]);maximum=max(maximum,float(abs(control-data['ctrl'][i,setup['actuator_ids']]).max()))
    row=commands[6174];bad=copy_state(checkpoint,frozen.Adapter);ideal=copy_state(checkpoint,frozen.Adapter)
    control_bad=bad.compute(row[1],row[2],row[3],row[4],False)
    control_ideal=ideal.compute(row[1],row[2],row[3],row[2],False)
    response=float(np.max(abs(control_bad-control_ideal)))
    result=dict(passed=False,models=0,integrations=0,saved_control_rows=len(commands),
                original_control_reconstruction_maximum_error=maximum,
                exact_original_map_reconstructed=maximum<=1e-8,
                original_driving_map_ignores_measured_yaw=response==0.,
                original_feedback_response_magnitude=response,request_v_w=row[1:3],measured_body_v_w=row[3:5],
                original_control=control_bad.tolist(),old_physical_outcome_unchanged='V982_NOT_PASSED')
    assert result['exact_original_map_reconstructed']and result['original_driving_map_ignores_measured_yaw']
    (O/'BASELINE_RED.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
