window.addEventListener("beforeunload", (event) => {
    const url = "/_logout/token_" + Date.now();
    const data = new Blob([], { type: "text/plain" });

    // 1️⃣ sendBeacon 시도
    const ok = navigator.sendBeacon(url, data);

    // 2️⃣ 일부 브라우저(특히 Chrome)에서 실패 시 fallback으로 동기 요청
    if (!ok) {
        const xhr = new XMLHttpRequest();
        xhr.open("GET", url, false);  // ⚠️ 동기 모드 (beforeunload용)
        try {
            xhr.send();
        } catch (e) {
            // 무시 — 창 닫을 때 실패 가능
        }
    }
});
