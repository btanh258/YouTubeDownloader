@echo off
chcp 65001 >nul
setlocal
echo ==========================================
echo      BUILD YOUTUBE DOWNLOADER 2.2.4 (EXE)
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
echo [OK] File exe: dist\YouTubeDownloader.exe
dist\YouTubeDownloader.exe --version
powershell -NoProfile -Command "Compress-Archive -Path 'dist\YouTubeDownloader.exe','README.md' -DestinationPath 'YouTubeDownloader-2.2.zip' -Force"
echo [OK] File zip: YouTubeDownloader-2.2.zip
echo.
echo Upload ca 2 file (exe + zip) len release GitHub v2.2.4
echo de tinh nang tu cap nhat trong app tim thay file exe.
pause
