"""CLI for the local loop. See docs/local-proof.md."""
import argparse
import json
from pathlib import Path
import sys

from .client import Client, private_read, private_write
from .server import serve
from .store import DomainError, Store


def parser():
    p=argparse.ArgumentParser(description='Unblock Any Agent local proof')
    p.add_argument('--config',default='.state/owner.json',help='Private 0600 credential file')
    sub=p.add_subparsers(dest='command',required=True)
    init=sub.add_parser('init');init.add_argument('--state',default='.state');init.add_argument('--port',type=int,default=8765)
    server=sub.add_parser('serve');server.add_argument('--db',default='.state/work.db');server.add_argument('--port',type=int,default=8765)
    enroll=sub.add_parser('enroll');enroll.add_argument('--name',required=True);enroll.add_argument('--kind',choices=['agent','listener'],default='agent');enroll.add_argument('--environment',required=True);enroll.add_argument('--workspace');enroll.add_argument('--out',required=True)
    ask=sub.add_parser('ask');ask.add_argument('--key',required=True);ask.add_argument('--need',required=True);ask.add_argument('--context',default='{}',help='JSON object')
    for cmd in ['show','answer','progress','revise','declare','settle']:
        command=sub.add_parser(cmd);command.add_argument('request_id')
        if cmd=='answer':
            command.add_argument('--revision',required=True);command.add_argument('--answer',required=True);command.add_argument('--key',required=True)
        elif cmd=='progress':
            command.add_argument('--response-id',required=True);command.add_argument('--state',required=True,choices=['acknowledged','resumed','completed','blocked']);command.add_argument('--evidence',required=True)
        elif cmd=='revise':
            command.add_argument('--need',required=True);command.add_argument('--context',required=True)
        elif cmd=='declare':
            command.add_argument('--key',required=True);command.add_argument('--description',required=True)
        elif cmd=='settle':
            command.add_argument('--action-id',required=True);command.add_argument('--evidence',required=True)
    sub.add_parser('attention');sub.add_parser('recent')
    revoke=sub.add_parser('revoke');revoke.add_argument('principal_id')
    listener=sub.add_parser('listen');listener.add_argument('--routes',required=True);listener.add_argument('--environment',required=True);listener.add_argument('--state',default='.state/delivery.db');listener.add_argument('--once',action='store_true');listener.add_argument('--interval',type=float,default=60)
    demo=sub.add_parser('demo-worker');demo.add_argument('--output',required=True,help='Private synthetic output directory; performs no external action')
    return p


def main():
    args=parser().parse_args()
    try:
        if args.command=='init':
            state=Path(args.state)
            if (state/'owner.json').exists() or (state/'work.db').exists():
                raise ValueError('State already exists; use its existing owner config')
            store=Store(state/'work.db');grant=store.bootstrap_owner('Local owner');owner=store.authenticate(grant['token']);workspace=store.create_workspace(owner,'My agents')
            private_write(state/'owner.json',{'url':f'http://127.0.0.1:{args.port}','workspace_id':workspace['id'],**grant})
            result={'owner_config':str(state/'owner.json'),'workspace_id':workspace['id'],'url':f'http://127.0.0.1:{args.port}'}
        elif args.command=='serve':
            serve(Store(args.db),port=args.port);return
        else:
            client=Client.from_file(args.config)
            if args.command in ('attention','recent'):
                result=client.call('GET','/api/'+args.command)
            elif args.command=='enroll':
                # Verify the destination before minting a credential we cannot safely save.
                if Path(args.out).exists():raise ValueError('Output config already exists')
                workspace=args.workspace or private_read(args.config).get('workspace_id')
                grant=client.call('POST','/api/enroll',{'workspace_id':workspace,'name':args.name,'kind':args.kind,'environment':args.environment})
                private_write(args.out,{'url':client.url,**grant});result={'id':grant['id'],'config':args.out}
            elif args.command=='ask':
                result=client.call('POST','/api/requests',{'key':args.key,'need':args.need,'context':json.loads(args.context)})
            elif args.command=='revoke':
                result=client.call('POST','/api/revoke',{'principal_id':args.principal_id})
            elif args.command=='listen':
                from .listener import Listener
                listener=Listener(client,args.environment,args.routes,args.state)
                if args.interval<1:raise ValueError('Interval must be at least one second')
                import time
                while True:
                    print(json.dumps(listener.tick()),flush=True)
                    if args.once:return
                    time.sleep(args.interval)
            elif args.command=='demo-worker':
                payload=json.load(sys.stdin);rid=payload['request_id'];work=client.call('GET','/api/requests/'+rid)
                current=[r for r in work['responses'] if not r['stale']]
                if not current:raise ValueError('No current answer')
                response=current[-1]
                if work['conflicting_answers'] or any(a['status']=='uncertain' for a in work['actions']):
                    result=client.call('POST',f'/api/requests/{rid}/progress',{'response_id':response['id'],'state':'blocked','evidence':'Synthetic worker requires reconciliation before acting.'})
                else:
                    artifact=Path(args.output)/f'{rid}-{response["id"]}.json'
                    if not artifact.exists():
                        client.call('POST',f'/api/requests/{rid}/progress',{'response_id':response['id'],'state':'acknowledged','evidence':'Synthetic worker retrieved current context and answer.'})
                        private_write(artifact,{'request_id':rid,'response_id':response['id'],'goal':work['context'].get('goal'),'decision':response['answer'],'synthetic':True})
                    result=client.call('POST',f'/api/requests/{rid}/progress',{'response_id':response['id'],'state':'resumed','evidence':'Synthetic local continuation wrote '+str(artifact)})
            else:
                path='/api/requests/'+args.request_id
                if args.command=='show':result=client.call('GET',path)
                else:
                    operations={'answer':('answers',{'revision':getattr(args,'revision',None),'answer':getattr(args,'answer',None),'key':getattr(args,'key',None)}),'progress':('progress',{'response_id':getattr(args,'response_id',None),'state':getattr(args,'state',None),'evidence':getattr(args,'evidence',None)}),'revise':('revise',{'need':getattr(args,'need',None),'context':json.loads(getattr(args,'context','{}'))}),'declare':('actions',{'key':getattr(args,'key',None),'description':getattr(args,'description',None)}),'settle':('settle',{'action_id':getattr(args,'action_id',None),'evidence':getattr(args,'evidence',None)})}
                    operation,data=operations[args.command];result=client.call('POST',path+'/'+operation,data)
        print(json.dumps(result,indent=2))
    except (DomainError,ValueError,OSError,KeyError) as error:
        # Do not include HTTP headers, credential files or server response bodies.
        print(json.dumps({'error':str(error)}),file=sys.stderr)
        raise SystemExit(1) from None


if __name__=='__main__':main()
