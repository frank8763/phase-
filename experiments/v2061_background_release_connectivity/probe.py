from pathlib import Path
import concurrent.futures,json,os,subprocess,time
R=Path(__file__).resolve().parents[2];D=R/'runs'/Path(__file__).resolve().parent.name
start=time.monotonic();time.sleep(3)
url='https://api.github.com/repos/frank8763/phase-/releases/458891864'
def probe(direct):
 args=['curl','--http1.1','--silent','--show-error','--connect-timeout','4','--max-time','8','--output','/dev/null','--write-out','%{http_code}',url]
 if direct:args[1:1]=['--noproxy','*']
 t=time.monotonic();p=subprocess.run(args,capture_output=True,timeout=10);return dict(direct=direct,returncode=p.returncode,http_status=p.stdout.decode(),stderr=p.stderr.decode()[:1000],wall_s=time.monotonic()-t)
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:rows=list(pool.map(probe,[False,True]))
(D/'RESULT.json').write_text(json.dumps(dict(closed=True,models=0,physics=0,read_only=True,netns=os.readlink('/proc/self/ns/net'),rows=rows,wall_s=time.monotonic()-start),indent=2)+'\n')
