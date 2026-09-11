"""專案 id 與 API 共用設定。**只在這裡寫一次。**

要換到新專案，改 PROJ 這一行就好。
"""
import json, pathlib, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJ = "project-bec1644c-0dfe-4447-86c0-0c592e2f939f"
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
BASE = f"https://larch.ink/api/agent/projects/{PROJ}"
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
STORE = ROOT / "larch/assets.json"


# 平台 2026-09-08 起在寫入端點上加了樂觀鎖：每個回應帶 `ETag: "<整數>"`，
# PUT 要原樣放進 `If-Match`。少了回 428 PROJECT_REVISION_REQUIRED，
# 拿舊的回 409 PROJECT_REVISION_CONFLICT（編輯器分頁開著就會一直墊高版本）。
# 所以這裡記住每個路徑最新的 ETag，PUT 之前先讀一次，409 就重抓再送。
ETAGS = {}


def api(data=None, method="GET", path="", tries=4):
    body = json.dumps(data).encode() if data is not None else None
    if method == "PUT" and path not in ETAGS:
        api(path=path)
    for i in range(tries):
        head = dict(H)
        if method == "PUT" and ETAGS.get(path):
            head["If-Match"] = ETAGS[path]
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    BASE + path, body, head, method=method), timeout=300) as r:
                tag = r.headers.get("ETag")
                if tag:
                    ETAGS[path] = tag
                elif method == "PUT":
                    ETAGS.pop(path, None)
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 409 and i < tries - 1:
                print("  Larch 回 409（版本被墊高），重抓 ETag 再送")
                ETAGS.pop(path, None)
                api(path=path)
                time.sleep(2)
                continue
            if e.code < 500 or i == tries - 1:
                raise
            print(f"  Larch 回 {e.code}，{2 ** i * 5} 秒後重試")
            time.sleep(2 ** i * 5)
