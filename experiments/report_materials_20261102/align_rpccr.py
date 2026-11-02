"""Correct research identity in presentation materials; retain audited video bytes."""
from pathlib import Path
import json,hashlib,zipfile,shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from matplotlib.font_manager import FontProperties
repo=Path(__file__).resolve().parents[2];root=repo/'runs/report_materials_20261102';out=root/'rpccr_alignment_v2';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
original=root/'Phase_PPT_Materials_20261102.zip'
with zipfile.ZipFile(original)as z:
    for name in z.namelist():
        assert Path(name).name==name
        if name!='DOWNLOAD_MANIFEST.json':(out/name).write_bytes(z.read(name))
text=(repo/'docs/PHASE_PPT_CONTENT_20261102.md').read_text();(out/'Phase_PPT_Content.md').write_text(text);(out/'Phase_PPT_Content.txt').write_text(text)
shutil.copy2(repo/'docs/RPCCR_RESEARCH_CONTRACT.md',out/'RPCCR_RESEARCH_CONTRACT.md')
font=lambda size:FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',size=size)
plt.rcParams['svg.fonttype']='path';fig,ax=plt.subplots(figsize=(22,5.8));fig.patch.set_facecolor('#f6f8fc');ax.set(xlim=(0,22),ylim=(0,5.8));ax.axis('off')
ax.text(.3,5.35,'RP-CCR研究主线：风险约束 × 目标进展 × 连续走廊恢复',fontproperties=font(23),color='#17354d')
ax.text(.3,4.72,'以下为当前实现支撑模块；完整机制贡献须通过同输入、同控制、同预算的对照与消融验证。',fontproperties=font(14),color='#536b7e')
blocks=[('1  因果观测','测距一致约束\n静态记忆 / 动态集合'),('2  进展路径规划','Hybrid A*前进 / 倒车\n曲率与密集净空检查'),('3  控制提案','解析Ackermann候选\n冻结学习提案辅助'),('4  风险与执行准入','原生动力学 / 制动预测\n完整自体与净空代理门'),('5  恢复轨迹交接','保留已验证有限后备\n新证书通过后才替换'),('6  执行与新观测','执行首公开步\n完整状态 / 控制 / 接触日志')]
width=3.30;gap=.30
for i,(title,detail)in enumerate(blocks):
    x=.25+i*(width+gap);ax.add_patch(FancyBboxPatch((x,2.05),width,2.25,boxstyle='round,pad=0.035,rounding_size=.12',lw=1.5,ec='#a8bfd4',fc='white'))
    ax.text(x+.16,3.68,title,fontproperties=font(17),color='#174c73');ax.text(x+.16,2.63,detail,fontproperties=font(13.2),color='#314e65',linespacing=1.7)
    if i<5:ax.add_patch(FancyArrowPatch((x+width+.025,3.13),(x+width+gap-.025,3.13),arrowstyle='-|>',mutation_scale=15,lw=1.8,color='#34799e'))
ax.plot([20.2,20.2,1.85,1.85],[2.03,1.35,1.35,2.03],color='#33977f',lw=1.8);ax.annotate('',xy=(1.85,2.03),xytext=(1.85,1.7),arrowprops={'arrowstyle':'-|>','color':'#33977f','lw':1.8})
ax.text(11,1.53,'反馈：每公开步0.08秒，联合检查风险代理、目标进展与恢复交接',fontproperties=font(15),ha='center',color='#247662',bbox=dict(fc='#f6f8fc',ec='none',pad=3))
ax.text(.3,.70,'研究主体为RP-CCR；Hybrid A*、动力学准入、有限后备、BC提案是实现或验证部件。SAC收益尚未隔离。',fontproperties=font(13),color='#536b7e')
ax.text(.3,.22,'当前风险以集合 / 净空代理表示；尚未完成概率风险校准、持续可续接 / 活性证明或强基线净收益验证。',fontproperties=font(13),color='#536b7e')
fig.subplots_adjust(left=.01,right=.995,bottom=.015,top=.99);fig.savefig(out/'phase_method.png',dpi=180,facecolor=fig.get_facecolor());fig.savefig(out/'phase_method.svg',facecolor=fig.get_facecolor());plt.close(fig)
html=(out/'index.html').read_text().replace('Phase汇报素材','RP-CCR汇报素材').replace('<h2>方法与汇报文字</h2>','<h2>RP-CCR研究主线与汇报文字</h2><p>研究算法是RP-CCR；感知、规划、动力学准入、有限后备和学习提案是实现支撑。当前实验未建立完整RP-CCR相对基线的独立收益。</p><p><a download href="RPCCR_RESEARCH_CONTRACT.md">下载RP-CCR研究定位与实验约束</a></p>')
(out/'index.html').write_text(html)
videos=['phase_static_single_1080p.mp4','phase_static_double_1080p.mp4'];assert all(sha(out/name)==sha(root/name)for name in videos)
alignment={'status':'RPCCR_RESEARCH_IDENTITY_ALIGNED','original_package_sha256':sha(original),'scope':'presentation and research-claim correction only; no renaming historical evidence or new performance claim','video_hashes_unchanged':{name:sha(out/name)for name in videos},'new_simulation_steps':0,'new_training_updates':0}
(out/'RPCCR_ALIGNMENT.json').write_text(json.dumps(alignment,indent=2,ensure_ascii=False)+'\n')
files=sorted(p for p in out.iterdir()if p.is_file());inventory=[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)}for p in files]
(out/'DOWNLOAD_MANIFEST.json').write_text(json.dumps(inventory,indent=2)+'\n');files.append(out/'DOWNLOAD_MANIFEST.json')
bundle=root/'RPCCR_PPT_Materials_20261102_v2.zip'
with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_STORED)as z:
    for f in files:z.write(f,arcname=f.name)
with zipfile.ZipFile(bundle)as z:
    assert z.testzip()is None
    for row in inventory:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
for ext in ['png','svg']:shutil.copy2(out/('phase_method.'+ext),repo/('docs/figures/rpccr_method_20261102.'+ext))
dest=repo/'evidence/rpccr_presentation_alignment_20261102';dest.mkdir(exist_ok=False)
shutil.copy2(bundle,dest/bundle.name);shutil.copy2(out/'RPCCR_ALIGNMENT.json',dest/'RPCCR_ALIGNMENT.json')
(dest/'README.md').write_text('# RP-CCR研究定位修正版汇报素材\n\n用户明确研究算法为RP-CCR。本v2仅修正PPT文字、方法图与研究定位，原V657两个视频字节不变；不回填历史结果、不把组件开发追认为已验证完整RP-CCR收益。原素材保留，建议使用本修正版。包内含研究定位合同、8页文字、框图、两个已完整解码的视频及原来源核验。新增仿真/训练0。\n')
(dest/'MANIFEST.json').write_text(json.dumps([{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(dest.iterdir())if p.is_file()],indent=2)+'\n')
print(json.dumps({'status':'READY','bundle':str(bundle.relative_to(repo)),'bytes':bundle.stat().st_size,'sha256':sha(bundle),'video_bytes_unchanged':True,'new_simulation_steps':0},indent=2))
