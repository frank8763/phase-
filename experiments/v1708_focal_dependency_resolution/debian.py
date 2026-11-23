"""Data-only Debian index/dependency parser and deterministic selection."""
import functools
import re
import subprocess

FIELDS = ['Package','Version','Architecture','Filename','Size','SHA256','Installed-Size','Depends','Pre-Depends','Provides']

def fields(text):
    out = {}; key = None
    for line in text.splitlines():
        if line.startswith((' ', '\t')):
            assert key is not None; out[key] += '\n' + line[1:]
        else:
            key, sep, value = line.partition(':'); assert sep and key not in out
            out[key] = value.strip()
    return out

def alternatives(group):
    result=[]
    for value in group.split('|'):
        match=re.fullmatch(r'([a-zA-Z0-9+.-]+)(?::[a-zA-Z0-9-]+)?(?:\s*\((>=|<=|=|>>|<<)\s*([^()]+)\))?',value.strip())
        assert match,('DEBIAN_DEPENDENCY_SYNTAX',value);result.append(match.groups())
    return result

@functools.lru_cache(maxsize=10000)
def satisfies(actual,op,required):
    return not op or subprocess.run(['/usr/bin/dpkg','--compare-versions',actual,op,required],capture_output=True,timeout=3).returncode==0

def closure(groups, records, already):
    names={};provided={}
    for row in records:
        names.setdefault(row['Package'],[]).append(row)
        for group in filter(None,(v.strip()for v in row.get('Provides','').split(','))):
            for name,op,version in alternatives(group):
                assert op in (None,'=');provided.setdefault(name,[]).append((row,version))
    chosen={};unresolved=[];edges=[];pending=[('ROOT',g)for g in groups];seen=set()
    while pending:
        parent,group=pending.pop(0)
        if(parent,group)in seen:continue
        seen.add((parent,group));selection=None
        for name,op,version in alternatives(group):
            if name in already and satisfies(already[name],op,version):selection=dict(package=name,version=already[name],already_locked_ROS=True,requested=name);break
            candidates=[(x,x['Version'])for x in names.get(name,[])]+provided.get(name,[])
            candidates.sort(key=lambda item:(0 if item[0].get('source')=='ROS_SIGNED'else 1,item[0]['Package']))
            for row,offered in candidates:
                if op and(not offered or not satisfies(offered,op,version)):continue
                if row['Package']in chosen and chosen[row['Package']]['Version']!=row['Version']:continue
                selection=dict(package=row['Package'],version=row['Version'],already_locked_ROS=False,requested=name,record=row);break
            if selection:break
        if selection is None:unresolved.append(dict(parent=parent,group=group));continue
        edges.append(dict(parent=parent,group=group,selected=selection['package'],version=selection['version'],virtual_requested=selection['requested'],already_locked_ROS=selection['already_locked_ROS']))
        if selection['already_locked_ROS']or selection['package']in chosen:continue
        row=selection['record'];chosen[row['Package']]=row
        for key in ['Pre-Depends','Depends']:
            pending.extend((row['Package'],g.strip())for g in row.get(key,'').split(',')if g.strip())
        assert len(chosen)<=1500 and len(pending)<=30000,'DEPENDENCY_GRAPH_CAP'
    return dict(packages=sorted(chosen.values(),key=lambda x:x['Package']),edges=edges,unresolved=unresolved,
                download_bytes=sum(int(x['Size'])for x in chosen.values()),declared_installed_bytes=sum(int(x.get('Installed-Size',0))*1024 for x in chosen.values()),
                declared_size_not_exact_allocation=True,package_execution_authority=False)
