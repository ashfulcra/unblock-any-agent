"""Restricted synthetic native pickup proof; never executes instructions from work data."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import uuid
from .client import private_read,private_write
from .native_client import NativeClient
from .store import DomainError

APPROVAL='APPROVE SYNTHETIC BLUE MARKER'
NEED_KEY='native-manifest-continuity-pilot-1'


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def run_worker(client,request_id,output,poll_attempts=12):
    request_id=str(uuid.UUID(request_id));me=client.call('identity')
    if me.get('kind')!='agent':raise ValueError('Worker requires an agent credential')
    def recover():
        result=client.call('recover',{'request_id':request_id})
        if result.get('source')!='checked' or len(result.get('requests',[]))!=1:raise ValueError('Source is not checked')
        row=result['requests'][0]
        if row['id']!=request_id or row['agent_id']!=me['id']:raise ValueError('Worker identity mismatch')
        return row
    row=recover()
    if len(row['revisions'])!=1 or len(row['answers'])!=1:raise ValueError('Synthetic worker requires one current question and answer')
    revision=row['revisions'][0];answer=row['answers'][0]
    if revision['payload']['need_key']!=NEED_KEY or answer['payload']['answer']!=APPROVAL:raise ValueError('Explicit synthetic approval required')
    artifact=Path(output).resolve()/f'{request_id}-{answer["id"]}.json'
    expected={'request_id':request_id,'revision':revision['id'],'answer_id':answer['id'],'context_sha256':digest(revision['payload']['context']),'marker':'blue','synthetic':True}
    key=digest([expected,str(artifact)]);action_intent='synthetic-action:'+key
    existing=[a for a in row['actions'] if a['intent_id']==action_intent]
    if any(a['id'] not in {e['id'] for e in existing} for a in row['uncertain_actions']):raise ValueError('Unrelated uncertain action requires reconciliation')
    def publish(operation,body,field):
        receipt=client.call(operation,body)
        for attempt in range(poll_attempts):
            current=recover()
            if any(r['id']==receipt['record_id'] for r in current.get(field,[])):return receipt,current
            if attempt+1<poll_attempts:time.sleep(1)
        raise ValueError('Native write pending readback; retain intent before continuing')
    # Declare and read back the exact idempotent private-file effect before touching it.
    action,_=publish('action',{'intent_id':action_intent,'request_id':request_id,'effect':'Write and verify only the private synthetic blue marker '+str(artifact)},'actions')
    if not artifact.exists():
        try:private_write(artifact,expected)
        except FileExistsError:pass
    if private_read(artifact)!=expected:raise ValueError('Existing artifact differs; reconcile without overwriting it')
    sha=hashlib.sha256(artifact.read_bytes()).hexdigest()
    publish('settle',{'intent_id':'synthetic-settle:'+key,'request_id':request_id,'action':action['record_id'],'evidence':'Read back exact synthetic blue marker; sha256='+sha},'settlements')
    receipt,_=publish('progress',{'intent_id':'synthetic-resumed:'+key,'request_id':request_id,'revision':revision['id'],'answers':[answer['id']],'stage':'resumed','reconciled':False,'evidence':'Replacement worker recovered current context and approval, verified the private blue marker without repeating an existing effect; sha256='+sha},'progress_history')
    return {'request_id':request_id,'stage':'resumed','sha256':sha,'record_id':receipt['record_id']}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',required=True);parser.add_argument('--output',required=True);parser.add_argument('--request-id',required=True)
    args=parser.parse_args()
    try:print(json.dumps(run_worker(NativeClient.from_file(args.config),args.request_id,args.output)))
    except (ValueError,KeyError,OSError,DomainError):
        print(json.dumps({'error':'synthetic_native_worker_stopped_recover_pending_state'}),file=sys.stderr);raise SystemExit(1) from None

if __name__=='__main__':main()
