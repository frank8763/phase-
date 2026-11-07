"""Render actual saved native states; all integration/rollout entry points sealed."""
import os,json,gzip,hashlib,time,signal,fcntl,subprocess,math
from pathlib import Path
import numpy as np
import mujoco,mujoco.rollout
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
repo=Path(os.environ['PHASE_REPO']);root=repo/'runs/v804_no_dynamic_static_contact';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert read(root/'FINALIZED.json')['complete_five'];summary=read(root/'FINAL_INDEPENDENT_AUDIT.json');assert summary['completed']
with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('STATIC_SAVED_RENDER_600S')));signal.alarm(600)
calls=0
def forbidden(*a,**kw):
 global calls
 calls+=1;raise AssertionError('SAVED_MEDIA_CANNOT_ADVANCE_PHYSICS')
for n in ['mj_step','mj_step1','mj_step2']:setattr(mujoco,n,forbidden)
mujoco.rollout.rollout=forbidden
selected=next((r for r in summary['rows']if r['strict_static_success']),min(summary['rows'],key=lambda r:r['metrics']['goal_remaining_m']));pair=root/selected['name']/'paired';cell=pair/'geometry_memory';p=read(pair/'STATIC_PROTOCOL.json');res=read(cell/'result.json');model=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));assert model.nmocap==0;data=mujoco.MjData(model)
with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as f:native=list(map(json.loads,f))
assert len(native)==res['physics_steps']and read(pair/'NATIVE_REPLAY_AUDIT.json')['maximum_full_native_state_ctrl_error']<=1e-8
out=repo/'runs/report_materials_v804_20261104';assert not out.exists();out.mkdir();model.vis.global_.offwidth=1180;model.vis.global_.offheight=850;model.vis.headlight.ambient[:]=.65;model.vis.headlight.diffuse[:]=.8
for i in range(model.ngeom):
 name=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,i)or''
 if name.startswith(('real_rect_obs_','real_circle_obs_'))and model.geom_pos[i,2]>-1:model.geom_rgba[i]=[.49,.56,.63,1];model.geom_matid[i]=-1
renderer=mujoco.Renderer(model,height=850,width=1180,max_geom=6000);close=mujoco.Renderer(model,height=540,width=680,max_geom=6000);cam=mujoco.MjvCamera();cam.type=mujoco.mjtCamera.mjCAMERA_FREE;cam.lookat[:]=[0,0,.1];cam.distance=13.6;cam.azimuth=90;cam.elevation=-90;follow=mujoco.MjvCamera();follow.type=mujoco.mjtCamera.mjCAMERA_FREE;follow.distance=3.;follow.elevation=-50
fontfile='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';fonts={n:ImageFont.truetype(fontfile,n)for n in [22,25,28,32,40]};goal=np.asarray(p['goal_xy']);plan=np.asarray(read(cell/'planning_0000.json')['path'])
def decorations(r,trail):
 scene=r.scene
 def geom(kind,size,pos,color):
  g=scene.geoms[scene.ngeom];mujoco.mjv_initGeom(g,kind,np.asarray(size,float),np.asarray(pos,float),np.eye(3).ravel(),np.asarray(color,np.float32));g.category=int(mujoco.mjtCatBit.mjCAT_DECOR);scene.ngeom+=1;return g
 def line(a,b,color,width):
  if np.linalg.norm(np.asarray(a)-b)<1e-10:return
  g=geom(mujoco.mjtGeom.mjGEOM_CAPSULE,[width,0,0],[0,0,0],color);mujoco.mjv_connector(g,mujoco.mjtGeom.mjGEOM_CAPSULE,width,np.asarray(a,float),np.asarray(b,float))
 for a,b in zip(plan[:-1],plan[1:]):line([*a[:2],.024],[*b[:2],.024],[.1,.72,.32,1],.018)
 for a,b in zip(trail[:-1],trail[1:]):line([*a,.044],[*b,.044],[.04,.40,.95,1],.021)
 geom(mujoco.mjtGeom.mjGEOM_CYLINDER,[.15,.015,0],[*goal,.04],[.98,.72,.04,1]);scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW]=False

