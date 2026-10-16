"""Environment-local checks and trusted command dispatch; no shell execution."""
from contextlib import contextmanager
import hashlib
import json
import math
import os
import signal
import uuid
from pathlib import Path
import sqlite3
import subprocess
import time
import urllib.error

from .client import private_read
from .store import DomainError


class Listener:
    def __init__(self, client, environment, routes, state_path, retry_after=60):
        if not isinstance(retry_after,(int,float)) or not math.isfinite(retry_after) or retry_after<0:
            raise ValueError('Invalid retry interval')
        self.client,self.environment,self.routes,self.retry_after=client,environment,Path(routes),retry_after
        self.state=Path(state_path)
        self.state.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        with self.ledger() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS attempts (
                delivery_key TEXT PRIMARY KEY, request_id TEXT NOT NULL,
                attempted REAL NOT NULL, result TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS pending (request_id TEXT PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS claims (request_id TEXT PRIMARY KEY, claim_id TEXT NOT NULL, lease_until REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS recoveries (claim_id TEXT PRIMARY KEY, request_id TEXT NOT NULL, evidence TEXT NOT NULL, created REAL NOT NULL);''')
        self.state.chmod(0o600)

    @contextmanager
    def ledger(self):
        db=sqlite3.connect(self.state,timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def _routes(self):
        routes=private_read(self.routes)
        if not isinstance(routes,dict):
            raise ValueError('Routes must map agent IDs to local argv definitions')
        for route in routes.values():
            if not isinstance(route,dict) or set(route)!={'argv','cwd','timeout'}:
                raise ValueError('Route requires exactly argv, cwd and timeout; shell execution is forbidden')
            argv=route['argv']
            if not isinstance(argv,list) or not argv or len(argv)>64 or any(not isinstance(arg,str) or not arg or len(arg)>8192 for arg in argv):
                raise ValueError('Route argv must be a bounded nonempty string list')
            if not Path(argv[0]).is_absolute() or not Path(argv[0]).is_file():
                raise ValueError('Route executable must be an existing absolute file')
            if not isinstance(route['cwd'],str) or not Path(route['cwd']).is_absolute() or not Path(route['cwd']).is_dir():
                raise ValueError('Route cwd must be an existing absolute directory')
            if not isinstance(route['timeout'],(int,float)) or not math.isfinite(route['timeout']) or not 0<route['timeout']<=300:
                raise ValueError('Route timeout must be between 0 and 300 seconds')
        return routes

    def recover(self,request_id,evidence):
        """Release an expired claim only after the operator reconciles its worker."""
        if not isinstance(evidence,str) or not evidence.strip() or len(evidence)>4000:
            raise ValueError('Recovery requires evidence that the previous worker stopped and its actions were reconciled')
        me=self.client.call('GET','/api/me')
        if me['kind']!='listener' or me['environment']!=self.environment:
            raise ValueError('Listener credential does not match this environment')
        self.client.call('GET','/api/requests/'+request_id)
        with self.ledger() as db:
            db.execute('BEGIN IMMEDIATE')
            claim=db.execute('SELECT claim_id,lease_until FROM claims WHERE request_id=?',(request_id,)).fetchone()
            if not claim:raise ValueError('No outstanding claim')
            if claim[1]>time.time():raise ValueError('Worker claim is still active')
            db.execute('INSERT INTO recoveries VALUES (?,?,?,?)',(claim[0],request_id,evidence,time.time()))
            db.execute('DELETE FROM claims WHERE request_id=? AND claim_id=?',(request_id,claim[0]))
        return {'request_id':request_id,'recovered':True}

    def _run(self,route,payload):
        # A timed-out command and its children must stop before the claim is released.
        process=subprocess.Popen(route['argv'],stdin=subprocess.PIPE,text=True,cwd=route['cwd'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,shell=False,start_new_session=True)
        try:
            process.communicate(json.dumps(payload),timeout=route['timeout'])
            return 'queued' if process.returncode==0 else 'failed'
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL)
            process.communicate()
            return 'failed'
        finally:
            # A launcher can exit while children still hold authority. Stop its
            # remaining process group before releasing the exclusive work claim.
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass

    def tick(self):
        routes=self._routes()
        try:
            me=self.client.call('GET','/api/me')
            if me['kind']!='listener' or me['environment']!=self.environment:
                raise ValueError('Listener credential does not match this environment')
            work=self.client.call('GET','/api/attention')
        except (DomainError,urllib.error.URLError,TimeoutError,OSError):
            with self.ledger() as db:
                known=db.execute('SELECT COUNT(*) FROM pending').fetchone()[0]
            return {'checked':False,'error':'source_unavailable','pending_known':known,'attempts':[]}
        result={'checked':True,'pending':len(work),'attempts':[],'errors':[]}
        with self.ledger() as db:
            db.execute('DELETE FROM pending')
            db.executemany('INSERT INTO pending VALUES (?)',[(item['id'],) for item in work])
        for item in work:
            if item.get('environment')!=self.environment:
                result['errors'].append({'request_id':item['id'],'code':'environment_mismatch'})
                continue
            route=routes.get(item['agent_id'])
            if not route:
                result['errors'].append({'request_id':item['id'],'code':'route_missing'})
                continue
            responses=[r['id'] for r in item['responses'] if not r['stale']]
            if not responses:
                continue
            payload={'request_id':item['id'],'agent_id':item['agent_id'],'revision':item['revision'],'response_ids':responses,'answer_revision':item['answer_revision'],'action_revision':item['action_revision']}
            key=hashlib.sha256(json.dumps([payload,route],sort_keys=True).encode()).hexdigest()
            now=time.time()
            with self.ledger() as db:
                db.execute('BEGIN IMMEDIATE')
                claim=db.execute('SELECT claim_id,lease_until FROM claims WHERE request_id=?',(item['id'],)).fetchone()
                if claim:
                    result['errors'].append({'request_id':item['id'],'code':'worker_active' if claim[1]>now else 'dispatch_recovery_required'})
                    continue
                prior=db.execute('SELECT attempted,result FROM attempts WHERE delivery_key=?',(key,)).fetchone()
                if prior and (now-prior[0]<self.retry_after or (item['status']=='blocked' and item['progress'] and item['progress'][-1]['created']>=prior[0])):
                    continue
                claim_id=str(uuid.uuid4())
                db.execute('INSERT INTO claims VALUES (?,?,?)',(item['id'],claim_id,now+route['timeout']+30))
                db.execute('INSERT INTO attempts VALUES (?,?,?,?) ON CONFLICT(delivery_key) DO UPDATE SET attempted=excluded.attempted,result=excluded.result',(key,item['id'],now,'dispatching'))
            try:
                outcome=self._run(route,payload)
            except OSError:
                outcome='failed'
            try:
                observed=self.client.call('GET','/api/requests/'+item['id'])
                if observed['revision']==item['revision'] and observed['answer_revision']==item['answer_revision'] and observed['status'] in ('resumed','completed','blocked') and observed['progress'] and observed['progress'][-1]['created']>=now:
                    outcome=observed['status']
            except (DomainError,urllib.error.URLError,TimeoutError,OSError):
                if outcome!='failed':outcome='delivery_unverified'
            with self.ledger() as db:
                db.execute('BEGIN IMMEDIATE')
                held=db.execute('SELECT 1 FROM claims WHERE request_id=? AND claim_id=?',(item['id'],claim_id)).fetchone()
                if held:
                    db.execute('UPDATE attempts SET result=? WHERE delivery_key=?',(outcome,key))
                    db.execute('DELETE FROM claims WHERE request_id=? AND claim_id=?',(item['id'],claim_id))
                else:
                    outcome='claim_replaced_reconcile_required'
            result['attempts'].append({'request_id':item['id'],'result':outcome})
        return result
