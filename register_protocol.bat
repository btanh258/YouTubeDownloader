@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo    DANG KY CUSTOM PROTOCOL ytdl://
echo ==========================================
echo.

:: Thu muc chua file bat nay (thu muc goc cua tool)
set "CURRENT_DIR=%~dp0"
set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

:: Uu tien 1: file exe dong goi (neu da build / da cai)
:: Uu tien 2: exe da cai o %LOCALAPPDATA%\YouTubeDownloader
:: Uu tien 3: chay .py qua Python Launcher
set "TARGET="
set "TARGET_KIND="
if exist "%CURRENT_DIR%\YouTubeDownloader.exe" (
    set "TARGET=%CURRENT_DIR%\YouTubeDownloader.exe"
    set "TARGET_KIND=exe"
)
if not defined TARGET if exist "%LOCALAPPDATA%\YouTubeDownloader\YouTubeDownloader.exe" (
    set "TARGET=%LOCALAPPDATA%\YouTubeDownloader\YouTubeDownloader.exe"
    set "TARGET_KIND=exe"
)
if not defined TARGET (
    set "GUI_PATH=%CURRENT_DIR%\app\youtube_gui.py"
    if not exist "!GUI_PATH!" (
        echo [!] Khong tim thay YouTubeDownloader.exe cung khong thay "!GUI_PATH!"
        pause
        exit /b 1
    )
    set "PYW=C:\Windows\pyw.exe"
    if not exist "!PYW!" (
        for /f "delims=" %%i in ('where pyw 2^>nul') do set "PYW=%%i"
    )
    if not exist "!PYW!" (
        echo [!] Khong tim thay pyw.exe (Python Launcher).
        echo     Hay cai Python tu python.org roi chay lai file nay,
        echo     hoac dung ban exe YouTubeDownloader.exe.
        pause
        exit /b 1
    )
    echo [OK] Python Launcher: !PYW!
    py -c "import yt_dlp" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [..] Chua co yt-dlp, dang cai...
        py -m pip install -U yt-dlp
    )
    echo [OK] yt-dlp da san sang.
)

:: Dang ky protocol ytdl:// vao HKCU (khong can quyen admin)
echo Dang dang ky ytdl:// ...
reg add "HKCU\Software\Classes\ytdl" /ve /d "URL:YouTube Downloader Protocol" /f >nul
reg add "HKCU\Software\Classes\ytdl" /v "URL Protocol" /d "" /f >nul
if "%TARGET_KIND%"=="exe" (
    reg add "HKCU\Software\Classes\ytdl\shell\open\command" /ve /d "\"%TARGET%\" \"%%1\"" /f >nul
    echo [OK] Protocol tro toi exe: %TARGET%
) else (
    reg add "HKCU\Software\Classes\ytdl\shell\open\command" /ve /d "\"%PYW%\" \"%GUI_PATH%\" \"%%1\"" /f >nul
    echo [OK] Protocol tro toi Python: %PYW% %GUI_PATH%
)
if %errorlevel% neq 0 (
    echo [!] Ghi registry that bai.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo HOAN TAT!
echo.
echo  B1. Vao chrome://extensions, bat Developer mode,
echo      chon "Load unpacked" -^> chon thu muc extension.
echo      (Neu dung ban exe thi mo app, bam nut Cai Extension
echo       de app copy san thu muc extension + mo trang nay.)
echo  B2. Mo mot video YouTube, bam nut TAI VIDEO,
echo      Chrome hoi thi tick "Always allow" roi bam Open.
echo.
echo  Thu nhanh protocol (Win+R, dan roi Enter):
echo      ytdl://https%%3A%%2F%%2Fwww.youtube.com%%2Fwatch%%3Fv%%3DdQw4w9WgXcQ
echo ==========================================
pause
