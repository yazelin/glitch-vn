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


def api(data=None, method="GET", path="", tries=4):
    body = json.dumps(data).encode() if data is not None else None
    for i in range(tries):
        try:
            return json.load(urllib.request.urlopen(
                urllib.request.Request(BASE + path, body, H, method=method), timeout=300))
        except urllib.error.HTTPError as e:
            if e.code < 500 or i == tries - 1:
                raise
            print(f"  Larch 回 {e.code}，{2 ** i * 5} 秒後重試")
            time.sleep(2 ** i * 5)
