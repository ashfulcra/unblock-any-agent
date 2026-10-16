"""One disposable, unattended local pickup proof. Add --claude for a model-backed worker."""
import argparse
import json
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unblock.client import Client,private_write
from unblock.server import create_server
from unblock.store import Store


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--claude',action='store_true');args=parser.parse_args()
    repo=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='unblock-proof-') as temporary:
        root=Path(temporary);store=Store(root/'work.db');og=store.bootstrap_owner('Synthetic owner');owner=store.authenticate(og['token']);wid=store.create_workspace(owner,'Synthetic proof')['id']
        worker=store.enroll(owner,wid,'Synthetic worker','agent','proof');listener=store.enroll(owner,wid,'Synthetic listener','listener','proof')
        server=create_server(store,port=0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url=f'http://127.0.0.1:{server.server_port}'
        process=None
        try:
            private_write(root/'worker.json',{'url':url,**worker});private_write(root/'listener.json',{'url':url,**listener})
            session=str(uuid.uuid4())
            argv=[sys.executable,'-m','unblock.claude_route','--config',str(root/'worker.json'),'--output',str(root/'artifacts'),'--session-id',session,'--new'] if args.claude else [sys.executable,'-m','unblock','--config',str(root/'worker.json'),'demo-worker','--output',str(root/'artifacts')]
            private_write(root/'routes.json',{worker['id']:{'argv':argv,'cwd':str(repo),'timeout':150 if args.claude else 10}})
            agent=Client(url,worker['token']);human=Client(url,og['token'])
            work=agent.call('POST','/api/requests',{'key':'delayed-result','need':'Which decision should be retained?','context':{'goal':'Unattended pickup and context recovery','next_action':'Save a synthetic continuation artifact'}})
            process=subprocess.Popen([sys.executable,'-m','unblock','--config',str(root/'listener.json'),'listen','--environment','proof','--routes',str(root/'routes.json'),'--state',str(root/'delivery.db'),'--interval','1'],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            events=queue.Queue()
            def read_events():
                for line in process.stdout:
                    try:events.put(json.loads(line))
                    except ValueError:events.put({'error':'invalid_listener_output'})
            reader=threading.Thread(target=read_events,daemon=True);reader.start()
            initial=events.get(timeout=10)
            assert initial.get('checked') and initial.get('pending')==0,initial
            # The listener is already running independently before the human answers.
            human.call('POST',f'/api/requests/{work["id"]}/answers',{'revision':work['revision'],'answer':'Use the tested listener route.','key':'human-answer'})
            deadline=time.monotonic()+(160 if args.claude else 15);observed=None
            while time.monotonic()<deadline:
                observed=human.call('GET','/api/requests/'+work['id'])
                if observed['status']=='resumed':break
                if process.poll() is not None:raise RuntimeError('Listener exited before continuation')
                time.sleep(.2)
            if not observed or observed['status']!='resumed':raise RuntimeError('No observed continuation before proof deadline')
            artifact=json.loads(next((root/'artifacts').glob('*.json')).read_text())
            assert artifact['decision']=='Use the tested listener route.'
            assert artifact['goal']=='Unattended pickup and context recovery'
            assert len(list((root/'artifacts').glob('*.json')))==1
            print(json.dumps({'passed':True,'worker':'Claude Code restricted session' if args.claude else 'real synthetic CLI subprocess','independent_listener':True,'human_check_prompt':False,'status':observed['status'],'progress_states':[p['state'] for p in observed['progress']],'continuity_context_verified':True,'synthetic':True},indent=2))
        finally:
            if process:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait()
                process.stdout.close();process.stderr.close()
            server.shutdown();server.server_close();thread.join()

if __name__=='__main__':main()
