"""Compile and verify Windows GUI + service independently using native PyInstaller."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/ci'))
from version import read_version,validate_build
from verify_artifacts import verify_pe,sha


def command(*parts):
    subprocess.run(list(map(str,parts)),cwd=ROOT,check=True)


def create(arch,version):
    if sys.platform!='win32' or struct.calcsize('P')*8!={'x86':32,'x64':64}[arch]:
        raise RuntimeError('Execute com Python nativo da arquitetura Windows selecionada.')
    build_meta=ROOT/'src/nfse/distribution.json'
    build_meta.write_text(json.dumps({'version':version}),encoding='utf-8')
    target=ROOT/'dist'/arch
    if target.exists():raise RuntimeError('Saída já existe: remova pelo fluxo de limpeza explícita.')
    target.mkdir(parents=True)
    payload=[('--add-data',f'{ROOT/"src/nfse/portal"}:src/nfse/portal'),
             ('--add-data',f'{ROOT/"assets"}:assets'),('--add-data',f'{ROOT/"VERSION"}:.')]
    args=[p for pair in payload for p in pair]
    common=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--noupx',
            '--paths',str(ROOT),'--icon',str(ROOT/'assets/app.ico'),
            '--collect-submodules','uvicorn','--collect-submodules','cryptography',
            '--collect-submodules','win32com','--hidden-import','win32timezone',
            '--distpath',str(target),'--workpath',str(ROOT/'build'/arch),
            '--specpath',str(ROOT/'build'/arch),*args]
    command(*common,'--windowed','--name','CodisplanNFSe',ROOT/'winbundle/desktop_entry.py')
    command(*common,'--console','--name','CodisplanNFSeServico',ROOT/'winbundle/service_entry.py')
    bundle=target/'CodisplanNFSe'
    service=target/'CodisplanNFSeServico'
    shutil.copy2(service/'CodisplanNFSeServico.exe',bundle/'CodisplanNFSeServico.exe')
    shutil.copytree(service/'_internal',bundle/'_internal',dirs_exist_ok=True)
    exe=bundle/'CodisplanNFSe.exe'
    verify_pe(exe.read_bytes(),arch,'gui')
    verify_pe((bundle/'CodisplanNFSeServico.exe').read_bytes(),arch,'service')
    # Native GUI smoke exits automatically and records window/tray/console state.
    check_file=ROOT/'build'/arch/'smoke.json'
    os.environ['NFSE_SMOKE_STATUS_FILE']=str(check_file)
    command(exe)
    status=json.loads(check_file.read_text(encoding='utf-8'))
    if not status['tk_window'] or status['console_window'] or not status['tray_window']:
        raise RuntimeError('GUI/Tray/console native smoke failed: '+str(status))
    del os.environ['NFSE_SMOKE_STATUS_FILE']
    from subprocess import check_output
    sha_src=check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    files=[]
    for p in sorted(bundle.rglob('*')):
        if p.is_file():
            files.append({'path':p.relative_to(bundle).as_posix(),'size':p.stat().st_size,'sha256':sha(p.read_bytes())})
    name=f'codisplan-nfse-{version}-windows-{arch}'
    manifest={'name':name,'version':version,'source_sha':sha_src,'architecture':arch,'windows_subsystem':'GUI',
              'identity':{'name':'Codisplan NFS-e','icon_sha256':sha((ROOT/'assets/app.ico').read_bytes()),
                          'embedded_pe_icons':'reviewed'},'smoke_test':'passed','files':files,
              'python':platform.python_version(),'service':'CodisplanNFSe','fiscal_homologation':False}
    (bundle/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    output=ROOT/'artifacts';output.mkdir(exist_ok=True)
    archive=Path(shutil.make_archive(str(output/name),'zip',root_dir=target,base_dir='CodisplanNFSe'))
    (output/(name+'.sha256')).write_text(f'{sha(archive.read_bytes())}  {archive.name}\n',encoding='ascii')
    shutil.copy2(bundle/'manifest.json',output/(name+'.manifest.json'))
    print('Windows GUI + service built:',archive)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--arch',choices=['x86','x64'],required=True);p.add_argument('--version',required=True)
    a=p.parse_args();create(a.arch,validate_build(a.version,read_version()))
