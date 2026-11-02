"""Full video decode, source hash checks, and a portable report download bundle."""
from pathlib import Path
import json,hashlib,zipfile,subprocess,signal,os
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg

repo=Path(__file__).resolve().parents[2];out=repo/'runs/report_materials_20261102'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('VIDEO_QA_300S')));signal.alarm(300)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(out/'VIDEOS_MANIFEST.json');assert manifest['integration_calls']==manifest['training_updates']==0
qa=[]
for video in manifest['videos']:
    path=out/video['video'];assert path.is_file()and sha(path)==video['video_sha256']
    assert all(sha(repo/f)==h for f,h in video['source_hashes'].items())
    cap=cv2.VideoCapture(str(path));assert cap.isOpened()
    width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT));fps=cap.get(cv2.CAP_PROP_FPS);declared=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));cc=int(cap.get(cv2.CAP_PROP_FOURCC));codec=''.join(chr((cc>>(8*i))&255)for i in range(4))
    count=0;sample={};needed={0,declared//2,declared-1}
    while True:
        ok,frame=cap.read()
        if not ok:break
        assert frame.shape==(1080,1920,3)
        if count in needed:sample[count]=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
        count+=1
    cap.release()
    checks={'native1080p':(width,height)==(1920,1080),'fps25':abs(fps-25)<1e-9,'full_decode_frame_count':count==declared==video['expected_video_frames'],'expected_duration':abs(count/fps-video['expected_duration_s'])<1e-7,'h264':codec in ['avc1','h264','H264'],'source_and_video_hashes_verified':True,'three_visual_samples':len(sample)==3}
    probe=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-i',str(path),'-t','0','-f','null','-'],capture_output=True,text=True,timeout=20)
    stream=next((s.strip()for s in probe.stderr.splitlines()if'Stream #0:0'in s and'Video:'in s),'');checks['yuv420p']='yuv420p'in stream;assert all(checks.values()),checks
    strip=Image.new('RGB',(1920,398),'white');draw=ImageDraw.Draw(strip);font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',23)
    for i,(index,img)in enumerate(sorted(sample.items())):
        strip.paste(img.resize((640,360)),(640*i,38));draw.text((640*i+12,5),['起点介绍','完整过程抽帧','原始终态：严格到达'][i],font=font,fill='#17354d')
    strip.save(out/(video['case']+'_VIDEO_QA.png'))
    qa.append({'video':video['video'],'checks':checks,'codec_fourcc':codec,'stream_description':stream,'decoded_frames':count,'fps':fps,'width':width,'height':height,'duration_s':count/fps,'bytes':path.stat().st_size,'sha256':sha(path)})
result={'status':'BOTH_VIDEOS_FULL_DECODE_AND_PROVENANCE_PASS','videos':qa,'new_physics_integration_steps':0,'new_training_updates':0,'review_guard_preserved':(repo/'REVIEW_PENDING').exists(),'no_new_independent_trials':True}
(out/'VIDEO_QA.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
manifest['status']='FULL_DECODE_QA_PASS';manifest['qa']='VIDEO_QA.json';(out/'VIDEOS_MANIFEST.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Phase汇报素材</title><style>body{font:17px system-ui,sans-serif;max-width:1180px;margin:30px auto;padding:0 20px;color:#17354d;background:#f5f7fa}section{background:white;padding:24px;border-radius:12px;margin:20px 0}video,img{width:100%;height:auto}a{color:#0867a0}p{line-height:1.7}h1,h2{line-height:1.4}</style><h1>Phase汇报素材 · 2026-11-02</h1><p>两个视频均为已审核静态成功记录的MuJoCo状态回放：1920×1080、H.264、25fps、1倍仿真时间。绘图与视频不增加任何仿真积分或训练。</p><section><h2>方法与汇报文字</h2><p><a download href="Phase_PPT_Content.md">下载8页PPT文字（Markdown）</a> · <a download href="Phase_PPT_Content.txt">下载纯文本</a> · <a download href="phase_method.png">下载方法图PNG</a> · <a download href="phase_method.svg">下载方法图SVG</a></p><img src="phase_method.png" alt="方法框架"></section><section><h2>视频1：单未知障碍 · 95000011</h2><video controls preload="metadata" poster="phase_static_single_poster.png"><source src="phase_static_single_1080p.mp4" type="video/mp4"></video><p><a download href="phase_static_single_1080p.mp4">下载1080p MP4</a> · 原轨迹39.92秒，视频44.92秒；最低实际净空0.222714米，零障碍接触。</p></section><section><h2>视频2：双未知障碍 · 95000004</h2><video controls preload="metadata" poster="phase_static_double_poster.png"><source src="phase_static_double_1080p.mp4" type="video/mp4"></video><p><a download href="phase_static_double_1080p.mp4">下载1080p MP4</a> · 原轨迹54.32秒，视频59.32秒；最低实际净空0.201887米，零障碍接触。</p></section><section><h2>长距离问题</h2><p>两相位8米途中发现开发与重复通过；独立24任务确认被旧初始化距离门拦住，24项导航未执行。算法层仍需验证未来不确定性下的持续可续接、复杂场地泛化及计算开销，具体讲述见PPT文字。</p><img src="long_distance_diagnosis.png" alt="长距离问题"></section></html>'''
(out/'index.html').write_text(html)
files=['index.html','Phase_PPT_Content.md','Phase_PPT_Content.txt','phase_method.png','phase_method.svg','long_distance_diagnosis.png','VIDEOS_MANIFEST.json','VIDEO_QA.json']
for key in ['single','double']:files += [f'phase_static_{key}_1080p.mp4',f'phase_static_{key}_poster.png',f'phase_static_{key}_finish.png',f'{key}_VIDEO_PROVENANCE.json',f'{key}_VIDEO_QA.png']
inventory=[{'path':name,'bytes':(out/name).stat().st_size,'sha256':sha(out/name)}for name in files]
(out/'DOWNLOAD_MANIFEST.json').write_text(json.dumps(inventory,indent=2)+'\n');files.append('DOWNLOAD_MANIFEST.json')
bundle=out/'Phase_PPT_Materials_20261102.zip'
with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_STORED)as z:
    for name in files:z.write(out/name,arcname=name)
with zipfile.ZipFile(bundle)as z:
    assert z.testzip()is None
    for row in inventory:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
(out/'PACKAGE_READY.json').write_text(json.dumps({'status':'READY','bundle':bundle.name,'bytes':bundle.stat().st_size,'sha256':sha(bundle),'deliverable_files_read_back':len(files),'video_qa_status':result['status'],'new_simulation_steps':0,'new_training_updates':0},indent=2)+'\n')
print(json.dumps(result,indent=2));print('PACKAGE_READY',bundle.stat().st_size,flush=True);signal.alarm(0)
