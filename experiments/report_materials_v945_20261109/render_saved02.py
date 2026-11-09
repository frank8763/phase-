"""Recorded native states only; block every dynamics integration entry point."""
import fcntl
import hashlib
import json
import math
import os
import signal
import subprocess
import time
from pathlib import Path

import imageio_ffmpeg
import mujoco
import mujoco.rollout
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(os.environ['PHASE_REPO']); RAW=ROOT/'runs/v858_nav2_verified/v945/main_we'
OUT=ROOT/'runs/report_materials_v945_20261109/render02';OUT.mkdir(exist_ok=False)
lock=(ROOT/'runs/v648_static_unknown/execution.lock').open('a+')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
begun=time.monotonic();integrations=0;forward_calls=0


def forbid(*args,**kwargs):
    global integrations
    integrations+=1
    raise AssertionError('SAVED_RENDER_CANNOT_ADVANCE_PHYSICS')


for name in ['mj_step','mj_step1','mj_step2']:setattr(mujoco,name,forbid)
mujoco.rollout.rollout=forbid
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('RENDER600S')))
signal.alarm(600)
read=lambda name:json.loads((RAW/name).read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
setup=read('physics/SETUP.json');task=read('TASK.json');plans=read('PLANS.json')
recovery=read('RECOVERY_CORRIDORS.json')[0];summary=json.loads((OUT.parent/'PATH_VISUALIZATION.json').read_text())
with np.load(RAW/'physics/NATIVE_TRACE.npz')as z:trace={k:z[k].copy()for k in z.files}
commands=np.asarray(read('physics/BODY_COMMANDS.json'),float)
assert len(commands)==len(trace['qpos'])==13517
assert sha(RAW/'physics/scene_model.mjb')==setup['model_sha256']
inputs={str((RAW/name).relative_to(ROOT)):sha(RAW/name)for name in ['physics/scene_model.mjb','physics/NATIVE_TRACE.npz','physics/SETUP.json','physics/BODY_COMMANDS.json','PLANS.json','RECOVERY_CORRIDORS.json','INGRESS.json.gz']}
model=mujoco.MjModel.from_binary_path(str(RAW/'physics/scene_model.mjb'));data=mujoco.MjData(model)
model.vis.global_.offwidth=545;model.vis.global_.offheight=410
model.vis.headlight.ambient[:]=.65;model.vis.headlight.diffuse[:]=.8
for gid in range(model.ngeom):
    name=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,gid)or''
    if name.startswith(('real_rect_obs_','real_circle_obs_')):
        model.geom_rgba[gid]=[.49,.56,.63,1.];model.geom_matid[gid]=-1
    if gid==setup['actor']['actor_geom_id']:
        model.geom_rgba[gid]=[1.,.42,.05,1.];model.geom_matid[gid]=-1
main=mujoco.Renderer(model,height=410,width=545,max_geom=6000)
close=mujoco.Renderer(model,height=260,width=368,max_geom=6000)
cam=mujoco.MjvCamera();cam.type=mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat[:]=[0.,0.,.1];cam.distance=13.6;cam.elevation=-90;cam.azimuth=90
follow=mujoco.MjvCamera();follow.type=mujoco.mjtCamera.mjCAMERA_FREE
follow.lookat[:]=[2.8,-1.8,.2];follow.distance=4.4;follow.elevation=-64;follow.azimuth=90
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
fonts={n:ImageFont.truetype(font,n)for n in [21,23,25,27,31,38]}
goal=np.asarray(task['goal_xy']);plan_times=np.array([p['at']for p in plans])
start=summary['first_under2_tick']-1;stop=summary['runtime_stop_native_tick']-1
install=recovery['install_packet']['native_tick']-1;recovery_end=recovery['end_packet']['native_tick']-1
segment=np.asarray(recovery['proposal']['path'])


