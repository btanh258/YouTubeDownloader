import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont
import yt_dlp
import threading
import webbrowser
try:
    import winreg
    _HAS_WINREG = True
except Exception:
    winreg = None
    _HAS_WINREG = False
import os
import json
import ctypes
import urllib.parse
import urllib.request
import urllib.error
import zipfile
import tempfile
import shutil
import subprocess
import time
import re
import hashlib


def parse_launch_url(arg):
    """Nhan link khoi dong: link YouTube thuong hoac link qua Custom Protocol ytdl://.

    Chrome goi: ytdl://https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D... (da encode)
    hoac:     ytdl://https://www.youtube.com/watch?v=... (chua encode)
    Ca hai deu tra ve link YouTube sach de dua vao yt-dlp.
    """
    if not arg:
        return ""
    url = arg.strip().strip('"').strip()
    low = url.lower()
    if low.startswith("ytdl://"):
        url = url[7:]
    elif low.startswith("ytdl:"):
        url = url[5:]
    if url.startswith("//"):
        url = url[2:]
    url = urllib.parse.unquote(url)
    if "%3A" in url.upper() or "%2F" in url.upper():
        url = urllib.parse.unquote(url)
    return url.strip()

VERSION = "2.4.0"
APP_NAME = "YouTubeDownloader"
GITHUB_REPO = "btanh258/YouTubeDownloader"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
# Tu 2.3.0 app dong goi onedir (thu muc app) chu khong phai onefile nua,
# nen file cap nhat la file zip chua thu muc app, vd YouTubeDownloader-v2.3.0.zip
UPDATE_ASSET_PREFIX = "youtubedownloader-v"
# File du lieu cua app (config, FFmpeg, log, danh dau portable) - khi cap
# nhat / cai dat thi mang theo sang thu muc moi, khong de mat.
APP_DATA_FILES = ("config.json", "ffmpeg.exe", "ffprobe.exe",
                  "YouTubeDownloader.log", "YouTubeDownloader.portable")


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def resource_path(rel):
    """Duong dan file dong kem trong exe (PyInstaller _MEIPASS) hoac trong source.
    Khi chay .py: icon o cung thu muc app/, extension o thu muc goc (canh app/)."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, rel)
    here = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.join(here, rel)
    if os.path.exists(cand):
        return cand
    return os.path.join(os.path.dirname(here), rel)


def install_dir():
    """Thu muc cai dat co dinh tren Windows (LOCALAPPDATA/YouTubeDownloader)."""
    local = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(local, APP_NAME)


def data_dir():
    """Noi luu config + FFmpeg + extension (CHI 1 NOI DUY NHAT).
    Chay exe: thu muc cai dat neu exe da o do, hoac neu da co ban cai trong
    thu muc cai dat thi dung chung noi do (ke ca khi dang chay ban portable
    o cho khac) de khoi bi trung lap du lieu 2 noi (vd extension vua co
    ben canh exe vua co trong AppData). Chi khi chua co ban cai nao thi
    moi luu ben canh exe (portable that su).
    Chay .py: thu muc source."""
    if is_frozen():
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        inst = install_dir()
        if os.path.isfile(os.path.join(inst, "YouTubeDownloader.exe")):
            return inst
        if os.path.normcase(exe_dir) == os.path.normcase(inst):
            return inst
        return exe_dir
    return os.path.dirname(os.path.abspath(__file__))


def _exe_version(exe_path):
    """Chay 'exe --version', tra ve chuoi version hoac '' neu khong chay duoc."""
    try:
        out = subprocess.run([exe_path, "--version"], capture_output=True,
                             text=True, timeout=10,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if out.returncode != 0:
            return ""
        m = re.search(r"\d+(?:\.\d+)+", out.stdout or "")
        return m.group(0) if m else ""
    except Exception:
        return ""


def is_onefile_build():
    """True neu exe dang chay la ban onefile (cau cu): DLL nam trong _MEIPASS
    o %TEMP%, khong co thu muc _internal canh exe. Ban onedir thi co
    _internal canh exe. Chay .py thi False."""
    if not is_frozen():
        return False
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    return not os.path.isdir(os.path.join(exe_dir, "_internal"))


def _is_app_folder(folder):
    """Thu muc co phai thu muc app (onedir) khong: ten dung 'YouTubeDownloader'
    va co file exe + thu muc _internal. Dung de tranh copy / doi nham ca thu
    muc chung (vd Downloads) khi cai dat / cap nhat."""
    try:
        return (os.path.basename(os.path.normpath(folder)) == APP_NAME
                and os.path.isfile(os.path.join(folder, "YouTubeDownloader.exe"))
                and os.path.isdir(os.path.join(folder, "_internal")))
    except Exception:
        return False


def _install_app_folder(src_dir, dst_dir):
    """Copy ca thu muc app tu src_dir sang dst_dir (xoa sach dst truoc).
    Cac file du lieu cua app dang co trong dst (config, FFmpeg, log...) duoc
    giu lai: chuyen tam ra cho khac truoc, copy xong thi tra ve neu thu muc
    moi chua co."""
    tmp = None
    try:
        tmp = tempfile.mkdtemp(prefix="ytdl-data-")
        for name in APP_DATA_FILES:
            p = os.path.join(dst_dir, name)
            if os.path.isfile(p):
                shutil.move(p, os.path.join(tmp, name))
    except Exception:
        pass
    if os.path.isdir(dst_dir):
        shutil.rmtree(dst_dir, ignore_errors=True)
    shutil.copytree(src_dir, dst_dir)
    if tmp:
        for name in APP_DATA_FILES:
            p = os.path.join(dst_dir, name)
            q = os.path.join(tmp, name)
            if not os.path.exists(p) and os.path.isfile(q):
                try:
                    shutil.move(q, p)
                except Exception:
                    pass
        shutil.rmtree(tmp, ignore_errors=True)


def maybe_install_and_relaunch():
    """Chi dung khi chay exe dong goi: neu exe chua o thu muc cai dat thi hoi
    nguoi dung co cai dat khong. Cai thi copy CA THU MUC APP + extension,
    dang ky protocol, tao shortcut Desktop, mo lai ban da cai roi thoat ban
    nay. Tra ve True neu da mo lai ban cai dat (caller nen thoat ngay).
    Chi hoi 1 lan cho moi ban exe: chon No thi ghi file danh dau portable ben
    canh exe, lan sau khong hoi nua. Neu da co ban cai san bang hoac moi hon
    thi mo thang ban do, khong hoi."""
    if not is_frozen():
        return False
    installed = os.path.join(install_dir(), "YouTubeDownloader.exe")
    current = os.path.abspath(sys.executable)
    if os.path.normcase(current) == os.path.normcase(installed):
        return False
    exe_dir = os.path.dirname(current)
    marker = os.path.join(exe_dir, "YouTubeDownloader.portable")
    if os.path.isfile(marker):
        return False
    if os.path.isfile(installed):
        ver_inst = _exe_version(installed)
        v_inst = parse_version(ver_inst) if ver_inst else None
        v_cur = parse_version(VERSION)
        if v_inst and v_cur and v_inst >= v_cur:
            try:
                subprocess.Popen([installed] + sys.argv[1:],
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                return True
            except Exception:
                pass
    # Chi cai dat khi exe dang chay trong thu muc app dung ten, hoac la ban
    # onefile (cau cu). Neu nguoi dung giai nen zip le ra cho khac (exe
    # onedir nam thang trong Downloads) thi copy ca thu muc do se copy nham
    # file cua nguoi dung.
    if _is_app_folder(exe_dir):
        try:
            os.makedirs(install_dir(), exist_ok=True)
            _install_app_folder(exe_dir, install_dir())
            copy_bundled_extension()
            register_protocol(installed)
            create_desktop_shortcut(installed)
        except Exception:
            return False
    elif is_onefile_build():
        # Ban onefile (cau cu): chi copy 1 file exe nhu cu
        try:
            os.makedirs(install_dir(), exist_ok=True)
            shutil.copy2(current, installed)
            copy_bundled_extension()
            register_protocol(installed)
            create_desktop_shortcut(installed)
        except Exception:
            return False
    else:
        try:
            import ctypes as _ct0
            _ct0.windll.user32.MessageBoxW(
                None,
                "Không cài đặt được: file exe không nằm trong thư mục app 'YouTubeDownloader'.\n\nHãy giải nén file zip ra thư mục YouTubeDownloader rồi chạy file exe trong đó.",
                "Cài đặt YouTube Downloader", 0x10)
        except Exception:
            pass
        return False
    try:
        import ctypes as _ct
        ans = _ct.windll.user32.MessageBoxW(
            None,
            "Cai dat YouTube Downloader vao thu muc:\n" + install_dir() +
            "\n\nSau khi cai, app se tu dang ky protocol ytdl://, copy extension " +
            "va tai FFmpeg khi can.\n\nChon No de chay portable tu cho hien tai (se khong hoi lai cho ban nay).",
            "Cai dat YouTube Downloader", 0x24)
    except Exception:
        return False
    if ans != 6:  # IDYES = 6: chay portable, van dang ky protocol toi exe nay
        # (khong dang ky thi bam TAI VIDEO tren YouTube se khong mo duoc app)
        # Ghi file danh dau de lan sau khong hoi lai nua
        try:
            with open(marker, "w", encoding="utf-8") as f:
                f.write("Portable mode - khong hoi cai dat lai. Xoa file nay de app hoi lai.\n")
        except Exception:
            pass
        register_protocol(current)
        return False
    # Mo thang ban vua cai, khong chay thu truoc: file vua copy la file goc
    # tu release (da duoc build + chay thu tren Actions), chay thu o day chi
    # de Defender hien hop thoai loi DLL voi file vua ghi xuong dia.
    try:
        subprocess.Popen([installed] + sys.argv[1:],
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception:
        return False
    return True


def bundled_extension_dir():
    return resource_path("extension")


def installed_extension_dir():
    # Chay .py: extension goc da la thu muc cai dat (khong copy trung lap).
    # Chay exe: extension nam trong thu muc cai dat.
    if is_frozen():
        return os.path.join(data_dir(), "extension")
    return bundled_extension_dir()


def extension_manifest_version(folder):
    try:
        with open(os.path.join(folder, "manifest.json"), "r", encoding="utf-8") as f:
            return json.load(f).get("version", "")
    except Exception:
        return ""


def copy_bundled_extension():
    """Copy extension dong kem trong exe (hoac source) ra thu muc cai dat, ghi de.
    Tra ve version cua extension sau khi copy, '' neu that bai."""
    src = bundled_extension_dir()
    dst = installed_extension_dir()
    try:
        os.makedirs(dst, exist_ok=True)
        for name in os.listdir(src):
            s = os.path.join(src, name)
            d = os.path.join(dst, name)
            if os.path.isfile(s) and os.path.normcase(os.path.abspath(s)) != os.path.normcase(os.path.abspath(d)):
                shutil.copy2(s, d)
        return extension_manifest_version(dst)
    except Exception:
        return ""


def register_protocol(exe_path):
    """Dang ky ytdl:// -> exe_path (HKCU, khong can admin). Tra ve True/False."""
    if not _HAS_WINREG:
        return False
    try:
        base = r"Software\Classes\ytdl"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base) as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "URL:YouTube Downloader Protocol")
            winreg.SetValueEx(k, "URL Protocol", 0, winreg.REG_SZ, "")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base + r"\shell\open\command") as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f'"{exe_path}" "%1"')
        return True
    except Exception:
        return False


