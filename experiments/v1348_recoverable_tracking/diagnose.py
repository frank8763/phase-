"""Saved-trajectory red signal for losing the unchanged recovery clearance."""
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sys.path.insert(0,str(R/'experiments/v1347_cusp_segment_execution'))
from observed_route import geometry


def field(known):
    return SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),
        rectangles=np.array(known['known_rectangles']),circles=np.array(known['known_circles']),
        sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))


def rear(body):
    b=np.asarray(body,float)
    return np.c_[b[:,:2]-.3*np.c_[np.cos(b[:,2]),np.sin(b[:,2])],b[:,2]]


def main():
    raw=R/'runs/v858_nav2_verified/v1347/rpp_async_default_dynamic_main'
    known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
    j=json.loads((raw/'APPLIED_JOURNAL.json').read_text())
    body=np.array([x['body'] for x in j]);clear=geometry.pose_values(field(known),rear(body))
    lo,hi=13965,15415;idx=np.flatnonzero(clear[lo:hi]<.22)+lo
    assert len(idx)>0
    lost=int(idx[0]);assert j[lost]['request'][0]>.005
    segment=json.loads((raw/'SEGMENT_RECORDS.json').read_text())[-1]['segments'][0]
    path=np.array(segment['poses']);pose=rear(body[[lost]])[0]
    nearest=int(np.linalg.norm(path[:,:2]-pose[:2],axis=1).argmin())
    heading=math.atan2(math.sin(pose[2]-path[nearest,2]),math.cos(pose[2]-path[nearest,2]))
    braking=[]
    for version in ['v1345','v1346','v1347']:
        p=R/'runs/v858_nav2_verified'/version/'rpp_async_default_dynamic_main'
        journal=json.loads((p/'APPLIED_JOURNAL.json').read_text())
        bodies=np.array([x['body'] for x in journal]);vals=geometry.pose_values(field(known),rear(bodies))
        for i in range(1,len(journal)-200):
            if abs(journal[i]['request'][0])<.005 and abs(journal[i-1]['request'][0])>=.005:
                if all(abs(x['request'][0])<.005 for x in journal[i:i+200]):
                    braking.append(dict(version=version,native=i,clearance_loss_m=float(vals[i]-vals[i:i+201].min()),
                                        speed=abs(journal[i]['body'][3])))
    proof=dict(red_reproduced=True,lost_recovery_clearance_native=lost,
               still_executing_forward=j[lost]['request'][0],nominal_clearance_m=float(clear[lost]),
               reference_heading_error_rad=heading,first_recovery_gate_m=.22,
               original_brake_native=15415,brake_episodes=braking,
               maximum_observed_braking_clearance_loss_m=max(x['clearance_loss_m'] for x in braking),
               scope='saved known-map geometry/commands; empirical braking examples, not universal braking bound',
               models=0,physical_native=0)
    (O/'SAVED_FAILURE_DIAGNOSIS.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='brake_episodes'}))


if __name__=='__main__':main()
