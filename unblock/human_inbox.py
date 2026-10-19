"""Explicit human inbox, separate from worker grants and the renewal operator."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import uuid

from .client import private_read
from .store import DomainError


def reference(value):
    try:return str(uuid.UUID(value))
    except (ValueError,TypeError,AttributeError):raise DomainError('invalid_decision_reference') from None


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)


def excerpt(value,limit):
    text=' '.join(value.split())
    return text if len(text)<=limit else text[:limit].rsplit(' ',1)[0]+'…'


def snapshot(row):
    value={'request_id':row['id'],'revisions':sorted(r['id'] for r in row['revisions']),
           'answers':sorted(a['id'] for a in row['answers']),
           'uncertain_actions':sorted(a['id'] for a in row['uncertain_actions'])}
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def cli_token():
    executable=shutil.which('fulcra-api')
    if not executable:raise DomainError('human_cli_sign_in_required',401)
    try:r=subprocess.run([executable,'auth','print-access-token'],capture_output=True,text=True,timeout=30)
    except (OSError,subprocess.TimeoutExpired):raise DomainError('human_cli_sign_in_required',401) from None
    token=r.stdout.strip()
    if r.returncode or not re.fullmatch(r'[A-Za-z0-9_.-]{1,20000}',token):raise DomainError('human_cli_sign_in_required',401)
    return token


def request_json(url,headers,body=None):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*_):return None
    request=urllib.request.Request(url,headers=headers,data=json.dumps(body).encode() if body is not None else None,method='POST' if body is not None else 'GET')
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect()).open(request,timeout=20) as response:
            data=response.read(4*1024*1024+1)
            if len(data)>4*1024*1024:raise DomainError('human_source_unavailable',503)
            return json.loads(data)
    except urllib.error.HTTPError as error:
        with error:
            status=error.code
            try:detail=json.loads(error.read(65537))
            except (ValueError,OSError):detail={}
        if body is not None and 400<=status<500 and isinstance(detail,dict) and detail.get('outcome')=='rejected':
            failure=DomainError('decision_changed_review_again' if detail.get('error')=='Decision changed; review again' else 'human_answer_rejected',status)
            failure.write_outcome='rejected'
            raise failure from None
        raise DomainError('human_auth_required' if status in (401,403) else 'human_source_unavailable',status if status in (401,403) else 503) from None
    except (urllib.error.URLError,TimeoutError,OSError,ValueError):raise DomainError('human_source_unavailable',503) from None


def platform_request(token,path):
    return request_json('https://api.fulcradynamics.com'+path,{'Authorization':'Bearer '+token})


def dashboard_request(origin,token,operation,data=None):
    if operation not in ('attention','answer'):raise DomainError('human_operation_not_permitted',403)
    return request_json(origin+'/api/unblock/'+operation,{'Cookie':'fulcra_access_token='+token,'Origin':origin,'Content-Type':'application/json'},data)


class HumanInbox:
    def __init__(self,project_id,owner_id,state,*,token_provider=cli_token,platform=platform_request,dashboard=dashboard_request):
        self.project_id,self.owner_id=reference(project_id),reference(owner_id)
        self.workspace_id=hashlib.sha256((self.owner_id+':'+self.project_id).encode()).hexdigest()
        self.state=Path(state)
        if not self.state.is_absolute() or self.state.is_symlink():raise ValueError('Human journal requires an absolute private regular file')
        self.state.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        try:
            fd=os.open(self.state,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
        except FileExistsError:pass
        info=self.state.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077 or info.st_nlink!=1:raise ValueError('Human journal must be private, owned and unlinked')
        self.token_provider,self.platform,self.dashboard=token_provider,platform,dashboard
        binding=canonical({'project_id':self.project_id,'owner_id':self.owner_id})
        with self.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY,value TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS answers (intent TEXT PRIMARY KEY,body TEXT NOT NULL,status TEXT NOT NULL,record_id TEXT)')
            prior=db.execute("SELECT value FROM meta WHERE key='binding'").fetchone()
            if prior and prior[0]!=binding:raise ValueError('Human journal belongs to another owner or project')
            db.execute("INSERT OR IGNORE INTO meta VALUES ('binding',?)",(binding,))

    @classmethod
    def from_file(cls,path):
        if not Path(path).is_absolute():raise ValueError('Explicit private human profile required')
        p=private_read(path)
        if p.get('transport')!='fulcra-human' or set(p)!={'transport','project_id','owner_id','state_path'}:raise ValueError('Human profile contains only its approved project, owner and private journal path')
        return cls(p['project_id'],p['owner_id'],p['state_path'])

    @contextmanager
    def db(self):
        db=sqlite3.connect(self.state,timeout=10)
        try:
            db.execute('PRAGMA synchronous=FULL')
            with db:yield db
        finally:db.close()

    def connect(self):
        token=self.token_provider()
        user=self.platform(token,'/user/v1alpha1/info')
        if not isinstance(user,dict):raise DomainError('human_source_unavailable',503)
        if user.get('userid')!=self.owner_id:raise DomainError('human_owner_identity_changed',403)
        project=self.platform(token,'/user/v1/deploy/project/'+self.project_id)
        if not isinstance(project,dict):raise DomainError('human_source_unavailable',503)
        domain=project.get('domain','')
        if project.get('id')!=self.project_id or not isinstance(domain,str) or not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.my\.fulcra\.ai',domain):raise DomainError('human_owned_deployment_unverified',403)
        origin='https://'+domain
        with self.db() as db:
            prior=db.execute("SELECT value FROM meta WHERE key='origin'").fetchone()
            if prior and prior[0]!=origin:raise DomainError('human_deployment_origin_changed',403)
            db.execute("INSERT OR IGNORE INTO meta VALUES ('origin',?)",(origin,))
        return origin,token

    def checked(self,connection):
        data=self.dashboard(*connection,'attention')
        try:
            if data['source']!='checked' or data['principal']!={'kind':'owner','id':self.owner_id} or not isinstance(data['requests'],list):raise ValueError()
            for row in data['requests']:
                reference(row['id']);snapshot(row)
                if not row['revisions'] or any(not isinstance(r['payload']['need'],str) for r in row['revisions']):raise ValueError()
            if not isinstance(data['checked_at'],str):raise ValueError()
        except (KeyError,ValueError,TypeError):raise DomainError('human_source_unavailable',503) from None
        with self.db() as db:db.execute("INSERT OR REPLACE INTO meta VALUES ('last_known',?)",(canonical(data),))
        return data

    def pending_answers(self):
        with self.db() as db:rows=db.execute("SELECT body FROM answers WHERE status='pending' ORDER BY rowid").fetchall()
        return [json.loads(row[0]) for row in rows]

    @contextmanager
    def answer_lock(self):
        # Serialize first attempts across processes without holding a DB transaction
        # over network I/O. A crashed writer leaves its durable pending intent.
        path=self.state.with_name(self.state.name+'.answer-lock')
        fd=os.open(path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:
            info=os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077 or info.st_nlink!=1:raise ValueError('Human answer lock must be private and owned')
            fcntl.flock(fd,fcntl.LOCK_EX)
            try:yield
            finally:fcntl.flock(fd,fcntl.LOCK_UN)
        finally:os.close(fd)

    def inbox(self,query='',agent_id='',include_completed=False):
        if not isinstance(query,str) or len(query)>400 or not isinstance(agent_id,str) or len(agent_id)>100:raise DomainError('invalid_inbox_filter')
        try:data=self.checked(self.connect());source='checked';error=None
        except DomainError as failure:
            if failure.status!=503:raise
            source='unavailable';error=failure.code
            with self.db() as db:known=db.execute("SELECT value FROM meta WHERE key='last_known'").fetchone()
            data=json.loads(known[0]) if known else {'requests':[],'grants':[],'checked_at':None}
        names={g['agent_id']:g.get('name') or g['agent_id'] for g in reversed(data.get('grants',[])) if g.get('kind','agent')=='agent'}
        rows=data['requests'];items=[]
        for row in rows:
            if not include_completed and row['state'] in ('completed','withdrawn'):continue
            if agent_id and row['agent_id']!=agent_id:continue
            q=row['revisions'][0]['payload'];name=names.get(row['agent_id'],row['agent_id'])
            if not all(t in (name+' '+row['agent_id']+' '+canonical(q)).casefold() for t in query.casefold().split()):continue
            items.append({'request_id':row['id'],'agent_id':row['agent_id'],'agent_name':name,'created_at':row.get('created_at'),'state':row['state'],'decision':excerpt(q['need'],160),'context':excerpt(q.get('context',''),280),'recommendation':excerpt(q.get('recommendation',''),200),'question_versions':len(row['revisions'])})
        items.sort(key=lambda r:(r['created_at'] is None,r['created_at'] or '',r['agent_name']))
        counts={'needs_you':sum(r['state'] in ('needs_you','conflict','answer_conflict','uncertain_action') for r in rows),'with_agents':sum(r['state'] in ('awaiting_pickup','acknowledged','resumed') for r in rows),'done':sum(r['state'] in ('completed','withdrawn') for r in rows)} if source=='checked' else None
        return {'workspace_id':self.workspace_id,'source':source,'last_known':source!='checked' and bool(data['checked_at']),'checked_at':data['checked_at'],'counts':counts,'items':items,'pending_answers':self.pending_answers(),'error':error}

    def get_decision(self,request_id):
        rid=reference(request_id);data=self.checked(self.connect())
        row=next((r for r in data['requests'] if r['id']==rid),None)
        if row is None:raise DomainError('decision_not_found',404)
        name=next((g.get('name') for g in data.get('grants',[]) if g['agent_id']==row['agent_id']),row['agent_id'])
        return {'workspace_id':self.workspace_id,'source':'checked','checked_at':data['checked_at'],'agent_name':name,'request':row,'reviewed_snapshot':snapshot(row),'can_answer':len(row['revisions'])==1 and row['state'] not in ('completed','withdrawn')}

    def answer_decision(self,request_id,revision,reviewed_snapshot,answer,intent_id):
        with self.answer_lock():
            return self._answer_decision(request_id,revision,reviewed_snapshot,answer,intent_id)

    def _answer_decision(self,request_id,revision,reviewed_snapshot,answer,intent_id):
        rid,rev=reference(request_id),reference(revision)
        if not isinstance(answer,str) or not answer.strip() or len(answer)>16000 or not isinstance(intent_id,str) or not intent_id.strip() or len(intent_id)>160 or not re.fullmatch(r'[a-f0-9]{64}',reviewed_snapshot):raise DomainError('invalid_human_answer')
        saved={'request_id':rid,'revision':rev,'reviewed_snapshot':reviewed_snapshot,'answer':answer,'intent_id':intent_id}
        encoded=canonical(saved)
        with self.db() as db:prior=db.execute('SELECT body,status,record_id FROM answers WHERE intent=?',(intent_id,)).fetchone()
        if prior and prior[0]!=encoded:raise DomainError('answer_intent_has_different_fields',409)
        if prior and prior[1]=='rejected':return {'visibility':'rejected','intent_id':intent_id,'request_id':rid,'reason':'This attempt was definitely rejected. Review the current decision and use a new intent.'}
        connection=self.connect();data=self.checked(connection)
        row=next((r for r in data['requests'] if r['id']==rid),None)
        if row is None:raise DomainError('decision_not_found',404)

        def observed(current):
            return next((a for a in [*current['answers'],*current['stale_answers']] if a.get('intent_id')==intent_id and a['payload'].get('revision')==rev and a['payload'].get('answer')==answer and a['payload'].get('responder')==self.owner_id),None)

        def finish(current,record):
            with self.db() as db:db.execute("UPDATE answers SET status='verified',record_id=? WHERE intent=?",(record['id'],intent_id))
            return {'visibility':'visible','record_id':record['id'],'request_id':rid,'revision':rev,'progress':current['state'],'current_question':len(current['revisions'])==1 and current['revisions'][0]['id']==rev,'intent_id':intent_id}

        match=observed(row)
        if prior and match:return finish(row,match)
        current=len(row['revisions'])==1 and row['revisions'][0]['id']==rev and snapshot(row)==reviewed_snapshot and row['state'] not in ('completed','withdrawn')
        if not current:
            if prior:return {'visibility':'pending','intent_id':intent_id,'request_id':rid,'reason':'Question or answers changed; original uncertain answer retained for reconciliation.'}
            raise DomainError('decision_changed_review_again',409)
        with self.db() as db:
            db.execute('INSERT OR IGNORE INTO answers VALUES (?,?,?,NULL)',(intent_id,encoded,'pending'))
            if db.execute('SELECT body FROM answers WHERE intent=?',(intent_id,)).fetchone()[0]!=encoded:raise DomainError('answer_intent_has_different_fields',409)
        try:
            self.dashboard(*connection,'answer',saved)
            current_data=self.checked(connection);row=next(r for r in current_data['requests'] if r['id']==rid)
            match=observed(row)
            if match:return finish(row,match)
        except DomainError as failure:
            if not prior and getattr(failure,'write_outcome',None)=='rejected':
                with self.db() as db:db.execute("UPDATE answers SET status='rejected' WHERE intent=?",(intent_id,))
                return {'visibility':'rejected','intent_id':intent_id,'request_id':rid,'reason':'Answer was rejected before publication. Review the current decision before sending again.'}
        except (OSError,TimeoutError,ValueError,KeyError,StopIteration):pass
        return {'visibility':'pending','intent_id':intent_id,'request_id':rid,'reason':'Write outcome remains uncertain. Retry the same saved answer; no agent progress is implied.'}
