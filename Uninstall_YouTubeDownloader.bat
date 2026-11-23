@echo off
chcp 65001 >nul
setlocal
echo ==========================================
echo    GO CAI DAT YOUTUBE DOWNLOADER
echo ==========================================
echo.
echo Se xoa:
echo  - Thu muc cai dat %LOCALAPPDATA%\YouTubeDownloader (exe, FFmpeg, extension, config, log)
echo  - Dang ky protocol ytdl://
echo  - Shortcut tren Desktop
echo  Video da tai se KHONG bi xoa.
echo.
echo Luu y: extension tren Chrome se bao loi vi thu muc da bi xoa,
echo hay bam Remove tren chrome://extensions de go not.
echo.
choice /C YN /M "Tiep tuc go cai dat"
if %errorlevel% neq 1 (
    echo Da huy.
    pause
    exit /b 0
)

set "DIR=%LOCALAPPDATA%\YouTubeDownloader"
set "EXE=%DIR%\YouTubeDownloader.exe"

:: Doi app thoat (neu dang chay) roi moi xoa duoc file exe
set /a tries=0
:retry
set /a tries+=1
del "%EXE%" >nul 2>&1
if exist "%EXE%" (
    if %tries% GEQ 60 goto cleanup
    echo Dang doi app thoat... (%tries%)
    ping -n 2 127.0.0.1 >nul
    goto retry
)

:cleanup
reg delete "HKCU\Software\Classes\ytdl" /f >nul 2>&1
del "%USERPROFILE%\Desktop\YouTube Downloader.lnk" >nul 2>&1
rmdir /s /q "%DIR%" >nul 2>&1
echo.
echo [OK] Da go sach YouTube Downloader khoi may.
pause
