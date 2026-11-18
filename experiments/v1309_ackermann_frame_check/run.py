import importlib.abc
import sys
class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name.split('.')[0] in {'mujoco', 'torch', 'vehicle', 'rclpy'}: raise AssertionError('ZERO_MODEL')
sys.meta_path.insert(0, NoPhysical())
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from frame import rear_pose, rear_footprint, REAR_OFFSET

R = Path(__file__).resolve().parents[2]; O = R / 'runs/v1309_ackermann_frame_check'


def world(pose, points):
    x, y, a = pose; c, s = math.cos(a), math.sin(a)
    return np.array([[x+c*px-s*py, y+s*px+c*py] for px, py in points])


def main():
    xml = R / 'runs/v858_nav2_verified/v1300/mppi_main/physics/PATCHED_ASSEMBLY.xml'
    tree = ET.parse(xml)
    rear = [tree.find('.//body[@name="'+name+'"]') for name in ['left_rear_wheel', 'right_rear_wheel']]
    assert all(float(node.attrib['pos'].split()[0]) == -REAR_OFFSET for node in rear)
    reports = []; footprint = [[.44,.375],[.44,-.375],[-.44,-.375],[-.44,.375]]
    maximum = 0.; wrong_error = 0.
    for task in ['rpp_main', 'mppi_main']:
        p = R / 'runs/v858_nav2_verified/v1300' / task / 'APPLIED_JOURNAL.json'
        rows = json.loads(p.read_text()); body = np.array([x['body'] for x in rows]); result = []
        for start in range(500, len(body)-100, 100):
            original = body[start,:2].copy(); corrected = original.copy(); yaw = body[start,2]
            for i in range(start, start+100):
                vx, wz = body[i,3:]; mid = yaw + .005*wz
                original += .01*vx*np.array([math.cos(mid), math.sin(mid)])
                corrected += .01*np.array([vx*math.cos(mid)-REAR_OFFSET*wz*math.sin(mid), vx*math.sin(mid)+REAR_OFFSET*wz*math.cos(mid)])
                yaw += .01*wz
            result.append(dict(start_native=start, center_zero_lateral_error_m=float(np.linalg.norm(original-body[start+100,:2])), rear_equivalent_error_m=float(np.linalg.norm(corrected-body[start+100,:2]))))
        for pose in body[::20,:3]:
            back = rear_pose(pose)
            maximum = max(maximum, float(np.abs(world(pose, footprint)-world(back,rear_footprint(footprint))).max()))
            points = [[2*math.cos(k*math.tau/32), 2*math.sin(k*math.tau/32)] for k in range(32)]
            maximum = max(maximum, float(np.abs(world(pose,points)-world(back,[[x+REAR_OFFSET,y] for x,y in points])).max()))
            wrong_error = max(wrong_error, float(np.linalg.norm(world(pose,[[0.,0.]])-world(back,[[0.,0.]]))))
        original = np.array([a['center_zero_lateral_error_m'] for a in result]); corrected = np.array([a['rear_equivalent_error_m'] for a in result])
        reports.append(dict(task=task, windows=len(result), center_median_m=float(np.median(original)), rear_median_m=float(np.median(corrected)), center_maximum_m=float(original.max()), rear_maximum_m=float(corrected.max()), windows_detail=result, source_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    proof = dict(passed=maximum<=1e-12 and abs(wrong_error-.3)<1e-12, mechanical_offset_m=REAR_OFFSET, xml_sha256=hashlib.sha256(xml.read_bytes()).hexdigest(), maximum_world_geometry_error_m=maximum, incorrect_zero_scan_offset_error_m=wrong_error, recordings=reports, models=0, physical_native=0, all_actuator_dynamics_fixed=False, no_physical_success_claim=True)
    (O/'FRAME_CHECK.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({**proof,'recordings':[{k:v for k,v in x.items() if k!='windows_detail'} for x in reports]}))
    return 0 if proof['passed'] else 1


if __name__ == '__main__': raise SystemExit(main())
