@echo off
chcp 65001 >nul
setlocal
echo ==========================================
echo      BUILD YOUTUBE DOWNLOADER 2.4.0 (THU MUC APP + BO CAI DAT)
echo ==========================================
echo.
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Chua co Python. Cai Python 3.11 tu python.org truoc.
    pause
    exit /b 1
)
python -m pip install --upgrade pyinstaller yt-dlp >nul 2>&1
python -m PyInstaller --noconfirm --clean YouTubeDownloader.spec
if %errorlevel% neq 0 (
    echo [!] Build onedir that bai.
    pause
    exit /b 1
)
echo.
echo [OK] Thu muc app: dist\YouTubeDownloader
dist\YouTubeDownloader\YouTubeDownloader.exe --version
powershell -NoProfile -Command "Compress-Archive -Path 'dist\YouTubeDownloader','README.md' -DestinationPath 'YouTubeDownloader-v2.4.0.zip' -Force"
echo [OK] File zip: YouTubeDownloader-v2.4.0.zip
echo.
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo Build bo cai dat Inno Setup:
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DMyAppVersion=2.4.0 YouTubeDownloader.iss
    if %errorlevel% neq 0 (
        echo [!] Build bo cai dat that bai.
        pause
        exit /b 1
    )
    echo [OK] Bo cai dat: Output\YouTubeDownloader-Setup-2.4.0.exe
) else (
    echo [Bo qua] May chua cai Inno Setup, khong build bo cai dat.
    echo          Cai tu https://jrsoftware.org/isdl.php neu muon build.
)
echo.
echo Upload ca 2 file (zip + bo cai dat) len release GitHub v2.4.0
echo de ban cu tim thay file exe, ban moi tim thay file zip.
pause
