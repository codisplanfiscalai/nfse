"""Build/test entrypoint for developers and CI; never required by the end user."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/ci'))
from version import read_version,validate_build


def run(*args):
    print('+',*map(str,args),flush=True)
    subprocess.run(list(map(str,args)),cwd=ROOT,check=True)


def check():
    read_version()
    run('node','frontend/build.mjs','--check')
    run('node','--check',ROOT/'src/nfse/portal/app.js')
    run(sys.executable,'-m','compileall','-q','src','desktop','winbundle','scripts','tests')
    run(sys.executable,'-m','pytest','-q','tests')
    run(sys.executable,'-m','unittest','discover','-s','scripts/ci/tests','-v')


def windows(arch,version,install):
    if sys.platform!='win32':raise ValueError('O build Windows exige runner Windows nativo.')
    if install:
        run(sys.executable,'-m','pip','install','-r','requirements-server.txt')
        run(sys.executable,'-m','pip','install','-r','winbundle/requirements-build.txt')
    check()
    run(sys.executable,'winbundle/build_windows.py','--arch',arch,'--version',version)


def container(version,no_cache):
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if not re.fullmatch('[0-9a-f]{40}',sha):raise ValueError('SHA inválido.')
    image='nfse-build:'+version
    cache=['--no-cache'] if no_cache else []
    run('docker','build',*cache,'--build-arg','APP_VERSION='+version,'--target','test','--tag','nfse-test:local','.')
    run('docker','build',*cache,'--build-arg','APP_VERSION='+version,'--target','final',
        '--label','org.opencontainers.image.version='+version,
        '--label','org.opencontainers.image.revision='+sha,'--tag',image,'.')
    image_id=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',image],text=True).strip()
    artifacts=ROOT/'artifacts';artifacts.mkdir(exist_ok=True)
    tar=artifacts/'container.tar';run('docker','save','--output',tar,image)
    gz=artifacts/'container.tar.gz'
    with tar.open('rb') as source,gz.open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as dest:shutil.copyfileobj(source,dest)
    tar.unlink();digest=hashlib.sha256(gz.read_bytes()).hexdigest()
    manifest={'schema':1,'version':version,'source_sha':sha,'image':image,'image_id':image_id,
              'file':gz.name,'sha256':digest,'size':gz.stat().st_size,'smoke_test':'passed'}
    (artifacts/'container.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('target',choices=['check','windows','container','all'])
    parser.add_argument('--arch',choices=['x86','x64'],default='x64');parser.add_argument('--version')
    parser.add_argument('--install-build-tools',action='store_true');parser.add_argument('--no-cache',action='store_true')
    args=parser.parse_args();version=validate_build(args.version or read_version(),read_version())
    if args.target=='check':check()
    elif args.target=='windows':windows(args.arch,version,args.install_build_tools)
    elif args.target=='container':container(version,args.no_cache)
    else:
        if sys.platform=='win32':windows(args.arch,version,args.install_build_tools)
        else:check()
        container(version,args.no_cache)

if __name__=='__main__':main()
