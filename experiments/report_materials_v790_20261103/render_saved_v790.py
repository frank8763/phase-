"""Render saved failed global states only. All integration entry points blocked."""
import os,json,hashlib,time,signal,subprocess,math,argparse,fcntl
from pathlib import Path
import numpy as np
import mujoco
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
repo=Path(os.environ['PHASE_REPO']);out=repo/'runs/report_materials_v790_20261103';out.mkdir(exist_ok=False);started=time.monotonic();calls=0
execution_lock=(repo/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(execution_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
def forbid(*a,**kw):
 global calls
 calls+=1;raise RuntimeError('FAILURE_MEDIA_MUST_NOT_ADVANCE_PHYSICS')
for name in ['mj_step','mj_step1','mj_step2']:setattr(mujoco,name,forbid)
import mujoco.rollout
mujoco.rollout.rollout=forbid
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FAILURE_MEDIA_600S_CAP')));signal.alarm(600)
p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');a=p.parse_args();read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pair=repo/'runs/v790_persistent_body_global/main_slot01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');result=read(cell/'result.json');replay=read(pair/'NATIVE_REPLAY_AUDIT.json');inputs=[pair/'scene_model.mjb',pair/'STATIC_PROTOCOL.json',pair/'DYNAMIC_PROTOCOL.json',cell/'v648_execution.jsonl',cell/'result.json',pair/'NATIVE_REPLAY_AUDIT.json'];hashes={str(p.relative_to(repo)):sha(p)for p in inputs}
assert sha(pair/'scene_model.mjb')==protocol['full_model_sha256']==replay['scene_model_sha256']
assert result['public_steps']==527 and not result['strict_safe_arrival'] and replay['maximum_full_native_state_ctrl_error']==0
rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];goal=np.asarray(protocol['goal_xy']);peak=int(np.argmin([np.linalg.norm(np.asarray(x['qpos_full'])[:2]-goal)for x in rows]));fontfile='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';fonts={n:ImageFont.truetype(fontfile,n)for n in [22,24,26,28,30,36,42]}
M=(24,155,1120,850);C=(1172,155,724,532)
model=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));data=mujoco.MjData(model);model.vis.global_.offwidth=M[2];model.vis.global_.offheight=M[3];model.vis.headlight.ambient[:]=[.65]*3;model.vis.headlight.diffuse[:]=[.8]*3;model.vis.headlight.specular[:]=[.1]*3
unknown={u['name']for u in protocol['physical_unknown_obstacles']}
for gid in range(model.ngeom):
 name=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,gid)or''
 if name in unknown:model.geom_rgba[gid]=[1.,.32,.02,1.];model.geom_matid[gid]=-1
 elif name.startswith(('real_rect_obs_','real_circle_obs_'))and model.geom_pos[gid,2]>-1:model.geom_rgba[gid]=[.49,.56,.63,1.];model.geom_matid[gid]=-1
main=mujoco.Renderer(model,height=M[3],width=M[2],max_geom=5000);close=mujoco.Renderer(model,height=C[3],width=C[2],max_geom=5000)
camera=mujoco.MjvCamera();camera.type=mujoco.mjtCamera.mjCAMERA_FREE;camera.lookat[:]=[0,0,.12];camera.distance=13.6;camera.azimuth=90;camera.elevation=-90
follow=mujoco.MjvCamera();follow.type=mujoco.mjtCamera.mjCAMERA_FREE;follow.distance=3.2;follow.elevation=-48

