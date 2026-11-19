"""Four actual installed stationary controller actions; exact producer audits."""
import subprocess
import sys
from component_context import *
from campaign import ros_environment
from relay_policy import FUNCTIONAL

def main():
    guard=(R/'REVIEW_PENDING').read_bytes();pointer=(R/'CURRENT_EXPERIMENT.json').read_bytes();(O/'software').mkdir(exist_ok=True);results=[];reuse=[]
    for index,task in enumerate(read(C/'SOFTWARE_TASKS.json')):
        ros,env=ros_environment(O,task['controller_kind']);env['ROS_DOMAIN_ID']=str(211+index)
        saved=O/'software'/task['id']/'RESULT.json'
        if saved.exists():
            assert (O/'PREPARATION_ERRORS.json').exists()
            proof=read(saved);assert proof['task']==task and proof['classification']=='LEGAL_ADMITTED_COMMAND'
            assert proof['interface_qualified'] and proof['controller_server_exited'] and proof['no_model_modules_loaded']
            code='import sys,json;sys.path.insert(0,sys.argv[1]);from software_common import plain;print(json.dumps(plain(json.load(open(sys.argv[2])))))'
            p=subprocess.run(ros.command(['/usr/bin/python3.12','-B','-c',code,str(C),str(saved)]),cwd=R,env=env,capture_output=True,text=True,timeout=10)
            assert p.returncode==0 and json.loads(p.stdout)['interface_qualified'];reuse.append(task['id'])
        else:
            p=subprocess.run(ros.command(['/usr/bin/python3.12','-B',str(C/'software_probe.py'),str(index)]),cwd=R,env=env,capture_output=True,text=True,timeout=60)
            (O/(task['id']+'.console')).write_text(p.stdout+p.stderr);proof=read(saved)
            assert p.returncode==0 and proof['interface_qualified'] and proof['controller_server_exited'] and proof['no_model_modules_loaded'],'ACTUAL_CONTROLLER_SOFTWARE '+task['id']
        results.append(proof)
    # Existing real full-route failure and successful recovery exercise both
    # production auditors in the exact producer environment, no physics.
    saved=[('recovery',R/'experiments/v1368_rolling_map_entry/TASKS.json'),('route',R/'experiments/v1361_dynamic_reserve_consistency/TASKS.json')];audits=[]
    for label,source in saved:
        task=read(source)[0];task['controller_kind']='rpp';path=O/('saved_'+label+'_audit_task.json');dump(path,task)
        ros,env=ros_environment(O,'rpp');p=subprocess.run(ros.command(['/usr/bin/python3.12','-B',str(C/'audit_entry.py'),str(path)]),cwd=R,env=env,capture_output=True,text=True,timeout=150)
        (O/(label+'_saved_audit.console')).write_text(p.stdout+p.stderr);assert p.returncode==0,'SAVED_AUDIT_ENTRY '+label;proof=json.loads(p.stdout);dump(O/(label.upper()+'_SAVED_AUDIT.json'),proof)
        assert all(value for name,value in proof['checks'].items() if name not in FUNCTIONAL),'SAVED_PHYSICAL_GATE '+label
        if label=='recovery':assert proof['passed']
        audits.append(proof)
    assert sources() and (R/'REVIEW_PENDING').read_bytes()==guard and (R/'CURRENT_EXPERIMENT.json').read_bytes()==pointer
    dump(O/'SOFTWARE_QUALIFICATION.json',dict(passed=True,actual_controller_cases=results,exact_runtime_saved_audits=audits,reused_qualified_action_after_print_only_failure=reuse,models=0,physical_native=0,new_navigation_trials=0));print(json.dumps(dict(passed=True,actual_software_cases=len(results),exact_runtime_saved_audits=len(audits),models=0)))

if __name__=='__main__':main()
