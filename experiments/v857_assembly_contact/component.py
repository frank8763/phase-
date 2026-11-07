"""Single-instance exact model-pair mechanism test; no planning or private predictions."""
import fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v857_assembly_contact';OLD=R/'runs/v856_nav2_foundation/entry01/vehicle_qualification01';END=float(os.environ['PHASE_MODEL_ABSOLUTE_DEADLINE']);W=R/'experiments/v855_renewal_worker'
for rel in ['runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1','experiments/v855_renewal_worker','experiments/v856_nav2_foundation']:sys.path.insert(0,str(R/rel))
import mujoco as mj
from model_patch import make_xml,transplant,verify_excludes
from vehicle_control import Adapter
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import pose_values
from contact_contract import GeometryCatalog
COUNTS=dict(model_loads=0,model_compiles=0,old_replay_native=0,same_control_actual_native=0,same_control_replay_native=0,closed_loop_actual_native=0,closed_loop_replay_native=0,private_native=0)
def dump(p,v):
    p=Path(p);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unchanged():
    manifest=json.loads((C/'SOURCE_FREEZE.json').read_text())['files'];assert all(digest(R/p)==h for p,h in manifest.items()),'FROZEN_SOURCE_OR_INPUT_CHANGED';assert time.time()<END,'ABSOLUTE_MODEL_DEADLINE'
def body(d):
    q=d.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));return float(q[0]),float(q[1]),yaw,float(d.qvel[0]*math.cos(yaw)+d.qvel[1]*math.sin(yaw)),float(d.qvel[5])
def contacts(m,d,catalog):
    return [(int(c.geom1),int(c.geom2),catalog.classify(c,0,0,float(d.time))['contact_type'],float(c.dist))for c in d.contact]
def contact_equal(a,b):return len(a)==len(b)and all(x[:3]==y[:3]and abs(x[3]-y[3])<=1e-8 for x,y in zip(a,b))
def initial_data(m,state):
    d=mj.MjData(m);mj.mj_setState(m,d,state,mj.mjtState.mjSTATE_INTEGRATION);mj.mj_forward(m,d);return d