def decorate(renderer,trail,q):
 scene=renderer.scene
 def geom(kind,size,pos,color):
  g=scene.geoms[scene.ngeom];mujoco.mjv_initGeom(g,kind,np.asarray(size,float),np.asarray(pos,float),np.eye(3).ravel(),np.asarray(color,np.float32));g.category=int(mujoco.mjtCatBit.mjCAT_DECOR);scene.ngeom+=1;return g
 def line(x,y,color,width=.015):
  if np.linalg.norm(np.asarray(x)-y)<1e-8:return
  g=geom(mujoco.mjtGeom.mjGEOM_CAPSULE,[width,0,0],[0,0,0],color);mujoco.mjv_connector(g,mujoco.mjtGeom.mjGEOM_CAPSULE,width,np.asarray(x,float),np.asarray(y,float))
 pts=np.asarray(trail)
 for x,y in zip(pts[:-1],pts[1:]):line([*x,.032],[*y,.032],[.02,.46,.95,1],.02)
 geom(mujoco.mjtGeom.mjGEOM_CYLINDER,[.16,.015,0],[*goal,.035],[.05,.76,.35,1])
 geom(mujoco.mjtGeom.mjGEOM_CYLINDER,[.10,.015,0],[*protocol['start_qpos'][:2],.035],[.08,.73,.88,1])
 yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));c,s=math.cos(yaw),math.sin(yaw);corners=np.array([[-.44,-.375],[.44,-.375],[.44,.375],[-.44,.375]])@np.array([[c,-s],[s,c]]).T+q[:2]
 for x,y in zip(corners,np.roll(corners,-1,axis=0)):line([*x,.05],[*y,.05],[0,.78,.90,1],.008)
 # A thin decorative pointer identifies the real small actor; its geometry is unchanged.
 xy=data.mocap_pos[config['mocap_id'],:2];line([*xy,.8],[*xy,.38],[1,.42,.04,1],.018)
 scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW]=False

def frame(row,trail,finished=False):
 data.qpos[:]=row['qpos_full'];data.qvel[:]=row['qvel_full'];data.ctrl[:]=row['ctrl'];data.time=float(row['time']);data.mocap_pos[:]=row['mocap_pos'];q=data.qpos.copy();v=data.qvel.copy();u=data.ctrl.copy();m=data.mocap_pos.copy();t=data.time;mujoco.mj_forward(model,data)
 assert np.array_equal(data.qpos,q)and np.array_equal(data.qvel,v)and np.array_equal(data.ctrl,u)and np.array_equal(data.mocap_pos,m)and data.time==t
 main.update_scene(data,camera=camera);decorate(main,trail,q);aa=main.render();yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));follow.lookat[:]=[q[0],q[1],.30];follow.azimuth=math.degrees(yaw)+125
 close.update_scene(data,camera=follow);decorate(close,trail[-100:],q);bb=close.render()
 canvas=Image.new('RGB',(1920,1080),'#f3f6fa');d=ImageDraw.Draw(canvas);d.rectangle((0,0,1920,102),fill='#172c45');d.text((24,12),'Phase RP-CCR V790｜完整场地动态回放',font=fonts[42],fill='white');d.text((26,66),'真实保存状态 · 未插值 · 1×播放 · 不新增仿真',font=fonts[24],fill='#d4e7f8');d.text((1465,28),'原任务 10010001',font=fonts[28],fill='#d4e7f8')
 d.text((24,113),'完整场地：原19个静态实体、原小动态障碍',font=fonts[28],fill='#17354d');d.text((1172,113),'车辆近景：观察、推进和退让',font=fonts[28],fill='#17354d');canvas.paste(Image.fromarray(aa),M[:2]);canvas.paste(Image.fromarray(bb),C[:2]);d.rounded_rectangle((1172,708,1896,1005),radius=12,fill='white',outline='#cdd9e5',width=2)
 status='未到达：原墙钟预算内未完成'if finished else'原始失败轨迹｜尚未发现动态障碍';d.text((1192,722),status,font=fonts[28],fill='#aa3932')
 distance=np.linalg.norm(q[:2]-goal);lines=[f"仿真时间  {data.time:.2f} / 42.16 s  ·  步 {row.get('step',-1)+1}/527",f'距目标  {distance:.3f} m  ·  最佳缩短 2.956 m',f"实际最低净空  {result['minimum_dynamic_native_clearance_m']:.3f} m",'障碍接触 / 穿透 / 未知：0 / 0 / 0','远端橙色障碍：直径0.20 m，未进入感知']
 for i,line in enumerate(lines):d.text((1192,773+i*42),line,font=fonts[24],fill='#243b50')
 d.text((24,1026),'蓝线：实际轨迹   青框：完整车身审核域   绿色：目标',font=fonts[24],fill='#29445a');d.text((1172,1026),'橙色与指示线仅供离线识别，不进入控制',font=fonts[22],fill='#975016');return canvas