def frame(row,trail):
 data.qpos[:]=row['qpos_full'];data.qvel[:]=row['qvel_full'];data.ctrl[:]=row['actual_ctrl'];data.time=float(row['time']);before=data.qpos.copy();v=data.qvel.copy();t=data.time;mujoco.mj_forward(model,data);assert np.array_equal(data.qpos,before)and np.array_equal(data.qvel,v)and data.time==t
 renderer.update_scene(data,camera=cam);decorations(renderer,trail);aa=renderer.render();q=data.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));follow.lookat[:]=[q[0],q[1],.3];follow.azimuth=math.degrees(yaw)+125;close.update_scene(data,camera=follow);decorations(close,trail[-400:]);bb=close.render()
 image=Image.new('RGB',(1920,1080),'#f3f6fa');d=ImageDraw.Draw(image);d.rectangle((0,0,1920,98),fill='#172c45');d.text((24,12),'Phase｜无动态障碍 · 完整场地路径跟随',font=fonts[40],fill='white');d.text((26,62),'真实原生状态回放 · 不插值 · 1×播放 · 零新增积分',font=fonts[25],fill='#d4e7f8');d.text((24,111),'原19个静态碰撞实体 · 原A*参考 · 原控制器',font=fonts[28],fill='#17354d');image.paste(Image.fromarray(aa),(20,154));image.paste(Image.fromarray(bb),(1220,154));d.rounded_rectangle((1220,720,1900,1004),radius=12,fill='white',outline='#cdd9e5',width=2)
 distance=float(np.linalg.norm(q[:2]-goal));finished=abs(data.time-native[-1]['time'])<.02;status='已到达原目标范围'if selected['strict_static_success']and finished else'沿原参考实际行驶'if not finished else'未到达：保留原失败';d.text((1240,735),status,font=fonts[32],fill='#187046'if selected['strict_static_success']and finished else'#17354d')
 values=[f"回合 {selected['name']}  /  种子 {selected['seed']}",f"仿真时间  {data.time:.2f} / {native[-1]['time']:.2f} s",f"距目标  {distance:.3f} m  ·  到达阈值0.45 m",f"实际最低净空  {selected['metrics']['minimum_native_clearance_m']:.3f} m",f"障碍接触 / 穿透 / 未知  0 / 0 / 0"]
 for i,text in enumerate(values):d.text((1240,785+i*40),text,font=fonts[25],fill='#243b50')
 d.text((24,1025),'绿色：原A*路径   蓝色：实际轨迹   黄色：原目标',font=fonts[25],fill='#29445a');d.text((1220,1025),'仅静态对照，不代表动态验收通过',font=fonts[22],fill='#975016');return image
frames=native[3::4]
if frames[-1]['time']!=native[-1]['time']:frames.append(native[-1])
assert all(abs((b['time']-a['time'])-.04)<1e-8 for a,b in zip(frames[:-2],frames[1:-1]))
for name,index in [('start',0),('mid',len(frames)//2),('end',len(frames)-1)]:frame(frames[index],[p['start_qpos'][:2]]+[x['qpos_full'][:2]for x in frames[:index+1]]).save(out/f'static_{name}_1080p.png')
target=out/'phase_no_dynamic_full_path_1080p.mp4';command=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-s','1920x1080','-pix_fmt','rgb24','-r','25','-i','-','-an','-c:v','libx264','-preset','faster','-crf','18','-pix_fmt','yuv420p','-threads','1','-movflags','+faststart',str(target)]
with(out/'encoder.log').open('wb')as log:
 enc=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log)
 try:
  trail=[p['start_qpos'][:2]]
  for x in frames:trail.append(x['qpos_full'][:2]);enc.stdin.write(frame(x,trail).tobytes())
  enc.stdin.close();assert enc.wait(timeout=20)==0
 finally:
  if enc.poll()is None:enc.kill();enc.wait()
renderer.close();close.close();assert calls==0
(out/'PROVENANCE.json').write_text(json.dumps(dict(selected_round=selected['name'],selection_rule='first strict success else minimum remaining distance',source_model_sha256=sha(pair/'scene_model.mjb'),source_native_sha256=sha(cell/'dynamic_native.jsonl.gz'),frames=len(frames),fps=25,interpolation=False,integrations=0,strict_static_success=selected['strict_static_success'],not_dynamic_acceptance=True,video_sha256=sha(target)),indent=2)+'\n');print(json.dumps(dict(video=str(target),frames=len(frames),integrations=0)))
