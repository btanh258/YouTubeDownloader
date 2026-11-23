@echo off
chcp 65001 >nul
setlocal
echo ==========================================
echo      BUILD YOUTUBE DOWNLOADER 2.3.0 (THU MUC APP)
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
    echo [!] Build that bai.
    pause
    exit /b 1
)
echo.
echo [OK] Thu muc app: dist\YouTubeDownloader
dist\YouTubeDownloader\YouTubeDownloader.exe --version
powershell -NoProfile -Command "Compress-Archive -Path 'dist\YouTubeDownloader','README.md' -DestinationPath 'YouTubeDownloader-v2.3.0.zip' -Force"
echo [OK] File zip: YouTubeDownloader-v2.3.0.zip
echo.
echo Upload file zip len release GitHub v2.3.0
echo de tinh nang tu cap nhat trong app tim thay file zip.
pause
