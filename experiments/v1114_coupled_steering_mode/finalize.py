"""Bounded zero-model archival; originals kept until remote readback."""
import sys,json,fcntl,importlib.util
from common import C,R,O,dump,sha,GUARD_SHA,used
def main():
 assert json.loads((O/'COMPLETION.json').read_text())['closed']and sha(R/'REVIEW_PENDING')==GUARD_SHA
 assert not(O/'FINALIZED.json').exists(),'NO_ARCHIVE_OVERWRITE'
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 spec=importlib.util.spec_from_file_location('v1114_archive',R/'experiments/v1065_preflight_metadata_continuation/archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc)
 files=[]
 for task in json.loads((C/'TASKS.json').read_text()):files.extend(p for p in arc.walk(task['output'])if not any(x in p.parts for x in ['cache','frozen_original']))
 for root in [C,O]:files.extend(p for p in root.iterdir()if p.is_file()and not p.is_symlink()and p.name not in ['campaign.console','watchdog.console','finalize.console','driver.lock'])
 files.append(R/'docs/RPCCR_PARKED_MODE_RESPONSE_V1114_REPORT.md');target=O/'cloud';baseline=used()
 record,inventory=arc.package(R,files,target,'v1114-parked-mode-response',budget_check=lambda:baseline+sum(p.stat().st_size for p in target.glob('*')if p.is_file())+1024**2<=2*1024**3)
 D=R/'records/nav2_v1114_20261113';D.mkdir(exist_ok=True);dump(D/'RECORD_INDEX.json',dict(repository='frank8763/phase-',release_tag='phase-parked-mode-v1114-20261113',archives=[record]));dump(D/'INVENTORY.json',dict(files=inventory));dump(D/'FINAL_SUMMARY.json',json.loads((O/'COMPLETION.json').read_text()))
 final=dict(all_source_decompressed_sha_verified=True,parts_reassembled_sha_verified=True,remote_delivery_pending=True,models=0,integrations=0,raw_retained=True);dump(D/'FINALIZED.json',final);dump(O/'FINALIZED.json',final);print(json.dumps(dict(sources=len(inventory),compressed_bytes=record['archive_bytes'])))
if __name__=='__main__':main()
