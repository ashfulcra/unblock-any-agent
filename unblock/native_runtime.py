"""Trusted, explicitly selected renewal runtime; never exported to workers."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import threading
import time
import urllib.error

from .client import private_read
from .native_owner import NativeOwner, cli_access_token
from .native_renewal import Renewal, replace_private
from .store import DomainError


def fingerprint(path):
    private_read(path)
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class RenewalRuntime:
    def __init__(self, config, owner_factory=None, now=time.time):
        self.config = Path(config).absolute()
        self.settings = private_read(self.config)
        if not isinstance(self.settings, dict) or set(self.settings) != {'operators','health','interval'}:
            raise ValueError('Runtime requires operators, health and interval')
        interval = self.settings['interval']
        if type(interval) is not int or not 30 <= interval <= 300:
            raise ValueError('Runtime interval must be 30 to 300 seconds')
        self.interval, self.now = interval, now
        self.owner_factory = owner_factory or (lambda url: NativeOwner(url, cli_access_token()))
        self.health = self._path(self.settings['health'])
        self.lock_path = self.health.with_suffix(self.health.suffix+'.lock')
        rows = self.settings['operators']
        if not isinstance(rows,list) or not 1 <= len(rows) <= 4:
            raise ValueError('Select one to four existing operators')
        paths = [self.config.resolve(), self.health.resolve(), self.lock_path.resolve()]
        operators = []
        for row in rows:
            if not isinstance(row,dict) or set(row) != {'config','state'}:
                raise ValueError('Each selection requires existing operator config and state paths')
            cfg, state = self._path(row['config']), self._path(row['state'])
            settings = private_read(cfg)
            if not isinstance(settings,dict) or not isinstance(settings.get('enrollments'),list):
                raise ValueError('Use a prepared native renewal operator')
            paths.extend([cfg.resolve(),state.resolve(),state.with_suffix(state.suffix+'.lock').resolve()])
            for selected in settings['enrollments']:
                profile = self._path(selected['profile']); private_read(profile)
                paths.append(profile.resolve())
            operators.append({'config':str(cfg),'state':str(state),'sha256':fingerprint(cfg)})
        if len(paths) != len(set(paths)):
            raise ValueError('Runtime files, operator ledgers and managed profiles must be separate')
        self.binding = {'configuration_sha256':fingerprint(self.config),'operators':operators}
        if self.health.exists() or self.health.is_symlink():
            prior = private_read(self.health)
            if prior.get('binding') != self.binding:
                raise ValueError('Runtime selections changed; reconcile retained health before replacement')

    @staticmethod
    def _path(value):
        if not isinstance(value,str) or not Path(value).is_absolute():
            raise ValueError('Use absolute private paths')
        return Path(value)

    @contextmanager
    def lock(self):
        self.lock_path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        fd = os.open(self.lock_path,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise ValueError('Runtime lock must be a private owned regular file')
            try: fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError: raise DomainError('runtime_already_running',409) from None
            yield
        finally:
            fcntl.flock(fd,fcntl.LOCK_UN); os.close(fd)

    def tick(self):
        previous = private_read(self.health) if self.health.exists() else {}
        results = []
        try:
            if previous and previous.get('binding') != self.binding:
                raise ValueError('Retained health binding changed')
            if fingerprint(self.config) != self.binding['configuration_sha256']:
                raise ValueError('Runtime configuration changed')
            # Validate every selection before allowing any owner operation.
            for row in self.binding['operators']:
                if fingerprint(row['config']) != row['sha256']:
                    raise ValueError('Operator configuration changed')
            for row in self.binding['operators']:
                try:
                    cfg = private_read(row['config'])
                    owner = self.owner_factory(cfg['url'])
                    result = Renewal(owner,row['config'],row['state'],renew_before=1200,now=self.now).tick()
                    safe = {key:result.get(key,0) for key in ('renewed','pending','unchanged','pending_known')}
                    safe['checked'] = result.get('checked') is True
                    safe['error_count'] = len(result.get('errors',[])) + int(bool(result.get('error')))
                    safe['healthy'] = safe['checked'] and not safe['pending'] and not safe['pending_known'] and not safe['error_count']
                except (DomainError,ValueError,KeyError,TypeError,OSError,urllib.error.URLError):
                    safe = {'checked':False,'healthy':False,'error_count':1}
                results.append(safe)
            healthy = all(row['healthy'] for row in results)
        except (ValueError,KeyError,TypeError,OSError):
            healthy = False
        result = {'schema':'unblock-renewal-runtime/1','binding':self.binding,
                  'checked_at':self.now(),'healthy':healthy,'operators':results,
                  'last_success_at':self.now() if healthy else previous.get('last_success_at'),
                  'configuration_error':len(results) != len(self.binding['operators']),
                  'scope':'Connection renewal only; no agent dispatch or progress is implied.'}
        replace_private(self.health,result)
        return result

    def run(self, stop):
        with self.lock():
            while not stop.is_set():
                self.tick()
                stop.wait(self.interval)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True)
    parser.add_argument('--once',action='store_true')
    args = parser.parse_args()
    try:
        runtime = RenewalRuntime(args.config)
        if args.once:
            with runtime.lock(): result = runtime.tick()
            print(json.dumps({'healthy':result['healthy'],'checked_at':result['checked_at']}))
            return 0 if result['healthy'] else 2
        stop = threading.Event()
        for signum in (signal.SIGINT,signal.SIGTERM):
            signal.signal(signum,lambda *_:stop.set())
        runtime.run(stop)
        return 0
    except (DomainError,ValueError,KeyError,TypeError,OSError):
        print(json.dumps({'healthy':False,'error':'runtime_failed_reconcile_private_state'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