# Intro and first PNG use the first actual recorded state (.08s), no invented initial velocities or controls.
initial=rows[0]
try:
 for tag,index in [('start',None),('best_progress',peak),('failure',len(rows)-1)]:
  trail=[protocol['start_qpos'][:2]]+[x['qpos_full'][:2]for x in rows[:index+1]]if index is not None else[protocol['start_qpos'][:2]]
  frame(initial if index is None else rows[index],trail,tag=='failure').save(out/f'global_failure_{tag}_1080p.png')
 print('THREE_IMAGES_RENDERED',flush=True)
 if not a.preview:
  target=out/'phase_global_dynamic_failure_1080p.mp4';assert not target.exists();command=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-s','1920x1080','-pix_fmt','rgb24','-r','25','-i','-','-an','-c:v','libx264','-preset','faster','-crf','18','-pix_fmt','yuv420p','-threads','1','-movflags','+faststart',str(target)]
  with(out/'encoder.log').open('wb')as f:
   enc=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=f)
   try:
    trail=[protocol['start_qpos'][:2]];blob=frame(initial,trail).tobytes()
    for _ in range(50):enc.stdin.write(blob)
    for i,row in enumerate(rows):
     trail.append(row['qpos_full'][:2]);blob=frame(row,trail).tobytes();enc.stdin.write(blob);enc.stdin.write(blob)
     if i%25==0:(out/'RENDER_PROGRESS.json').write_text(json.dumps(dict(recorded_state=i+1,total_states=len(rows),integrations=calls,elapsed_s=time.monotonic()-started),indent=2)+'\n');print('RENDER',i+1,'/',len(rows),flush=True)
    blob=frame(rows[-1],trail,True).tobytes()
    for _ in range(75):enc.stdin.write(blob)
    enc.stdin.close();assert enc.wait(timeout=60)==0
   except BaseException:enc.kill();enc.wait();raise
 assert calls==0 and all(sha(repo/p)==h for p,h in hashes.items())
 provenance=dict(status='SAVED_GLOBAL_FAILURE_RENDERED',source_pair=str(pair.relative_to(repo)),source_hashes=hashes,model_sha256=protocol['full_model_sha256'],render_only_visual_changes=['camera','RGBA','decorative trail/goal/footprint/actor pointer','captions'],source_public_steps=527,source_physical_native_steps=4216,source_strict_arrival=False,source_outcome=result['outcome'],intro_recorded_state_time_s=rows[0]['time'],first_png_is_first_saved_state=True,new_integration_calls=0,recorded_state_interpolation=False,video_fps=25,video_frames=1179,video_duration_s=47.16,video_trajectory_duration_s=42.16,intro_s=2,outro_s=3,source_state_interval_s=.08,playback_speed=1.,png_images=[p.name for p in sorted(out.glob('global_failure_*1080p.png'))],elapsed_s=time.monotonic()-started)
 if not a.preview:provenance.update(video=target.name,video_sha256=sha(target),video_bytes=target.stat().st_size)
 (out/'RENDER_PROVENANCE.json').write_text(json.dumps(provenance,indent=2,ensure_ascii=False)+'\n');print(json.dumps(provenance,ensure_ascii=False),flush=True)
finally:main.close();close.close();signal.alarm(0)
