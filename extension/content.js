setInterval(() => {
    if (!window.location.href.includes("watch") && !window.location.href.includes("/shorts/") && !window.location.href.includes("/live/")) return;
    if (document.getElementById("btn-yt-dl-custom")) return;

    // Quét nhiều lớp container khác nhau của YouTube
    let container = document.querySelector("#top-level-buttons-computed") ||
                    document.querySelector("#actions-inner") ||
                    document.querySelector("#top-row.ytd-watch-metadata #actions");

    if (!container) return;

    let btn = document.createElement("button");
    btn.id = "btn-yt-dl-custom";

    // Biến chứa mã SVG của mũi tên, fill:#ff0000 chính là màu đỏ
    let redIcon = '<svg style="width:18px;height:18px;vertical-align:middle;margin-bottom:3px;fill:#ff0000;" viewBox="0 0 24 24"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>';

    btn.innerHTML = redIcon + " TẢI VIDEO";
    btn.style.cssText = "background-color: #3ea6ff; color: #0f0f0f; font-weight: bold; border: none; border-radius: 18px; padding: 0 16px; height: 36px; cursor: pointer; margin-right: 8px;";

    btn.onclick = () => {
        const url = window.location.href;
        btn.innerHTML = "⏳ Đang mở Tool...";
        // Mo app qua Custom Protocol ytdl:// thay cho Native Messaging.
        // encodeURIComponent de dau & ? = trong link YouTube khong lam vo URL protocol.
        // Vi du: ytdl://https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D...
        // Dung the <a> click thay cho gan window.location.href: Chrome xu ly
        // external protocol on dinh hon, va neu protocol chua dang ky thi
        // trinh duyet se bao loi thay vi im lang khong co gi xay ra.
        try {
            const a = document.createElement("a");
            a.href = "ytdl://" + encodeURIComponent(url);
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (e) {
            window.location.href = "ytdl://" + encodeURIComponent(url);
        }
        // Du phong: copy link vao clipboard de mo app tay va dan neu app khong mo
        try { navigator.clipboard.writeText(url); } catch (e) {}
        // Toast bao cho nguoi dung biet nut da nhan (truoc day bam xong im lang)
        let toast = document.getElementById("ytdl-toast");
        if (!toast) {
            toast = document.createElement("div");
            toast.id = "ytdl-toast";
            toast.style.cssText = "position:fixed;bottom:24px;right:24px;z-index:99999;background:#0f0f0f;color:#fff;font:14px sans-serif;padding:12px 16px;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.4);max-width:360px;";
            document.body.appendChild(toast);
        }
        toast.textContent = "Đã gửi link sang app. Nếu app không mở, kiểm tra app đã cài chưa (link đã copy vào clipboard, mở app tay rồi dán).";
        toast.style.display = "block";
        setTimeout(() => { toast.style.display = "none"; }, 5000);

        // Trả lại icon đỏ sau khi bấm 2 giây
        setTimeout(() => { btn.innerHTML = redIcon + " TẢI VIDEO"; }, 2000);
    };

    container.prepend(btn); // Chèn nút lên đầu cụm Like/Share
}, 2000);
