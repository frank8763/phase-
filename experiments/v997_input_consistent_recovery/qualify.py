"""Candidate must qualify both original states before any model admission."""
import hashlib,json,math,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v997_input_consistent_recovery'
sys.path.insert(0,str(C))
from state_reference import construct,GAIN,RATE_COUPLING,VIRTUAL_RATE,REFERENCE_SPEED,K
from saved_qualification import reconstruct,independently_check_geometry
def read(p):return json.loads(p.read_text())
if __name__=='__main__':
    root=read(R/'runs/sim_time_recovery_20261110/ROUND_WINDOW.json');d=read(R/'runs/v995_sim_time_response/COMPLETION.json')
    assert d['diagnostic_evidence_passed']and time.time()<min(root['deadline_unix'],d['closed_unix']+1500.)
    saved=read(R/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json');known=read(R/'runs/v995_sim_time_response/prior_v974/physics/SETUP.json')['known']
    reports=[]
    for index in [0,1]:
        s=saved['rows'][index];packet=s['search_packet'];source=s['search_source'];now=packet['body_measured_at']
        p=construct(packet,source,[4.,-2.],known,now);checks=dict(reference_found=p['passed'])
        report=dict(index=index,passed=False,plan=p,checks=checks)
        if p['passed']:
            fine=reconstruct(p['initial_state'],p['edge_targets']);coarse=fine[::25];error=float(abs(coarse-np.array(p['state_path'])).max())
            raw=independently_check_geometry(fine,known,source['periodic'])
            gradient=GAIN*K+abs(RATE_COUPLING)*VIRTUAL_RATE/REFERENCE_SPEED
            rho=math.hypot(.44,.375);reserve=.04+rho*.035+.1*(.13+rho*.16)+.02*(.13+rho*.16+.08)
            lower=raw-reserve-.0005/2*(1+rho*gradient)
            progress=float(np.linalg.norm(fine[0,:2]-[4.,-2.])-np.linalg.norm(fine[-1,:2]-[4.,-2.]))-.08
            checks.update(independent_reference=error<=1e-5,full_cycle_geometry=lower>=.155,original_progress=progress>=.4,
                original_steering=bool(abs(fine[:,3]).max()<=math.atan(.6*K)+1e-10))
            report.update(independent_max_error=error,independent_full_cycle_lower_m=lower,actual_progress_lower_m=progress)
            report['passed']=all(checks.values())
        reports.append(report)
    outcome=dict(passed=all(x['passed']for x in reports),status='SOURCE_GEOMETRY_QUALIFIED'if all(x['passed']for x in reports)else'REJECTED_BEFORE_MODEL_ADMISSION',
        models=0,integrations=0,private_predictions=0,physics_replay=0,rows=reports,parameters_not_refit_on_second_state=True,
        root_deadline_unix=root['deadline_unix'],physical_controller_ready=False,model_authority=False,
        stop_reason='Second original state has no response-consistent route within the fixed bounded search; no dependent physical task started')
    (O/'QUALIFICATION.json').write_text(json.dumps(outcome,indent=2)+'\n')
    files={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in C.iterdir()if p.is_file()and p.name!='SOURCE_FREEZE.json'}
    (C/'SOURCE_FREEZE.json').write_text(json.dumps(dict(final=True,source_only=True,physical_authority=False,models=0,files=files),indent=2)+'\n')
    print(json.dumps(dict(passed=outcome['passed'],status=outcome['status'],models=0,rows=[{k:v for k,v in x.items()if k not in {'plan'}}for x in reports])))
