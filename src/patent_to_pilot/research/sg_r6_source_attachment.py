"""Prospective private join of frozen IDs to unchanged source, no extraction.

R6 owner-approved join; external declaration and resource admission required. No query/qrels/test inputs.
"""
import hashlib
import json
from pathlib import Path
import time
from .mtm_runtime import InputBoundaryError


def attach_fixed282_sources(corpus, destination, *, expected_sha256, fixed_ids,
                         max_seconds=1560, max_input_bytes=328999080,
                         max_output_bytes=64*1024**2, clock=time.monotonic):
    out=Path(destination);out.mkdir(exist_ok=False);start=clock()
    receipt={'status':'INCOMPLETE','model_calls':0,'gpu_seconds':0,'extraction':'NOT_RUN','retry':False}
    try:
        if (type(max_seconds) not in (int,float) or not 0<=max_seconds<=1560
                or type(max_input_bytes) is not int or not 0<max_input_bytes<=328999080
                or type(max_output_bytes) is not int or not 0<max_output_bytes<=64*1024**2):
            raise InputBoundaryError('R6 source join resource ceiling')
        ids=set(fixed_ids)
        if len(ids)!=len(fixed_ids) or not ids or len(ids)!=282:
            raise InputBoundaryError('fixed source IDs invalid')
        digest=hashlib.sha256();seen=set();found={};read_bytes=0;output_bytes=0
        with Path(corpus).open('rb') as stream:
            while raw:=stream.readline(8*1024**2+1):
                if clock()-start>=max_seconds:raise TimeoutError('source attachment deadline')
                read_bytes+=len(raw)
                if len(raw)>8*1024**2 or read_bytes>max_input_bytes:raise InputBoundaryError('source input ceiling')
                digest.update(raw);row=json.loads(raw)
                if set(row)!=set(['id','title','abstract','claims']) or any(type(v) is not str for v in row.values()):
                    raise InputBoundaryError('unexpected source fields')
                if row['id'] in seen:raise InputBoundaryError('duplicate corpus ID')
                seen.add(row['id'])
                if row['id'] in ids:
                    encoded=json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
                    output_bytes+=len(encoded)+1
                    if output_bytes>max_output_bytes-16384:raise InputBoundaryError('source output ceiling')
                    found[row['id']]=row
        if digest.hexdigest()!=expected_sha256 or set(found)!=ids:
            raise InputBoundaryError('source identity or fixed sample incomplete')
        with (out/'sources-private.jsonl').open('xb') as stream:
            for fid in sorted(ids):
                if clock()-start>=max_seconds:raise TimeoutError('source serialization deadline')
                stream.write(json.dumps(found[fid],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()+b'\n')
        receipt.update(status='COMPLETE_PRIVATE_SOURCE_ATTACHMENT_NOT_FIDELITY',source_units=len(found),
            corpus_sha256=digest.hexdigest(),input_bytes=read_bytes,private_output_bytes=output_bytes,
            private_output_sha256=hashlib.sha256((out/'sources-private.jsonl').read_bytes()).hexdigest())
        if clock()-start>=max_seconds:raise TimeoutError('source output hash deadline')
        receipt['fixed_ids_sha256']=hashlib.sha256(json.dumps(sorted(ids),separators=(',',':')).encode()).hexdigest()
    except BaseException as error:
        receipt.update(status='FAILED_NO_RETRY',exception_type=type(error).__name__)
        raise
    finally:
        receipt['wall_seconds']=clock()-start
        with (out/'receipt.json').open('x') as stream:json.dump(receipt,stream,indent=2)
    return receipt
