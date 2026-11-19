"""Sequential isolated actual installed map startup, no vehicle models."""
import subprocess
import sys
from component_context import *
from campaign import ros_environment


def main():
    guard=(R/'REVIEW_PENDING').read_bytes();pointer=(R/'CURRENT_EXPERIMENT.json').read_bytes();rows=[]
    assert not (O/'USER_WINDOW.json').exists() and sources()
    for index,method in enumerate(['rpp','mppi']):
        ros,env=ros_environment(O,method);env['ROS_DOMAIN_ID']=str(229+index)
        result=subprocess.run(ros.command(['/usr/bin/python3.12','-B',str(C/'map_probe.py'),method]),cwd=R,env=env,capture_output=True,text=True,timeout=40)
        (O/(method+'_map_software.console')).write_text(result.stdout+result.stderr)
        proof=read(O/('map_software_'+method)/'RESULT.json');rows.append(proof)
        assert result.returncode==0 and proof['passed'] and proof['controller_server_exited'] and proof['no_physical_modules_loaded'],'ACTUAL_MAP_ENTRY_FAILURE'
    assert sources() and (R/'REVIEW_PENDING').read_bytes()==guard and (R/'CURRENT_EXPERIMENT.json').read_bytes()==pointer
    dump(O/'ACTUAL_MAP_SOFTWARE_QUALIFICATION.json',dict(passed=True,results=rows,models=0,physical_native=0,no_actions_or_vehicle_models=True,source_unchanged=True))
    print(json.dumps(dict(passed=True,actual_installed_startups=len(rows),models=0,physical_native=0)))


if __name__=='__main__':main()
