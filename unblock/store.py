"""Authenticated, transactional local work state. Not a production OAuth server."""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import secrets
import sqlite3
import time
import uuid


class DomainError(Exception):
    def __init__(self, code, status=400):
        super().__init__(code)
        self.code, self.status = code, status


@dataclass(frozen=True)
class Principal:
    id: str
    kind: str
    owner_id: str
    workspace_id: str | None
    environment: str


def ident():
    return str(uuid.uuid4())


def text(value, limit=4000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise DomainError('invalid_text')
    return value


def context_json(value):
    if not isinstance(value, dict):
        raise DomainError('context_must_be_object')
    result = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
    if len(result.encode()) > 32768:
        raise DomainError('context_too_large')
    return result


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.transaction() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS principals (
                    id TEXT PRIMARY KEY, kind TEXT NOT NULL, owner_id TEXT NOT NULL,
                    workspace_id TEXT, name TEXT NOT NULL, environment TEXT NOT NULL,
                    token_hash TEXT UNIQUE NOT NULL, revoked INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS workspaces (id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, name TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS requests (
                    id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, agent_id TEXT NOT NULL,
                    need_key TEXT NOT NULL, revision TEXT NOT NULL, need TEXT NOT NULL,
                    context TEXT NOT NULL, status TEXT NOT NULL, created REAL NOT NULL,
                    UNIQUE(agent_id,need_key)
                );
                CREATE TABLE IF NOT EXISTS versions (
                    id TEXT PRIMARY KEY, request_id TEXT NOT NULL, need TEXT NOT NULL,
                    context TEXT NOT NULL, created REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS responses (
                    id TEXT PRIMARY KEY, request_id TEXT NOT NULL, revision TEXT NOT NULL,
                    actor_id TEXT NOT NULL, answer TEXT NOT NULL, response_key TEXT NOT NULL,
                    created REAL NOT NULL, UNIQUE(request_id,actor_id,response_key)
                );
                CREATE TABLE IF NOT EXISTS progress (
                    id TEXT PRIMARY KEY, request_id TEXT NOT NULL, response_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL, state TEXT NOT NULL, evidence TEXT NOT NULL, created REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS actions (
                    id TEXT PRIMARY KEY, request_id TEXT NOT NULL, agent_id TEXT NOT NULL,
                    action_key TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL,
                    evidence TEXT, UNIQUE(agent_id,action_key)
                );
            ''')
        self.path.chmod(0o600)

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('BEGIN IMMEDIATE')
            yield db
            if db.in_transaction:
                db.commit()
        except BaseException:
            if db.in_transaction:
                db.rollback()
            raise
        finally:
            db.close()

    def _principal(self, row):
        return Principal(**{field: row[field] for field in Principal.__dataclass_fields__})

    def _live(self, db, actor, kind=None):
        row = db.execute('SELECT * FROM principals WHERE id=? AND revoked=0', (actor.id,)).fetchone()
        if not row or self._principal(row) != actor:
            raise DomainError('credential_revoked', 401)
        if kind and actor.kind != kind:
            raise DomainError('role_forbidden', 403)

    def bootstrap_owner(self, name):
        """Local administrative operation; never exposed as an anonymous HTTP API."""
        pid, token = ident(), secrets.token_urlsafe(32)
        with self.transaction() as db:
            db.execute('INSERT INTO principals VALUES (?,?,?,?,?,?,?,0)', (pid, 'owner', pid, None, text(name,128), '', hashlib.sha256(token.encode()).hexdigest()))
        return {'id': pid, 'token': token}

    def authenticate(self, token):
        if not isinstance(token, str) or len(token) > 512:
            raise DomainError('invalid_credential', 401)
        with self.transaction() as db:
            row = db.execute('SELECT * FROM principals WHERE token_hash=? AND revoked=0', (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
            if not row:
                raise DomainError('invalid_credential', 401)
            return self._principal(row)

    def _workspace(self, db, actor, workspace_id):
        self._live(db, actor)
        row = db.execute('SELECT * FROM workspaces WHERE id=? AND owner_id=?', (workspace_id,actor.owner_id)).fetchone()
        if not row or (actor.kind != 'owner' and actor.workspace_id != workspace_id):
            raise DomainError('workspace_not_found', 404)
        return row

    def create_workspace(self, actor, name):
        with self.transaction() as db:
            self._live(db,actor,'owner')
            wid=ident()
            db.execute('INSERT INTO workspaces VALUES (?,?,?)',(wid,actor.id,text(name,128)))
        return {'id':wid,'name':name}

    def enroll(self, actor, workspace_id, name, kind, environment):
        if kind not in ('agent','listener'):
            raise DomainError('invalid_role')
        with self.transaction() as db:
            self._live(db,actor,'owner')
            self._workspace(db,actor,workspace_id)
            pid,token=ident(),secrets.token_urlsafe(32)
            db.execute('INSERT INTO principals VALUES (?,?,?,?,?,?,?,0)',(pid,kind,actor.id,workspace_id,text(name,128),text(environment,128),hashlib.sha256(token.encode()).hexdigest()))
        return {'id':pid,'name':name,'kind':kind,'environment':environment,'workspace_id':workspace_id,'token':token}

    def revoke(self, actor, principal_id):
        with self.transaction() as db:
            self._live(db,actor,'owner')
            target=db.execute('SELECT * FROM principals WHERE id=? AND owner_id=? AND kind!=?',(principal_id,actor.id,'owner')).fetchone()
            if not target:
                raise DomainError('grant_not_found',404)
            db.execute('UPDATE principals SET revoked=1 WHERE id=?',(principal_id,))
        return {'revoked':principal_id}

    def _request(self, db, actor, request_id):
        self._live(db,actor)
        row=db.execute('SELECT r.*,p.environment FROM requests r JOIN principals p ON p.id=r.agent_id WHERE r.id=?',(request_id,)).fetchone()
        if not row:
            raise DomainError('request_not_found',404)
        self._workspace(db,actor,row['workspace_id'])
        if (actor.kind=='agent' and row['agent_id']!=actor.id) or (actor.kind=='listener' and row['environment']!=actor.environment):
            raise DomainError('request_not_found',404)
        return row

    def _work(self, db, row):
        result=dict(row)
        result['context']=json.loads(result['context'])
        result['responses']=[{**dict(r),'stale':r['revision']!=row['revision']} for r in db.execute('SELECT * FROM responses WHERE request_id=? ORDER BY created,id',(row['id'],))]
        result['conflicting_answers']=len({r['answer'] for r in result['responses'] if not r['stale']})>1
        result['versions']=[{**dict(v),'context':json.loads(v['context'])} for v in db.execute('SELECT * FROM versions WHERE request_id=? ORDER BY created,id',(row['id'],))]
        result['progress']=[dict(p) for p in db.execute('SELECT * FROM progress WHERE request_id=? ORDER BY created,id',(row['id'],))]
        result['actions']=[dict(a) for a in db.execute('SELECT * FROM actions WHERE request_id=?',(row['id'],))]
        return result

    def request_help(self, actor, key, need, context):
        key,need,ctx=text(key,128),text(need),context_json(context)
        with self.transaction() as db:
            self._live(db,actor,'agent')
            self._workspace(db,actor,actor.workspace_id)
            old=db.execute('SELECT * FROM requests WHERE agent_id=? AND need_key=?',(actor.id,key)).fetchone()
            if old:
                # Compare with the original payload, even after an explicit revision.
                original=db.execute('SELECT * FROM versions WHERE request_id=? ORDER BY created,id LIMIT 1',(old['id'],)).fetchone()
                if original['need']!=need or original['context']!=ctx:
                    raise DomainError('logical_key_payload_conflict',409)
                return self._work(db,old)
            rid,rev,now=ident(),ident(),time.time()
            db.execute('INSERT INTO requests VALUES (?,?,?,?,?,?,?,?,?)',(rid,actor.workspace_id,actor.id,key,rev,need,ctx,'open',now))
            db.execute('INSERT INTO versions VALUES (?,?,?,?,?)',(rev,rid,need,ctx,now))
            return self._work(db,db.execute('SELECT * FROM requests WHERE id=?',(rid,)).fetchone())

    def revise_request(self, actor, request_id, need, context):
        need,ctx=text(need),context_json(context)
        with self.transaction() as db:
            row=self._request(db,actor,request_id)
            if actor.kind=='listener':
                raise DomainError('role_forbidden',403)
            rev=ident()
            db.execute('INSERT INTO versions VALUES (?,?,?,?,?)',(rev,request_id,need,ctx,time.time()))
            db.execute('UPDATE requests SET revision=?,need=?,context=?,status=? WHERE id=?',(rev,need,ctx,'open',request_id))
            return self._work(db,db.execute('SELECT * FROM requests WHERE id=?',(request_id,)).fetchone())

    def answer_request(self, actor, request_id, revision, answer, key):
        answer,key=text(answer),text(key,128)
        with self.transaction() as db:
            self._live(db,actor,'owner')
            row=self._request(db,actor,request_id)
            if not db.execute('SELECT 1 FROM versions WHERE id=? AND request_id=?',(revision,request_id)).fetchone():
                raise DomainError('unknown_request_revision',409)
            old=db.execute('SELECT * FROM responses WHERE request_id=? AND actor_id=? AND response_key=?',(request_id,actor.id,key)).fetchone()
            if old:
                if old['answer']!=answer or old['revision']!=revision:
                    raise DomainError('response_key_payload_conflict',409)
                return dict(old)
            response={'id':ident(),'request_id':request_id,'revision':revision,'actor_id':actor.id,'answer':answer,'response_key':key,'created':time.time()}
            db.execute('INSERT INTO responses VALUES (:id,:request_id,:revision,:actor_id,:answer,:response_key,:created)',response)
            if revision==row['revision']:
                db.execute('UPDATE requests SET status=? WHERE id=?',('answered',request_id))
            return response

    def get_request(self, actor, request_id):
        with self.transaction() as db:
            return self._work(db,self._request(db,actor,request_id))

    def get_attention(self, actor):
        with self.transaction() as db:
            self._live(db,actor)
            candidates=db.execute('SELECT r.id FROM requests r JOIN workspaces w ON w.id=r.workspace_id WHERE w.owner_id=? AND r.status NOT IN (?,?) ORDER BY r.created',(actor.owner_id,'completed','resumed')).fetchall()
            work=[]
            for candidate in candidates:
                try:
                    row=self._request(db,actor,candidate['id'])
                except DomainError as error:
                    if error.status==404:
                        continue
                    raise
                if actor.kind=='owner' or row['status']!='open':
                    work.append(self._work(db,row))
            return work

    def get_recent(self, actor):
        with self.transaction() as db:
            self._live(db,actor,'owner')
            rows=db.execute('SELECT r.* FROM requests r JOIN workspaces w ON w.id=r.workspace_id WHERE w.owner_id=? AND r.status IN (?,?) ORDER BY r.created DESC LIMIT 50',(actor.id,'resumed','completed')).fetchall()
            return [self._work(db,row) for row in rows]

    def report_progress(self, actor, request_id, response_id, state, evidence):
        evidence=text(evidence)
        if state not in ('acknowledged','resumed','completed','blocked'):
            raise DomainError('invalid_progress_state')
        with self.transaction() as db:
            self._live(db,actor,'agent')
            row=self._request(db,actor,request_id)
            response=db.execute('SELECT * FROM responses WHERE id=? AND request_id=?',(response_id,request_id)).fetchone()
            if not response or response['revision']!=row['revision']:
                raise DomainError('response_not_current',409)
            if state=='completed' and db.execute('SELECT 1 FROM actions WHERE request_id=? AND status=?',(request_id,'uncertain')).fetchone():
                raise DomainError('uncertain_action_needs_reconciliation',409)
            event={'id':ident(),'request_id':request_id,'response_id':response_id,'agent_id':actor.id,'state':state,'evidence':evidence,'created':time.time()}
            db.execute('INSERT INTO progress VALUES (:id,:request_id,:response_id,:agent_id,:state,:evidence,:created)',event)
            db.execute('UPDATE requests SET status=? WHERE id=?',(state,request_id))
            return event

    def declare_action(self, actor, request_id, key, description):
        key,description=text(key,128),text(description)
        with self.transaction() as db:
            self._live(db,actor,'agent')
            self._request(db,actor,request_id)
            old=db.execute('SELECT * FROM actions WHERE agent_id=? AND action_key=?',(actor.id,key)).fetchone()
            if old:
                if old['request_id']!=request_id or old['description']!=description:
                    raise DomainError('action_key_payload_conflict',409)
                return dict(old)
            action={'id':ident(),'request_id':request_id,'agent_id':actor.id,'action_key':key,'description':description,'status':'uncertain','evidence':None}
            db.execute('INSERT INTO actions VALUES (:id,:request_id,:agent_id,:action_key,:description,:status,:evidence)',action)
            return action

    def settle_action(self, actor, request_id, action_id, evidence):
        evidence=text(evidence)
        with self.transaction() as db:
            self._live(db,actor,'agent')
            self._request(db,actor,request_id)
            action=db.execute('SELECT * FROM actions WHERE id=? AND request_id=? AND agent_id=?',(action_id,request_id,actor.id)).fetchone()
            if not action:
                raise DomainError('action_not_found',404)
            db.execute('UPDATE actions SET status=?,evidence=? WHERE id=?',('confirmed',evidence,action_id))
            return dict(db.execute('SELECT * FROM actions WHERE id=?',(action_id,)).fetchone())
