# YouTube Downloader 2.2

Tải video / playlist YouTube bằng yt-dlp, giao diện Tkinter. Bấm nút
**TẢI VIDEO** ngay trên trang YouTube, app tự mở lên với link đã điền sẵn.

**Bản 2.2 là bản 1 file exe duy nhất.** Tải `YouTubeDownloader.exe` ở trang
Releases về, chạy là xong, không cần cài Python, không cần copy thêm file gì.

## Cài đặt lần đầu (chỉ làm 1 lần)

1. Tải `YouTubeDownloader.exe` ở
   [Releases](https://github.com/btanh258/YouTubeDownloader/releases) về,
   chạy file exe đó.
2. App hỏi có cài đặt không, bấm **Yes**. App sẽ tự:
   - Copy chính nó vào `%LOCALAPPDATA%\YouTubeDownloader\YouTubeDownloader.exe`
     (và tạo shortcut trên Desktop), rồi mở lại bản đã cài.
   - Đăng ký protocol `ytdl://` trỏ tới bản đã cài (không cần quyền admin).
   - Copy extension vào `%LOCALAPPDATA%\YouTubeDownloader\extension`.
   - Tải FFmpeg lần đầu (khoảng 119 MB, chỉ 1 lần) khi cần.
3. Cài extension: trong app bấm nút 🧩 **Cài Extension**. App đã copy sẵn
   thư mục extension, chỉ còn 3 bước tay: mở trang `chrome://extensions`,
   bật Developer mode, bấm Load unpacked rồi chọn đúng thư mục đó.

> **Vì sao extension vẫn cần 1 bước tay?** Chrome không cho app tự cài
> extension lén trên máy cá nhân. Cách duy nhất để Chrome tự cài + tự cập
> nhật extension là đăng extension lên Chrome Web Store rồi ép cài qua
> chính sách (ExtensionInstallForcelist) — trên máy không quản lý bởi tổ
> chức, Chrome cũng bỏ qua chính sách nếu update URL không phải Web Store.
> Nên bản này làm tới mức tối đa có thể tự động: copy sẵn extension, mở
> sẵn trang Extensions, copy sẵn đường dẫn vào clipboard.

Sau này mở video YouTube, bấm **TẢI VIDEO**, lần đầu Chrome hỏi thì tick
**Always allow** rồi bấm **Open**.

Thử nhanh không cần mở YouTube: bấm `Win+R`, dán rồi Enter:

```
ytdl://https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DdQw4w9WgXcQ
```

## Tự cập nhật (bấm nút 🔄 trong app)

- **App:** nút 🔄 kiểm tra GitHub Releases. Có bản mới thì hỏi, đồng ý là
  app tải `YouTubeDownloader.exe` mới về, tự thay file exe cũ và mở lại
  bản mới (dùng file `.bat` trung gian vì Windows không cho ghi đè file exe
  đang chạy). Bản mới kèm yt-dlp mới và extension mới.
- **Extension:** exe mới khi mở lên sẽ copy đè extension mới vào thư mục cài
  đặt, rồi nhắc bạn bấm **Reload** extension trên `chrome://extensions`
  (hoặc khởi động lại Chrome). Chrome không tự cập nhật extension nạp tay,
  nên đây là bước duy nhất còn phải bấm tay khi cập nhật extension.
- **FFmpeg:** bấm nút 🎬 để tải lại bản FFmpeg mới nhất từ Gyan.dev.
- **yt-dlp (bản chạy .py):** khi chạy từ source thì nút 🔄 chỉ cập nhật
  yt-dlp qua pip như cũ, xong khởi động lại app.

## FFmpeg tự tải

- **Lần đầu mở app:** nếu thiếu `ffmpeg.exe` / `ffprobe.exe` (hoặc file bị
  hỏng, nhỏ bất thường, chạy `--version` lỗi), app tự tải bản Essentials
  mới nhất từ [Gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
  (`ffmpeg-release-essentials.zip`, khoảng 119 MB, chỉ 1 lần), chỉ giải nén
  `bin/ffmpeg.exe` + `bin/ffprobe.exe` vào thư mục cài đặt, kiểm tra chạy
  được mới thay file cũ, file zip tạm luôn được xóa. Có sẵn 2 file này thì
  app dùng luôn, không tải lại.
- **Trước khi tải video:** app kiểm tra lại FFmpeg rồi mới cho yt-dlp tải,
  tránh trường hợp tải xong cả video mới báo lỗi ở bước gộp video + audio.

## Luồng hoạt động

```
YouTube (extension/content.js)  -- bấm TẢI VIDEO -->
  ytdl://https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D...
    -- Windows (registry HKCU\Software\Classes\ytdl) -->
      YouTubeDownloader.exe "ytdl://..."
        -- app bóc link, lấy thông tin, tải bằng yt-dlp + FFmpeg -->
```

## Chạy từ source (cho dev)

Yêu cầu Python 3.11+ và `pip install yt-dlp`. Chạy `app/youtube_gui.py`,
rồi chạy `register_protocol.bat` để đăng ký `ytdl://` trỏ tới Python.
Build exe trên Windows: chạy `Build_YouTubeDownloader.bat`
(PyInstaller theo `YouTubeDownloader.spec`).

## Cấu trúc

```
YouTubeDownloader.spec     PyInstaller: 1 file exe, kem extension + icon
Build_YouTubeDownloader.bat  Build exe tren Windows
.github/workflows/build.yml GitHub Actions: build exe khi push tag vX.Y.Z
register_protocol.bat      Đăng ký ytdl:// (exe uu tien, khong thi .py)
unregister_protocol.bat    Gỡ đăng ký ytdl://
README.md                  File này
app/
  youtube_gui.py           App chính (Tkinter + yt-dlp)
  icon_Youtube.ico
  ffmpeg.exe               Tự tải lần đầu mở app (không có trong repo)
  ffprobe.exe              Tự tải lần đầu mở app (không có trong repo)
  config.json              Tự tạo khi chạy (thư mục lưu, phiên bản FFmpeg)
extension/
  content.js               Chèn nút TẢI VIDEO, mở ytdl://...
  manifest.json            Manifest MV3 tối giản, không quyền gì cả
```

## Thay đổi trong 2.2.2 (so với 2.2.1)

- **Sửa lỗi "Failed to load Python DLL" sau khi cập nhật:** nguyên nhân là
  quá trình tải exe mới không kiểm tra độ đầy đủ — mạng ngắt giữa chừng thì
  file exe bị cắt ngắn mà app vẫn thay exe cũ bằng file lỗi đó, nên lần mở
  sau PyInstaller giải nén thiếu `python311.dll` và không chạy được nữa.
  Nay trước khi thay exe, app kiểm tra cả 3 thứ: số byte tải về phải khớp
  `Content-Length`, kích thước phải khớp asset trên Releases, và SHA-256
  phải khớp `digest` của asset. Sai một thứ là hủy cập nhật, bản cũ giữ nguyên.
- **Sao lưu exe cũ:** trước khi thay, app copy exe cũ thành
  `YouTubeDownloader.exe.bak`. Nếu exe mới vẫn lỗi thì đổi tên file `.bak`
  lại là có bản cũ chạy được. Bản mới mở lên được thì tự xóa file `.bak`.
- **Tắt UPX khi đóng gói:** UPX làm Defender dễ chặn file DLL khi giải nén
  ra `%TEMP%`, cũng là một nguyên nhân gây lỗi trên.

  **Nếu máy bạn đang bị lỗi này:** xóa các thư mục `%TEMP%\_MEI*`, tải lại
  `YouTubeDownloader.exe` ở trang Releases rồi chép đè vào
  `%LOCALAPPDATA%\YouTubeDownloader\YouTubeDownloader.exe` và chạy lại.
  Nếu vẫn lỗi, kiểm tra Windows Security → Protection history xem
  `python311.dll` có bị cách ly không, và thêm thư mục cài đặt vào Exclusions.

## Thay đổi trong 2.2.1 (so với 2.2)

- **Sửa lỗi mở trang Extensions:** trước đây nút 🧩 dùng `webbrowser.open("chrome://extensions")`
  nên Windows báo "Get an app to open this 'chrome' link" (Windows không có app nào
  đăng ký scheme `chrome`). Nay app chạy thẳng `chrome.exe` / `msedge.exe` với URL
  làm đối số, không tìm thấy trình duyệt thì báo rõ cách gõ tay.
- **FFmpeg chỉ cập nhật khi có bản mới hơn:** nút 🎬 giờ đọc bản mới nhất từ link
  redirect của Gyan.dev (vd 9.1) rồi so với bản đang có; đã là bản mới nhất thì
  báo luôn, không tải lại file 119 MB nữa. Không kiểm tra được bản mới thì hỏi
  người dùng có muốn tải lại không.
- **Bấm TẢI VIDEO không có gì xảy ra:** nguyên nhân là protocol `ytdl://` chưa
  đăng ký tới exe (vd chạy portable rồi chọn No, hoặc registry trỏ sai chỗ).
  Nay app tự đăng ký / tự sửa protocol mỗi lần mở (cả chế độ portable), và
  hiện cảnh báo trên thanh trạng thái nếu đăng ký thất bại. Nút trên YouTube
  giờ dùng thẻ `<a>` click, copy link vào clipboard làm dự phòng, và hiện
  toast báo đã gửi link sang app.
- **Thêm file log:** `%LOCALAPPDATA%\YouTubeDownloader\YouTubeDownloader.log`
  ghi lần mở app, link nhận được và lỗi tải FFmpeg, để gửi lại khi cần chẩn đoán.

## Thay đổi trong 2.2 (so với 2.1)

- **1 file exe:** PyInstaller onefile, kèm extension + icon bên trong.
  Lần đầu chạy exe hỏi cài đặt: tự copy vào `%LOCALAPPDATA%`,
  tự đăng ký protocol, tự copy extension, tạo shortcut Desktop.
- **Tự cập nhật app:** nút 🔄 kiểm tra Releases, tải exe mới, tự thay file
  và mở lại. Trước đây nút này chỉ cập nhật yt-dlp qua pip (không có tác
  dụng với bản exe vì yt-dlp đã đóng gói bên trong).
- **Tự cập nhật extension:** exe mới copy đè extension mới, nhắc Reload
  trên `chrome://extensions`. Trước đây extension nạp tay không có đường
  nào cập nhật.
- **Nút Cài Extension 🧩:** copy extension + mở trang Extensions + copy
  đường dẫn vào clipboard, kèm hướng dẫn 3 bước trong app.
- **Sửa lỗi đóng gói:** `ffmpeg_location` và thư mục config trước đây dùng
  `__file__` (khi đóng gói sẽ trỏ vào thư mục tạm `_MEIPASS` rồi mất);
  nay dùng thư mục cài đặt / thư mục chứa exe.
- **Kiểm tra nhanh:** `YouTubeDownloader.exe --version` in ra phiên bản,
  để GitHub Actions kiểm chứng sau khi build.

## Đề xuất chưa làm (để lần sau)

- **Chặn mở trùng app:** bấm nút 2 lần hiện mở 2 cửa sổ. Cần thêm cơ chế
  single-instance (vd socket localhost) để lần bấm sau chuyển link sang cửa
  sổ đang mở thay vì mở cửa sổ mới.
- **Video giới hạn độ tuổi / cần đăng nhập:** yt-dlp sẽ lỗi nếu video yêu
  cầu đăng nhập. Hướng sửa: thêm tùy chọn lấy cookies từ Chrome
  (`--cookies-from-browser`), hiện đang comment sẵn trong code.
- **Chrome Web Store:** nếu đăng extension lên Web Store thì mới ép cài +
  tự cập nhật extension hoàn toàn tự động được (cần tài khoản dev, phí
  đăng ký 1 lần, chờ duyệt).
- **Tiến trình gộp file:** lúc FFmpeg gộp video + audio thì thanh tiến trình
  đứng ở 100% vì yt-dlp không báo tiến độ bước này; có thể hiện trạng thái
  "Đang gộp..." cho rõ.
