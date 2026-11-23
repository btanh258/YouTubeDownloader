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
        btn.innerHTML = "⏳ Đang mở Tool...";
        // Mo app qua Custom Protocol ytdl:// thay cho Native Messaging.
        // encodeURIComponent de dau & ? = trong link YouTube khong lam vo URL protocol.
        // Vi du: ytdl://https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D...
        window.location.href = "ytdl://" + encodeURIComponent(window.location.href);

        // Trả lại icon đỏ sau khi bấm 2 giây
        setTimeout(() => { btn.innerHTML = redIcon + " TẢI VIDEO"; }, 2000);
    };

    container.prepend(btn); // Chèn nút lên đầu cụm Like/Share
}, 2000);
