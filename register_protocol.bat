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
set "GUI_PATH=%CURRENT_DIR%\app\youtube_gui.py"

if not exist "%GUI_PATH%" (
    echo [!] Khong tim thay "%GUI_PATH%"
    echo     Hay giai nen dung cau truc: register_protocol.bat o thu muc goc,
    echo     youtube_gui.py nam trong thu muc app.
    pause
    exit /b 1
)

:: 1. Tim Python Launcher (pyw.exe) - khong dung "python" tran de tranh alias Store
set "PYW=C:\Windows\pyw.exe"
if not exist "%PYW%" (
    for /f "delims=" %%i in ('where pyw 2^>nul') do set "PYW=%%i"
)
if not exist "%PYW%" (
    echo [!] Khong tim thay pyw.exe (Python Launcher).
    echo     Hay cai Python tu python.org (nho tick "Add python.exe to PATH",
    echo     muc nay cai kem Python Launcher) roi chay lai file nay.
    pause
    exit /b 1
)
echo [OK] Python Launcher: %PYW%
echo.

:: 2. Kiem tra yt-dlp, thieu thi cai
py -c "import yt_dlp" >nul 2>&1
if %errorlevel% neq 0 (
    echo [..] Chua co yt-dlp, dang cai...
    py -m pip install -U yt-dlp
    py -c "import yt_dlp" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [!] Cai yt-dlp that bai. Kiem tra mang roi chay lai.
        pause
        exit /b 1
    )
)
echo [OK] yt-dlp da san sang.
echo.

:: 3. FFmpeg: app tu tai lan dau mo (Gyan.dev, ~119 MB) nen khong can
::    copy tay nua. Neu may da co san ffmpeg.exe + ffprobe.exe trong
::    thu muc app thi app se dung luon, khong tai lai.
if exist "%CURRENT_DIR%\app\ffmpeg.exe" (
    echo [OK] Da co app\ffmpeg.exe, app se dung luon.
) else (
    echo [..] Chua co ffmpeg.exe - app se tu tai lan dau mo
    echo     (can mang, file zip khoang 119 MB, chi tai 1 lan).
)
echo.

:: 4. Dang ky protocol ytdl:// vao HKCU (khong can quyen admin)
::    Lenh mo app: "pyw.exe" "duong\dan\youtube_gui.py" "%1"
::    %1 la toan bo link ytdl://... do Chrome truyen sang, da duoc dat trong ngoac kep.
echo Dang dang ky ytdl:// ...
reg add "HKCU\Software\Classes\ytdl" /ve /d "URL:YouTube Downloader Protocol" /f >nul
reg add "HKCU\Software\Classes\ytdl" /v "URL Protocol" /d "" /f >nul
reg add "HKCU\Software\Classes\ytdl\shell\open\command" /ve /d "\"%PYW%\" \"%GUI_PATH%\" \"%%1\"" /f >nul
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
echo  B2. Mo mot video YouTube, bam nut TAI VIDEO,
echo      Chrome hoi thi tick "Always allow" roi bam Open.
echo.
echo  Thu nhanh protocol (Win+R, dan roi Enter):
echo      ytdl://https%%3A%%2F%%2Fwww.youtube.com%%2Fwatch%%3Fv%%3DdQw4w9WgXcQ
echo ==========================================
pause
