"""Immutable supplements: operational failures, analysis, media and provenance."""
import gzip,hashlib,json,zipfile
from pathlib import Path
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v805_static_five_continuation';read=lambda p:json.loads(p.read_text());assert(repo/'REVIEW_PENDING').exists()and read(root/'FINALIZED.json')['complete_five'];media=repo/'runs/report_materials_v805_20261104';qa=read(media/'MEDIA_QA.json');assert qa['visual_QA']=='PASS'
dest=repo/'evidence/rpccr_no_dynamic_five_v805_20261104_supplement';assert not dest.exists();dest.mkdir();(dest/'blobs').mkdir()
zipfile_path=dest/'five_static_routes_and_actual_1080p_video.zip'
with zipfile.ZipFile(zipfile_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in sorted(media.glob('*')):
  if p.is_file()and p.suffix in ['.mp4','.png','.json']:z.write(p,'media/'+p.name)
 for p in sorted((repo/'runs/v805_five_static_plots').glob('*')):
  if p.is_file():z.write(p,'five_routes/'+p.name)
 z.write(repo/'docs/RPCCR_NO_DYNAMIC_FIVE_V805_REPORT.md','REPORT.md')
with zipfile.ZipFile(zipfile_path)as z:
 assert z.testzip()is None
 for item in z.infolist():assert len(z.read(item.filename))==item.file_size
files=set()
for name in ['experiments/report_materials_v805_20261104','experiments/v804_no_dynamic_static_contact','runs/v805_five_static_plots','runs/v805_five_static_analysis','runs/report_materials_v805_20261104','runs/v804_no_dynamic_static_contact/five01','runs/v805_static_five_continuation/PRIOR_V804_DRIVER_FAILURE']:
 files.update(p for p in(repo/name).rglob('*')if p.is_file()and'__pycache__'not in p.parts and p.suffix not in ['.pyc','.lock'])
for name in ['RPCCR_NO_DYNAMIC_FIVE_AUTHORIZATION_20261104.json','RPCCR_NO_DYNAMIC_FIVE_FIXTURE_REPAIR_20261104.json','RPCCR_NO_DYNAMIC_FIVE_CONTINUATION_20261104.json','RPCCR_NO_DYNAMIC_FIVE_LEDGER_20261104.json','docs/RPCCR_NO_DYNAMIC_FIVE_V805_REPORT.md','CURRENT_EXPERIMENT.json','AGENTS.md','RESEARCH_STATUS.md','runs/v803_no_dynamic_five/FINALIZED.json','runs/v804_no_dynamic_static_contact/CONSOLIDATED_CLOSURE_V805.json','runs/v805_static_five_continuation/FINALIZED.json','runs/v805_static_five_continuation/FINAL_INDEPENDENT_AUDIT.json','runs/v805_static_five_continuation/CLOSURE_HANDOFF.md','runs/v803_driver.console','runs/v804_driver.console','runs/v805_driver.console','runs/v805_preparation_log.json','runs/v804_static_catalog_calibration.json','runs/v804_static_catalog_calibration.console','runs/v803_preparation_review.json','runs/v805_preparation_equivalence_review.json','runs/v805_finalize.console','runs/v805_plot.console','runs/v805_analysis.console','runs/v805_render.console','runs/v805_media_verify.console','runs/v805_transport.console','runs/v805_final_verification.json']:
 p=repo/name;assert p.exists(),str(p);files.add(p)
files.add(zipfile_path);sha=lambda raw:hashlib.sha256(raw).hexdigest();inventory=[]
for p in sorted(files):
 raw=p.read_bytes();h=sha(raw);blob=dest/'blobs'/(h+'.gz');packed=gzip.compress(raw,mtime=0)
 if blob.exists():assert blob.read_bytes()==packed
 else:blob.write_bytes(packed)
 inventory.append(dict(path=str(p.relative_to(repo)),bytes=len(raw),sha256=h,blob=str(blob.relative_to(dest))))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
for x in inventory:
 raw=gzip.decompress((dest/x['blob']).read_bytes());assert len(raw)==x['bytes']and sha(raw)==x['sha256']==sha((repo/x['path']).read_bytes())
manifest=[dict(path=str(p.relative_to(dest)),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in sorted(dest.rglob('*'))if p.is_file()];(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');assert all(sha((dest/x['path']).read_bytes())==x['sha256']for x in manifest)
result=dict(status='SUPPLEMENT_SOURCE_AND_DECOMPRESSED_BYTES_VERIFIED',raw_files=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),manifest_entries=len(manifest),media_ZIP_verified=True,media_ZIP=str(zipfile_path.relative_to(repo)),new_models=0,new_integrations=0,raw_deleted=False)
(repo/'runs/v805_supplement_archive_result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
