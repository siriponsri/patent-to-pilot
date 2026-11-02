
from pathlib import Path
import json,os,socket,sys,time
def denied(*a,**kw): raise RuntimeError('network forbidden in budget worker')
socket.socket.connect=denied; socket.socket.connect_ex=denied
socket.socket.bind=denied; socket.create_connection=denied; socket.getaddrinfo=denied
from patent_to_pilot.providers.project_budget import ProjectBudget
from patent_to_pilot.providers.openrouter import BudgetExceededError
db,aid,gate,ready,action=sys.argv[1:]
b=ProjectBudget(Path(db))
Path(ready).write_text('ready')
deadline=time.monotonic()+10
while not Path(gate).exists():
 if time.monotonic()>deadline: raise RuntimeError('test start gate timeout')
 time.sleep(.01)
try:
 b.reserve(attempt_id=aid,phase='calibration',model='openai/gpt-4.1-mini',provider='openai',payload_sha256='a'*64,upper_bound_usd='.75',bound_verified=True,data_class='synthetic')
 if action=='crash': os._exit(7)
 print(json.dumps({'result':'reserved'}))
except BudgetExceededError:
 print(json.dumps({'result':'blocked'}))
finally: b.close()
