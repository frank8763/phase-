"""Render audited recorded states; every physics integration entry is blocked."""
import os,json,hashlib,time,signal,subprocess,math,argparse
from pathlib import Path
import numpy as np
import mujoco
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg

repo=Path(os.environ['PHASE_REPO']);out=repo/'runs/report_materials_20261102';out.mkdir(exist_ok=True)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');a=p.parse_args()
started=time.monotonic();calls=0
def forbid(*args,**kwargs):
    global calls
    calls+=1;raise RuntimeError('REPORT_RENDER_MUST_NOT_ADVANCE_PHYSICS')
for name in ['mj_step','mj_step1','mj_step2']:setattr(mujoco,name,forbid)
import mujoco.rollout
mujoco.rollout.rollout=forbid
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('RENDER_1800_SECONDS')));signal.alarm(1800)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fontfile='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
fonts={n:ImageFont.truetype(fontfile,n)for n in [23,24,26,27,28,30,32,44]}
cases=[('single','confirm_95000011_single_event','单未知障碍',95000011),('double','confirm_95000004_legacy_two','双未知障碍',95000004)]
MAIN=(24,155,1120,850);CLOSE=(1172,155,724,532)
ffmpeg=imageio_ffmpeg.get_ffmpeg_exe();allmeta=[]

def decorate(renderer,trail,goal,pose):
    scene=renderer.scene
    def geom(kind,size,pos,color):
        assert scene.ngeom<scene.maxgeom
        g=scene.geoms[scene.ngeom];mujoco.mjv_initGeom(g,kind,np.asarray(size,float),np.asarray(pos,float),np.eye(3).ravel(),np.asarray(color,np.float32));g.category=int(mujoco.mjtCatBit.mjCAT_DECOR);scene.ngeom+=1;return g
    def line(first,last,color,width=.015):
        if np.linalg.norm(np.asarray(first)-last)<1e-8:return
        g=geom(mujoco.mjtGeom.mjGEOM_CAPSULE,[width,0.,0.],[0.,0.,0.],color);mujoco.mjv_connector(g,mujoco.mjtGeom.mjGEOM_CAPSULE,width,np.asarray(first,float),np.asarray(last,float))
    stride=max(1,len(trail)//250);points=np.asarray(trail)[::stride]
    if len(points)>1:
        for first,last in zip(points[:-1],points[1:]):line([*first,.027],[*last,.027],[.03,.48,.90,1.],.018)
    geom(mujoco.mjtGeom.mjGEOM_CYLINDER,[.15,.025,0.],[*goal,.035],[.05,.73,.35,.95])
    geom(mujoco.mjtGeom.mjGEOM_SPHERE,[.065,0.,0.],[*goal,.15],[.05,.80,.40,1.])
    yaw=pose[2];c,s=math.cos(yaw),math.sin(yaw);rot=np.array([[c,-s],[s,c]])
    corners=np.array([[-.44,-.375],[.44,-.375],[.44,.375],[-.44,.375]])@rot.T+pose[:2]
    for first,last in zip(corners,np.roll(corners,-1,axis=0)):line([*first,.045],[*last,.045],[.05,.75,.90,.9],.008)
    scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW]=False

def make_canvas(main,close,label,seed,row,result,audit,finished=False):
    canvas=Image.new('RGB',(1920,1080),'#f3f6fa');draw=ImageDraw.Draw(canvas)
    draw.rectangle((0,0,1920,102),fill='#132d48');draw.text((24,10),'Phase｜静态未知障碍成功回放',font=fonts[44],fill='white')
    draw.text((27,66),f'{label}  ·  已审核原始状态回放  ·  1×播放  ·  1920×1080',font=fonts[24],fill='#d4e7f8')
    draw.text((1450,25),f'V657 · Seed {seed}',font=fonts[28],fill='#d4e7f8')
    draw.text((24,113),'全局俯视：完整场地与实际行驶轨迹',font=fonts[28],fill='#17354d');draw.text((1172,113),'跟随近景：车辆与局部障碍',font=fonts[28],fill='#17354d')
    canvas.paste(Image.fromarray(main),MAIN[:2]);canvas.paste(Image.fromarray(close),CLOSE[:2])
    draw.rounded_rectangle((1172,716,1896,1005),radius=12,fill='white',outline='#cdd9e5',width=2)
    color='#09874b'if finished else'#17354d';status='严格到达：成功'if finished else'原始成功轨迹 · 完整过程'
    draw.text((1194,729),status,font=fonts[32],fill=color)
    distance=float(np.linalg.norm(np.asarray(row['qpos_full'])[:2]-audit['goal_xy']))
    lines=[f"仿真时间  {row['time']:.2f} / {result['public_steps']*.08:.2f} s",f'当前距目标  {distance:.3f} m',f"全程最低净空  {audit['minimum_clearance_m']:.3f} m（审核）",'障碍接触 / 穿透 / 未知：0 / 0 / 0']
    for i,text in enumerate(lines):draw.text((1194,784+i*45),text,font=fonts[27],fill='#243b50')
    draw.text((24,1026),'蓝线：已走轨迹   青框：全车身审核域   绿色：目标',font=fonts[26],fill='#29445a')
    draw.text((1172,1026),'橙色：起初未知障碍（离线回放着色）',font=fonts[24],fill='#975016')
    return canvas

