"""Independent native due checks; records concerns, never executes agent work."""
import argparse
from contextlib import contextmanager
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import stat
import sys
import time
import urllib.error
import uuid

from .native_client import NativeClient
from .store import DomainError

SOURCE_ERRORS=(DomainError,urllib.error.URLError,TimeoutError,OSError)
APPLICATION_ID=0x5541414D


class NativeMonitor:
    def __init__(self,client,environment,state):
        self.client,self.environment,self.state=client,environment,Path(state)
        if not self.state.is_absolute():raise ValueError('Use an absolute private monitor ledger')
        self.state.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        if self.state.parent.stat().st_mode&0o022:raise ValueError('Monitor directory is writable by others')
        try:
            fd=os.open(self.state,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600);os.close(fd)
        except FileExistsError:pass
        self._private_state()
        with self.ledger() as db:
            app=db.execute('PRAGMA application_id').fetchone()[0]
            if app!=APPLICATION_ID and self.state.stat().st_size:raise ValueError('Not an existing native monitor ledger')
            db.execute(f'PRAGMA application_id={APPLICATION_ID}')
            db.executescript('''CREATE TABLE IF NOT EXISTS binding (singleton INTEGER PRIMARY KEY CHECK(singleton=1), identity TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS known (id TEXT PRIMARY KEY, snapshot TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS observation_journal (
                    key TEXT PRIMARY KEY, body TEXT NOT NULL, record_id TEXT,
                    status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                    error INTEGER, uncertain INTEGER NOT NULL DEFAULT 0);''')

    def _private_state(self):
        if self.state.is_symlink():raise ValueError('Monitor ledger cannot be a symlink')
        info=self.state.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077 or info.st_nlink!=1:
            raise ValueError('Monitor ledger must be a private owned regular file')

    @contextmanager
    def ledger(self):
        self._private_state();db=sqlite3.connect(self.state,timeout=10)
        try:
            with db:yield db
        finally:db.close()

    def _identity(self):
        me=self.client.call('identity')
        if me.get('kind')!='listener' or me.get('environment')!=self.environment or not me.get('id') or not isinstance(me.get('agent_ids'),list) or not me['agent_ids'] or any(not isinstance(x,str) for x in me['agent_ids']):
            raise ValueError('Use a scoped listener for this environment')
        if not isinstance(getattr(self.client,'url',None),str):raise ValueError('Monitor source origin is required')
        binding=json.dumps({'origin':self.client.url,'principal':{**me,'agent_ids':sorted(me['agent_ids'])}},sort_keys=True)
        with self.ledger() as db:
            db.execute('BEGIN IMMEDIATE');prior=db.execute('SELECT identity FROM binding WHERE singleton=1').fetchone()
            if prior and prior[0]!=binding:raise ValueError('Source or scope changed; preserve and reconcile the original ledger')
            db.execute('INSERT OR IGNORE INTO binding VALUES (1,?)',(binding,))
        return me

    def _source(self,me):
        result=self.client.call('attention')
        if result.get('source')!='checked' or result.get('principal')!=me or not isinstance(result.get('expectations'),list):raise ValueError('Unverified monitor source')
        checked=datetime.datetime.fromisoformat(result['checked_at'].replace('Z','+00:00'))
        if checked.tzinfo is None:raise ValueError('Source clock requires a timezone')
        rows=result['expectations']
        for row in rows:
            uuid.UUID(row['id'])
            if row.get('agent_id') not in me['agent_ids'] or row.get('environment')!=self.environment or not all(isinstance(row.get(k),list) for k in ['history','revisions','observations']) or not row['revisions']:
                raise ValueError('Foreign or incomplete expectation source')
            if row.get('state') not in ['working','due','investigate','conflict','completed','cancelled']:raise ValueError('Unknown expectation state')
        with self.ledger() as db:known={x[0] for x in db.execute('SELECT id FROM known')}
        if not known.issubset({r['id'] for r in rows}):raise ValueError('Previously known work disappeared from source')
        return rows,checked.timestamp()

    @staticmethod
    def _found(rows,body,me):
        row=next((r for r in rows if r['id']==body['expectation_id']),None)
        if not row:return None
        revision=next((r for r in row['history'] if r['id']==body['revision']),None)
        if not revision:return None
        matches=[o for o in row['observations'] if o.get('agent_id')==row['agent_id'] and o.get('expectation_id')==row['id'] and o.get('payload',{}).get('revision')==body['revision'] and o['payload'].get('next_update_at')==revision['payload']['next_update_at'] and o['payload'].get('observer')==me['id'] and o['payload'].get('observer_kind')=='listener' and o['payload'].get('environment')==me['environment'] and o['payload'].get('condition')=='expected_update_missing']
        if len(matches)>1:raise ValueError('Ambiguous monitor observation')
        if matches:uuid.UUID(matches[0]['id']);return matches[0]['id']
        return None

    def _reconcile(self,rows,me):
        with self.ledger() as db:
            for key,body,receipt,status in db.execute('SELECT key,body,record_id,status FROM observation_journal').fetchall():
                actual=self._found(rows,json.loads(body),me)
                if status=='confirmed' and not actual:raise ValueError('Confirmed observation disappeared from source')
                if actual:
                    if receipt and receipt!=actual:raise ValueError('Observation receipt mismatch; preserve original evidence')
                    if status!='confirmed':db.execute("UPDATE observation_journal SET status='confirmed',record_id=?,error=NULL,uncertain=0 WHERE key=?",(actual,key))

    def _summary(self,checked,error=None):
        with self.ledger() as db:
            known=db.execute('SELECT COUNT(*) FROM known').fetchone()[0]
            persisted=db.execute("SELECT COUNT(*) FROM observation_journal WHERE status='confirmed'").fetchone()[0]
            pending=db.execute("SELECT COUNT(*) FROM observation_journal WHERE status='pending'").fetchone()[0]
            rejected=[{'body':json.loads(b),'status':s,'uncertain':bool(u)} for b,s,u in db.execute("SELECT body,error,uncertain FROM observation_journal WHERE status='rejected'")]
        return {'checked':checked,'source':'checked' if checked else 'unknown','pending_known':known,'persisted':persisted,'pending_receipts':pending,'receipt_errors':rejected,**({'error':error} if error else {})}

    def tick(self):
        try:me=self._identity()
        except SOURCE_ERRORS:return self._summary(False,'source_unavailable')
        try:
            rows,now=self._source(me);self._reconcile(rows,me)
        except (*SOURCE_ERRORS,ValueError,KeyError,TypeError):return self._summary(False,'source_unavailable_or_unverified')
        with self.ledger() as db:
            db.execute('BEGIN IMMEDIATE')
            if not {x[0] for x in db.execute('SELECT id FROM known')}.issubset({r['id'] for r in rows}):
                return self._summary(False,'overlapping_snapshot_missing_known_work')
            db.execute('DELETE FROM known')
            db.executemany('INSERT INTO known VALUES (?,?)',[(r['id'],json.dumps(r,sort_keys=True)) for r in rows if r['state'] not in ['completed','cancelled']])
            for row in rows:
                if len(row['revisions'])!=1:continue
                revision=row['revisions'][0];payload=revision['payload']
                if payload['status']!='working' or not isinstance(payload['next_update_at'],(int,float)) or payload['next_update_at']>now:continue
                body={'expectation_id':row['id'],'revision':revision['id']};encoded=json.dumps(body,sort_keys=True);key=hashlib.sha256(encoded.encode()).hexdigest()
                found=self._found(rows,body,me)
                db.execute('INSERT OR IGNORE INTO observation_journal(key,body,record_id,status) VALUES (?,?,?,?)',(key,encoded,found,'confirmed' if found else 'pending'))
            pending=db.execute("SELECT key,body,record_id FROM observation_journal WHERE status='pending' ORDER BY attempts,rowid LIMIT 32").fetchall()
        for key,body,receipt in pending:
            with self.ledger() as db:started=db.execute("UPDATE observation_journal SET attempts=attempts+1,uncertain=1 WHERE key=? AND status='pending'",(key,)).rowcount
            if not started:continue
            try:
                result=self.client.call('observe_due',json.loads(body));uuid.UUID(result['record_id'])
                if result.get('expectation_id')!=json.loads(body)['expectation_id'] or result.get('visibility') not in ['visible','pending'] or (receipt and receipt!=result['record_id']):raise ValueError('Unverified observation receipt')
                with self.ledger() as db:
                    db.execute('BEGIN IMMEDIATE');current=db.execute('SELECT record_id FROM observation_journal WHERE key=?',(key,)).fetchone()
                    if current and current[0] and current[0]!=result['record_id']:raise ValueError('Concurrent observation receipt mismatch')
                    db.execute("UPDATE observation_journal SET record_id=? WHERE key=?",(result['record_id'],key))
                rows,_=self._source(me);self._reconcile(rows,me)
            except DomainError as error:
                if error.status not in (400,413,415,422):return self._summary(False,'source_unavailable')
                with self.ledger() as db:db.execute("UPDATE observation_journal SET status='rejected',error=?,uncertain=CASE WHEN attempts>1 OR record_id IS NOT NULL THEN 1 ELSE 0 END WHERE key=? AND status='pending'",(error.status,key))
            except (*SOURCE_ERRORS,ValueError,KeyError,TypeError):return self._summary(False,'source_unavailable_or_unverified')
        return self._summary(True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True);parser.add_argument('--environment',required=True);parser.add_argument('--state',required=True)
    parser.add_argument('--interval',type=float,default=60);parser.add_argument('--once',action='store_true');parser.add_argument('--duration',type=float)
    args=parser.parse_args()
    if not math.isfinite(args.interval) or not 1<=args.interval<=3600 or (args.duration is not None and (not math.isfinite(args.duration) or args.duration<=0)):parser.error('Use interval1..3600 seconds and a positive optional duration')
    deadline=time.monotonic()+args.duration if args.duration is not None else math.inf
    try:
        while True:
            result=NativeMonitor(NativeClient.from_file(args.config),args.environment,args.state).tick();print(json.dumps(result),flush=True)
            if args.once or time.monotonic()+args.interval>=deadline:break
            time.sleep(args.interval)
    except (ValueError,KeyError,OSError,sqlite3.Error):
        print(json.dumps({'error':'native_monitor_configuration_or_source_failed_keep_original_ledger'}),file=sys.stderr);raise SystemExit(2) from None
    except KeyboardInterrupt:return
    if not result['checked'] or result['pending_receipts'] or result['receipt_errors']:raise SystemExit(1)

if __name__=='__main__':main()
