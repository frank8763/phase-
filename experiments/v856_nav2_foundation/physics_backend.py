"""Single native MuJoCo vehicle, evaluation truth kept out of the ROS policy."""
import gzip,hashlib,json,math,os,sys,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;W=R/'experiments/v855_renewal_worker'
for folder in ['runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1','runtime/mk-mini/experiments/phase_rpccr_p0b68_v1','runtime/mk-mini/training/phase14_lidar_depth_nav/envs','experiments/v733_early_low_translation_scan','experiments/v753_coupled_progress_repaired']:sys.path.insert(0,str(R/folder))
sys.path.insert(0,str(W));sys.path.insert(0,str(C))
import mujoco as mj
from factory import initialize
from instrumentation import install_physical_contract,Audit,dump
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import pose_values
from contact_contract import GeometryCatalog
from sensor_model import corrupt
from phase14_sensor_utils import get_lidar_features
from vehicle_control import Adapter
class Vehicle:
    def __init__(self,out,case,seed,dynamic=False):
        self.out=Path(out);self.out.mkdir(parents=True,exist_ok=False);os.environ['PHASE_FIELD_CASE']=case
        self.context,self.native=initialize(seed,self.out/'paired');self.env=self.context['env'];install_physical_contract(self.env);self.m=self.env.model;self.d=self.env.data;self.actor=None
        self.case=next(c for c in json.loads((W/'SCENE_CASES.json').read_text())if c['id']==case);self.seed=seed
        self.known=json.loads((W/'KNOWN_FIELD.json').read_text());self.noise=self.context['shift'].copy()
        # Disable only declared historical hidden static props; original 19 known bodies remain.
        for name in self.env.HIDDEN_GEOM_NAMES:
            gid=mj.mj_name2id(self.m,mj.mjtObj.mjOBJ_GEOM,name)
            if gid>=0:self.m.geom_contype[gid]=0;self.m.geom_conaffinity[gid]=0;self.m.geom_pos[gid,2]=-10
        mj.mj_forward(self.m,self.d)
        if dynamic:
            from dynamic_scene import setup
            from control_contract import planner_steering_bound
            os.environ['PHASE_COURSE_PHASE']=str([.6573753567727383,3.673083947600074,.9511239917756753][seed-10010001]);rect,circ=self.context['B'].clean_map(self.env)
            self.actor=setup(self.context,self.env,rect,circ,self.context['F'],self.context['H'],self.context['B'],mj,planner_steering_bound(self.env,mj)[0]);self.m,self.d=self.env.model,self.env.data
            from dynamic_contact import GeometryCatalog as DynamicCatalog
            self.catalog=DynamicCatalog(self.m,mj,self.context['xml'])
        else:self.catalog=GeometryCatalog(self.m,mj,self.context['xml'])
        self.geometry=SelfGeometry(self.m,mj);self.dt=float(self.m.opt.timestep);assert abs(self.dt-.01)<1e-12
        self.adapter=Adapter(self.m,mj,self.dt);self.audit=Audit();self.audit.begin(self.env,self.out,'NAV2_NATIVE_BODY_CONTROL')
        self.static={name:getattr(self.m,name).copy()for name in ['geom_pos','geom_quat','geom_size','geom_contype','geom_conaffinity']}
        self.count=0;self.bad=0;self.min_clear=1e6;self.min_self=1e6;self.rows=[];self.contacts=[];self.commands=[];self.sensor_rows=[]
        self.spec=mj.mjtState.mjSTATE_INTEGRATION;self.initial=np.zeros(mj.mj_stateSize(self.m,self.spec));mj.mj_getState(self.m,self.d,self.initial,self.spec)
        np.savez_compressed(self.out/'INITIAL_STATE.npz',state=self.initial);mj.mj_saveModel(self.m,str(self.out/'scene_model.mjb'),None)
        dump(self.out/'SETUP.json',dict(case=self.case,seed=seed,dynamic=dynamic,model_sha256=hashlib.sha256((self.out/'scene_model.mjb').read_bytes()).hexdigest(),known=self.known,noise=self.noise,dt=self.dt,actuator_ids=self.adapter.commands.ids,limits=np.c_[self.adapter.commands.lower,self.adapter.commands.upper],slew_per_second=self.adapter.commands.rate/.08,actor=None if self.actor is None else self.actor.config,stage_isolated=True))
        self.check()
    def body(self):
        q=self.d.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));v=float(self.d.qvel[0]*math.cos(yaw)+self.d.qvel[1]*math.sin(yaw));return float(q[0]),float(q[1]),yaw,v,float(self.d.qvel[5])
    def check(self):
        mj.mj_kinematics(self.m,self.d);mj.mj_collision(self.m,self.d);box=self.geometry.actual(self.m,self.d);margin=float(containment_margin(box,[-.44,-.375,.44,.375]));circles=self.known['known_circles']
        if self.actor is not None:circles=[*circles,[*self.actor.xy(self.d.time),.1]]
        field=SimpleNamespace(half=(box[2:]-box[:2])/2,center_local=(box[2:]+box[:2])/2,rectangles=np.asarray(self.known['known_rectangles']),circles=np.asarray(circles),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
        x,y,yaw,_,_=self.body();clear=float(pose_values(field,[[x,y,yaw]])[0]);self.min_clear=min(self.min_clear,clear);self.min_self=min(self.min_self,margin)
        contacts=[self.catalog.classify(c,self.count,self.count//8,float(self.d.time))for c in self.d.contact]
        bad=sum(r['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for r in contacts);self.bad+=bad
        self.contacts.append([(r['geom1_id'],r['geom2_id'],r['contact_type'],r['contact_distance'])for r in contacts])
        assert clear>=.15-1e-8 and margin>=-1e-10 and bad==0,'NATIVE_SAFETY_ANOMALY'
        assert all(np.array_equal(getattr(self.m,k),v)for k,v in self.static.items()),'STATIC_GEOMETRY_MUTATION'
        return clear,margin
    def step(self,v,w,stale=False):
        _,_,_,mv,mw=self.body();ctrl=self.adapter.compute(v,w,mv,mw,stale);self.audit.before_native(self.m,self.d);self.d.ctrl[self.adapter.commands.ids]=ctrl;before=self.d.ctrl.copy();self.native(self.m,self.d);self.count+=1;self.audit.after_native(self.m,self.d)
        if self.actor is not None:self.actor.synchronize(self.m,self.d)
        assert np.array_equal(self.d.ctrl,before),'NATIVE_CTRL_MUTATION';clear,margin=self.check();self.commands.append([time.monotonic(),v,w,mv,mw,stale]);self.rows.append(dict(time=float(self.d.time),qpos=self.d.qpos.copy(),qvel=self.d.qvel.copy(),ctrl=self.d.ctrl.copy(),mocap_pos=self.d.mocap_pos.copy(),mocap_quat=self.d.mocap_quat.copy(),clearance=clear,self_margin=margin))
    def scan(self):
        x,y,yaw,_,_=self.body();circles=self.known['known_circles']
        if self.actor is not None:circles=[*circles,[*self.actor.xy(self.d.time),.1]]
        sensor=SimpleNamespace(robot_xy=np.asarray([x,y],np.float32),robot_yaw=float(np.float32(yaw)),map_min=-5.,map_max=5.,rect_obstacles=np.asarray(self.known['known_rectangles'],np.float32),circle_obstacles=np.asarray(circles,np.float32))
        raw=get_lidar_features(sensor,num_rays=32,max_range=3.);values=corrupt(raw,self.seed,self.noise['lidar_call']+self.count//5,'lidar',3.)*3
        packet=dict(native_tick=self.count,time=float(self.d.time),xy=[x,y],yaw=float(np.float32(yaw)),ranges=values.tolist(),raw_lidar=raw.tolist());self.sensor_rows.append(packet);return packet
    def finish(self):
        if hasattr(self,'finished_summary'):return self.finished_summary
        if self.rows:
            np.savez_compressed(self.out/'NATIVE_TRACE.npz',**{k:np.asarray([r[k]for r in self.rows])for k in self.rows[0]})
        dump(self.out/'BODY_COMMANDS.json',self.commands)
        with gzip.open(self.out/'CONTACTS.json.gz','xt')as f:json.dump(self.contacts,f)
        with gzip.open(self.out/'SENSORS.json.gz','xt')as f:json.dump(self.sensor_rows,f)
        self.finished_summary=dict(actual_native=self.count,minimum_actual_clearance_m=self.min_clear,minimum_self_margin_m=self.min_self,bad_contacts=self.bad,final_body=self.body(),goal_distance_m=float(np.linalg.norm(self.d.qpos[:2]-self.case['goal_xy'])))
        return self.finished_summary
    def replay(self):
        d=mj.MjData(self.m);mj.mj_setState(self.m,d,self.initial,self.spec);mj.mj_forward(self.m,d);maxerror=0.;contacterror=0
        # check() adds one t0 contact row, so actual native rows begin at index 1.
        for i,row in enumerate(self.rows):
            if time.time()>=1794052800:raise TimeoutError('ROOT_DEADLINE_REPLAY')
            d.ctrl[:]=row['ctrl'];self.native(self.m,d)
            if self.actor is not None:self.actor.apply(self.m,d)
            mj.mj_kinematics(self.m,d);mj.mj_collision(self.m,d)
            for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
                if getattr(d,k).size:maxerror=max(maxerror,float(np.max(abs(getattr(d,k)-row[k]))))
            contacts=[self.catalog.classify(c,i+1,(i+1)//8,float(d.time))for c in d.contact];actual=[(r['geom1_id'],r['geom2_id'],r['contact_type'],r['contact_distance'])for r in contacts]
            expected=self.contacts[i+1]
            if len(actual)!=len(expected):contacterror+=1
            elif any(a[:3]!=b[:3]or abs(a[3]-b[3])>1e-8 for a,b in zip(actual,expected)):contacterror+=1
        result=dict(replay_native=len(self.rows),maximum_qpos_qvel_ctrl_mocap_error=maxerror,contact_mismatched_ticks=contacterror,passed=maxerror<=1e-8 and contacterror==0);dump(self.out/'REPLAY.json',result);return result