try:
 for key,name,label,seed in cases:
    pair=repo/'runs/v657_static_fixed_work_confirmation'/name/'paired';cell=pair/'geometry_memory'
    inputs=[pair/'scene_model.mjb',pair/'STATIC_PROTOCOL.json',cell/'v648_execution.jsonl',cell/'result.json',pair/'NATIVE_REPLAY_AUDIT.json']
    hashes={str(f.relative_to(repo)):sha(f)for f in inputs};protocol=read(pair/'STATIC_PROTOCOL.json');result=read(cell/'result.json');replay=read(pair/'NATIVE_REPLAY_AUDIT.json')
    assert result['strict_safe_arrival']and result['outcome']=='GOAL'and result['seed']==seed
    assert replay['status']=='MATCHED_RECORDED_PUBLIC_STATES'and replay['maximum_full_public_qpos_error']==replay['maximum_full_public_qvel_error']==0
    assert sha(pair/'scene_model.mjb')==protocol['full_model_sha256']==replay['scene_model_sha256']
    assert sha(cell/'v648_execution.jsonl')==replay['recorded_state_log_sha256']
    assert result['contacts']['robot_obstacle_contact_records']==result['contacts']['robot_obstacle_penetration_records']==result['contacts']['unknown_contact_records']==0
    rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];assert len(rows)==result['public_steps']
    model=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));data=mujoco.MjData(model)
    model.vis.global_.offwidth=1120;model.vis.global_.offheight=850
    model.vis.headlight.ambient[:]=[.65,.65,.65];model.vis.headlight.diffuse[:]=[.8,.8,.8];model.vis.headlight.specular[:]=[.1,.1,.1]
    unknown={u['name']for u in protocol['physical_unknown_obstacles']}
    for gid in range(model.ngeom):
        gname=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,gid)or''
        if gname in unknown:model.geom_rgba[gid]=[1.,.34,.03,1.];model.geom_matid[gid]=-1
        elif gname.startswith(('real_rect_obs_','real_circle_obs_'))and model.geom_pos[gid,2]>-1:
            model.geom_rgba[gid]=[.49,.56,.63,1.];model.geom_matid[gid]=-1
    main=mujoco.Renderer(model,height=MAIN[3],width=MAIN[2],max_geom=5000);close=mujoco.Renderer(model,height=CLOSE[3],width=CLOSE[2],max_geom=5000)
    camera=mujoco.MjvCamera();camera.type=mujoco.mjtCamera.mjCAMERA_FREE;camera.lookat[:]=[0.,0.,.12];camera.distance=13.6;camera.azimuth=90.;camera.elevation=-90.
    follow=mujoco.MjvCamera();follow.type=mujoco.mjtCamera.mjCAMERA_FREE;follow.distance=3.9;follow.elevation=-48.
    audit={'goal_xy':protocol['goal_xy'],'minimum_clearance_m':replay['minimum_reconstructed_native_actual_axis_AABB_clearance_m']}
    initial={'time':0.,'qpos_full':protocol['start_qpos'],'qvel_full':np.zeros(model.nv).tolist(),'ctrl':np.zeros(model.nu).tolist()}
    worst=0.;trail=[np.asarray(initial['qpos_full'])[:2].tolist()]
    def frame(row,finished=False):
        data.qpos[:]=row['qpos_full'];data.qvel[:]=row['qvel_full'];data.ctrl[:]=row['ctrl'];data.time=float(row['time'])
        q=data.qpos.copy();v=data.qvel.copy();t=float(data.time);mujoco.mj_forward(model,data)
        assert np.array_equal(data.qpos,q)and np.array_equal(data.qvel,v)and data.time==t,'RENDER_CHANGED_RECORDED_STATE'
        yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));pose=np.r_[q[:2],yaw]
        main.update_scene(data,camera=camera);decorate(main,trail,protocol['goal_xy'],pose);rgbmain=main.render()
        follow.lookat[:]=[q[0],q[1],.30];follow.azimuth=math.degrees(yaw)+125.
        close.update_scene(data,camera=follow);decorate(close,trail[-100:],protocol['goal_xy'],pose);rgbclose=close.render()
        return make_canvas(rgbmain,rgbclose,label,seed,row,result,audit,finished)
    if a.preview:
        for tag,index in [('start',None),('middle',len(rows)//2),('end',len(rows)-1)]:
            trail=[np.asarray(initial['qpos_full'])[:2].tolist()]+[x['xy']for x in rows[:index+1]]if index is not None else[np.asarray(initial['qpos_full'])[:2].tolist()]
            frame(initial if index is None else rows[index],tag=='end').save(out/f'{key}_preview_{tag}.png')
        main.close();close.close();print('PREVIEW',key,flush=True);continue
    target=out/f'phase_static_{key}_1080p.mp4';assert not target.exists(),'DERIVED_VIDEO_ALREADY_EXISTS'
    command=[ffmpeg,'-hide_banner','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-s','1920x1080','-pix_fmt','rgb24','-r','25','-i','-','-an','-c:v','libx264','-preset','faster','-crf','18','-pix_fmt','yuv420p','-threads','1','-movflags','+faststart',str(target)]
    with(out/f'{key}_encoder.log').open('wb')as log:
        encoder=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log)
        try:
            first=frame(initial);first.save(out/f'phase_static_{key}_poster.png');blob=first.tobytes()
            for _ in range(50):encoder.stdin.write(blob)
            for index,row in enumerate(rows):
                trail.append(row['xy']);image=frame(row);blob=image.tobytes();encoder.stdin.write(blob);encoder.stdin.write(blob)
                if index%25==0:
                    (out/'RENDER_PROGRESS.json').write_text(json.dumps({'case':key,'recorded_state':index+1,'total_states':len(rows),'integration_calls':calls,'elapsed_s':time.monotonic()-started},indent=2)+'\n');print('RENDER',key,index+1,'/',len(rows),flush=True)
            last=frame(rows[-1],True);last.save(out/f'phase_static_{key}_finish.png');blob=last.tobytes()
            for _ in range(75):encoder.stdin.write(blob)
            encoder.stdin.close();assert encoder.wait(timeout=120)==0,'ENCODER_FAILED'
        except BaseException:
            encoder.kill();encoder.wait();raise
    main.close();close.close()
    assert all(sha(repo/f)==h for f,h in hashes.items())and calls==0
    meta={'case':key,'seed':seed,'label':label,'source_pair':str(pair.relative_to(repo)),'source_hashes':hashes,'video':target.name,'video_sha256':sha(target),'width':1920,'height':1080,'fps':25,'expected_video_frames':125+2*len(rows),'expected_duration_s':5+len(rows)*.08,'original_simulation_time_s':len(rows)*.08,'original_public_steps':len(rows),'recorded_state_interval_s':.08,'state_interpolation':False,'playback_speed':1.,'intro_s':2,'outro_s':3,'source_strict_arrival':True,'source_final_goal_distance_m':result['goal_distance_m'],'source_minimum_native_clearance_m':audit['minimum_clearance_m'],'render_integration_calls':calls,'new_training_updates':0,'render_only_visual_changes':['camera','obstacle RGBA','decorative trail/goal/footprint','Chinese captions'],'maximum_qpos_qvel_time_change_after_forward':0.}
    (out/f'{key}_VIDEO_PROVENANCE.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n');allmeta.append(meta);print('VIDEO_DONE',key,flush=True)
 if not a.preview:(out/'VIDEOS_MANIFEST.json').write_text(json.dumps({'status':'RENDERED_NEEDS_FULL_DECODE_QA','videos':allmeta,'integration_calls':calls,'training_updates':0,'review_guard_preserved':(repo/'REVIEW_PENDING').exists(),'elapsed_s':time.monotonic()-started},indent=2,ensure_ascii=False)+'\n')
finally:signal.alarm(0)
