# -*- mode: python ; coding: utf-8 -*-
# Build 1 file exe duy nhat (onefile) cho YouTube Downloader.
# CHI DUNG LAM CAU NOI cho ban cu 2.2.x cap nhat len: ban 2.2.x chi biet
# tai file YouTubeDownloader.exe, khong biet tai file zip, nen release
# tu 2.3.1 phai kem ca file exe nay. Ban exe nay chay code 2.3.1 nen khi
# bam cap nhat them 1 lan nua no se tu chuyen sang dang onedir (thu muc
# app) de het loi DLL. Nguoi dung moi khong can file nay, chi can zip.
# Chay tren Windows: python -m PyInstaller --noconfirm --clean --distpath dist-onefile YouTubeDownloader-onefile.spec

from PyInstaller.utils.hooks import collect_all

_tmp = collect_all('yt_dlp')

a = Analysis(
    ['app/youtube_gui.py'],
    pathex=[],
    binaries=_tmp[1],
    datas=[('extension', 'extension'), ('app/icon_Youtube.ico', '.')] + _tmp[0],
    hiddenimports=_tmp[2],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='YouTubeDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app/icon_Youtube.ico'],
)