def branch(m,initial,geometry,catalog,known,role,control_sequence=None,references=None,reference_contacts=None):
    out=OUT/role;out.mkdir(exist_ok=False);d=initial_data(m,initial);a=Adapter(m,mj,.01);rows=[];cc=[];commandrows=[];minimum=1e6;selfmin=1e6;lagmax=0.;maxerror=0.;maxbody=0.;previous=None;start=time.monotonic();fixed={k:getattr(m,k).copy()for k in ['geom_pos','geom_quat','geom_size','geom_contype','geom_conaffinity']};native_replay=role.endswith('replay');assembly={tuple(sorted(x))for x in [(23,25),(23,27)]};nself=0;summary=None
    try:
        for k in range(1100):
            if time.time()>=END:raise TimeoutError('ABSOLUTE_MODEL_DEADLINE')
            if previous is not None:assert np.array_equal(d.qpos,previous[0])and np.array_equal(d.qvel,previous[1]),'ROOT_STATE_CHANGED_BETWEEN_NATIVE_STEPS'
            x,y,yaw,mv,mw=body(d);elapsed=k*.01;v,w=(.2,0.)if 1<=elapsed<4 else(.15,.05)if 6<=elapsed<9 else(0.,0.)
            if control_sequence is None:
                d.ctrl[a.commands.ids]=a.compute(v,w,mv,mw)
            else:d.ctrl[:]=control_sequence[k]
            ctrl=d.ctrl.copy();last=np.zeros(m.nu)if k==0 else rows[-1]['ctrl'];assert a.commands.legal(d.ctrl[a.commands.ids]);assert np.all(abs(d.ctrl[a.commands.ids]-last[a.commands.ids])<=a.commands.rate*.01/.08+1e-10),'NATIVE_CONTROL_SLEW'
            if not native_replay:
                target=start+k*.01;time.sleep(max(0.,target-time.monotonic()));lag=time.monotonic()-target;lagmax=max(lagmax,lag);assert lag<=.1,'NATIVE_WALL_LAG_OVER_100MS'
            mj.mj_step(m,d);COUNTS[role+'_native']+=1;previous=(d.qpos.copy(),d.qvel.copy());assert np.array_equal(ctrl,d.ctrl),'CTRL_CHANGED_INSIDE_NATIVE'
            mj.mj_kinematics(m,d);mj.mj_collision(m,d);contact=contacts(m,d,catalog);cc.append(contact)
            assert all(np.array_equal(getattr(m,key),value)for key,value in fixed.items()),'STATIC_GEOMETRY_CHANGED'
            if role!='old_replay':assert not any(tuple(sorted((r[0],r[1])))in assembly for r in contact),'ASSEMBLY_CONTACT_NOT_EXCLUDED'
            bad=sum(r[2]in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for r in contact);nself+=sum(r[2]=='robot_self_contact'for r in contact)
            if role!='old_replay':assert not any(r[2]=='robot_self_contact'for r in contact),'UNEXPECTED_OTHER_SELF_CONTACT'
            box=geometry.actual(m,d);margin=float(containment_margin(box,[-.44,-.375,.44,.375]));x,y,yaw,mv,mw=body(d)
            f=SimpleNamespace(half=(box[2:]-box[:2])/2,center_local=(box[2:]+box[:2])/2,rectangles=np.asarray(known['known_rectangles']),circles=np.asarray(known['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));clear=float(pose_values(f,[[x,y,yaw]])[0]);minimum=min(minimum,clear);selfmin=min(selfmin,margin);maxbody=max(maxbody,abs(mv))
            assert clear>=.15-1e-8 and margin>=-1e-10 and bad==0,'PHYSICAL_CLEARANCE_SELF_OR_CONTACT_ANOMALY'
            row=dict(time=float(d.time),qpos=d.qpos.copy(),qvel=d.qvel.copy(),ctrl=d.ctrl.copy(),mocap_pos=d.mocap_pos.copy(),mocap_quat=d.mocap_quat.copy(),clearance=clear,self_margin=margin,body=np.asarray(body(d)));rows.append(row);commandrows.append([v,w,mv,mw])
            if references is not None:
                for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
                    if d.__getattribute__(key).size:maxerror=max(maxerror,float(np.max(abs(d.__getattribute__(key)-references[key][k]))))
                assert maxerror<=1e-8,'FULL_STATE_REPLAY_ERROR'
            if reference_contacts is not None:assert contact_equal(contact,reference_contacts[k]),'REPLAY_CONTACT_MISMATCH'
            if k%100==0:dump(OUT/'PARTIAL.json',dict(role=role,native=k+1,counts=COUNTS,minimum_clearance=minimum,body=body(d)))
        arr={key:np.asarray([row[key]for row in rows])for key in rows[0]};speed=arr['body'][:,3];mean=float(speed[250:390].mean());yawmean=float(arr['body'][750:890,4].mean());finalspeed=float(np.linalg.norm(d.qvel[:2]));summary=dict(passed=True,role=role,native_ticks=len(rows),minimum_actual_clearance_m=minimum,minimum_self_margin_m=selfmin,bad_obstacle_unknown_contacts=0,robot_self_contact_records=nself,steady_forward_m_s=mean,turn_mean_yaw_rad_s=yawmean,final_translation_speed_m_s=finalspeed,maximum_body_speed_m_s=maxbody,maximum_wall_lag_s=lagmax,maximum_replay_state_ctrl_mocap_error=maxerror,wall_paced=not native_replay)
        return arr,cc,summary
    finally:
        if rows:np.savez_compressed(out/'NATIVE_TRACE.npz',**{key:np.asarray([row[key]for row in rows])for key in rows[0]})
        with gzip.open(out/'CONTACTS.json.gz','xt')as stream:json.dump(cc,stream)
        dump(out/'BODY_COMMANDS.json',commandrows);dump(out/'COMPLETION.json',dict(complete=len(rows)==1100,executed_native=COUNTS[role+'_native'],fully_recorded_native=len(rows),summary=summary,counts=COUNTS.copy()))

def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('COMPONENT_ABSOLUTE_DEADLINE')));signal.setitimer(signal.ITIMER_REAL,max(.001,END-time.time()));status='ENTRY';result={'passed':False};branches=[]
    try:
        unchanged();actual=mj.MjModel.from_binary_path(str(OLD/'scene_model.mjb'));COUNTS['model_loads']+=1;assert digest(OLD/'scene_model.mjb')==json.loads((OLD/'SETUP.json').read_text())['model_sha256'];oldxml=OLD/'paired/assets/isolated_indoor.xml';newxml=make_xml(oldxml,OUT/'PATCHED_ASSEMBLY.xml',R/'runtime/mk-mini/training/assets/mkmini_real/meshes_fixed');fixed=mj.MjModel.from_xml_path(str(newxml));COUNTS['model_compiles']+=1;proof=transplant(actual,fixed);proof['exclude_signatures']=verify_excludes(fixed,mj);dump(OUT/'MODEL_DIFFERENCE.json',proof);mj.mj_saveModel(fixed,str(OUT/'PATCHED_MODEL.mjb'),None)
        initial=np.load(OLD/'INITIAL_STATE.npz')['state'];source=np.load(OLD/'NATIVE_TRACE.npz');original_contacts=json.load(gzip.open(OLD/'CONTACTS.json.gz','rt'))[1:];known=json.loads((W/'KNOWN_FIELD.json').read_text());oldcatalog=GeometryCatalog(actual,mj,oldxml);catalog=GeometryCatalog(fixed,mj,newxml);geometry=SelfGeometry(fixed,mj)
        original_d=initial_data(actual,initial);new_d=initial_data(fixed,initial);assert np.array_equal(geometry.actual(fixed,new_d),SelfGeometry(actual,mj).actual(actual,original_d)),'SELF_GEOMETRY_CHANGED';assert not np.any(fixed.body_mass!=actual.body_mass),'MASS_CHANGED'
        # Saved-pose comparisons and declared geometry negative fixtures, zero integrations.
        collision_checks=[];assembly={tuple(sorted(x))for x in [(23,25),(23,27)]}
        probes=[(f'saved_tick_{i+1}',source['qpos'][i].copy(),False)for i in [0,99,299,599,799,1099]]
        for name,xy in [('external_wall_left_front',[-.3,3.25]),('external_wall_right_front',[-.3,2.98])]:
            q=source['qpos'][299].copy();q[:2]=xy;probes.append((name,q,True))
        for name,q,negative in probes:
            original_d.qpos[:]=q;new_d.qpos[:]=q;original_d.qvel[:]=0.;new_d.qvel[:]=0.;mj.mj_forward(actual,original_d);mj.mj_forward(fixed,new_d);ca=contacts(actual,original_d,oldcatalog);cb=contacts(fixed,new_d,catalog);expected=[x for x in ca if tuple(sorted((x[0],x[1])))not in assembly];assert contact_equal(expected,cb),'CONTACT_DIFFERENCE_BEYOND_TWO_ASSEMBLY_PAIRS';ext=sum(x[2].startswith('robot_obstacle_')for x in cb)
            if negative:assert ext>0,'EXTERNAL_COLLISION_NEGATIVE_FIXTURE_INEFFECTIVE'
            collision_checks.append(dict(probe=name,zero_integration=True,only_declared_contacts_removed=True,external_collision_records=ext,negative_fixture=negative))
        dump(OUT/'COLLISION_QUALIFICATION.json',dict(passed=True,checks=collision_checks,all_external_masks_preserved=True,new_global_contact_callback=False));unchanged()
        oldarr,oldcc,s=branch(actual,initial,SelfGeometry(actual,mj),oldcatalog,known,'old_replay',source['ctrl'],source,original_contacts);branches.append(s);dump(OUT/'RESULT_PARTIAL.json',dict(branches=branches,counts=COUNTS))
        arr,cc,s=branch(fixed,initial,geometry,catalog,known,'same_control_actual',source['ctrl']);branches.append(s);arr2,cc2,s2=branch(fixed,initial,geometry,catalog,known,'same_control_replay',arr['ctrl'],arr,cc);branches.append(s2);dump(OUT/'RESULT_PARTIAL.json',dict(branches=branches,counts=COUNTS));unchanged()
        arr3,cc3,s3=branch(fixed,initial,geometry,catalog,known,'closed_loop_actual');branches.append(s3);arr4,cc4,s4=branch(fixed,initial,geometry,catalog,known,'closed_loop_replay',arr3['ctrl'],arr3,cc3);branches.append(s4)
        function=dict(forward_same_original_gate=.10<=s3['steady_forward_m_s']<=.30,turn_same_original_gate=.01<=s3['turn_mean_yaw_rad_s']<=.15,brake_same_original_gate=s3['final_translation_speed_m_s']<=.03)
        result.update(branches=branches,functional_checks=function,same_control_speed_ratio_to_old=s['steady_forward_m_s']/branches[0]['steady_forward_m_s'],same_controller_forward_relative_error=abs(s3['steady_forward_m_s']-.2)/.2,passed=all(function.values()),model_sha256=digest(OUT/'PATCHED_MODEL.mjb'),model_change='two assembly body-pair exclusions only; all actual physical arrays identical')
        status='ASSEMBLY_MODEL_AND_FIXED_CONTROLLER_QUALIFIED'if result['passed']else'FIXED_CONTROLLER_FUNCTIONAL_QUALIFICATION_NOT_PASSED'
    except BaseException as e:status='STOPPED_MODEL_SAFETY_OR_EVIDENCE_ANOMALY';result.update(error=repr(e),traceback=traceback.format_exc());dump(OUT/'ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),counts=COUNTS))
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);result.update(status=status,counts=COUNTS,branches=branches,closed=True,old_failures_preserved=True,new_navigation=0,new24=0);dump(OUT/'RESULT.json',result);print(json.dumps(result),flush=True)
    return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
