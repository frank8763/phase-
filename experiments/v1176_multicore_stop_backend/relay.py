from pathlib import Path
import sys,subprocess,json,time
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1176_multicore_stop_backend'
def main():
    assert not(O/'COMPLETION.json').exists();r=dict(started_unix=time.time(),run=None,audit=None,error=None)
    try:
        with(O/'run.console').open('w')as f:r['run']=subprocess.run([sys.executable,'-B',str(C/'run.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=930).returncode
        if r['run']==0:
            with(O/'audit.console').open('w')as f:r['audit']=subprocess.run([sys.executable,'-B',str(C/'audit_saved.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=120).returncode
    except BaseException as e:r['error']=repr(e)
    finally:
        (O/'RELAY_RESULT.json').write_text(json.dumps(r,indent=2)+'\n');code=subprocess.run([sys.executable,'-B',str(C/'finish.py')],cwd=R,timeout=120).returncode
    return code
if __name__=='__main__':sys.exit(main())
