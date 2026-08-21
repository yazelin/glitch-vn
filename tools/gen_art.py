#!/usr/bin/env python3
"""批次產圖：走 .11 的 codex-image-service（非同步 job API，可以並行）。

本機那支 codex-imagegen.sh 是序列的，一張 60 到 90 秒；一次要二十幾張就走這裡。
背後是同一個 codex `$imagegen`（gpt-image），不是 gemini。

用法：
    python3 tools/gen_art.py manifest.json
manifest 是 [{"name":"bg-living","prompt":"...","refs":["art/bg-room.jpg"],"size":"1536x1024"}, ...]
產出放 art/out/<name>.png。
"""
import base64, json, pathlib, sys, time, urllib.error, urllib.request

BASE = "https://ching-tech.ddns.net/codex-image"
KEY = pathlib.Path.home().joinpath(".config/codex-image/auth").read_text().strip()
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "art/out"


def _req(url, data=None, method="GET", timeout=90):
    body = json.dumps(data).encode() if data is not None else None
    return json.load(urllib.request.urlopen(
        urllib.request.Request(url, body, H, method=method), timeout=timeout))


def submit(item):
    payload = {"prompt": item["prompt"], "count": 1}
    if item.get("size"):
        payload["size"] = item["size"]
    refs = [base64.b64encode((ROOT / r).read_bytes()).decode() for r in item.get("refs", [])]
    if refs:
        payload["reference_images_base64"] = refs
    r = _req(f"{BASE}/v1/images/jobs", payload, "POST", timeout=180)
    return r["id"]


def main(path):
    OUT.mkdir(parents=True, exist_ok=True)
    items = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    jobs = {}
    for it in items:
        try:
            jobs[submit(it)] = it
            print(f"  送出 {it['name']}")
        except urllib.error.HTTPError as e:
            print(f"  ★ {it['name']} 送不出去：{e.code} {e.read()[:160]!r}")
        time.sleep(1)          # 別一秒打十幾發，服務那邊是輪流用帳號的
    print(f"\n{len(jobs)} 個工作在跑，開始輪詢……")
    done, t0 = {}, time.time()
    while jobs and time.time() - t0 < 2400:
        time.sleep(20)
        for jid in list(jobs):
            try:
                r = _req(f"{BASE}/v1/images/jobs/{jid}")
            except Exception as e:
                print(f"  查詢失敗（會再試）：{e}"); continue
            if r["status"] in ("queued", "running", "processing", "pending"):
                continue
            it = jobs.pop(jid)
            if r["status"] != "succeeded" or not r.get("images"):
                print(f"  ★ {it['name']} 失敗：{r.get('error') or r['status']}")
                continue
            url = r["images"][0]["url"]
            raw = urllib.request.urlopen(url, timeout=180).read()
            # 服務踩過「回上一張舊圖」的坑，所以自己也擋一次重複
            import hashlib
            h = hashlib.sha256(raw).hexdigest()
            if h in done:
                print(f"  ★ {it['name']} 跟 {done[h]} 是同一張圖，丟掉"); continue
            done[h] = it["name"]
            (OUT / f"{it['name']}.png").write_bytes(raw)
            print(f"  ✓ {it['name']}  {len(raw)//1024} KB  （剩 {len(jobs)}）")
    if jobs:
        print(f"\n★ 逾時沒回來：{[v['name'] for v in jobs.values()]}")
    print(f"\n完成 {len(done)} 張 → {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