def protocol_target():
    """Exe hien dang duoc dang ky cho ytdl://, '' neu chua dang ky / doc loi."""
    if not _HAS_WINREG:
        return ""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\ytdl\shell\open\command") as k:
            return winreg.QueryValueEx(k, "")[0]
    except Exception:
        return ""


def create_desktop_shortcut(exe_path):
    """Tao shortcut Desktop (best effort, loi thi bo qua)."""
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        link = os.path.join(desktop, "YouTube Downloader.lnk")
        if os.path.exists(link):
            return True
        ps = (
            "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%s');"
            "$s.TargetPath='%s';$s.WorkingDirectory='%s';$s.Save()"
            % (link.replace("'", "''"), exe_path.replace("'", "''"),
               os.path.dirname(exe_path).replace("'", "''"))
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                       timeout=20)
        return os.path.exists(link)
    except Exception:
        return False


def log_line(msg):
    """Ghi 1 dong log vao data_dir()/YouTubeDownloader.log (best effort)."""
    try:
        with open(os.path.join(data_dir(), "YouTubeDownloader.log"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " " + str(msg) + "\n")
    except Exception:
        pass


def _find_browser_exe():
    """Tim chrome.exe / msedge.exe, tra ve (exe_path, extensions_url) hoac (None, None).
    webbrowser.open('chrome://extensions') KHONG dung duoc: Windows khong co app
    nao dang ky scheme 'chrome', nen no hien loi 'Get an app to open this link'."""
    cands = []
    if _HAS_WINREG:
        for root, sub in ((winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
                          (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
                          (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
                          (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe")):
            try:
                with winreg.OpenKey(root, sub) as k:
                    cands.append((winreg.QueryValueEx(k, "")[0], "chrome://extensions" if "chrome" in sub else "edge://extensions"))
            except Exception:
                pass
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local = os.environ.get("LOCALAPPDATA", "")
    cands += [
        (os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"), "chrome://extensions"),
        (os.path.join(pf86, "Google", "Chrome", "Application", "chrome.exe"), "chrome://extensions"),
        (os.path.join(local, "Google", "Chrome", "Application", "chrome.exe"), "chrome://extensions"),
        (os.path.join(pf, "Microsoft", "Edge", "Application", "msedge.exe"), "edge://extensions"),
        (os.path.join(pf86, "Microsoft", "Edge", "Application", "msedge.exe"), "edge://extensions"),
    ]
    for exe, url in cands:
        if exe and os.path.isfile(exe):
            return exe, url
    return None, None


def open_extensions_page():
    """Mo trang Extensions. Tra ve True neu mo duoc, False neu khong tim thay trinh duyet.
    Edge: mo qua scheme 'microsoft-edge:' - cach Windows mo Edge voi URL.
    Chay thang msedge.exe voi 'edge://extensions' lam doi so doi khi chi mo Edge
    ma khong mo trang (Edge bo qua doi so khi da co cua so dang chay).
    Chrome: chay thang chrome.exe voi 'chrome://extensions' lam doi so."""
    exe, url = _find_browser_exe()
    if not exe:
        return False
    if "msedge" in os.path.basename(exe).lower():
        try:
            os.startfile("microsoft-edge:" + url)
            return True
        except Exception:
            pass
    try:
        subprocess.Popen([exe, url])
        return True
    except Exception:
        return False


def parse_version(text):
    if not isinstance(text, str):
        return None
    cleaned = text.strip().lstrip("vV")
    if not cleaned:
        return None
    parts = []
    for chunk in cleaned.split("."):
        digits = ""
        for ch in chunk:
            if ch.isdigit():
                digits += ch
            else:
                break
        if not digits:
            return None
        parts.append(int(digits))
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer(latest, current):
    a, b = parse_version(latest), parse_version(current)
    return bool(a and b and a > b)


def fetch_latest_release(timeout=8):
    """(release_dict|None, reason) - reason: ok/not-found/rate-limited/offline/error."""
    req = urllib.request.Request(RELEASES_API, headers={
        "User-Agent": "YouTubeDownloader-update-check",
        "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, "not-found"
        if e.code in (403, 429):
            return None, "rate-limited"
        return None, "error"
    except Exception:
        return None, "offline"
    if not isinstance(payload, dict):
        return None, "error"
    return {"tag": payload.get("tag_name") or "",
            "url": payload.get("html_url") or "",
            "notes": payload.get("body") or "",
            "assets": [{"name": a.get("name") or "",
                        "url": a.get("browser_download_url") or "",
                        "size": a.get("size") or 0,
                        "digest": a.get("digest") or ""}
                       for a in (payload.get("assets") or []) if isinstance(a, dict)]}, "ok"


def pick_update_asset(release):
    """Tra ve dict asset {url, size, digest} cua file zip cap nhat, hoac None.
    File cap nhat tu 2.3.0 la zip chua thu muc app, vd YouTubeDownloader-v2.3.0.zip.
    digest cua GitHub co dang 'sha256:<hex>' - dung de kiem tra file tai ve
    co day du / nguyen ven khong truoc khi thay ban cu."""
    if not isinstance(release, dict):
        return None
    fallback = None
    for a in release.get("assets") or []:
        url = a.get("url") or ""
        name = (a.get("name") or "").lower()
        if name.startswith(UPDATE_ASSET_PREFIX) and name.endswith(".zip"):
            return a
        if fallback is None and name.endswith(".zip") and not name.startswith("source code"):
            fallback = a
    return fallback


# Da bo verify_exe / verify_exe_retry (2.3.2): chung chay thu file exe vua
# tai ve de "kiem tra", nhung chinh viec chay thu file moi do moi de
# Defender hien hop thoai loi DLL (file vua ghi xuong dia, Defender dang
# quet). Kiem tra SHA-256 + kich thuoc da du de biet file day du / dung
# file goc tren Releases (da duoc Actions chay thu --version khi build).
# _exe_version van giu lai de so sanh version ban da cai.
def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_asset(url, destination, progress=None):
    """Tai file ve destination (qua file .part), tra ve path hoac None neu loi."""
    if not url:
        return None
    destination = os.fspath(destination)
    partial = destination + ".part"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "YouTubeDownloader-update-check"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length") or 0)
            done = 0
            with open(partial, "wb") as f:
                while True:
                    chunk = resp.read(1024 * 256)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    if progress:
                        try:
                            progress(done, total)
                        except Exception:
                            pass
    except Exception:
        try:
            os.remove(partial)
        except Exception:
            pass
        return None
    try:
        if os.path.getsize(partial) <= 0:
            os.remove(partial)
            return None
        # Mang ngat giua chung: urllib doc duoc bao nhieu thi tra bay nhieu,
        # khong bao loi. Neu Content-Length noi 22 MB ma chi tai duoc 10 MB
        # thi file bi cut, phai huy chu khong duoc dung.
        if total > 0 and done != total:
            os.remove(partial)
            return None
        os.replace(partial, destination)
    except Exception:
        return None
    return destination


def extract_update_zip(zip_path, dest_dir):
    """Giai nen file zip cap nhat vao dest_dir, tra ve duong dan thu muc app
    moi (dest_dir/YouTubeDownloader) hoac None neu zip loi / thieu exe."""
    try:
        if os.path.isdir(dest_dir):
            shutil.rmtree(dest_dir, ignore_errors=True)
        os.makedirs(dest_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(dest_dir)
        app_dir = os.path.join(dest_dir, APP_NAME)
        if not os.path.isfile(os.path.join(app_dir, "YouTubeDownloader.exe")):
            return None
        return app_dir
    except Exception:
        return None


def migrate_app_data(src_dir, dst_dir):
    """Mang cac file du lieu cua app (config, FFmpeg, log...) tu thu muc cu
    sang thu muc moi, chi copy nhung file thu muc moi chua co."""
    for name in APP_DATA_FILES:
        s = os.path.join(src_dir, name)
        d = os.path.join(dst_dir, name)
        if os.path.isfile(s) and not os.path.exists(d):
            try:
                shutil.copy2(s, d)
            except Exception:
                pass


_UPDATE_SCRIPT = r"""@echo off
setlocal
set "OLD={old_dir}"
set "NEW={new_dir}"
set "BAK={old_dir}.old"
set "EXE={old_dir}\YouTubeDownloader.exe"
rem Doi app thoat han (tien trinh cu bien mat) roi moi doi thu muc,
rem vi Windows khoa file exe dang chay. Neu app van chua thoat sau
rem 60 giay thi cu thu doi (that bai thi exe cu van chay binh thuong).
set /a wtry=0
:wait
set /a wtry+=1
tasklist /FI "IMAGENAME eq YouTubeDownloader.exe" 2>nul | find /I "YouTubeDownloader.exe" >nul
if errorlevel 1 goto gone
if %wtry% GEQ 60 goto gone
ping -n 2 127.0.0.1 >nul
goto wait
:gone
if exist "%BAK%" rmdir /s /q "%BAK%" >nul 2>&1
ren "%OLD%" "YouTubeDownloader.old" >nul 2>&1
move /y "%NEW%" "%OLD%" >nul 2>&1
start "" "%EXE%"
del "%~f0" >nul 2>&1
exit /b 0
"""


def apply_update(new_dir, current_exe):
    """Viet file .bat doi thu muc app cu bang thu muc app moi sau khi app
    thoat, roi chay ban moi. Tra ve duong dan file .bat hoac None.
    Caller phai thoat app ngay sau do. Thu muc cu duoc doi ten thanh
    '<thu muc>.old' de phong ban moi loi, app mo len duoc se tu xoa."""
    if not os.path.isdir(new_dir):
        return None
    old_dir = os.path.dirname(os.path.abspath(current_exe))
    # Thu muc cu phai la thu muc app dung ten, hoac la thu muc cai dat co dinh
    # (truong hop ban onefile cu cap nhat len onedir). Cac thu muc khac
    # (vd Downloads) thi khong doi, de tranh xoa nham file nguoi dung.
    if (not _is_app_folder(old_dir)
            and os.path.normcase(old_dir) != os.path.normcase(install_dir())):
        return None
    try:
        helper = os.path.join(tempfile.gettempdir(), "ytdl_update.bat")
        with open(helper, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(_UPDATE_SCRIPT.format(old_dir=old_dir,
                                          new_dir=os.path.abspath(new_dir)))
        flags = 0
        for n in ("CREATE_NO_WINDOW", "CREATE_NEW_PROCESS_GROUP"):
            flags |= getattr(subprocess, n, 0)
        subprocess.Popen(["cmd", "/c", helper], creationflags=flags,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, close_fds=True)
        return helper
    except Exception:
        return None


# ==========================================
# FFMPEG: TU TAI / TU CAP NHAT (Gyan.dev Essentials, ~119 MB, 1 lan duy nhat)
# ==========================================
# Nguon chinh thuc, duoc yt-dlp gioi thieu: https://www.gyan.dev/ffmpeg/builds/
# Zip Essentials gom ffmpeg.exe + ffprobe.exe (+ ffplay.exe, khong can lay).
# URL nay luon tro toi ban moi nhat (hien tai 9.1), urllib se tu theo redirect.
FFMPEG_ZIP_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
FFMPEG_MIN_SIZE = 1_000_000  # file that nho hon 1 MB coi nhu hong / tai do


def ffmpeg_paths(base_dir):
    return (os.path.join(base_dir, "ffmpeg.exe"),
            os.path.join(base_dir, "ffprobe.exe"))


def ffmpeg_version(exe_path):
    """Tra ve chuoi version, vd '9.1', hoac '' neu khong chay duoc."""
    try:
        out = subprocess.run([exe_path, "-version"], capture_output=True,
                             text=True, timeout=10,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        first = (out.stdout or "").splitlines()
        if out.returncode == 0 and first:
            parts = first[0].split()
            # Dong dau: 'ffmpeg version 9.1-essentials_build ...'
            if len(parts) >= 3 and parts[0] == "ffmpeg":
                return parts[2].split("-")[0]
            return first[0][:40]
    except Exception:
        pass
    return ""


def ffmpeg_latest_version(timeout=8):
    """Ban FFmpeg moi nhat tren Gyan.dev, vd '9.1', hoac '' neu khong xac dinh duoc.
    URL zip luon redirect toi file ffmpeg-<ver>-essentials_build.zip, nen chi can
    doc URL cuoi cung sau redirect, khong can tai gi ca."""
    try:
        req = urllib.request.Request(FFMPEG_ZIP_URL, headers={"User-Agent": "YouTubeDownloader/" + VERSION}, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            m = re.search(r"ffmpeg-(\d+(?:\.\d+)+)-essentials", resp.geturl())
            return m.group(1) if m else ""
    except Exception:
        return ""


def ffmpeg_is_usable(exe_path):
    try:
        if not os.path.isfile(exe_path) or os.path.getsize(exe_path) < FFMPEG_MIN_SIZE:
            return False
    except Exception:
        return False
    return bool(ffmpeg_version(exe_path))


def ffmpeg_missing(base_dir):
    """Tra ve danh sach file thieu/hong trong ['ffmpeg.exe', 'ffprobe.exe']."""
    ff, fp = ffmpeg_paths(base_dir)
    missing = []
    if not ffmpeg_is_usable(ff):
        missing.append("ffmpeg.exe")
    if not ffmpeg_is_usable(fp):
        missing.append("ffprobe.exe")
    return missing


def download_ffmpeg(base_dir, progress_cb=None):
    """Tai zip Gyan, chi giai nen bin/ffmpeg.exe + bin/ffprobe.exe vao base_dir.

    progress_cb(downloaded_bytes, total_bytes_or_0, stage_text)
    Tra ve version ffmpeg, raise Exception neu that bai. File zip tam luon
    duoc xoa, file cu chi bi thay khi file moi da chay duoc.
    """
    if progress_cb:
        progress_cb(0, 0, "Dang ket noi may chu FFmpeg...")
    req = urllib.request.Request(FFMPEG_ZIP_URL, headers={"User-Agent": "YouTubeDownloader/2.1"})
    tmp_zip = os.path.join(base_dir, ".ffmpeg-download.zip")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp, open(tmp_zip, "wb") as f:
            total = int(resp.headers.get("Content-Length") or 0)
            done = 0
            while True:
                chunk = resp.read(1024 * 256)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if progress_cb:
                    progress_cb(done, total, "Dang tai FFmpeg...")
        if progress_cb:
            progress_cb(done, total, "Dang giai nen FFmpeg...")
        with zipfile.ZipFile(tmp_zip) as zf:
            names = {}
            for info in zf.infolist():
                base = os.path.basename(info.filename)
                if base in ("ffmpeg.exe", "ffprobe.exe") and "/bin/" in info.filename.replace("\\", "/"):
                    names[base] = info.filename
            if "ffmpeg.exe" not in names or "ffprobe.exe" not in names:
                raise RuntimeError("File zip FFmpeg khong chua du ffmpeg.exe/ffprobe.exe")
            tmp_dir = tempfile.mkdtemp(prefix="ffmpeg-", dir=base_dir)
            try:
                zf.extract(names["ffmpeg.exe"], tmp_dir)
                zf.extract(names["ffprobe.exe"], tmp_dir)
                for base in ("ffmpeg.exe", "ffprobe.exe"):
                    src = os.path.join(tmp_dir, names[base])
                    dst = os.path.join(base_dir, base)
                    try:
                        os.chmod(src, 0o755)
                    except Exception:
                        pass
                    if not ffmpeg_is_usable(src):
                        raise RuntimeError(f"File {base} vua tai ve khong chay duoc")
                    os.replace(src, dst)
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)
    finally:
        try:
            if os.path.exists(tmp_zip):
                os.remove(tmp_zip)
        except Exception:
            pass
    ff, _ = ffmpeg_paths(base_dir)
    ver = ffmpeg_version(ff)
    if not ver:
        raise RuntimeError("Da giai nen xong nhung ffmpeg.exe khong chay duoc")
    return ver


# ==========================================
# LỚP NÚT BẤM BO TRÒN TÙY CHỈNH (CANVAS WINDOWS 11 STYLE)
# ==========================================
# ==========================================
class ModernButton(tk.Canvas):
    def __init__(self, master, text, bg, hover_bg, fg="white", disabled_bg="#E0E0E0", command=None, radius=8, width=None, **kwargs):
        # Lấy màu nền của master để nút hòa quyện vào giao diện
        try:
            master_bg = master.cget("bg")
            if not master_bg or master_bg == "SystemButtonFace":
                master_bg = "#F3F3F3"
        except:
            master_bg = "#F3F3F3"
            
        super().__init__(master, highlightthickness=0, bg=master_bg, **kwargs)
        self.text = text
        self.bg_color = bg
        self.hover_bg = hover_bg
        self.fg_color = fg
        self.disabled_bg = disabled_bg
        self.command = command
        self.radius = radius
        self.state = tk.NORMAL
        self._is_hovered = False

        # Căn chỉnh kích thước linh hoạt dựa trên text
        self.font = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        if width:
            char_w = self.font.measure("0")
            self.req_w = width * char_w + 20
        else:
            self.req_w = self.font.measure(self.text) + 30
            
        self.req_h = self.font.metrics("linespace") + 16
        self.config(width=self.req_w, height=self.req_h)

        self.bind("<Configure>", self.draw)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)
        
    def draw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            w = self.req_w
            h = self.req_h
        
        # Đảm bảo bán kính không bị biến dạng
        r = min(self.radius, w/2, h/2)
        
        bg = self.disabled_bg if self.state == tk.DISABLED else (self.hover_bg if self._is_hovered else self.bg_color)
        fg = "#999999" if self.state == tk.DISABLED else self.fg_color

        # Vẽ hình chữ nhật bo tròn mềm mại bằng các cung và hcn
        self.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=bg, outline="")
        self.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=bg, outline="")
        self.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=bg, outline="")
        self.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=bg, outline="")
        self.create_rectangle(r, 0, w-r, h, fill=bg, outline="")
        self.create_rectangle(0, r, w, h-r, fill=bg, outline="")
        
        self.create_text(w/2, h/2, text=self.text, fill=fg, font=self.font)

    def on_enter(self, e):
        if self.state == tk.NORMAL:
            self._is_hovered = True
            self.config(cursor="hand2")
            self.draw()
            
    def on_leave(self, e):
        if self.state == tk.NORMAL:
            self._is_hovered = False
            self.config(cursor="")
            self.draw()
            
    def on_click(self, e):
        pass # Có thể mở rộng hiệu ứng nhấn tại đây
        
    def on_release(self, e):
        if self.state == tk.NORMAL and self.command:
            # Xác nhận click diễn ra trong biên giới của nút
            if 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height():
                self.command()

    def set_state(self, state):
        self.state = state
        self.draw()


# ==========================================
# GIAO DIỆN CHÍNH CỦA PHẦN MỀM
# ==========================================
class YouTubeDownloaderApp:
    def __init__(self, root, initial_url=""):
        self.root = root
        self.root.title("YouTube Downloader " + VERSION)
        self.app_dir = data_dir()
        self.ffmpeg_busy = False
        
        # --- THÊM ICON TẠI ĐÂY ---
        try:
            icon_path = resource_path("icon_Youtube.ico")
            self.root.iconbitmap(icon_path)
        except Exception:
            pass # Bỏ qua nếu không tìm thấy file icon để tránh crash app
        # -------------------------
        
        # --- Kích thước và Căn giữa màn hình ---
        window_width = 560
        window_height = 570 # Tăng chiều cao lên 570 để chứa Checkbox
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
        self.root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        self.root.resizable(False, False)
        
        # Màu nền chuẩn Windows 11 (Light mode)
        self.bg_color = "#F3F3F3"
        self.root.configure(bg=self.bg_color)
        
        # Style cho các thành phần nhập liệu
        style = ttk.Style()
        style.theme_use('vista') # Giao diện native của hệ điều hành
        
        # Đọc cấu hình
        self.config_file = os.path.join(self.app_dir, "config.json")
        default_dir = os.path.join(os.path.expanduser("~"), "Downloads", "Video")
        self.recent_dirs = [default_dir]
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "recent_dirs" in data and isinstance(data["recent_dirs"], list) and data["recent_dirs"]:
                        self.recent_dirs = data["recent_dirs"]
            except: pass

        self.save_dir = tk.StringVar(value=self.recent_dirs[0])
        self.downloaded_file = None

        # --- XÂY DỰNG GIAO DIỆN ---
        
        # Header Frame: Chứa Tiêu đề và Nút Cập nhật Lõi thu gọn (Icon)
        header_frame = tk.Frame(root, bg=self.bg_color)
        header_frame.pack(pady=(25, 20))
        
        tk.Label(header_frame, text="YOUTUBE DOWNLOADER", font=("Segoe UI", 17, "bold"), bg=self.bg_color, fg="#1A1A1A").pack(side=tk.LEFT)
        self.update_btn = ModernButton(header_frame, text="🔄", bg="#D83B01", hover_bg="#B23101", command=self.update_core_thread, width=3)
        self.update_btn.pack(side=tk.LEFT, padx=(10, 0), ipady=2)
        # Nut cap nhat FFmpeg: tai lai ban moi nhat tu Gyan.dev (khi nao can thi bam)
        self.ffmpeg_btn = ModernButton(header_frame, text="🎬", bg="#6C757D", hover_bg="#5A6268", command=self.ffmpeg_update_thread, width=3)
        self.ffmpeg_btn.pack(side=tk.LEFT, padx=(6, 0), ipady=2)
        # Nut cai extension: copy extension ra thu muc cai dat + mo trang chrome://extensions
        self.ext_btn = ModernButton(header_frame, text="🧩", bg="#6C757D", hover_bg="#5A6268", command=self.install_extension_guide, width=3)
        self.ext_btn.pack(side=tk.LEFT, padx=(6, 0), ipady=2)

        # Khung Link
        tk.Label(root, text="Đường dẫn Video / Playlist:", font=("Segoe UI", 9, "bold"), bg=self.bg_color, fg="#1A1A1A").pack(anchor="w", padx=35)
        self.url_entry = ttk.Entry(root, font=("Segoe UI", 10))
        self.url_entry.pack(fill=tk.X, padx=35, pady=(2, 2), ipady=4)
        if initial_url:
            self.url_entry.insert(0, initial_url)
            
        # Thêm Checkbox tải Playlist
        self.is_playlist_var = tk.BooleanVar(value=False)
        chk_playlist = tk.Checkbutton(root, text="Tải toàn bộ Danh sách phát (Playlist)", variable=self.is_playlist_var, bg=self.bg_color, font=("Segoe UI", 9), activebackground=self.bg_color, cursor="hand2")
        chk_playlist.pack(anchor="w", padx=31, pady=(0, 10))

        # Khung Thư mục
        tk.Label(root, text="Lưu tại:", font=("Segoe UI", 9, "bold"), bg=self.bg_color, fg="#1A1A1A").pack(anchor="w", padx=35)
        frame_dir = tk.Frame(root, bg=self.bg_color)
        frame_dir.pack(fill=tk.X, padx=35, pady=(2, 12))
        self.dir_combo = ttk.Combobox(frame_dir, textvariable=self.save_dir, values=self.recent_dirs, state="readonly", font=("Segoe UI", 10))
        self.dir_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.dir_combo.bind("<<ComboboxSelected>>", self.on_combo_select)
        
        self.browse_btn = ModernButton(frame_dir, text=" 📂 Duyệt ", bg="#6C757D", hover_bg="#5A6268", command=self.browse_folder)
        self.browse_btn.pack(side=tk.RIGHT, padx=(10, 0), ipady=1)

        # Cụm Nút chức năng phụ (Giờ chỉ còn nút Lấy thông tin)
        btn_frame = tk.Frame(root, bg=self.bg_color)
        btn_frame.pack(pady=5)
        self.check_btn = ModernButton(btn_frame, text="🔍 Lấy thông tin", bg="#107C10", hover_bg="#0B5A0B", command=self.fetch_info_thread, width=20)
        self.check_btn.pack(side=tk.LEFT, padx=10, ipady=2)

        # Hiển thị Tiêu đề Video
        self.title_label = tk.Label(root, text="Vui lòng nhập link và bấm Lấy thông tin...", font=("Segoe UI", 10, "italic"), bg=self.bg_color, fg="#005FB8", wraplength=450)
        self.title_label.pack(pady=(15, 5))

        # Chọn Chất lượng
        tk.Label(root, text="Chất lượng / Định dạng:", font=("Segoe UI", 9, "bold"), bg=self.bg_color, fg="#1A1A1A").pack(anchor="w", padx=35)
        self.option_var = tk.StringVar()
        self.options_combo = ttk.Combobox(root, textvariable=self.option_var, state="readonly", font=("Segoe UI", 10))
        self.options_combo.pack(fill=tk.X, padx=35, pady=(2, 15), ipady=4)

        # Nút Tải xuống Chính (Màu xanh dương của Windows 11)
        self.download_btn = ModernButton(root, text="⬇ TẢI XUỐNG NGAY", bg="#005FB8", hover_bg="#004C93", command=self.download_thread)
        self.download_btn.pack(fill=tk.X, padx=35, pady=(5, 10), ipady=5)
        self.download_btn.set_state(tk.DISABLED)

        # Thanh Tiến trình
        self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, padx=35, pady=5)
        
        status_frame = tk.Frame(root, bg=self.bg_color)
        status_frame.pack(fill=tk.X, padx=35)
        self.percent_label = tk.Label(status_frame, text="0%", font=("Segoe UI", 9, "bold"), bg=self.bg_color, fg="#1A1A1A")
        self.percent_label.pack(side=tk.RIGHT)
        self.status_label = tk.Label(status_frame, text="Sẵn sàng.", font=("Segoe UI", 9), bg=self.bg_color, fg="#666666")
        self.status_label.pack(side=tk.LEFT)

        # Link Gioi thieu + Go cai dat o goc duoi (nho, khong lam roi giao dien chinh)
        bottom_frame = tk.Frame(root, bg=self.bg_color)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=35, pady=(0, 8))
        self.about_label = tk.Label(bottom_frame, text="ℹ️ Giới thiệu", font=("Segoe UI", 8, "underline"),
                                    bg=self.bg_color, fg="#888888", cursor="hand2")
        self.about_label.pack(side=tk.LEFT)
        self.about_label.bind("<Button-1>", lambda e: self.show_about())
        self.uninstall_label = tk.Label(bottom_frame, text="🗑 Gỡ cài đặt", font=("Segoe UI", 8, "underline"),
                                        bg=self.bg_color, fg="#888888", cursor="hand2")
        self.uninstall_label.pack(side=tk.RIGHT)
        self.uninstall_label.bind("<Button-1>", lambda e: self.uninstall_app())

        # Auto fetch nếu có link từ Chrome
        if initial_url:
            self.fetch_info_thread()
        elif not self.url_entry.get().strip():
            # Mo app tay: tu dan link YouTube trong clipboard (neu co) cho do phai Ctrl+V
            try:
                clip = self.root.clipboard_get().strip()
                if "youtube.com/" in clip or "youtu.be/" in clip:
                    self.url_entry.insert(0, clip.split()[0])
            except Exception:
                pass

        # Tu kiem tra FFmpeg sau khi mo app: thieu/hong thi tu tai (~119 MB, 1 lan)
        self.root.after(500, self.ffmpeg_startup_check)
        # Extension trong exe moi hon ban da copy thi copy de + nhac reload tren Chrome
        self.root.after(1000, self.sync_extension_on_startup)
        # Tu kiem tra / sua protocol ytdl:// (bam TAI VIDEO khong mo app neu thieu buoc nay)
        self.root.after(1500, self.check_protocol_status)

    # --- FFMPEG: tu tai khi mo app / bam nut 🎬 / truoc khi tai video ---
    def ffmpeg_startup_check(self):
        if ffmpeg_missing(self.app_dir):
            self.ffmpeg_download_thread(force=False)
        else:
            ver = ffmpeg_version(os.path.join(self.app_dir, "ffmpeg.exe"))
            if ver:
                self.status_label.config(text=f"Sẵn sàng. FFmpeg {ver} đã có.", fg="#107C10")

    def ffmpeg_download_thread(self, force=False):
        if self.ffmpeg_busy:
            return
        self.ffmpeg_busy = True
        self.ffmpeg_btn.set_state(tk.DISABLED)
        threading.Thread(target=self.run_ffmpeg_download, args=(force,), daemon=True).start()

    def ffmpeg_update_thread(self):
        # Bam nut 🎬: chi tai khi co ban FFmpeg moi hon ban dang co
        if self.ffmpeg_busy:
            return
        self.status_label.config(text="Đang kiểm tra bản FFmpeg mới nhất...", fg="#D83B01")
        threading.Thread(target=self.run_ffmpeg_update_check, daemon=True).start()

    def run_ffmpeg_update_check(self):
        cur = ffmpeg_version(os.path.join(self.app_dir, "ffmpeg.exe"))
        latest = ffmpeg_latest_version()
        if not latest:
            # Khong xac dinh duoc ban moi (mat mang / Gyan doi link): hoi nguoi dung
            def _ask():
                if messagebox.askyesno("Cập nhật FFmpeg",
                        "Không kiểm tra được bản FFmpeg mới nhất (mạng hoặc Gyan.dev không trả lời).\n\nVẫn tải lại FFmpeg (khoảng 119 MB) ngay bây giờ?"):
                    self.ffmpeg_download_thread(force=True)
                else:
                    self.status_label.config(text="Đã hủy cập nhật FFmpeg.", fg="#666666")
            self.root.after(0, _ask)
            return
        if cur and not is_newer(latest, cur):
            self.root.after(0, self.status_label.config, {"text": f"FFmpeg đã là bản mới nhất ({cur}), không cần cập nhật.", "fg": "#107C10"})
            return
        def _go():
            msg = f"Có bản FFmpeg {latest} mới hơn bản đang có ({cur or 'chưa có'}).\nTải về ngay? File zip khoảng 119 MB."
            if messagebox.askyesno("Cập nhật FFmpeg", msg):
                self.ffmpeg_download_thread(force=True)
            else:
                self.status_label.config(text="Đã hủy cập nhật FFmpeg.", fg="#666666")
        self.root.after(0, _go)

    def _ffmpeg_progress(self, done, total, stage):
        if total > 0:
            pct = int(done * 100 / total)
            self.root.after(0, self.update_progress, pct)
            self.root.after(0, self.status_label.config, {"text": f"{stage} {pct}% ({done // 1048576} / {total // 1048576} MB)", "fg": "#D83B01"})
        else:
            self.root.after(0, self.status_label.config, {"text": stage, "fg": "#D83B01"})

    def run_ffmpeg_download(self, force=False):
        missing = ffmpeg_missing(self.app_dir)
        try:
            if not force and not missing:
                return
            self.root.after(0, self.status_label.config, {"text": "Đang tải FFmpeg (khoảng 119 MB, chỉ 1 lần)...", "fg": "#D83B01"})
            ver = download_ffmpeg(self.app_dir, progress_cb=self._ffmpeg_progress)
            self.root.after(0, self.status_label.config, {"text": f"FFmpeg {ver} đã sẵn sàng.", "fg": "#107C10"})
            self.root.after(0, self.update_progress, 100)
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                cfg = {"recent_dirs": self.recent_dirs}
            cfg["ffmpeg_version"] = ver
            cfg["ffmpeg_updated_at"] = time.strftime("%Y-%m-%d")
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(cfg, f)
        except Exception as e:
            log_line(f"ffmpeg download failed: {e}")
            self.root.after(0, self.status_label.config, {"text": f"Không tải được FFmpeg: {e}. Vẫn tải được video chất lượng thấp, MP3 thì cần FFmpeg.", "fg": "#C42B1C"})
        finally:
            self.ffmpeg_busy = False
            self.root.after(0, self.ffmpeg_btn.set_state, tk.NORMAL)

    def ensure_ffmpeg(self):
        """Dung trong luong tai video: thieu FFmpeg thi tai ngay roi moi tai video."""
        if self.ffmpeg_busy:
            # Dang tai o luong khoi dong thi doi toi da 5 phut
            for _ in range(300):
                if not self.ffmpeg_busy:
                    break
                time.sleep(1)
        if ffmpeg_missing(self.app_dir):
            self.ffmpeg_busy = True
            try:
                ver = download_ffmpeg(self.app_dir, progress_cb=self._ffmpeg_progress)
                self.root.after(0, self.status_label.config, {"text": f"FFmpeg {ver} đã sẵn sàng, bắt đầu tải video...", "fg": "#107C10"})
            finally:
                self.ffmpeg_busy = False
                self.root.after(0, self.ffmpeg_btn.set_state, tk.NORMAL)

    def on_combo_select(self, event):
        self.update_recent_dirs(self.save_dir.get())

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.save_dir.get())
        if folder:
            folder = os.path.normpath(folder)
            self.update_recent_dirs(folder)

    def update_recent_dirs(self, folder):
        if folder in self.recent_dirs:
            self.recent_dirs.remove(folder)
        self.recent_dirs.insert(0, folder)
        self.recent_dirs = self.recent_dirs[:5]
        self.dir_combo['values'] = self.recent_dirs
        self.save_dir.set(self.recent_dirs[0])
        self.dir_combo.current(0)
        try:
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                cfg = {}
            cfg["recent_dirs"] = self.recent_dirs
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(cfg, f)
        except: pass

    def fetch_info_thread(self):
        url = self.url_entry.get().strip()
        if not url: return
        
        # 1. LÀM SẠCH URL: Tự động cắt bỏ đuôi Playlist (&list=) hoặc thời gian (&t=)
        # Giúp yt-dlp đi thẳng vào video đơn lẻ, tốc độ quét sẽ tăng gấp chục lần
        # CHỈ làm sạch link nếu người dùng KHÔNG tick chọn tải Playlist
        if not self.is_playlist_var.get() and "watch?v=" in url and "&" in url:
            url = url.split("&")[0]
            # Cập nhật lại thanh địa chỉ cho gọn gàng
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)

        self.status_label.config(text="Đang phân tích video...", fg="#D83B01")
        self.check_btn.set_state(tk.DISABLED)
        threading.Thread(target=self.fetch_info, args=(url,), daemon=True).start()

    def fetch_info(self, url):
        is_playlist = self.is_playlist_var.get()
        ydl_opts = {
            'quiet': True,
            # Playlist: quet nhe (extract_flat) lay ten + so luong, khong tai sau tung video
            'noplaylist': not is_playlist,
            'source_address': '0.0.0.0', # ÉP DÙNG IPv4: Khắc phục triệt để lỗi treo/delay mạng
            'extract_flat': 'in_playlist' if is_playlist else False,
            'no_warnings': True,
            'ignoreerrors': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            if not info:
                raise RuntimeError("YouTube không trả về thông tin (video riêng tư / đã xóa / giới hạn độ tuổi?)")
            if is_playlist:
                entries = info.get('entries') or []
                count = info.get('playlist_count') or len(entries)
                title = info.get('title', 'Không xác định')
                if count:
                    title = f"{title} ({count} video)"
                # Lay do phan giai tu video dau tien co formats (neu co)
                resolutions = set()
                for entry in entries[:3]:
                    if isinstance(entry, dict):
                        for f in entry.get('formats') or []:
                            h = f.get('height')
                            if h and f.get('vcodec') != 'none':
                                resolutions.add(h)
            else:
                title = info.get('title', 'Không xác định')
                resolutions = set()
                for f in info.get('formats', []):
                    height = f.get('height')
                    if height and f.get('vcodec') != 'none':
                        resolutions.add(height)

            options = ["Tự động (Chất lượng Video & Âm thanh cao nhất)"]
            for res in sorted(list(resolutions), reverse=True):
                options.append(f"Video - {res}p")
            options.append("Chỉ tải Âm thanh (MP3)")

            self.root.after(0, self.update_ui_after_fetch, title, options)
        except Exception as e:
            err = str(e).strip()
            if len(err) > 120:
                err = err[:120] + "..."
            self.root.after(0, self.status_label.config, {"text": f"Lỗi lấy thông tin: {err}", "fg": "#C42B1C"})
            self.root.after(0, self.check_btn.set_state, tk.NORMAL)

    def update_ui_after_fetch(self, title, options):
        # Thông báo trực quan nếu đang tải playlist
        if self.is_playlist_var.get():
            title = f"📦 ĐANG CHỌN TẢI PLAYLIST:\n{title}"
            
        self.title_label.config(text=f"{title}", font=("Segoe UI", 11, "bold"), fg="#1A1A1A")
        self.options_combo['values'] = options
        if options: self.options_combo.current(0)
        self.status_label.config(text="Đã lấy thông tin thành công.", fg="#107C10")
        self.check_btn.set_state(tk.NORMAL)
        self.download_btn.set_state(tk.NORMAL)

    def download_thread(self):
        url = self.url_entry.get().strip()
        choice = self.options_combo.get()
        if not url:
            messagebox.showwarning("Thiếu link", "Hãy dán link YouTube rồi bấm Lấy thông tin trước.")
            return
        if not choice:
            messagebox.showwarning("Chưa lấy thông tin", "Hãy bấm Lấy thông tin rồi chọn chất lượng trước khi tải.")
            return
        self.status_label.config(text="Đang tải xuống...", fg="#D83B01")
        self.download_btn.set_state(tk.DISABLED)
        self.progress['value'] = 0
        self.percent_label.config(text="0%")
        self.downloaded_file = None 
        threading.Thread(target=self.download_video, args=(url, choice), daemon=True).start()

    def my_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                percent = int((downloaded / total) * 100)
                
                # Cập nhật số thứ tự Video nếu đang tải Playlist
                pl_idx = d.get('playlist_index')
                pl_count = d.get('playlist_count')
                if pl_idx and pl_count:
                    status_text = f"Đang tải Video {pl_idx} / {pl_count}..."
                    self.root.after(0, self.status_label.config, {"text": status_text, "fg": "#D83B01"})
                    
                self.root.after(0, self.update_progress, percent)
                
        elif d['status'] == 'finished':
            if not self.downloaded_file:
                self.downloaded_file = d.get('filename')
            self.root.after(0, self.update_progress, 100)

    def my_post_hook(self, d):
        if d['status'] == 'finished':
            filepath = d.get('info_dict', {}).get('filepath') or d.get('info_dict', {}).get('_filename')
            if filepath:
                self.downloaded_file = filepath

    def update_progress(self, percent):
        self.progress['value'] = percent
        self.percent_label.config(text=f"{percent}%")

    def download_video(self, url, choice):
        # FFmpeg can cho gop video+audio va xuat MP3: thieu thi tu tai truoc,
        # khong de yt-dlp tai xong ca video roi moi bao loi o buoc gop.
        try:
            self.ensure_ffmpeg()
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Thiếu FFmpeg",
                            f"Không tải được FFmpeg nên không gộp/xuất MP3 được.\nChi tiết: {e}\n\nHãy kiểm tra mạng rồi bấm lại, hoặc copy ffmpeg.exe + ffprobe.exe vào thư mục app.")
            self.root.after(0, self.download_btn.set_state, tk.NORMAL)
            self.root.after(0, self.status_label.config, {"text": "Thiếu FFmpeg, chưa tải video.", "fg": "#C42B1C"})
            return
        save_path = self.save_dir.get()
        os.makedirs(save_path, exist_ok=True)

        # Thu muc chua FFmpeg: thu muc cai dat (exe) hoac thu muc source (.py)
        current_dir = self.app_dir
        
        is_playlist = self.is_playlist_var.get()
        
        # Logic đường dẫn thông minh cho Playlist
        if is_playlist:
            # Tạo thư mục con tên playlist, file có số thứ tự
            out_template = '%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s'
        else:
            out_template = '%(title)s.%(ext)s'
            
        ydl_opts = {
            'outtmpl': os.path.join(save_path, out_template),
            'noplaylist': not is_playlist, # Bật mode tải danh sách nếu chọn Playlist
            'progress_hooks': [self.my_hook],
            'postprocessor_hooks': [self.my_post_hook],
            'concurrent_fragment_downloads': 5,
            'ffmpeg_location': current_dir, # Ép tìm FFmpeg ngay tại thư mục hiện tại
            #'cookiesfrombrowser': ('chrome',), # Vượt rào kiểm duyệt của YouTube
            'ignoreerrors': True, # BỎ QUA VIDEO LỖI ĐỂ TẢI TIẾP PLAYLIST
            'postprocessors': [] # Khởi tạo danh sách xử lý rỗng
        }

        if "Tự động" in choice:
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif "Âm thanh" in choice:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegExtractAudio', 
                'preferredcodec': 'mp3'
            })
        elif "Video -" in choice:
            res_number = choice.split("-")[1].strip().replace("p", "")
            ydl_opts['format'] = f'bestvideo[height<={res_number}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            
        # Thêm Metadata (Siêu dữ liệu) cho mọi file tải về
        # Giúp file MP4/MP3 hiển thị đúng Tác giả, Tiêu đề trong máy nghe nhạc hoặc điện thoại
        ydl_opts['postprocessors'].append({'key': 'FFmpegMetadata'})

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            # ignoreerrors=True nen yt-dlp co the "xong" ma khong co file nao
            # (toan bo video loi): chi bao thanh cong khi file that su ton tai.
            if self.downloaded_file and os.path.exists(self.downloaded_file):
                self.root.after(0, self.download_complete)
            else:
                raise RuntimeError("yt-dlp báo xong nhưng không tìm thấy file đã tải (video có thể đã lỗi / bị chặn). Hãy thử Cập nhật lõi bằng nút 🔄 rồi tải lại.")
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Lỗi", str(e))
            self.root.after(0, self.download_btn.set_state, tk.NORMAL)
            self.root.after(0, self.status_label.config, {"text": "Tải thất bại.", "fg": "#C42B1C"})

    # --- HỘP THOẠI POPUP PHONG CÁCH MỚI ---
    def download_complete(self):
        self.status_label.config(text="Hoàn tất!", fg="#107C10")
        self.download_btn.set_state(tk.NORMAL)
        
        top = tk.Toplevel(self.root)
        top.title("Thành công")
        top.geometry("460x220")
        top.resizable(False, False)
        top.attributes('-topmost', True) 
        top.configure(bg=self.bg_color)
        
        top.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (460 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (220 // 2)
        top.geometry(f"+{x}+{y}")
        
        tk.Label(top, text="🎉 ĐÃ TẢI XONG!", font=("Segoe UI", 14, "bold"), bg=self.bg_color, fg="#107C10").pack(pady=(15, 5))
        
        path = self.save_dir.get()
        if len(path) > 50: path = path[:25] + "..." + path[-20:]
        tk.Label(top, text=f"File đã được lưu an toàn tại:\n{path}", font=("Segoe UI", 10), bg=self.bg_color, fg="#1A1A1A", justify=tk.CENTER).pack(pady=5)
        
        def open_file():
            try:
                if self.downloaded_file and os.path.exists(self.downloaded_file): os.startfile(self.downloaded_file)
                else: os.startfile(self.save_dir.get())
            except: pass
            # Mo file xong thi dong luon cua so phan mem
            self.root.destroy()

        def open_folder():
            try:
                if self.downloaded_file and os.path.exists(self.downloaded_file):
                    import subprocess
                    subprocess.Popen(f'explorer /select,"{os.path.normpath(self.downloaded_file)}"')
                else: os.startfile(self.save_dir.get())
            except: pass
            # Mo thu muc xong thi dong luon cua so phan mem
            self.root.destroy()
        
        btn_frame1 = tk.Frame(top, bg=self.bg_color)
        btn_frame1.pack(pady=5)
        ModernButton(btn_frame1, text="▶ Mở File", bg="#005FB8", hover_bg="#004C93", command=open_file, width=16).pack(side=tk.LEFT, padx=10, ipady=3)
        ModernButton(btn_frame1, text="📁 Mở Thư mục", bg="#6C757D", hover_bg="#5A6268", command=open_folder, width=16).pack(side=tk.LEFT, padx=10, ipady=3)
        
        btn_frame2 = tk.Frame(top, bg=self.bg_color)
        btn_frame2.pack(pady=5)
        ModernButton(btn_frame2, text="Tải tiếp video", bg="#4CAF50", hover_bg="#388E3C", command=top.destroy, width=16).pack(side=tk.LEFT, padx=10, ipady=3)
        ModernButton(btn_frame2, text="Đóng phần mềm", bg="#C42B1C", hover_bg="#A42012", command=self.root.destroy, width=16).pack(side=tk.LEFT, padx=10, ipady=3)

        top.focus_set()
        top.grab_set()

    # --- EXTENSION: copy + huong dan cai (Chrome khong cho app tu cai len) ---
    def open_extensions_page_ui(self):
        # KHONG copy URL vao clipboard o day: hop thoai Cai Extension da copy
        # duong dan thu muc extension vao clipboard de dan vao hop chon thu
        # muc (Load unpacked); copy URL de len se lam mat duong dan do
        # (nguoi dung dan ra duoc "edge://extensions"). URL chi nam trong
        # thong bao du phong khi khong mo duoc trinh duyet.
        if not open_extensions_page():
            messagebox.showinfo("Mở trang Extensions",
                "Không tìm thấy Chrome/Edge trên máy.\nHãy mở trình duyệt rồi gõ vào thanh địa chỉ:\nchrome://extensions  (hoặc edge://extensions)")

    def check_protocol_status(self):
        # Tu sua protocol moi lan mo app: neu registry khong tro toi exe nay thi
        # bam TAI VIDEO tren YouTube se khong mo duoc app (khong co gi xay ra)
        if not is_frozen():
            return
        try:
            exe = os.path.abspath(sys.executable)
            target = protocol_target()
            if exe.lower() not in target.lower():
                ok = register_protocol(exe)
                if not ok:
                    self.status_label.config(
                        text="Chưa đăng ký được protocol ytdl:// - bấm TẢI VIDEO trên YouTube sẽ không mở app. Hãy chạy app bằng quyền admin 1 lần.",
                        fg="#C42B1C")
        except Exception:
            pass

    def uninstall_app(self):
        """Go sach app khoi may: xoa thu muc cai dat, protocol ytdl://, shortcut.
        App phai thoat truoc thi file .bat moi xoa duoc file exe dang chay."""
        if not is_frozen():
            # Chay .py: khong co thu muc cai dat, chi go dang ky protocol
            if messagebox.askyesno("Gỡ cài đặt",
                    "Bạn đang chạy bản .py (không phải exe đã cài).\n\nApp sẽ gỡ đăng ký protocol ytdl://, còn thư mục source thì bạn xóa tay.\n\nTiếp tục?"):
                try:
                    if _HAS_WINREG:
                        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\ytdl\shell\open\command")
                        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\ytdl\shell\open")
                        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\ytdl\shell")
                        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\ytdl")
                except Exception:
                    pass
                messagebox.showinfo("Gỡ cài đặt", "Đã gỡ đăng ký protocol ytdl://.")
            return
        exe_path = os.path.abspath(sys.executable)
        exe_dir = os.path.dirname(exe_path)
        is_installed = os.path.normcase(exe_dir) == os.path.normcase(install_dir())
        if is_installed:
            what = "Thư mục cài đặt (thư mục app, gồm exe, DLL, FFmpeg, extension, config, log)"
            cleanup = 'rmdir /s /q "%DIR%" >nul 2>&1\r\n'
        elif _is_app_folder(exe_dir):
            # Portable onedir: exe nam trong thu muc app dung ten thi xoa ca
            # thu muc app do (chi chua file cua app)
            what = f"Thư mục app đang chạy ({exe_dir})"
            cleanup = 'rmdir /s /q "%DIR%" >nul 2>&1\r\n'
        else:
            # Portable: exe nam le trong thu muc chung (vd Downloads) nen CHI
            # duoc xoa file exe + cac file cua app trong thu muc do, tuyet
            # doi khong xoa ca thu muc (se xoa nham file cua nguoi dung)
            what = f"File exe đang chạy ({exe_path}) và các file của app bên cạnh nó (FFmpeg, extension, config, log)"
            cleanup = ('del "%DIR%\\config.json" >nul 2>&1\r\n'
                       'del "%DIR%\\ffmpeg.exe" >nul 2>&1\r\n'
                       'del "%DIR%\\ffprobe.exe" >nul 2>&1\r\n'
                       'del "%DIR%\\ffplay.exe" >nul 2>&1\r\n'
                       'del "%DIR%\\.ffmpeg-download.zip" >nul 2>&1\r\n'
                       'del "%DIR%\\YouTubeDownloader.log" >nul 2>&1\r\n'
                       'del "%DIR%\\YouTubeDownloader.portable" >nul 2>&1\r\n'
                       'rmdir /s /q "%DIR%\\extension" >nul 2>&1\r\n')
        if not messagebox.askyesno("Gỡ cài đặt",
                "Gỡ sạch YouTube Downloader khỏi máy?\n\nSẽ xóa:\n- " + what + "\n- Đăng ký protocol ytdl://\n- Shortcut trên Desktop\n\nVideo đã tải sẽ KHÔNG bị xóa.\n\nLưu ý: extension trên Chrome sẽ báo lỗi vì thư mục đã bị xóa,\nbạn bấm Remove trên chrome://extensions để gỡ nốt."):
            return
        bat = os.path.join(tempfile.gettempdir(), "ytdl_uninstall.bat")
        script = ("@echo off\r\nsetlocal\r\n"
                  f'set "DIR={exe_dir}"\r\n'
                  f'set "EXE={exe_path}"\r\n'
                  "set /a tries=0\r\n:retry\r\nset /a tries+=1\r\n"
                  'del "%EXE%" >nul 2>&1\r\n'
                  'if exist "%EXE%" (\r\n'
                  "if %tries% GEQ 60 goto cleanup\r\n"
                  "ping -n 2 127.0.0.1 >nul\r\n goto retry\r\n)\r\n"
                  ":cleanup\r\n"
                  'reg delete "HKCU\\Software\\Classes\\ytdl" /f >nul 2>&1\r\n'
                  'del "%USERPROFILE%\\Desktop\\YouTube Downloader.lnk" >nul 2>&1\r\n'
                  + cleanup +
                  '(goto) 2>nul & del "%~f0"\r\n')
        try:
            with open(bat, "w", encoding="utf-8", newline="") as f:
                f.write(script)
            subprocess.Popen(["cmd", "/c", bat],
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tạo được trình gỡ cài đặt: {e}")
            return
        self.root.destroy()

    def sync_extension_on_startup(self):
        try:
            # Xoa thu muc extension thua ben canh file exe neu du lieu cua app
            # da chuyen ve thu muc cai dat (chi giu 1 ban duy nhat). Chi xoa
            # khi do dung la thu muc extension cua app (co manifest.json +
            # content.js), khong dong vao thu muc khac.
            try:
                _exe_dir = os.path.dirname(os.path.abspath(sys.executable))
                _dup = os.path.join(_exe_dir, "extension")
                if (is_frozen()
                        and os.path.normcase(self.app_dir) != os.path.normcase(_exe_dir)
                        and os.path.isfile(os.path.join(_dup, "manifest.json"))
                        and os.path.isfile(os.path.join(_dup, "content.js"))):
                    shutil.rmtree(_dup, ignore_errors=True)
            except Exception:
                pass
            bundled_ver = extension_manifest_version(bundled_extension_dir())
            installed_ver = extension_manifest_version(installed_extension_dir())
            if bundled_ver and bundled_ver != installed_ver:
                copy_bundled_extension()
                self.status_label.config(
                    text=f"Extension đã cập nhật lên {bundled_ver}. Hãy bấm Reload extension trên chrome://extensions (hoặc khởi động lại Chrome).",
                    fg="#D83B01")
        except Exception:
            pass

    def show_about(self):
        # Hop thoai Gioi thieu: ten + version + mo ta ngan + link GitHub
        top = tk.Toplevel(self.root)
        top.title("Giới thiệu")
        top.geometry("460x260")
        top.resizable(False, False)
        top.configure(bg=self.bg_color)
        try:
            top.iconbitmap(resource_path("icon_Youtube.ico"))
        except Exception:
            pass
        tk.Label(top, text=f"YouTube Downloader {VERSION}",
                 font=("Segoe UI", 13, "bold"), bg=self.bg_color, fg="#1A1A1A").pack(pady=(20, 5))
        tk.Label(top, text="Tải video YouTube bằng 1 cú bấm\ntừ nút TẢI VIDEO trên YouTube.",
                 font=("Segoe UI", 10), bg=self.bg_color, fg="#1A1A1A", justify=tk.CENTER).pack(pady=5)
        link = tk.Label(top, text=f"https://github.com/{GITHUB_REPO}",
                        font=("Segoe UI", 10, "underline"), bg=self.bg_color, fg="#005FB8", cursor="hand2")
        link.pack(pady=5)
        link.bind("<Button-1>", lambda e: webbrowser.open(f"https://github.com/{GITHUB_REPO}"))
        tk.Label(top, text="Bấm vào link trên để mở trang GitHub của dự án.",
                 font=("Segoe UI", 9), bg=self.bg_color, fg="#666666").pack(pady=2)
        ModernButton(top, text="Đóng", bg="#6C757D", hover_bg="#5A6268",
                     command=top.destroy, width=10).pack(pady=15, ipady=3)
        top.focus_set()

    def install_extension_guide(self):
        ext_dir = installed_extension_dir()
        copy_bundled_extension()
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(ext_dir)
        except Exception:
            pass
        top = tk.Toplevel(self.root)
        top.title("Cài Extension")
        top.geometry("520x300")
        top.resizable(False, False)
        top.configure(bg=self.bg_color)
        try:
            top.iconbitmap(resource_path("icon_Youtube.ico"))
        except Exception:
            pass
        tk.Label(top, text="CÀI EXTENSION - CHỈ CÒN 1 BƯỚC TAY",
                 font=("Segoe UI", 12, "bold"), bg=self.bg_color, fg="#1A1A1A").pack(pady=(15, 5))
        tk.Label(top, text="Chrome không cho app tự cài extension lén, nên app đã copy sẵn\nextension vào thư mục dưới đây. Bạn chỉ cần làm 3 bước sau:",
                 font=("Segoe UI", 10), bg=self.bg_color, fg="#1A1A1A", justify=tk.LEFT).pack(pady=5, padx=20, anchor="w")
        tk.Label(top, text=f"Thư mục extension (đã copy vào clipboard):\n{ext_dir}",
                 font=("Segoe UI", 9), bg=self.bg_color, fg="#005FB8", justify=tk.LEFT).pack(pady=5, padx=20, anchor="w")
        tk.Label(top, text="1. Bấm nút Mở trang Extensions dưới đây\n2. Bật Developer mode (góc phải trên)\n3. Bấm Load unpacked rồi chọn đúng thư mục trên",
                 font=("Segoe UI", 10), bg=self.bg_color, fg="#1A1A1A", justify=tk.LEFT).pack(pady=5, padx=20, anchor="w")
        btns = tk.Frame(top, bg=self.bg_color)
        btns.pack(pady=10)
        ModernButton(btns, text="Mở trang Extensions", bg="#005FB8", hover_bg="#004C93",
                     command=self.open_extensions_page_ui, width=20).pack(side=tk.LEFT, padx=5, ipady=3)
        ModernButton(btns, text="Đóng", bg="#6C757D", hover_bg="#5A6268",
                     command=top.destroy, width=10).pack(side=tk.LEFT, padx=5, ipady=3)
        top.focus_set()

    # --- TU CAP NHAT APP + EXTENSION qua GitHub Releases ---
    def update_core_thread(self):
        # Nut cap nhat chinh: exe thi kiem tra ban moi tren GitHub Releases
        # (app + extension + yt-dlp dong kem deu duoc cap nhat theo exe moi);
        # chay .py thi chi cap nhat duoc yt-dlp qua pip nhu cu.
        if is_frozen():
            self.status_label.config(text="Đang kiểm tra bản mới trên GitHub...", fg="#D83B01")
            self.update_btn.set_state(tk.DISABLED)
            threading.Thread(target=self.run_app_update_check, daemon=True).start()
        else:
            self.status_label.config(text="Đang tải bản cập nhật yt-dlp... Vui lòng chờ.", fg="#D83B01")
            self.update_btn.set_state(tk.DISABLED)
            threading.Thread(target=self.run_update, daemon=True).start()

    def run_update(self):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], creationflags=subprocess.CREATE_NO_WINDOW)
            self.root.after(0, self.status_label.config, {"text": "Cập nhật yt-dlp thành công! Khởi động lại app để dùng bản mới.", "fg": "#107C10"})
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Lỗi", f"Không thể cập nhật. Chi tiết: {e}")
        finally:
            self.root.after(0, self.update_btn.set_state, tk.NORMAL)

    def run_app_update_check(self):
        release, reason = fetch_latest_release()
        if not release:
            msg = {"offline": "Không có mạng, không kiểm tra được bản mới.",
                   "rate-limited": "GitHub giới hạn lượt gọi, hãy thử lại sau.",
                   "not-found": "Chưa có release nào trên GitHub.",
                   "error": "Không đọc được thông tin release trên GitHub."}.get(reason, "Không kiểm tra được bản mới.")
            self.root.after(0, self.status_label.config, {"text": msg, "fg": "#C42B1C"})
            self.root.after(0, self.update_btn.set_state, tk.NORMAL)
            return
        if not is_newer(release.get("tag", ""), VERSION):
            # Ban dang dung da la moi nhat, NHUNG neu dang chay ban onefile
            # (cau cu, hay loi DLL) ma release co file zip dong goi onedir
            # thi van de nghi chuyen sang dang onedir de het loi DLL.
            # (Can cho ban cau noi 2.3.1 onefile: ban 2.2.x cap nhat len exe
            # cau noi roi bam cap nhat them 1 lan nua de chuyen sang onedir.)
            if is_onefile_build() and pick_update_asset(release):
                self.root.after(0, self.prompt_app_update, release)
            else:
                self.root.after(0, self.status_label.config, {"text": f"Đã là bản mới nhất ({VERSION}).", "fg": "#107C10"})
                self.root.after(0, self.update_btn.set_state, tk.NORMAL)
            return
        self.root.after(0, self.prompt_app_update, release)

    def prompt_app_update(self, release):
        tag = release.get("tag", "")
        notes = (release.get("notes") or "")[:300]
        if not is_newer(tag, VERSION):
            # Chuyen dang dong goi: cung version, chi doi tu onefile sang onedir
            if not messagebox.askyesno("Đổi dạng đóng gói",
                    "Bạn đang dùng bản đóng gói cũ (1 file exe), bản này hay bị lỗi DLL sau khi cập nhật.\n\nCó bản đóng gói mới (thư mục app) giúp hết lỗi này. Chuyển sang bản mới ngay? App sẽ tự mở lại bản mới, extension cũng được cập nhật theo (nhớ bấm Reload extension trên chrome://extensions)."):
                self.status_label.config(text="Đã hủy cập nhật.", fg="#666666")
                self.update_btn.set_state(tk.NORMAL)
                return
        elif not messagebox.askyesno("Có bản mới", f"Có bản {tag} (bạn đang dùng {VERSION}).\n\n{notes}\n\nTải và cài đặt ngay? App sẽ tự mở lại bản mới, extension cũng được cập nhật theo (nhớ bấm Reload extension trên chrome://extensions)."):
            self.status_label.config(text="Đã hủy cập nhật.", fg="#666666")
            self.update_btn.set_state(tk.NORMAL)
            return
        self.status_label.config(text=f"Đang tải bản {tag}...", fg="#D83B01")
        threading.Thread(target=self.run_app_update_download, args=(release,), daemon=True).start()

    def run_app_update_download(self, release):
        asset = pick_update_asset(release)
        if not asset or not asset.get("url"):
            self.root.after(0, messagebox.showerror, "Lỗi", "Release mới không có file zip cập nhật để tải.")
            self.root.after(0, self.update_btn.set_state, tk.NORMAL)
            return
        url = asset["url"]
        new_zip = os.path.join(tempfile.gettempdir(), "YouTubeDownloader-new.zip")
        def _prog(done, total):
            if total > 0:
                pct = int(done * 100 / total)
                self.root.after(0, self.update_progress, pct)
                self.root.after(0, self.status_label.config, {"text": f"Đang tải bản mới... {pct}% ({done // 1048576} / {total // 1048576} MB)", "fg": "#D83B01"})
        got = download_asset(url, new_zip, progress=_prog)
        if not got or os.path.getsize(got) < 1_000_000:
            self.root.after(0, messagebox.showerror, "Lỗi", "Tải bản mới thất bại (file lỗi / mạng ngắt). Hãy thử lại. Bản cũ vẫn giữ nguyên.")
            self.root.after(0, self.update_btn.set_state, tk.NORMAL)
            return
        # Kiem tra nguyen ven truoc khi thay ban cu: file tai ve ma thieu byte
        # thi ban moi se loi va khong mo duoc nua.
        expect_size = asset.get("size") or 0
        expect_digest = (asset.get("digest") or "").removeprefix("sha256:")
        bad = False
        if expect_size and os.path.getsize(got) != expect_size:
            bad = True
        if expect_digest:
            try:
                if file_sha256(got) != expect_digest:
                    bad = True
            except Exception:
                bad = True
        if bad:
            try:
                os.remove(got)
            except Exception:
                pass
            self.root.after(0, messagebox.showerror, "Lỗi", "File bản mới tải về không đầy đủ (mạng ngắt giữa chừng). Đã hủy cập nhật, bản cũ vẫn giữ nguyên. Hãy bấm cập nhật lại.")
            self.root.after(0, self.update_btn.set_state, tk.NORMAL)
            return
        # Giai nen zip ra thu muc tam. KHONG chay thu exe moi o day nua:
        # file zip da duoc kiem tra SHA-256 + kich thuoc (du byte, dung file
        # goc tren Releases, da duoc Actions chay thu --version khi build),
        # chay thu chi de Defender hien hop thoai loi DLL voi file vua tai
        # ve - chinh buoc "kiem tra" do moi gay ra loi. Cu the ma doi.
        new_dir = extract_update_zip(got, os.path.join(tempfile.gettempdir(), "ytdl-update"))
        try:
            os.remove(got)
        except Exception:
            pass
        if not new_dir:
            self.root.after(0, messagebox.showerror, "Lỗi", "Giải nén bản mới thất bại. Đã hủy cập nhật, bản cũ vẫn giữ nguyên.")
            self.root.after(0, self.update_btn.set_state, tk.NORMAL)
            return
        # Mang du lieu cua app (config, FFmpeg, log) sang thu muc moi
        migrate_app_data(self.app_dir, new_dir)
        current_exe = os.path.abspath(sys.executable)
        if not apply_update(new_dir, current_exe):
            self.root.after(0, messagebox.showerror, "Lỗi", "Không khởi động được trình cập nhật. Hãy tải tay file zip ở trang Releases, giải nén rồi chạy file exe trong thư mục YouTubeDownloader.")
            self.root.after(0, self.update_btn.set_state, tk.NORMAL)
            return
        # File .bat se doi thu muc app sau khi app thoat roi mo lai ban moi
        self.root.after(0, self.root.destroy)

if __name__ == "__main__":
    if "--version" in sys.argv or "-v" in sys.argv:
        print(VERSION)
        sys.exit(0)
    # Exe lan dau chay o cho khac: hoi cai dat, cai xong thi mo lai ban da cai
    if maybe_install_and_relaunch():
        sys.exit(0)
    # Exe: luon dang ky protocol toi exe hien tai (ca khi chay portable o Downloads)
    if is_frozen():
        try:
            register_protocol(os.path.abspath(sys.executable))
        except Exception:
            pass
    # App mo len duoc nghia la ban moi chay tot: xoa thu muc sao luu .old
    # (ban truoc doi ten lai khi cap nhat) va file .bak cua ban 2.2.x neu con
    if is_frozen():
        try:
            _parent = os.path.dirname(os.path.dirname(os.path.abspath(sys.executable)))
            _old = os.path.join(_parent, APP_NAME + ".old")
            if os.path.isdir(_old):
                shutil.rmtree(_old, ignore_errors=True)
            _bak = os.path.abspath(sys.executable) + ".bak"
            if os.path.exists(_bak):
                os.remove(_bak)
        except Exception:
            pass
    init_url = parse_launch_url(sys.argv[1]) if len(sys.argv) > 1 else ""
    log_line(f"start version={VERSION} frozen={is_frozen()} arg={init_url!r}")
    root = tk.Tk()
    app = YouTubeDownloaderApp(root, init_url)
    root.mainloop()
