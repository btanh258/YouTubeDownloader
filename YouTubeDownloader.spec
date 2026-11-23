# -*- mode: python ; coding: utf-8 -*-
# Build thu muc app (onedir) cho YouTube Downloader.
# Tu 2.3.0 khong dung onefile nua: onefile tu giai nen python311.dll ra
# %TEMP%\_MEI* moi lan mo app, Defender chan file DLL vua giai nen ngay
# sau khi cap nhat nen bao loi "Failed to load Python DLL" 1 lan.
# Onedir de python311.dll + cac DLL canh file exe trong thu muc app nen
# khong con buoc giai nen, loi nay khong the xay ra nua. Nguoi dung van
# chi can bam 1 file exe duy nhat (YouTubeDownloader.exe) de chay app.
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
    [],
    exclude_binaries=True,
    name='YouTubeDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app/icon_Youtube.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='YouTubeDownloader',
)
