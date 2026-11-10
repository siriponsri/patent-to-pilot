import subprocess,json
from pathlib import Path
source='''import json
from pathlib import Path
from datetime import datetime,timezone
memory={}
for line in Path('/proc/meminfo').read_text().splitlines():
 key,_,value=line.partition(':')
 if key in {'MemTotal','MemAvailable','SwapTotal','SwapFree'}: memory[key+'_bytes']=int(value.split()[0])*1024
result={'observed_utc':datetime.now(timezone.utc).isoformat(),'host_memory':memory,'cgroup_v2':[],'scope':'SSH observer only; not a declared isolated research runtime'}
for line in Path('/proc/self/cgroup').read_text().splitlines():
 if line.startswith('0::'):
  relative=line.split('::',1)[1].lstrip('/')
  root=Path('/sys/fs/cgroup'); current=root/relative
  while current==root or root in current.parents:
   row={}
   for name in ['memory.max','memory.high','memory.current','memory.swap.max','memory.swap.current']:
    p=current/name
    if p.is_file(): row[name]=p.read_text().strip()
   if row: result['cgroup_v2'].append(row)
   if current==root: break
   current=current.parent
print(json.dumps(result))
'''
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','chaw@100.77.149.83','python3','-'],input=source,text=True,capture_output=True,timeout=30)
r.check_returncode(); d=json.loads(r.stdout)
d['recorded_index_payload_bytes']=6363865088
d['input_plus_detached_copy_bytes']=12727730176
d['host_available_minus_two_arrays_bytes']=d['host_memory']['MemAvailable_bytes']-12727730176
d['acceptance']='NOT_ESTABLISHED_NO_RUNTIME_BUDGET_OR_MEASURED_INDEX_PEAK'
p=Path('docs/healthtech/audits/ptp-method-first-host-memory-20261110'); p.mkdir(exist_ok=True)
with (p/'observation.json').open('x', encoding='utf-8') as handle:
    handle.write(json.dumps(d,indent=2)+'\n')
print(json.dumps(d,indent=2))
