"""Full saved-video decode and image dimension checks, no simulator."""
import json,subprocess,hashlib
from pathlib import Path
from PIL import Image
import numpy as np
import imageio_ffmpeg
repo=Path(__file__).resolve().parents[2];out=repo/'runs/report_materials_v805_20261104';p=json.loads((out/'PROVENANCE.json').read_text());video=out/'phase_no_dynamic_full_path_1080p.mp4';run=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-threads','1','-i',str(video),'-progress','pipe:1','-f','null','-'],capture_output=True,text=True,timeout=120);assert run.returncode==0,run.stderr
frames=[int(x.split('=',1)[1].strip())for x in run.stdout.splitlines()if x.startswith('frame=')];assert frames[-1]==p['frames'];images=[]
for file in sorted(out.glob('*.png')):
 im=Image.open(file);assert im.size==(1920,1080)and np.asarray(im).std()>10;images.append(dict(path=str(file.relative_to(repo)),size=list(im.size),sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
assert len(images)==3;result=dict(status='FULL_VIDEO_DECODE_AND_PNG_DIMENSION_QA_PASS',decoded_frames=frames[-1],expected_frames=p['frames'],video_sha256=hashlib.sha256(video.read_bytes()).hexdigest(),PNGs=images,integrations=0,interpolation=False,visual_QA='PENDING_MODEL_INSPECTION')
(out/'MEDIA_QA.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
