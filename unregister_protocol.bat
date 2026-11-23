@echo off
echo Dang go dang ky protocol ytdl:// ...
reg delete "HKCU\Software\Classes\ytdl" /f
if %errorlevel% equ 0 (
    echo [OK] Da go xong.
) else (
    echo [!] Khong tim thay khoa ytdl:// (co the chua dang ky).
)
pause
