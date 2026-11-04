"""Check Windows release ZIP manifests, SHA-256, and both native PE subsystems."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import struct
import zipfile


def sha(data):return hashlib.sha256(data).hexdigest()


def verify_pe(data,architecture,subsystem):
    assert data.startswith(b'MZ'),'Invalid PE DOS header'
    offset=struct.unpack_from('<I',data,0x3c)[0]
    assert data[offset:offset+4]==b'PE\0\0', 'Invalid PE signature'
    machine=struct.unpack_from('<H',data,offset+4)[0]
    assert machine=={'x86':0x14c,'x64':0x8664}[architecture],'Incorrect architecture'
    actual=struct.unpack_from('<H',data,offset+24+68)[0]
    assert actual=={'gui':2,'service':3}[subsystem],f'Incorrect Windows subsystem {actual}'


def verify(folder:Path,source_sha:str):
    found=set()
    for name in sorted(folder.glob('codisplan-nfse-*-windows-*.manifest.json')):
        data=json.loads(name.read_text(encoding='utf-8'))
        assert data['source_sha']==source_sha
        assert data['smoke_test']=='passed'
        arch=data['architecture'];found.add(arch)
        base=data['name'];assert name.name==base+'.manifest.json'
        archive=folder/(base+'.zip')
        checksum=(folder/(base+'.sha256')).read_text(encoding='ascii').split()
        assert checksum==[sha(archive.read_bytes()),archive.name]
        with zipfile.ZipFile(archive) as z:
            members=[f.filename for f in z.infolist() if not f.is_dir()]
            assert len(members)==len(set(members))
            for m in members:
                p=PurePosixPath(m)
                assert not p.is_absolute() and '..' not in p.parts and '\\' not in m
                assert p.parts[0]=='CodisplanNFSe'
            expected={'CodisplanNFSe/'+x['path'] for x in data['files']}
            expected.add('CodisplanNFSe/manifest.json')
            assert expected==set(members),'Unexpected or missing bundle files'
            for row in data['files']:
                raw=z.read('CodisplanNFSe/'+row['path'])
                assert len(raw)==row['size'] and sha(raw)==row['sha256']
            assert json.loads(z.read('CodisplanNFSe/manifest.json'))==data
            verify_pe(z.read('CodisplanNFSe/CodisplanNFSe.exe'),arch,'gui')
            verify_pe(z.read('CodisplanNFSe/CodisplanNFSeServico.exe'),arch,'service')
            assert sha(z.read('CodisplanNFSe/_internal/assets/app.ico'))==data['identity']['icon_sha256']
            assert data['identity']['name']=='Codisplan NFS-e'
    assert found=={'x86','x64'},'Both architectures required'
    print('Windows distribution manifests and executables validated:',source_sha)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);parser.add_argument('--source-sha',required=True)
    args=parser.parse_args();verify(args.directory,args.source_sha)
