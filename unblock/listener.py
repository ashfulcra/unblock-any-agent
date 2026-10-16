"""Environment-local checks and trusted command dispatch; no shell execution."""
from contextlib import contextmanager
import hashlib
import json
import math
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
                CREATE TABLE IF NOT EXISTS pending (request_id TEXT PRIMARY KEY);''')
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
            payload={'request_id':item['id'],'agent_id':item['agent_id'],'revision':item['revision'],'response_ids':responses}
            key=hashlib.sha256(json.dumps([payload,route],sort_keys=True).encode()).hexdigest()
            now=time.time()
            with self.ledger() as db:
                db.execute('BEGIN IMMEDIATE')
                prior=db.execute('SELECT attempted,result FROM attempts WHERE delivery_key=?',(key,)).fetchone()
                if prior and (now-prior[0]<self.retry_after or (item['status']=='blocked' and item['progress'] and item['progress'][-1]['created']>=prior[0])):
                    continue
                db.execute('INSERT INTO attempts VALUES (?,?,?,?) ON CONFLICT(delivery_key) DO UPDATE SET attempted=excluded.attempted,result=excluded.result',(key,item['id'],now,'dispatching'))
            try:
                process=subprocess.run(route['argv'],input=json.dumps(payload),text=True,cwd=route['cwd'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=route['timeout'],shell=False)
                outcome='queued' if process.returncode==0 else 'failed'
            except (OSError,subprocess.TimeoutExpired):
                outcome='failed'
            try:
                observed=self.client.call('GET','/api/requests/'+item['id'])
                if observed['revision']==item['revision'] and observed['status'] in ('resumed','completed','blocked'):
                    outcome=observed['status']
            except (DomainError,urllib.error.URLError,TimeoutError,OSError):
                if outcome!='failed':outcome='delivery_unverified'
            with self.ledger() as db:
                db.execute('UPDATE attempts SET result=? WHERE delivery_key=?',(outcome,key))
            result['attempts'].append({'request_id':item['id'],'result':outcome})
        return result
