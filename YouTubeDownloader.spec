# -*- mode: python ; coding: utf-8 -*-
# Build 1 file exe duy nhat cho YouTube Downloader.
# Chay tren Windows: python -m PyInstaller --noconfirm --clean YouTubeDownloader.spec
# (xem Build_YouTubeDownloader.bat). Khong build duoc exe Windows tren Linux.

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
    upx=True,
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
