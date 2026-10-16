"""Environment-local native pickup. Trusted argv routes receive references only."""
import argparse
import hashlib
import json
import sys
import time
import urllib.error
import uuid

from .listener import Listener
from .native_client import NativeClient
from .store import DomainError

SOURCE_ERRORS=(DomainError,urllib.error.URLError,TimeoutError,OSError)


class NativeListener(Listener):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        with self.ledger() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS binding (singleton INTEGER PRIMARY KEY CHECK(singleton=1), identity TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS native_attempts (delivery_key TEXT PRIMARY KEY, count INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS receipt_outbox (intent_id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS receipt_confirmed (intent_id TEXT PRIMARY KEY);''')

    def _identity(self):
        me=self.client.call('identity')
        if me.get('kind')!='listener' or me.get('environment')!=self.environment or not me.get('id') or not isinstance(me.get('agent_ids'),list) or not me['agent_ids']:
            raise ValueError('Listener credential does not match this environment or explicit agent set')
        binding=json.dumps({**me,'agent_ids':sorted(me['agent_ids'])},sort_keys=True)
        with self.ledger() as db:
            db.execute('BEGIN IMMEDIATE')
            prior=db.execute('SELECT identity FROM binding WHERE singleton=1').fetchone()
            if prior and prior[0]!=binding:raise ValueError('Listener identity or scope changed; reconcile the retained environment ledger')
            db.execute('INSERT OR IGNORE INTO binding VALUES (1,?)',(binding,))
        return me

    def _work(self,me,request_id=None):
        work=self.client.call('recover',{'request_id':request_id}) if request_id else self.client.call('attention')
        if work.get('source')!='checked' or work.get('principal')!=me or not isinstance(work.get('requests'),list):raise ValueError('Unverified listener source')
        rows=work['requests']
        for row in rows:
            uuid.UUID(row['id'])
            if row['agent_id'] not in me['agent_ids'] or (request_id and row['id']!=request_id):raise ValueError('Foreign request in listener source')
        if request_id and len(rows)!=1:raise ValueError('Owned request not found')
        return rows

    def _flush(self):
        with self.ledger() as db:pending=db.execute('SELECT intent_id,body FROM receipt_outbox').fetchall()
        for intent,body in pending:
            result=self.client.call('delivery',json.loads(body))
            if result.get('visibility')=='visible':
                with self.ledger() as db:
                    db.execute('INSERT OR IGNORE INTO receipt_confirmed VALUES (?)',(intent,))
                    db.execute('DELETE FROM receipt_outbox WHERE intent_id=?',(intent,))

    def _receipt(self,item,revision,answers,disposition,evidence,intent):
        body={'intent_id':intent,'request_id':item['id'],'revision':revision,'answers':answers,'disposition':disposition,'evidence':evidence}
        with self.ledger() as db:
            if db.execute('SELECT 1 FROM receipt_confirmed WHERE intent_id=?',(intent,)).fetchone():return
            db.execute('INSERT OR IGNORE INTO receipt_outbox VALUES (?,?)',(intent,json.dumps(body,sort_keys=True)))
        try:self._flush()
        except SOURCE_ERRORS:pass # Exact receipt remains durable for readback/retry.

    def recover(self,request_id,evidence):
        if not isinstance(evidence,str) or not evidence.strip() or len(evidence)>4000:raise ValueError('Recovery requires evidence that the previous worker stopped and its actions were reconciled')
        self._work(self._identity(),request_id)
        with self.ledger() as db:
            db.execute('BEGIN IMMEDIATE')
            claim=db.execute('SELECT claim_id,lease_until FROM claims WHERE request_id=?',(request_id,)).fetchone()
            if not claim:raise ValueError('No outstanding claim')
            if claim[1]>time.time():raise ValueError('Worker claim is still active')
            db.execute('INSERT INTO recoveries VALUES (?,?,?,?)',(claim[0],request_id,evidence,time.time()))
            db.execute('DELETE FROM claims WHERE request_id=? AND claim_id=?',(request_id,claim[0]))
        return {'request_id':request_id,'recovered':True}

    def tick(self):
        routes=self._routes()
        try:
            me=self._identity();rows=self._work(me);self._flush()
        except SOURCE_ERRORS:
            with self.ledger() as db:known=db.execute('SELECT COUNT(*) FROM pending').fetchone()[0]
            return {'checked':False,'error':'source_unavailable','pending_known':known,'attempts':[]}
        pending=[r for r in rows if r['state'] not in ('resumed','completed')]
        result={'checked':True,'pending':len(pending),'attempts':[],'errors':[]}
        with self.ledger() as db:
            db.execute('DELETE FROM pending');db.executemany('INSERT INTO pending VALUES (?)',[(r['id'],) for r in pending])
        for item in pending:
            if len(item['revisions'])!=1:
                result['errors'].append({'request_id':item['id'],'code':'question_conflict_reconcile'});continue
            revision=item['revisions'][0]['id'];answers=sorted(a['id'] for a in item['answers'])
            if not answers:continue
            route=routes.get(item['agent_id'])
            if not route:
                result['errors'].append({'request_id':item['id'],'code':'route_missing'})
                self._receipt(item,revision,answers,'blocked','Configure a trusted local route for this agent, then check again. No agent progress was observed.','missing:'+item['id']+':'+revision+':'+hashlib.sha256(json.dumps(answers).encode()).hexdigest()[:16]);continue
            payload={'request_id':item['id'],'agent_id':item['agent_id'],'revision':revision,'answer_ids':answers}
            snapshot=[payload,sorted(a['id'] for a in item['actions']),sorted(a['id'] for a in item['settlements']),route]
            key=hashlib.sha256(json.dumps(snapshot,sort_keys=True).encode()).hexdigest();now=time.time()
            with self.ledger() as db:
                db.execute('BEGIN IMMEDIATE')
                claim=db.execute('SELECT claim_id,lease_until FROM claims WHERE request_id=?',(item['id'],)).fetchone()
                prior=db.execute('SELECT attempted,result FROM attempts WHERE delivery_key=?',(key,)).fetchone()
                count=db.execute('SELECT count FROM native_attempts WHERE delivery_key=?',(key,)).fetchone()
                if claim:code='worker_active' if claim[1]>now else 'dispatch_recovery_required'
                elif count and count[0]>=3:code='retry_limit_repair_route_or_reconcile'
                else:code=None
                if code:
                    result['errors'].append({'request_id':item['id'],'code':code});continue
                if prior and (now-prior[0]<self.retry_after or prior[1] in ('resumed','completed')):continue
                claim_id=str(uuid.uuid4())
                db.execute('INSERT INTO claims VALUES (?,?,?)',(item['id'],claim_id,now+route['timeout']+30))
                db.execute('INSERT INTO attempts VALUES (?,?,?,?) ON CONFLICT(delivery_key) DO UPDATE SET attempted=excluded.attempted,result=excluded.result',(key,item['id'],now,'dispatching'))
                db.execute('INSERT INTO native_attempts VALUES (?,1) ON CONFLICT(delivery_key) DO UPDATE SET count=count+1',(key,))
            try:outcome=self._run(route,payload)
            except OSError:outcome='failed'
            disposition=outcome
            old_progress={p['id'] for p in item['progress']}
            try:
                observed=self._work(me,item['id'])[0]
                same=len(observed['revisions'])==1 and observed['revisions'][0]['id']==revision and sorted(a['id'] for a in observed['answers'])==answers
                fresh=[p for p in observed['progress'] if p['id'] not in old_progress] if same else []
                for stage in ('completed','resumed','acknowledged'):
                    if any(p['payload']['stage']==stage for p in fresh):outcome=stage;break
            except SOURCE_ERRORS:
                outcome='delivery_unverified';disposition='unknown'
            with self.ledger() as db:
                db.execute('BEGIN IMMEDIATE')
                held=db.execute('SELECT 1 FROM claims WHERE request_id=? AND claim_id=?',(item['id'],claim_id)).fetchone()
                if held:
                    db.execute('UPDATE attempts SET result=? WHERE delivery_key=?',(outcome,key));db.execute('DELETE FROM claims WHERE request_id=? AND claim_id=?',(item['id'],claim_id))
                else:outcome='claim_replaced_reconcile_required';disposition='unknown'
            evidence={'queued':'Trusted local launcher returned zero. This receipt does not assert agent progress.','failed':'Local route failed or timed out. Repair the trusted route and check retained actions before retrying.','unknown':'Delivery or source could not be verified. Inspect the previous worker and retained actions before retrying.'}[disposition]
            self._receipt(item,revision,answers,disposition,evidence,claim_id)
            result['attempts'].append({'request_id':item['id'],'result':outcome})
        repairs={'dispatch_recovery_required':'Verify the previous process stopped and reconcile its effects, then use recover with that evidence before another dispatch.',
                 'retry_limit_repair_route_or_reconcile':'Three attempts produced no fresh agent progress. Repair the trusted route or reconcile the retained work before another work or route snapshot can dispatch.'}
        for error in result['errors']:
            if error['code'] not in repairs:continue
            item=next(r for r in pending if r['id']==error['request_id'])
            revision=item['revisions'][0]['id'];answers=sorted(a['id'] for a in item['answers'])
            intent='gap:'+hashlib.sha256(json.dumps([item['id'],revision,answers,error['code'],routes.get(item['agent_id'])],sort_keys=True).encode()).hexdigest()
            self._receipt(item,revision,answers,'blocked',repairs[error['code']],intent)
        with self.ledger() as db:result['receipts_pending']=db.execute('SELECT COUNT(*) FROM receipt_outbox').fetchone()[0]
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True);parser.add_argument('--environment',required=True)
    parser.add_argument('--routes',required=True);parser.add_argument('--state',required=True)
    sub=parser.add_subparsers(dest='command',required=True)
    listen=sub.add_parser('listen');listen.add_argument('--once',action='store_true');listen.add_argument('--interval',type=float,default=30)
    recover=sub.add_parser('recover');recover.add_argument('--request-id',required=True);recover.add_argument('--evidence',required=True)
    args=parser.parse_args()
    if args.command=='listen' and not 1<=args.interval<=3600:parser.error('Interval must be between 1 and 3600 seconds')
    try:
        while True:
            # Reopen private profile each tick so explicitly renewed grants can rotate safely.
            listener=NativeListener(NativeClient.from_file(args.config),args.environment,args.routes,args.state)
            result=listener.recover(args.request_id,args.evidence) if args.command=='recover' else listener.tick()
            print(json.dumps(result),flush=True)
            if args.command=='recover' or args.once:break
            time.sleep(args.interval)
    except (ValueError,KeyError,OSError,DomainError):
        print(json.dumps({'error':'native_listener_failed_pending_work_retained'}),file=sys.stderr);raise SystemExit(1) from None

if __name__=='__main__':main()
