from pathlib import Path
import hashlib,json,os,re,subprocess,time,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2];O=R/'runs/v1981_mppi_static_runtime_inputs';root=R/'runs/v856_nav2_foundation/rootfs';overlay=R/'runs/v931_deadband_consistent_mppi/install'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{6});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));start=time.monotonic();assert not(O/'RESULT.json').exists();build=read(R/'runs/v1976_mppi_plugin_sync_api/BUILD_RESULT.json');assert build['build_passed']and sha(R/build['binary_path'])==build['binary_sha256']
 for n,h in build['source_pins'].items():assert sha(R/n)==h
 plugin=overlay/'share/phase_deadband_mppi/plugin.xml';tree=ET.fromstring(plugin.read_text());classes=tree.findall('.//class');assert any(c.attrib['name']=='phase_deadband/DeadbandMPPI'and c.attrib['base_class_type']=='nav2_core::Controller'for c in classes)
 manifest=overlay/'share/ament_index/resource_index/nav2_core__pluginlib__plugin/phase_deadband_mppi';assert manifest.is_file()
 folders=[overlay/'lib',root/'opt/ros/jazzy/lib',root/'opt/ros/jazzy/lib/x86_64-linux-gnu',root/'usr/lib/x86_64-linux-gnu',root/'usr/lib',root/'lib/x86_64-linux-gnu',root/'usr/lib/x86_64-linux-gnu/blas',root/'usr/lib/x86_64-linux-gnu/lapack',Path('/usr/lib/x86_64-linux-gnu'),Path('/lib/x86_64-linux-gnu')]
 initial=[R/build['binary_path'],overlay/'lib/libphase_deadband_mppi.so',R/'runs/v1319_mppi_coherent_sampling/libcoherent.so'];todo=initial[:];seen={};missing=[]
 while todo:
  assert time.monotonic()-start<120 and len(seen)<512
  p=todo.pop();key=str(p)
  if key in seen:continue
  data=subprocess.check_output(['readelf','-d',str(p)],timeout=5,text=True);needed=re.findall(r'\(NEEDED\).*?\[(.*?)\]',data);providers={}
  for name in needed:
   found=next((d/name for d in folders if(d/name).is_file()),None)
   if found is None:missing.append(dict(parent=key,needed=name));continue
   providers[name]=str(found);todo.append(found)
  seen[key]=dict(sha256=sha(p),bytes=p.stat().st_size,needed=needed,providers=providers,symlink=p.is_symlink(),link_text=os.readlink(p)if p.is_symlink()else None)
 exports=subprocess.check_output(['readelf','--dyn-syms','--wide',str(initial[0])],timeout=5,text=True);symbols=['phase_mppi_'+x for x in ['abi_version','request_dimension','error','create','solve','call_count','poisoned','destroy']];assert all(re.search(r'\b'+name+r'\b',exports)for name in symbols)
 value=dict(passed=not missing,closed=True,static_only=True,CPU=6,ELF_files=seen,missing=missing,exported_CABI_symbols=symbols,plugin_XML=dict(path=str(plugin.relative_to(R)),sha256=sha(plugin),library=tree.find('library').attrib,classes=[c.attrib for c in classes]),plugin_manifest=dict(path=str(manifest.relative_to(R)),sha256=sha(manifest),text=manifest.read_text()),future_environment_required=dict(AMENT_PREFIX_PATH=str(overlay)+':/opt/ros/jazzy',LD_PRELOAD=str(initial[2]),PHASE_COHERENT_NOISE='1'),dynamic_constructor_and_critic_dependencies_unknown=True,coherent_sampler_preload_not_yet_qualified=True,seed_RNG_reproducibility_not_yet_qualified=True,full_current_vehicle_safety_gate_not_yet_qualified=True,production_ready=False,DLL_loads=0,controller_constructors=0,optimizer_calls=0,models=0,physical_native=0,replay_native=0,wall_s=time.monotonic()-start,source_late_after_406bd3d5=True)
 (O/'RESULT.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(dict(passed=value['passed'],ELF_count=len(seen),missing=missing,production_ready=False,wall_s=value['wall_s'])))
if __name__=='__main__':main()
