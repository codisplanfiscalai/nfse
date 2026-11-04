# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
root=Path.cwd().resolve()
hiddenimports=collect_submodules('uvicorn')+collect_submodules('win32com')+['win32timezone','servicemanager','desktop.service']
datas=[(str(root/'frontend'/'dist'),'frontend'),(str(root/'assets'/'app.ico'),'assets')]
a=Analysis([str(root/'desktop'/'main.py')],pathex=[str(root),str(root/'backend')],binaries=[],datas=datas,hiddenimports=hiddenimports,
    hookspath=[],hooksconfig={},runtime_hooks=[],excludes=['tkinter'],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='CodisplanNFSe',debug=False,bootloader_ignore_signals=False,
    strip=False,upx=False,console=False,disable_windowed_traceback=False,icon=str(root/'assets'/'app.ico'))
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='CodisplanNFSe')
