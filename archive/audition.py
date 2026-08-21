#!/usr/bin/env python3
"""用 gemini-web 代聽,只問二選一或是非題,每題投三票。

開放題(「聽到哪些樂器?」)Gemini 會編:同一個檔案送三次會給三份互相矛盾的
樂器清單(小提琴/電吉他/搖滾鼓)。但強迫選擇題答得準——「鋼琴、吉他、還是
小提琴?」兩次都對,「有沒有人在唱歌?」也對。所以問法一律是比對題。
"""
import base64, json, pathlib, re, sys, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

KEY = re.search(r'GEMINI_IMAGE_KEY\s*=\s*"?([^"\n]+)',
                (pathlib.Path.home()/".bashrc").read_text()).group(1).strip()
B = "https://ching-tech.ddns.net/gemini-web"

QS = [
  ("鼓",   "這段音訊裡聽得到鼓聲或打擊樂節奏嗎?只回「聽得到」或「聽不到」,不要解釋。"),
  ("人聲", "這段音訊裡有沒有人在唱歌或哼唱?只回「有」或「沒有」,不要解釋。"),
  ("質地", "這段音訊比較像「有明確旋律的歌曲」還是「沒有旋律的環境鋪底」?只回其中一個,不要解釋。"),
  ("亮度", "這段音訊的音色偏「明亮」還是偏「低沉」?只回其中一個,不要解釋。"),
]

def ask(args):
    path, q = args
    body = {"prompt": q, "filename": pathlib.Path(path).name, "model": "gemini-3-pro",
            "timeout": 300, "file": base64.b64encode(pathlib.Path(path).read_bytes()).decode()}
    req = urllib.request.Request(f"{B}/api/chat-file", json.dumps(body).encode(),
        {"Content-Type": "application/json", "x-goog-api-key": KEY}, method="POST")
    try:
        r = json.load(urllib.request.urlopen(req, timeout=420))
        return (r.get("text") or r.get("message") or "").strip().replace("\n", " ")[:24]
    except Exception as e:
        return f"錯誤:{e}"

def audition(path, votes=3):
    jobs = [(path, q) for _, q in QS for _ in range(votes)]
    with ThreadPoolExecutor(max_workers=4) as ex:
        out = list(ex.map(ask, jobs))
    res = {}
    for i, (label, _) in enumerate(QS):
        v = out[i*votes:(i+1)*votes]
        top, n = Counter(v).most_common(1)[0]
        res[label] = (top, n, votes, v)
    return res

if __name__ == "__main__":
    for path in sys.argv[1:]:
        print(f"\n### {pathlib.Path(path).name}")
        for label, (top, n, tot, v) in audition(path).items():
            flag = "一致" if n == tot else f"{n}/{tot} 分歧"
            print(f"  {label:4} {top:<14} {flag}   {v}")
