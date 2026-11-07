"""Pre-model fixed map/config/task derivation. No simulator import or initialization."""
import json,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v858_nav2_verified';W=R/'experiments/v855_renewal_worker'
def prepare():
    known=json.loads((W/'KNOWN_FIELD.json').read_text());resolution=.05;width=height=200;cells=bytearray([254]*40000)
    # Occupied if cell square intersects any known obstacle; circle uses enclosing half-diagonal.
    for y in range(height):
        for x in range(width):
            px=-5+(x+.5)*resolution;py=-5+(y+.5)*resolution
            hit=x==0 or y==0 or x==width-1 or y==height-1
            hit|=any(abs(px-cx)<=hx+.025 and abs(py-cy)<=hy+.025 for cx,cy,hx,hy in known['known_rectangles'])
            hit|=any(math.hypot(px-cx,py-cy)<=r+math.sqrt(2)*.025 for cx,cy,r in known['known_circles'])
            if hit:cells[(height-y-1)*width+x]=0
    (OUT/'field.pgm').write_bytes(b'P5\n200 200\n255\n'+cells)
    (OUT/'field.yaml').write_text(json.dumps(dict(image=str(OUT/'field.pgm'),mode='trinary',resolution=.05,origin=[-5.,-5.,0.],negate=0,occupied_thresh=.65,free_thresh=.196),indent=2)+'\n')
    config=json.loads((R/'experiments/v856_nav2_foundation/phase_nav2_params.yaml').read_text());config['map_server']['ros__parameters']['yaml_filename']=str(OUT/'field.yaml');(C/'physical_nav2_params.yaml').write_text(json.dumps(config,indent=2)+'\n')
    cases=json.loads((W/'SCENE_CASES.json').read_text());tasks=[]
    for stage in ['static_main','dynamic_main','dynamic_repeat']:
        for i,case in enumerate(cases):
            ident=f'{stage}_{i+1:02d}';task=dict(id=ident,stage=stage,case_id=case['id'],seed=10010001+i,goal_xy=case['goal_xy'],goal_yaw=case['yaw'],dynamic=stage!='static_main',wall_limit_s=600,output=str(OUT/ident),nav2_params=str(C/'physical_nav2_params.yaml'),kind='NAV2_BASELINE_DEVELOPMENT_NOT_RPCCR_OR_FRESH_CONFIRMATION',root_deadline_unix=1794052800.)
            tasks.append(task)
    (C/'MAP_DERIVATION_TASKS.json').write_text(json.dumps(tasks,indent=2)+'\n')
    for task in tasks:(OUT/(task['id']+'.task.json')).write_text(json.dumps(task,indent=2)+'\n')
    return tasks
if __name__=='__main__':print(len(prepare()))
