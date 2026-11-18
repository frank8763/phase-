"""Conservative common public-map raster; no physical imports or integrations."""
import hashlib
import json
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parents[2]; C=Path(__file__).resolve().parent


def dump(p,x): p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def main():
    source=R/'experiments/v855_renewal_worker/KNOWN_FIELD.json'
    known=json.loads(source.read_text()); res=.05; origin=-6.; size=240
    x=origin+(np.arange(size)+.5)*res; xx,yy=np.meshgrid(x,x)
    occupied=(xx-res/2 < -5.)|(xx+res/2 > 5.)|(yy-res/2 < -5.)|(yy+res/2 > 5.)
    for cx,cy,hx,hy in known['known_rectangles']:
        occupied|=(abs(xx-cx)<=hx+res/2+1e-12)&(abs(yy-cy)<=hy+res/2+1e-12)
    for cx,cy,radius in known['known_circles']:
        occupied|=np.maximum(abs(xx-cx)-res/2,0)**2+np.maximum(abs(yy-cy)-res/2,0)**2 <= radius**2+1e-12
    grid=dict(resolution=res,width=size,height=size,origin=[origin,origin,0.],data=occupied.astype(int).ravel().__mul__(100).tolist(),
              source=str(source.relative_to(R)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              scope='public static map only; no actor or failed-state information')
    samples=[]
    for cx,cy,hx,hy in known['known_rectangles']:
        v=np.linspace(-1,1,101)
        samples.extend(np.c_[cx+v*hx,np.full(101,cy-hy)])
        samples.extend(np.c_[cx+v*hx,np.full(101,cy+hy)])
        samples.extend(np.c_[np.full(101,cx-hx),cy+v*hy])
        samples.extend(np.c_[np.full(101,cx+hx),cy+v*hy])
    for cx,cy,radius in known['known_circles']:
        theta=np.linspace(0,2*np.pi,721)
        samples.extend(np.c_[cx+radius*np.cos(theta),cy+radius*np.sin(theta)])
    samples=np.asarray(samples); index=np.floor((samples-origin)/res).astype(int)
    assert ((index>=0)&(index<size)).all()
    covered=occupied[index[:,1],index[:,0]]
    assert covered.all(),'PUBLIC_OBSTACLE_BOUNDARY_MISSING'
    header=f'P5\n{size} {size}\n255\n'.encode()
    pixels=np.where(occupied[::-1],0,254).astype('uint8')
    pgm=header+pixels.tobytes(); (C/'public_static.pgm').write_bytes(pgm)
    parsed=np.frombuffer(pgm[len(header):],dtype='uint8').reshape(size,size)[::-1]==0
    assert np.array_equal(parsed,occupied),'ROW_ORIENTATION_ERROR'
    dump(C/'PUBLIC_STATIC_GRID.json',grid)
    (C/'public_static.yaml').write_text('image: public_static.pgm\nmode: trinary\nresolution: 0.05\norigin: [-6.0, -6.0, 0.0]\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n')
    original=json.loads((R/'experiments/v1329_coherent_mppi_static_route/params.json').read_text())
    params=json.loads(json.dumps(original)); local=params['local_costmap']['local_costmap']['ros__parameters']
    local['plugins']=['static_layer',*local['plugins']]
    local['static_layer']=dict(plugin='nav2_costmap_2d::StaticLayer',enabled=True,map_topic='/phase_public_static',map_subscribe_transient_local=True,subscribe_to_updates=False)
    dump(C/'mppi_common_map_params.json',params)
    assert params['controller_server']==original['controller_server']
    old={k:v for k,v in local.items() if k not in ['plugins','static_layer']}
    assert old=={k:v for k,v in original['local_costmap']['local_costmap']['ros__parameters'].items() if k!='plugins'}
    checks=dict(public_source_only=True,all_entity_boundary_samples_covered=bool(covered.all()),
                pgm_grid_roundtrip_exact=True,controller_parameters_unchanged=True,original_scan_retained=True,
                actual_nav2_map_receipt_qualified=False,physical_navigation_qualified=False)
    dump(C/'PREPARATION.json',dict(prepared=True,checks=checks,public_entities=len(known['known_rectangles'])+len(known['known_circles']),
         boundary_samples=len(samples),occupied_cells=int(occupied.sum()),source_sha256=grid['source_sha256'],
         models=0,physical_native=0,automatic_physical_launch=False))
    print(json.dumps(dict(prepared=True,entities=19,boundary_samples=len(samples),models=0,physical_native=0)))


if __name__=='__main__': main()
