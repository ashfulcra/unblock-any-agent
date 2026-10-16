"""Explicit fixed-scope native enrollment renewal; no scheduler installation."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import uuid
from .client import private_read,private_write
from .native_client import NativeClient
from .native_owner import NativeOwner,cli_access_token
from .store import DomainError


def replace_private(path,value):
    path=Path(path)
    if path.exists() or path.is_symlink():private_read(path)
    temporary=path.with_name('.'+path.name+'.'+str(uuid.uuid4()))
    private_write(temporary,value)
    try:
        os.replace(temporary,path)
        directory=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if temporary.exists():temporary.unlink()


def file_hash(path):
    path=Path(path)
    if not path.exists() and not path.is_symlink():return None
    private_read(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Renewal:
    def __init__(self,owner,config,state,lease_seconds=3600,renew_before=300,now=time.time):
        if not isinstance(lease_seconds,int) or not 30<=lease_seconds<=3600 or not isinstance(renew_before,int) or not 1<=renew_before<lease_seconds:raise ValueError('Invalid bounded renewal timing')
        self.owner,self.state,self.now=owner,Path(state).absolute(),now
        self.lease,self.margin=lease_seconds,renew_before
        self.config=private_read(config)
        if set(self.config)!={'url','enrollments'} or self.config['url']!=owner.url:raise ValueError('Operator origin must match saved configuration')
        NativeClient(self.config['url'],'validate-origin')
        rows=self.config['enrollments']
        if not isinstance(rows,list) or not 1<=len(rows)<=20:raise ValueError('Select existing enrollment anchors')
        profiles=[];anchors=[]
        for row in rows:
            if not isinstance(row,dict) or set(row)!={'anchor_grant_id','profile'}:raise ValueError('Anchor and private profile required')
            anchors.append(str(uuid.UUID(row['anchor_grant_id'])))
            profile=Path(row['profile'])
            if not profile.is_absolute():raise ValueError('Use an absolute private profile')
            file_hash(profile)
            if profile.resolve() in (self.state.resolve(),Path(config).resolve(),self.state.with_suffix(self.state.suffix+'.lock').resolve()):raise ValueError('Use a separate private profile')
            profiles.append(str(profile.resolve()))
        if len(set(anchors))!=len(anchors) or len(set(profiles))!=len(profiles):raise ValueError('Duplicate anchors or profile targets')
        self.state.parent.mkdir(parents=True,exist_ok=True,mode=0o700)

    @contextmanager
    def _lock(self):
        lock=self.state.with_suffix(self.state.suffix+'.lock')
        fd=os.open(lock,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            info=os.fstat(fd)
            if info.st_uid!=os.getuid() or info.st_mode&0o077:raise ValueError('Operator lock must be private and owned')
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise DomainError('operator_active',409) from None
            yield
        finally:
            fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)

    def _save(self,state):replace_private(self.state,state)

    def _grants(self,state):
        me=self.owner.call('identity')
        if me.get('kind')!='owner' or not me.get('id'):raise DomainError('operator_owner_required',403)
        if state.get('owner_id',me['id'])!=me['id']:raise DomainError('operator_owner_changed',403)
        work=self.owner.call('attention')
        if work.get('source')!='checked' or work.get('principal')!=me or not isinstance(work.get('grants'),list):raise DomainError('operator_source_unverified',503)
        state['owner_id']=me['id']
        return work['grants']

    @staticmethod
    def _scope(grant):
        return {'agent_id':grant['agent_id'],'name':grant['name'],'kind':grant.get('kind','agent'),'environment':grant.get('environment','pilot'),'agent_ids':sorted(grant.get('agent_ids',[grant['agent_id']]))}

    def _anchor(self,grants,anchor,entry):
        matches=[g for g in grants if g['grant_id']==anchor]
        if len(matches)!=1 or matches[0].get('revoked'):raise DomainError('operator_anchor_missing_ambiguous_or_revoked',403)
        scope=self._scope(matches[0])
        if entry.get('scope',scope)!=scope:raise DomainError('operator_scope_changed_reconcile',403)
        if entry.get('latest'):
            current=[g for g in grants if g['grant_id']==entry['latest']['grant_id']]
            if len(current)!=1 or current[0].get('revoked') or self._scope(current[0])!=scope:raise DomainError('operator_latest_grant_missing_or_revoked',403)
        return scope

    def tick(self):
        state={};result={'checked':True,'renewed':0,'pending':0,'unchanged':0,'errors':[]}
        try:
            with self._lock():
                if self.state.exists():state=private_read(self.state)
                binding={'url':self.config['url'],'enrollments':sorted(self.config['enrollments'],key=lambda r:r['anchor_grant_id'])}
                if state.get('binding',binding)!=binding:raise DomainError('operator_configuration_changed_reconcile',403)
                state.setdefault('entries',{});state['binding']=binding
                for selected in binding['enrollments']:
                    anchor=selected['anchor_grant_id'];path=Path(selected['profile']);entry=state['entries'].setdefault(anchor,{})
                    grants=self._grants(state);scope=self._anchor(grants,anchor,entry)
                    entry.setdefault('scope',scope);entry.setdefault('profile_hash',file_hash(path))
                    pending=entry.get('pending');current_hash=file_hash(path)
                    desired=pending.get('profile') if pending else None
                    if current_hash!=entry['profile_hash'] and (not desired or not path.exists() or private_read(path)!=desired):raise DomainError('operator_profile_changed_reconcile',409)
                    if not pending and entry.get('latest',{}).get('expires_at',0)>self.now()+self.margin:
                        result['unchanged']+=1;continue
                    if not pending:
                        expiry=min(self.owner.call('prepare_enrollment')['expires_at'],int(self.now())+self.lease)
                        if expiry<=self.now():raise DomainError('operator_session_expired_reconnect',401)
                        pending={'body':{**scope,'intent_id':'renew:'+str(uuid.uuid4()),'expires_at':expiry}}
                        entry['pending']=pending;self._save(state) # Durable before any enrollment attempt.
                    if pending['body']['expires_at']<=self.now():
                        body=pending['body'];visible=[g for g in grants if g.get('intent_id')==body['intent_id'] and g['agent_id']==scope['agent_id']]
                        if len(visible)>1:raise DomainError('operator_expired_intent_ambiguous_reconcile',409)
                        if visible:
                            grant=visible[0]
                            if grant.get('revoked') or grant['expires_at']!=body['expires_at'] or self._scope(grant)!=scope:raise DomainError('operator_expired_intent_changed_or_revoked',403)
                            entry.setdefault('expired_visible',[]).append({'body':body,'record_id':grant['record_id']});del entry['pending'];self._save(state)
                        result['pending']+=1
                        result['errors'].append({'anchor_grant_id':anchor,'code':'expired_intent_read_back_next_tick' if visible else 'expired_intent_pending_readback','repair':'Retain the exact expired intent until native readback verifies it. Only a verified expired record permits a new intent on a later tick.'})
                        continue
                    response=self.owner.call('enroll',pending['body'])
                    pending['response']={k:response[k] for k in ('record_id','grant_id','credential')}
                    self._save(state)
                    grants=self._grants(state);self._anchor(grants,anchor,entry)
                    visible=[g for g in grants if g['record_id']==response['record_id']]
                    if not visible:
                        result['pending']+=1;continue
                    grant=visible[0];body=pending['body']
                    if grant.get('revoked') or grant['grant_id']!=response['grant_id'] or grant['intent_id']!=body['intent_id'] or grant['expires_at']!=body['expires_at'] or self._scope(grant)!=scope:raise DomainError('operator_enrollment_readback_mismatch',403)
                    if grant['expires_at']<=self.now():
                        entry.setdefault('expired_visible',[]).append({'body':body,'record_id':grant['record_id']});del entry['pending'];self._save(state)
                        result['pending']+=1;continue
                    desired={'transport':'fulcra-native','url':self.config['url'],'token':response['credential'],'expires_at':grant['expires_at'],'grant_id':grant['grant_id']}
                    # Preserve the exact candidate across a crash after publication.
                    if pending.get('profile'):
                        desired=pending['profile']
                    else:pending['profile']=desired;self._save(state)
                    current_hash=file_hash(path)
                    if current_hash!=entry['profile_hash']:
                        if not path.exists() or private_read(path)!=desired:raise DomainError('operator_profile_changed_reconcile',409)
                    else:replace_private(path,desired)
                    entry['profile_hash']=file_hash(path);entry['latest']={k:grant[k] for k in ('grant_id','record_id','expires_at')};del entry['pending'];self._save(state);result['renewed']+=1
                self._save(state)
        except (DomainError,urllib.error.URLError,TimeoutError,OSError) as error:
            code=error.code if isinstance(error,DomainError) else 'operator_source_or_publication_unavailable'
            return {**result,'checked':False,'error':code,'pending_known':sum(bool(e.get('pending')) for e in state.get('entries',{}).values()),'repair':'Reconnect the owner CLI or reconcile the named enrollment/profile change. Retain pending intents and the previous private profiles.'}
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--owner-auth',required=True,choices=['fulcra-cli']);parser.add_argument('--config',required=True);parser.add_argument('--state',required=True);parser.add_argument('--once',action='store_true');parser.add_argument('--interval',type=int,default=30);parser.add_argument('--lease-seconds',type=int,default=3600);parser.add_argument('--renew-before',type=int,default=300)
    args=parser.parse_args()
    if not 1<=args.interval<=3600:parser.error('Interval must be between1 and3600 seconds')
    try:
        while True:
            config=private_read(args.config)
            try:
                owner=NativeOwner(config['url'],cli_access_token())
                result=Renewal(owner,args.config,args.state,args.lease_seconds,args.renew_before).tick()
            except DomainError:result={'checked':False,'error':'operator_auth_unavailable','repair':'Reconnect the existing owner CLI; retain previous profiles and pending enrollment state.'}
            print(json.dumps(result),flush=True)
            if args.once:return
            time.sleep(args.interval)
    except (ValueError,KeyError,OSError):
        print(json.dumps({'checked':False,'error':'operator_configuration_failed_reconcile_private_state'}),file=sys.stderr);raise SystemExit(1) from None

if __name__=='__main__':main()