def decoration(renderer,index,reference):
    scene=renderer.scene
    def geom(kind,size,pos,color):
        assert scene.ngeom<scene.maxgeom
        g=scene.geoms[scene.ngeom]
        mujoco.mjv_initGeom(g,kind,np.asarray(size,float),np.asarray(pos,float),np.eye(3).ravel(),np.asarray(color,np.float32))
        g.category=int(mujoco.mjtCatBit.mjCAT_DECOR);scene.ngeom+=1
        return g
    def line(a,b,color,width):
        if np.linalg.norm(np.asarray(a)-b)<1e-9:return
        g=geom(mujoco.mjtGeom.mjGEOM_CAPSULE,[width,0,0],[0,0,0],color)
        mujoco.mjv_connector(g,mujoco.mjtGeom.mjGEOM_CAPSULE,width,np.asarray(a,float),np.asarray(b,float))
    trail=trace['qpos'][:index+1:50,:2]
    if len(trail)==0 or not np.array_equal(trail[-1],trace['qpos'][index,:2]):trail=np.vstack([trail,trace['qpos'][index,:2]])
    for a,b in zip(trail[:-1],trail[1:]):line([*a,.04],[*b,.04],[.02,.36,.98,1.],.016)
    if reference is not None:
        for a,b in zip(reference[:-1],reference[1:]):line([*a[:2],.055],[*b[:2],.055],[.03,.77,.28,1.],.014)
    if install<=index<=recovery_end:
        for a,b in zip(segment[:-1],segment[1:]):line([*a[:2],.07],[*b[:2],.07],[.69,.22,.86,1.],.022)
    geom(mujoco.mjtGeom.mjGEOM_CYLINDER,[.11,.014,0],[*goal,.06],[.04,.74,.28,1.])
    theta=np.linspace(0,2*math.pi,65);ring=np.c_[goal[0]+.45*np.cos(theta),goal[1]+.45*np.sin(theta),np.full(65,.035)]
    for a,b in zip(ring[:-1],ring[1:]):line(a,b,[.05,.67,.24,.8],.008)
    scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW]=False


def frame(index,label):
    global forward_calls
    for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:getattr(data,key)[:]=trace[key][index]
    data.time=float(trace['time'][index]);before={k:getattr(data,k).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};clock=data.time
    mujoco.mj_forward(model,data);forward_calls+=1
    assert data.time==clock and all(np.array_equal(getattr(data,k),v)for k,v in before.items())
    plan_index=int(np.searchsorted(plan_times,commands[index,0],side='right')-1)
    reference=np.asarray(plans[plan_index]['path'])if plan_index>=0 else None
    main.update_scene(data,camera=cam);decoration(main,index,reference);aa=main.render()
    # Keep goal and last2m visible together; no camera rotation hides reversals.
    close.update_scene(data,camera=follow);decoration(close,index,reference);bb=close.render()
    image=Image.new('RGB',(1920,1080),'#f3f6fa');draw=ImageDraw.Draw(image)
    draw.rectangle((0,0,1920,99),fill='#172c45')
    draw.text((24,10),'V945｜保存状态回放：为什么最后不到两米仍未到达',font=fonts[38],fill='white')
    draw.text((26,62),label+' · 原生状态抽样，无插值，新增积分0',font=fonts[25],fill='#d4e7f8')
    draw.text((24,113),'全场与实际轨迹',font=fonts[27],fill='#17354d')
    draw.text((1145,113),'目标区域固定近景：观察前进/倒行',font=fonts[27],fill='#17354d')
    image.paste(Image.fromarray(aa).resize((1090,820),Image.Resampling.BILINEAR),(20,156));image.paste(Image.fromarray(bb).resize((735,520),Image.Resampling.BILINEAR),(1145,156))
    draw.rounded_rectangle((1145,698,1880,990),radius=12,fill='white',outline='#cdd9e5',width=2)
    distance=float(np.linalg.norm(data.qpos[:2]-goal));v,w=commands[index,1:3]
    direction='前进'if v>.005 else'倒行'if v<-.005 else'停车'
    status='观测超时触发停车（原记录）'if index>=stop else'完整恢复段：跟随误差另审'if install<=index<=recovery_end else'正常参考导航'
    values=[f'仿真时间 {clock:6.2f} / 135.17秒   距目标 {distance:.3f}米',
            f'当前实际接收命令：{direction}   v={v:+.3f} m/s',
            f'转向指令 L/R：{data.ctrl[0]:+.3f} / {data.ctrl[1]:+.3f} rad',
            status,'末22秒前后切换16次，目标净进展仅0.143米',
            '全程最低净空0.245米，坏接触0；任务仍未通过']
    for i,text in enumerate(values):draw.text((1163,710+i*43),text,font=fonts[23],fill='#a22e2e'if i==3 and index>=stop else'#243b50')
    draw.text((24,1010),'蓝色：实际轨迹   绿色：当时最新规划路径及目标范围   紫色：接管中的恢复参考',font=fonts[25],fill='#243b50')
    draw.text((24,1048),'橙色actor仅供离线识别；直线参考在50.61秒首次航向超界，133.16秒收到停车请求。',font=fonts[23],fill='#975016')
    return image


