"""Select only saved records from verified Release; never load a vehicle model."""
import gzip,hashlib,json,math,subprocess,tarfile
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v883_observation_dispatch'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    inv=json.loads((O/'v882-runtime-evidence.INVENTORY.json').read_text());archive=O/'v882-runtime-evidence.tar.zst.part000';assert sha(archive)==inv['archive_sha256'];expected={x['path']:x for x in inv['files']}
    names=['TASK.json','RESULT.json','ROS_RESULT.json','PLANS.json','ROUTER_REQUESTS.json','COMMANDS.json','physics/NATIVE_TRACE.npz','physics/BODY_COMMANDS.json','physics/SENSORS.json.gz','physics/SETUP.json','ros/controller_server.console'];prefix='runs/v858_nav2_verified/v882/main_ns/';wanted={prefix+n for n in names};out=O/'selected_inputs';out.mkdir(exist_ok=False);seen=[]
    proc=subprocess.Popen(['zstd','-q','-dc',str(archive)],stdout=subprocess.PIPE)
    try:
        with tarfile.open(fileobj=proc.stdout,mode='r|')as tf:
            for member in tf:
                if member.name not in wanted:continue
                assert member.isfile();p=out/member.name[len(prefix):];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tf.extractfile(member).read());assert sha(p)==expected[member.name]['sha256'];seen.append(member.name)
        assert proc.wait(timeout=15)==0 and set(seen)==wanted
    finally:
        if proc.poll()is None:proc.kill();proc.wait()
    rows=np.load(out/'physics/NATIVE_TRACE.npz');commands=json.loads((out/'physics/BODY_COMMANDS.json').read_text());sensors=json.loads(gzip.decompress((out/'physics/SENSORS.json.gz').read_bytes()));plans=json.loads((out/'PLANS.json').read_text());task=json.loads((out/'TASK.json').read_text());fixtures={}
    for sec in [100,130,150,165,170,171.95,175]:
        i=round(sec*100)-1;q=rows['qpos'][i];v=rows['qvel'][i];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));at=commands[i][0];sensor=max((s for s in sensors if s['native_tick']<=i+1),key=lambda s:s['native_tick']);plan=max((p for p in plans if p['at']<=at),key=lambda p:p['at'])
        fixtures[str(sec)]=dict(body=[float(q[0]),float(q[1]),yaw,float(v[0]*math.cos(yaw)+v[1]*math.sin(yaw)),float(v[5])],scan=sensor,path=plan['path'],task=task,source=dict(release_tag='phase-nav2-v882-20261108',native_tick=i+1,sim_time=float(rows['time'][i]),command_completed_monotonic=at,plan_at=plan['at'],original_goal_distance_m=float(np.linalg.norm(q[:2]-task['goal_xy']))))
    (O/'FIXTURES.json').write_text(json.dumps(fixtures,indent=2)+'\n');proof=dict(passed=True,selected_members=len(seen),release_archive_sha256=sha(archive),members={name:expected[name]['sha256']for name in seen},model_initializations=0,integrations=0,scope='Saved input recovery only; original local costmap was not recorded, so exact old collision-grid replay is unavailable')
    (O/'RESTORE_PROOF.json').write_text(json.dumps(proof,indent=2)+'\n');archive.unlink();print(json.dumps(dict(passed=True,members=len(seen),archive_removed=True,models=0,integrations=0)))
if __name__=='__main__':main()
