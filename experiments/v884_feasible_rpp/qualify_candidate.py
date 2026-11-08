"""Zero-model release gate over genuine ROS saved-input evidence and source-bound contracts."""
import ast,hashlib,json,math,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v884_feasible_rpp';D=R/'runs/v883_observation_dispatch'
sys.path.insert(0,str(C));from twist_contract import require_representable,MAX_CURVATURE
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    checks={};sources=[]
    def load(p):sources.append(p);return read(p)
    checks['native_loop_19_fault_cases']=load(O/'ZERO_QUALIFICATION.json')['passed']
    checks['actual_entry_15_authority_cases']=load(O/'ENTRY_QUALIFICATION.json')['passed']
    checks['build_real_plugin']=load(O/'BUILD_RESULT.json')['passed']
    checks['only_declared_upstream_method_and_config_changes']=load(O/'SOURCE_SCOPE_AUDIT.json')['passed']
    old=load(D/'checkpoint_175_originaldelay/ROS_RESULT.json');new=load(D/'checkpoint_175_concurrentdelay/ROS_RESULT.json')
    checks['full_bridge_original350ms_failure']=old.get('error')=="ProtocolError('PHYSICS_STOPPED_OR_STALE')"
    checks['full_bridge_concurrent350ms_success']=new['passed']and new['maximum_observation_age_s']<=.2
    for attempt in ['01','02']:
        checks['original_dispatch_red_'+attempt]=load(D/('DISPATCH_original_'+attempt+'.json'))['reproduced_original_watchdog_failure']
        row=load(D/('DISPATCH_concurrent_'+attempt+'.json'));checks['concurrent_dispatch_green_'+attempt]=row['passed']and row['cached_age_s']<=.2
    checks['real_missing_source_still_stops']=load(D/'DISPATCH_source_stopped_01.json')['reproduced_original_watchdog_failure']
    original=load(D/'checkpoint_150_original/COMMANDS.json')['cmd_vel_nav'][0]
    checks['old_saved_command_provably_unrepresentable']=abs(original[2]/original[1])>MAX_CURVATURE
    checks['post_smoother_violation_preserved']=load(D/'checkpoint_150_feasible02/ROS_RESULT.json').get('error')=="ValueError('FINAL_TWIST_OUTSIDE_NATIVE_CURVATURE')"
    for name in ['checkpoint_150_feasible03','checkpoint_175_feasible']:
        ros=load(D/name/'ROS_RESULT.json');commands=load(D/name/'COMMANDS.json');checks[name+'_real_nav2_nonzero']=ros['passed']and ros['qualified_initial_control']and any(abs(c[1])>=.005 for c in commands['cmd_vel'])
        checks[name+'_nominal_and_final_curve_feasible']=bool(commands['cmd_vel'])and all(require_representable(c[1],c[2])for group in ['cmd_vel','cmd_vel_nav']for c in commands[group])
    for v,w in [(0.,1.),(.01,.1),(float('nan'),0.)]:
        try:require_representable(v,w);checks['invalid_'+str(v)+'_'+str(w)]=False
        except ValueError:checks['invalid_'+str(v)+'_'+str(w)]=True
    p=subprocess.run(['g++','-std=c++17','-O2',str(C/'test_feasible_twist.cpp'),'-o',str(O/'test_feasible_twist')],cwd=R,capture_output=True,text=True,timeout=20);checks['projection_unit_compiles']=p.returncode==0
    p=subprocess.run([str(O/'test_feasible_twist')],cwd=R,capture_output=True,text=True,timeout=5);checks['actual_cpp_projection_saved_case_and100000_properties']=p.returncode==0 and '100000_CONTRACT_CASES_PASS'in p.stdout;(O/'CPP_CONTRACT.console').write_text(p.stdout+p.stderr)
    for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    checks['no_live_model_authority']=not(O/'AUTHORIZATION.json').exists()and not(O/'ROUND_WINDOW.json').exists()and not(R/'runs/v858_nav2_verified/v884').exists()
    build=read(O/'BUILD_RESULT.json');checks['compiled_source_and_plugin_match_current_bytes']=build['source_sha256']==sha(C/'feasible_rpp.cpp')and build['plugin_sha256']==sha(O/'install/lib/libphase_feasible_rpp.so')
    record=dict(passed=all(checks.values()),checks=checks,underlying_loop_and_entry_tests=34,cpp_fixed_seed_cases=100000,genuine_saved_checkpoint_qualifications=2,models=0,native_integrations=0,real_actuator_commands_executed=0,new_window_started=False,models_authorized=False,evidence_sources={str(p.relative_to(R)):sha(p)for p in sources},limits=['No new closed-loop vehicle navigation','No exact reproduction of the unsaved old local costmap','No proof of closed-loop success, hard realtime,RP-CCR328 or RAS novelty','Native steering dynamics and original safety checks still require bounded actual validation'])
    (O/'CANDIDATE_QUALIFICATION.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items()if k!='evidence_sources'}),flush=True);return 0 if record['passed']else 1
if __name__=='__main__':sys.exit(main())
