"""Archive bounded zero-integration diagnostics/media and verify exact readback."""
import gzip,hashlib,json,signal,zipfile
from pathlib import Path
repo=Path(__file__).resolve().parents[2];dest=repo/'evidence/global_dynamic_overnight_20261103_supplement';dest.mkdir(exist_ok=False);(dest/'blobs').mkdir()
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SUPPLEMENT_ARCHIVE_600S_CAP')));signal.alarm(600)
assert(repo/'REVIEW_PENDING').exists();qa=json.loads((repo/'runs/report_materials_v790_20261103/VIDEO_QA.json').read_text());assert qa['status']=='FULL_VIDEO_DECODE_QA_PASS'and qa['all_three_png_visual_qa_passed']and qa['render_integrations']==0
sources=[]
for folder in ['runs/v788_global_information_diagnosis','runs/global_dynamic_overnight_20261103','runs/report_materials_v790_20261103','experiments/global_night_20261103_analysis','experiments/report_materials_v790_20261103']:
 sources.extend(p for p in(repo/folder).rglob('*')if p.is_file()and'__pycache__'not in p.parts and p.suffix not in['.pyc','.tmp','.lock'])
for pattern in ['v788*.console','v789*.console','v790*.console']:sources.extend((repo/'runs').glob(pattern))
sources.extend(repo/p for p in ['AGENTS.md','RESEARCH_STATUS.md','CURRENT_EXPERIMENT.json','GLOBAL_DYNAMIC_OVERNIGHT_AUTHORIZATION_20261103.json','GLOBAL_DYNAMIC_OVERNIGHT_LEDGER_20261103.json','docs/GLOBAL_DYNAMIC_OVERNIGHT_20261103_REPORT.md','docs/GLOBAL_DYNAMIC_OVERNIGHT_20261103_PLAN.md','docs/RPCCR_FAIR_COMPARISON_DRAFT_20261103.md','docs/figures/RPCCR_GLOBAL_NIGHT_V790_DIAGNOSIS.png','docs/figures/RPCCR_GLOBAL_NIGHT_V790_DIAGNOSIS.pdf'])
inventory=[]
for p in sorted(set(sources)):
 raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();encoding='identity'if p.suffix in['.gz','.zip','.mp4','.png','.pdf']else'gzip';blob=dest/'blobs'/(h+('.raw'if encoding=='identity'else'.gz'));data=raw if encoding=='identity'else gzip.compress(raw,mtime=0)
 if blob.exists():assert blob.read_bytes()==data
 else:blob.write_bytes(data)
 inventory.append(dict(source=str(p.relative_to(repo)),sha256=h,bytes=len(raw),encoding=encoding,blob=str(blob.relative_to(dest))))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
for row in inventory:
 data=(dest/row['blob']).read_bytes();raw=data if row['encoding']=='identity'else gzip.decompress(data);assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']and hashlib.sha256((repo/row['source']).read_bytes()).hexdigest()==row['sha256']
media=repo/'runs/report_materials_v790_20261103';bundle=dest/'V790_actual_failed_global_1080p_media.zip';names=['phase_global_dynamic_failure_1080p.mp4','global_failure_start_1080p.png','global_failure_best_progress_1080p.png','global_failure_failure_1080p.png','RENDER_PROVENANCE.json','VIDEO_QA.json']
with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_DEFLATED)as z:
 for name in names:z.write(media/name,name)
 z.writestr('README.txt','V790 recorded full-field failure, not a success video. 527 actual saved states /42.16s physical duration;1080p25fps,47.16s including5s titles. No new integration or interpolation. See provenance and QA. Actor never entered3m sensor range; original task ended BOUNDED_WALL_STOP. Raw results and older failures retained.\n')
with zipfile.ZipFile(bundle)as z:
 assert z.testzip()is None
 for name in names:assert z.read(name)==(media/name).read_bytes()
manifest=[dict(path=str(p.relative_to(dest)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in sorted(dest.rglob('*'))if p.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in manifest:assert hashlib.sha256((dest/row['path']).read_bytes()).hexdigest()==row['sha256']
result=dict(status='SUPPLEMENT_ALL_SOURCE_AND_BLOB_READBACK_PASS',sources=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),manifest_entries=len(manifest),media_bundle=str(bundle.relative_to(repo)),bundle_readback=True,original_deleted=False,new_models=0,new_integrations=0,operational_metadata_snapshot='before final bounded git synchronization; later operational ledger may legitimately change')
(repo/'runs/global_dynamic_overnight_20261103/SUPPLEMENT_ARCHIVE_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');signal.alarm(0);print(json.dumps(result,indent=2))
