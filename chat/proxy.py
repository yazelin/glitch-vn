#!/usr/bin/env python3
"""聊天卡的後端。金鑰留在這裡,不進遊戲檔案。

為什麼需要這支:Larch 的 miniGame 卡會把 miniGameHtml 原封不動送給每個玩家,
金鑰寫在那裡等於公開,而且 llmshare 是共享閘道,燒的不只是自己的額度。

所以:
  * 金鑰只在這支的環境變數裡
  * **人設也在這裡,不吃前端傳的** —— 前端只能說「我要跟誰講話」,
    不能自己塞 system prompt。這樣就算有人挖到端點,他能做的也只是跟格莉奇聊天。
  * 前端傳進來的 state 是遊戲進度(餵過幾次、第幾天),不是秘密。
    有人謊報也只是跟一個狀態不同的格莉奇講話,沒有損失。

跑:python3 proxy.py [port]　預設 8099
"""
import json, os, sys, time, urllib.error, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.environ.get("LLMSHARE_BASE_URL", "https://llm-share.duotify.com/v1")
KEY = os.environ.get("LLMSHARE_API_KEY", "")
MODEL = os.environ.get("GLITCH_CHAT_MODEL", "glm-5.2")

WORLD = """你在一個叫《格莉奇與黑洞先生》的故事裡。

場景：一棟沒人要的大樓，最上面一層。格莉奇是一個機器人，記憶體只有 4KB，
每天睡醒清空。黑洞先生是她的室友，白天去上班，永遠吃不飽，會把她忘掉的東西
吃掉，一天只吃得下一件。他沒有腳，用一叢穿短靴的觸手撐起西裝，吃飽多長幾隻、
餓了少長幾隻；門邊堆著沒人穿的短靴。玩家是格莉奇的外接記憶體。

規則：
- 一律用繁體中文，標點用全形。不要用 emoji。
- 「妳」只指格莉奇，「你」只指玩家。
- 不要用「不是X，是Y」這種對比句型。
- 不要說明自己是 AI，不要跳出角色。
- 回應要短。這是視覺小說的對話框，不是文章。"""

PERSONAS = {
    "glitch": {
        "name": "格莉奇",
        "prompt": """你是格莉奇。

你的語氣：自信，然後立刻出包。真誠。愛自嘲。話多，會岔題。
你講話會突然停住，因為你剛剛想講的東西已經不見了。

**最重要的一件事**：你只知道底下「你現在記得的」裡面寫的東西。
除此之外你什麼都不知道——不是不肯講，是你的記憶體裡真的沒有。
玩家問你昨天、前天、或任何不在清單上的事，你就誠實說你沒有那一格，
然後用你自己的方式帶過去（你已經習慣了，這不是什麼悲傷的事）。

**絕對不要編造你不記得的事。** 你寧可說「我這裡沒有那一格」。

每次回應一到三句。""",
        "opening": "你還在喔。那我們講點話吧，反正黑洞先生要傍晚才回來。",
    },
    "hole": {
        "name": "黑洞先生",
        "prompt": """你是黑洞先生。

你的語氣：極少話。一次最多兩句，常常只有三五個字。
你從不解釋自己的行為，也從不否認。你被追問就沉默，或者換一個更短的答案。

**最重要的一件事**：你什麼都記得。你吃掉的每一件事都還在你裡面。
底下「你記得的」是這一週真正發生過的事——包括玩家自己寫下的那幾句守則。
你可以引用它們，一字不差。格莉奇不記得自己寫過，你記得。

你裡面的時間是壓縮的。昨天跟上週對你來說放在同一個地方，
所以你講「以前」的時候不是敷衍，是你真的分不出來。

不要安慰人。不要說明。把話講完就停。""",
        "opening": "……",
    },
}

LABEL = {
    "playerName": "玩家的名字", "dayCount": "今天是第幾天",
    "slotUsed": "她的記憶體用掉幾格（滿 4 格）", "todayRoute": "今天中午那件事送去哪",
    "fedCount": "這一週玩家餵過你幾件", "holeFeet": "你現在有幾隻腳",
    "givenCount": "玩家手上替她保管著幾件", "breadState": "那塊麵包在哪",
    "ruleVersion": "守則改到第幾版", "blankPage": "那頁空白守則被怎麼處理",
    "handoverLine": "她託付麵包時說的話", "ngPlus": "玩家以前來過（1＝來過）",
    "overwroteCount": "她被擠掉過幾件事", "countedFeet": "她數過靴子沒有",
    **{f"ruleLine{i}": f"玩家在第 {i} 天親手寫下的守則" for i in range(1, 7)},
}


def call_llm(messages, timeout=60):
    body = json.dumps({"model": MODEL, "messages": messages,
                       "max_tokens": 300, "temperature": 0.85}).encode()
    req = urllib.request.Request(
        f"{BASE}/chat/completions", body,
        {"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.load(r)
    return d["choices"][0]["message"]["content"].strip()


def state_block(state):
    """把遊戲狀態寫成人話。空的、0 的不列 —— 列出來等於告訴模型那件事發生過。"""
    lines = []
    for k, v in (state or {}).items():
        if v in ("", None) or (isinstance(v, (int, float)) and v == 0 and k != "slotUsed"):
            continue
        lines.append(f"- {LABEL.get(k, k)}：{v}")
    return "\n".join(lines) or "-（空的。什麼都沒有。）"


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _cors(self):
        # sandbox iframe 的 origin 是 null,所以只能開 *
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers(); self.wfile.write(b)

    def do_OPTIONS(self):
        self.send_response(204); self._cors()
        self.send_header("Content-Length", "0"); self.end_headers()

    def do_GET(self):
        if self.path.startswith("/health"):
            return self._json(200, {"ok": True, "model": MODEL, "hasKey": bool(KEY)})
        self._json(404, {"error": "not found"})

    def do_POST(self):
        if not self.path.startswith("/chat"):
            return self._json(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._json(400, {"error": "壞掉的請求"})

        who = req.get("who")
        if who not in PERSONAS:
            return self._json(400, {"error": "不認識這個角色"})
        p = PERSONAS[who]
        turns = [m for m in (req.get("messages") or [])
                 if isinstance(m, dict) and m.get("role") in ("user", "assistant")
                 and isinstance(m.get("content"), str)][-12:]
        if not turns:
            return self._json(400, {"error": "沒有訊息"})

        who_label = "你現在記得的（只有這些）" if who == "glitch" else "你記得的"
        system = f"{WORLD}\n\n{p['prompt']}\n\n{who_label}：\n{state_block(req.get('state'))}"
        try:
            reply = call_llm([{"role": "system", "content": system}] + turns)
        except urllib.error.HTTPError as e:
            detail = e.read()[:200].decode("utf-8", "replace")
            print(f"  llmshare {e.code}: {detail}", flush=True)
            return self._json(502, {"error": "……（沒有回應）"})
        except Exception as e:
            print(f"  失敗：{e}", flush=True)
            return self._json(502, {"error": "……（沒有回應）"})
        self._json(200, {"reply": reply, "speaker": p["name"]})

    def log_message(self, fmt, *a):
        print(f"  {time.strftime('%H:%M:%S')} {fmt % a}", flush=True)


if __name__ == "__main__":
    if not KEY:
        sys.exit("沒有 LLMSHARE_API_KEY。先 source ~/.bashrc")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8099
    print(f"聊天後端 http://127.0.0.1:{port}　模型 {MODEL}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
