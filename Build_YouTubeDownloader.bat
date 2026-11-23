@echo off
chcp 65001 >nul
setlocal
echo ==========================================
echo      BUILD YOUTUBE DOWNLOADER 2.3.3 (THU MUC APP + EXE CAU NOI)
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
powershell -NoProfile -Command "Compress-Archive -Path 'dist\YouTubeDownloader','README.md' -DestinationPath 'YouTubeDownloader-v2.3.3.zip' -Force"
echo [OK] File zip: YouTubeDownloader-v2.3.3.zip
echo.
echo Build them file exe 1 file lam cau noi cho ban 2.2.x cap nhat len:
python -m PyInstaller --noconfirm --clean --distpath dist-onefile YouTubeDownloader-onefile.spec
if %errorlevel% neq 0 (
    echo [!] Build onefile that bai.
    pause
    exit /b 1
)
dist-onefile\YouTubeDownloader.exe --version
echo [OK] File exe cau noi: dist-onefile\YouTubeDownloader.exe
echo.
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo Build bo cai dat Inno Setup:
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DMyAppVersion=2.3.3 YouTubeDownloader.iss
    if %errorlevel% neq 0 (
        echo [!] Build bo cai dat that bai.
        pause
        exit /b 1
    )
    echo [OK] Bo cai dat: Output\YouTubeDownloader-Setup-2.3.3.exe
) else (
    echo [Bo qua] May chua cai Inno Setup, khong build bo cai dat.
    echo          Cai tu https://jrsoftware.org/isdl.php neu muon build.
)
echo.
echo Upload ca 3 file (zip + exe + bo cai dat) len release GitHub v2.3.3
echo de ban cu tim thay file exe, ban moi tim thay file zip.
pause