def encode(name,indices,label):
    target=OUT/name;assert not target.exists()
    command=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-s','1920x1080','-pix_fmt','rgb24','-r','10','-i','-','-an','-c:v','libx264','-preset','faster','-crf','20','-pix_fmt','yuv420p','-threads','1','-movflags','+faststart',str(target)]
    with(OUT/(name+'.encoder.log')).open('xb')as log:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log)
        try:
            for i,index in enumerate(indices):
                blob=frame(int(index),label).tobytes();process.stdin.write(blob)
                if i%20==0:
                    (OUT/'RENDER_PROGRESS.json').write_text(json.dumps(dict(video=name,frames=i+1,total=len(indices)+30,integrations=integrations,elapsed_s=time.monotonic()-begun))+'\n')
            for _ in range(30):process.stdin.write(blob)
            process.stdin.close();assert process.wait(timeout=30)==0
        finally:
            if process.poll()is None:process.kill();process.wait()
    return dict(name=name,frames=len(indices)+30,fps=10,video_duration_s=(len(indices)+30)/10,
                first_native_tick=int(indices[0]+1),last_native_tick=int(indices[-1]+1),
                first_saved_time_s=float(trace['time'][indices[0]]),last_saved_time_s=float(trace['time'][indices[-1]]),
                final_hold_frames=30,sha256=sha(target),bytes=target.stat().st_size)


try:
    for name,index in [('recovery_handoff',install),('last2m_start',start),('stopping',stop),('final',len(commands)-1)]:
        frame(index,'预览').save(OUT/(name+'.png'))
    print('PREVIEWS_READY',flush=True)
    overview=np.arange(39,len(commands),40)
    if overview[-1]!=len(commands)-1:overview=np.r_[overview,len(commands)-1]
    detail=np.arange(start,len(commands),10)
    if detail[-1]!=len(commands)-1:detail=np.r_[detail,len(commands)-1]
    media=[encode('v945_last2m_with_paths_1x.mp4',detail,'末段1×'),
           encode('v945_full_route_with_paths_4x.mp4',overview,'全程4×')]
    assert integrations==0 and all(sha(ROOT/p)==h for p,h in inputs.items())
    result=dict(status='SAVED_STATE_RENDERED',render_model_loads=1,new_integrations=integrations,
                recorded_state_interpolation=False,saved_forward_calls=forward_calls,pixel_resampling_only=True,
                mutable_saved_state_fields_changed=False,source_hashes=inputs,
                plan_alignment='last saved PLANS publication at or before the recorded native BODY_COMMANDS wall clock',
                media=media,elapsed_s=time.monotonic()-begun,scientific_outcome='NOT_PASSED')
    (OUT/'RENDER_PROVENANCE.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
finally:
    main.close();close.close();signal.alarm(0)
