#!/usr/bin/env python3
"""批次產 BGM：走 .11 的 suno-web（job API，跟 gen_art.py 同一個形狀）。

**一律 instrumental。** API 有 `instrumental` 旗標，可是光靠旗標不夠保險，
prompt 裡也要寫死 no vocals / no lyrics —— 這條線是網頁版自動化，
Simple 模式沒指定的話 Suno 會自己寫詞唱起來。

金鑰在 ~/.bashrc，可是那個檔第 15 行對非互動 shell 就 return 了，
所以這裡自己撈那一行，不要指望 os.environ。

用法：python3 tools/gen_bgm.py bgm-manifest.json
產出放 art/bgm/<name>.mp3
"""
import json, pathlib, re, sys, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "art/bgm"


def _bashrc(name, default=""):
    m = re.search(rf"^export {name}=(.*)$",
                  (pathlib.Path.home() / ".bashrc").read_text(), re.M)
    return m.group(1).strip().strip("\"'") if m else default


BASE = _bashrc("SUNO_WEB_SERVER", "http://192.168.11.11:8071")
H = {"Content-Type": "application/json", "x-api-key": _bashrc("SUNO_WEB_API_KEY")}


def _req(url, data=None, timeout=90):
    body = json.dumps(data).encode() if data is not None else None
    return json.load(urllib.request.urlopen(
        urllib.request.Request(url, body, H), timeout=timeout))


def main(path):
    OUT.mkdir(parents=True, exist_ok=True)
    items = json.loads((ROOT / path).read_text(encoding="utf-8"))
    todo = [it for it in items if not (OUT / f"{it['name']}.mp3").exists()]
    print(f"{len(items)} 首，要生 {len(todo)} 首（已有的跳過）")
    jobs = {}
    for it in todo:
        # 佇列上限預設 10，滿了會回 429，所以送不進去就等
        while True:
            try:
                r = _req(f"{BASE}/api/generate",
                         {"prompt": it["prompt"], "instrumental": True,
                          "timeout": 900}, timeout=60)
                break
            except urllib.error.HTTPError as e:
                if e.code != 429:
                    print(f"  ★ {it['name']} 送不出去：{e.code} {e.read()[:160]!r}")
                    r = None; break
                print("  佇列滿，等 60 秒"); time.sleep(60)
        if not r: continue
        jobs[r["job_id"]] = it
        print(f"  送出 {it['name']}　job {r['job_id']}")
        time.sleep(2)

    print(f"\n{len(jobs)} 單在跑，開始輪詢……")
    t0 = time.time()
    while jobs and time.time() - t0 < 5400:
        time.sleep(30)
        for jid in list(jobs):
            try:
                r = _req(f"{BASE}/api/jobs/{jid}")
            except Exception as e:
                print(f"  查詢失敗（會再試）：{e}"); continue
            if r["status"] in ("queued", "generating"): continue
            it = jobs.pop(jid)
            clips = [c for c in (r.get("clips") or []) if c.get("audio_url")]
            if r["status"] != "done" or not clips:
                print(f"  ★ {it['name']} 失敗：{r.get('error_message') or r['status']}")
                continue
            # 一單通常回兩首，取比較長的那首（短的常常是沒發展完的）
            c = max(clips, key=lambda c: c.get("duration") or 0)
            raw = urllib.request.urlopen(urllib.request.Request(
                BASE + c["audio_url"], headers=H), timeout=300).read()
            (OUT / f"{it['name']}.mp3").write_bytes(raw)
            print(f"  ✓ {it['name']}　{c.get('duration', 0):.0f} 秒　"
                  f"{len(raw)//1024} KB　（剩 {len(jobs)}）")
    if jobs:
        print(f"\n★ 逾時：{[v['name'] for v in jobs.values()]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "art/bgm-manifest.json")
