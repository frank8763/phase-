"""Actual saved trajectory and last published reference; no models/integrations."""
import gzip
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Circle, Polygon, Rectangle
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'runs/v858_nav2_verified/v945/main_we'
OUT=ROOT/'runs/report_materials_v945_20261109'
REC=ROOT/'records/nav2_v945_media_20261109'


def main():
    read=lambda name:json.loads((RAW/name).read_text())
    setup=read('physics/SETUP.json');plans=read('PLANS.json');recovery=read('RECOVERY_CORRIDORS.json')[0]
    with np.load(RAW/'physics/NATIVE_TRACE.npz')as z:
        q=z['qpos'];vel=z['qvel'];t=z['time'];actor=z['mocap_pos'][:,setup['actor']['mocap_id'],:2]
    goal=np.asarray(read('TASK.json')['goal_xy']);distance=np.linalg.norm(q[:,:2]-goal,axis=1)
    start=int(np.flatnonzero(distance<2.)[0]);closest=int(np.argmin(distance))
    yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    speed=vel[:,0]*np.cos(yaw)+vel[:,1]*np.sin(yaw)
    length=np.linalg.norm(np.diff(q[start:,:2],axis=0),axis=1)
    body_commands=np.asarray(read('physics/BODY_COMMANDS.json'),float)
    signs=np.sign(body_commands[start:,1]);moving=signs[signs!=0]
    summary=dict(first_under2_tick=start+1,first_under2_time_s=float(t[start]),final_time_s=float(t[-1]),
                 final_goal_distance_m=float(distance[-1]),closest_goal_distance_m=float(distance[closest]),
                 last_window_duration_s=float(t[-1]-t[start]),last_window_actual_path_m=float(length.sum()),
                 last_window_reverse_path_m=float(length[speed[start+1:]<-.005].sum()),
                 last_window_net_goal_progress_m=float(distance[start]-distance[-1]),
                 last_window_command_sign_switches=int(np.count_nonzero(moving[1:]!=moving[:-1])),
                 goal_tolerance_m=.45,last_reference_published_at=plans[-1]['at'],
                 last_reference_endpoint=plans[-1]['path'][-1],
                 runtime_stop_native_tick=13316,runtime_stop_sim_time_s=133.16000000002387,
                 runtime_stop_source='first stop CONTROL_EVENT receipt in INGRESS.json.gz',
                 plots_use_actual_actor_for_offline_display_only=True,models=0,integrations=0)
    # Independently verify the stopping marker rather than inferring it from animation.
    ingress=json.loads(gzip.decompress((RAW/'INGRESS.json.gz').read_bytes()))['receipts']
    stop=next(x for x in ingress if x['packet']['kind']=='stop')
    assert stop['native_tick']==summary['runtime_stop_native_tick']
    font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False,'font.size':11})
    fig,axs=plt.subplots(1,2,figsize=(15,7.6),layout='constrained')
    path=np.asarray(plans[-1]['path']);segment=np.asarray(recovery['proposal']['path'])
    displacement=np.diff(path[:,:2],axis=0)
    projection=np.sum(displacement*np.c_[np.cos(path[:-1,2]),np.sin(path[:-1,2])],axis=1)
    reverse=np.flatnonzero(projection< -1e-8)
    summary['last_reference_reverse_segments']=len(reverse)
    summary['last_reference_reverse_length_m']=float(np.linalg.norm(displacement[reverse],axis=1).sum())
    for ax in axs:
        for x,y,w,h in setup['known']['known_rectangles']:
            # MuJoCo box sizes and the saved rectangle catalog use half extents.
            ax.add_patch(Rectangle((x-w,y-h),2*w,2*h,facecolor='#aab5c2',edgecolor='#728094',lw=.7))
        for x,y,r in setup['known']['known_circles']:
            ax.add_patch(Circle((x,y),r,facecolor='#aab5c2',edgecolor='#728094',lw=.7))
        ax.plot(q[:,0],q[:,1],c='#9ac9ed',lw=1.8,label='全程实际轨迹')
        ax.plot(path[:,0],path[:,1],c='#169b55',lw=2.5,ls='--',label='停止前最后发布的规划路径')
        for n,j in enumerate(reverse):
            ax.plot(path[j:j+2,0],path[j:j+2,1],c='#c03c55',lw=3.5,
                    label='规划路径自带的倒行段'if n==0 else None)
        ax.plot(segment[:,0],segment[:,1],c='#9956c5',lw=3,label='先前实际接管的恢复段参考')
        ax.plot(q[start:,0],q[start:,1],c='#0064bf',lw=2.5,label='最后不到2米阶段的实际轨迹')
        ax.add_patch(Circle(goal,.45,facecolor='#d5f3df',edgecolor='#169b55',lw=1.5,alpha=.65))
        ax.scatter(*goal,marker='*',s=180,c='#11964e',zorder=6,label='原目标及0.45米到达范围')
        ax.add_patch(Circle(actor[-1],.1,color='#f28a35',zorder=5))
        corners=np.array([[-.44,-.375],[.44,-.375],[.44,.375],[-.44,.375]])
        angle=yaw[-1];rot=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
        footprint=corners@rot.T+q[-1,:2]
        ax.add_patch(Polygon(footprint,facecolor='#0064bf',alpha=.12,edgecolor='#005394',lw=2,zorder=4))
        ax.scatter(*q[-1,:2],s=50,c='#00477f',zorder=7)
        ax.arrow(*q[-1,:2],.40*np.cos(angle),.40*np.sin(angle),width=.014,color='#00477f',zorder=7)
        ax.set_aspect('equal');ax.grid(alpha=.13);ax.set_xlabel('x / m');ax.set_ylabel('y / m')
    axs[0].set(xlim=(-4.8,4.8),ylim=(-4.5,4.4),title='全场：原19个静态实体，蓝线来自保存状态')
    axs[0].legend(loc='upper left',fontsize=9,framealpha=.94)
    axs[1].set(xlim=(1.45,4.7),ylim=(-3.4,-.35),title='末段放大：有规划路径，但实际反复进退')
    axs[1].plot([q[-1,0],goal[0]],[q[-1,1],goal[1]],c='#be3f3f',ls=':',lw=1.5)
    axs[1].text(3.05,-2.13,'停止时距目标1.857米',color='#a22e2e',ha='center',fontsize=11)
    axs[1].annotate('实际停止位置',xy=q[-1,:2],xytext=(1.52,-1.05),arrowprops={'arrowstyle':'->','color':'#00477f'},color='#00477f')
    axs[1].annotate('参考自身含0.177米倒行\n需要从规划层取消普通换向',xy=path[reverse[len(reverse)//2],:2],
                    xytext=(3.8,-.7),ha='center',arrowprops={'arrowstyle':'->','color':'#c03c55'},color='#a12d46',fontsize=10)
    fig.suptitle('V945失败回放｜已走到目标附近，但尚未满足到达与完整审核',fontsize=18)
    fig.supxlabel('最后22.31秒：实际行驶1.135米，其中倒行0.493米，前后切换16次；距目标净缩短仅0.143米。\n直接运行停止：133.16秒收到观测活性异常的停车请求；不是碰撞或180秒导航截止。',fontsize=12)
    target=OUT/'v945_paths_and_last2m.png';fig.savefig(target,dpi=170);plt.close(fig)
    (REC/target.name).write_bytes(target.read_bytes())
    (OUT/'PATH_VISUALIZATION.json').write_text(json.dumps(summary,indent=2)+'\n')
    (REC/'PATH_VISUALIZATION.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
