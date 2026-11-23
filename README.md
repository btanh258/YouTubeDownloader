# YouTube Downloader 2.1

Tải video / playlist YouTube bằng yt-dlp, giao diện Tkinter. Bấm nút
**TẢI VIDEO** ngay trên trang YouTube, app tự mở lên với link đã điền sẵn.

## Luồng hoạt động

```
YouTube (extension/content.js)  -- bấm TẢI VIDEO -->
  ytdl://https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D...
    -- Windows (registry HKCU\Software\Classes\ytdl) -->
      pyw.exe app\youtube_gui.py "ytdl://..."
        -- youtube_gui.py bóc link, lấy thông tin, tải bằng yt-dlp + FFmpeg -->
```

Không dùng Native Messaging nên không cần `host.py`, `manifest_native.json`,
file `.crx`/`.pem` hay quyền `nativeMessaging` nữa. Extension chỉ còn
`content.js` + `manifest.json`, ID thay đổi mỗi máy cũng chạy được.

## FFmpeg tự tải / tự cập nhật

- **Lần đầu mở app:** nếu thiếu `ffmpeg.exe` / `ffprobe.exe` (hoặc file bị
  hỏng, nhỏ bất thường, chạy `--version` lỗi), app tự tải bản Essentials
  mới nhất từ [Gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
  (`ffmpeg-release-essentials.zip`, khoảng 119 MB, chỉ 1 lần), chỉ giải nén
  `bin/ffmpeg.exe` + `bin/ffprobe.exe` vào thư mục `app`, kiểm tra chạy được
  mới thay file cũ, file zip tạm luôn được xóa. Có sẵn 2 file này thì app
  dùng luôn, không tải lại.
- **Trước khi tải video:** app kiểm tra lại FFmpeg rồi mới cho yt-dlp tải,
  tránh trường hợp tải xong cả video mới báo lỗi ở bước gộp video + audio.
- **Cập nhật tay:** bấm nút 🎬 trên header để tải lại bản FFmpeg mới nhất.
- **Cập nhật yt-dlp:** bấm nút 🔄, xong khởi động lại app để dùng bản mới.

## Cài đặt (làm 1 lần)

**Yêu cầu:** Python 3.11+ cài từ python.org (kèm Python Launcher `pyw.exe`),
có mạng.

**Bước 1 — Đăng ký protocol:** chạy `register_protocol.bat`.
File này tìm `pyw.exe`, cài `yt-dlp` nếu thiếu, rồi ghi 1 khóa registry
`HKCU\Software\Classes\ytdl` trỏ tới `pyw.exe app\youtube_gui.py`.
Không cần quyền admin. Dời thư mục tool sang chỗ khác thì chạy lại file này.

**Bước 2 — Nạp extension:** mở `chrome://extensions`, bật **Developer mode**,
chọn **Load unpacked**, chọn thư mục `extension`. Làm tương tự trên Edge
(`edge://extensions`) — protocol là của Windows nên dùng chung được cho cả
2 trình duyệt.

**Bước 3 — Dùng:** mở video / Shorts / livestream YouTube, bấm nút
**TẢI VIDEO**. Lần đầu Chrome hỏi thì tick **Always allow** rồi bấm **Open**.
App mở lên, tự điền link (mở tay thì app tự dán link YouTube trong
clipboard) và tự lấy thông tin.

Thử nhanh không cần mở YouTube: bấm `Win+R`, dán rồi Enter:

```
ytdl://https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DdQw4w9WgXcQ
```

## Cấu trúc

```
register_protocol.bat      Đăng ký ytdl:// (chạy 1 lần, không cần admin)
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

## Sửa lỗi trong 2.1 (so với 2.0)

- **FFmpeg:** tự tải khi thiếu/hỏng, kiểm tra trước khi tải video, nút 🎬
  cập nhật tay. Trước đây thiếu FFmpeg thì yt-dlp tải xong mới lỗi ở bước gộp.
- **Lấy thông tin playlist:** trước đây luôn dùng `noplaylist=True` nên lấy
  nhầm tiêu đề video đơn; nay tick Playlist thì quét nhẹ playlist, hiện tên
  playlist + số video.
- **Báo thành công giả:** trước đây `ignoreerrors=True` nên tải lỗi hết vẫn
  hiện popup "ĐÃ TẢI XONG"; nay chỉ báo thành công khi file thật sự tồn tại.
- **Lỗi lấy thông tin:** trước đây `info=None` làm crash và chỉ hiện thông
  báo chung chung; nay hiện đúng lý do yt-dlp trả về.
- **Tải khi chưa lấy thông tin:** nay chặn và nhắc dán link / bấm Lấy thông
  tin trước, thay vì chạy với lựa chọn trống.
- **Tự di chuột:** bỏ trò tự di con trỏ tới nút Tải xuống / nút Đóng (gây khó
  chịu, giật chuột khi đang làm việc khác).
- **Cập nhật yt-dlp:** nay báo rõ phải khởi động lại app mới dùng bản mới.
- **Shorts / live:** nút TẢI VIDEO giờ hiện cả trên Shorts và livestream,
  trước đây chỉ có trang xem thường.
- **Cấu hình:** ghi thư mục gần đây không còn làm mất các khóa khác trong
  `config.json` (vd phiên bản FFmpeg).

## Đề xuất chưa làm (để lần sau)

- **Chặn mở trùng app:** bấm nút 2 lần hiện mở 2 cửa sổ. Cần thêm cơ chế
  single-instance (vd socket localhost) để lần bấm sau chuyển link sang cửa
  sổ đang mở thay vì mở cửa sổ mới.
- **Video giới hạn độ tuổi / cần đăng nhập:** yt-dlp sẽ lỗi nếu video yêu
  cầu đăng nhập. Hướng sửa: thêm tùy chọn lấy cookies từ Chrome
  (`--cookies-from-browser`), hiện đang comment sẵn trong code.
- **Đóng gói exe:** build bằng PyInstaller (như AutoClickTool, dùng GitHub
  Actions) để máy không cài Python vẫn chạy được; khi đó chỉ cần sửa 1 dòng
  trong `register_protocol.bat` cho protocol trỏ tới file exe thay vì `pyw.exe`.
- **Tiến trình gộp file:** lúc FFmpeg gộp video + audio thì thanh tiến trình
  đứng ở 100% vì yt-dlp không báo tiến độ bước này; có thể hiện trạng thái
  "Đang gộp..." cho rõ.
