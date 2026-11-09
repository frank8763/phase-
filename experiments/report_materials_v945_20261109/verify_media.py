"""Decode all final video frames and validate actual-state rendering provenance."""
import hashlib
import json
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runs/report_materials_v945_20261109/render02'
REC=ROOT/'records/nav2_v945_media_20261109'


def main():
    proof=json.loads((OUT/'RENDER_PROVENANCE.json').read_text())
    assert proof['new_integrations']==0 and not proof['recorded_state_interpolation']
    movies=[]
    for row in proof['media']:
        path=OUT/row['name']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
        run=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-threads','1','-i',str(path),'-progress','pipe:1','-f','null','-'],capture_output=True,text=True,timeout=100)
        assert run.returncode==0,run.stderr
        frames=[int(x.split('=',1)[1])for x in run.stdout.splitlines()if x.startswith('frame=')]
        assert frames[-1]==row['frames']
        movies.append(dict(name=path.name,frames=frames[-1],sha256=row['sha256'],full_decode_passed=True))
    pictures=[]
    for path in OUT.glob('*.png'):
        image=Image.open(path);assert image.size==(1920,1080)and np.asarray(image).std()>10
        pictures.append(dict(name=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),dimensions=list(image.size)))
    assert len(pictures)==4
    result=dict(passed=True,videos=movies,pictures=pictures,new_integrations=0,
                render_model_loads_completed_attempt=proof['render_model_loads'],
                total_render_model_loads_including_canceled_attempt=2,
                actual_physics_or_navigation_restarted=False,scientific_outcome='NOT_PASSED',
                visual_qa='Recorded PNGs inspected: paths/goal/car legible, orange actor identified, fixed close view and actual stopping marker; rectangle half extents corrected in 2D chart.')
    (REC/'MEDIA_QA.json').write_text(json.dumps(result,indent=2)+'\n')
    (REC/'RENDER_PROVENANCE.json').write_bytes((OUT/'RENDER_PROVENANCE.json').read_bytes())
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
