#!/usr/bin/env python3
"""把角色建成平台真的認得的樣子。

**之前做錯了**：只丟 name 建了空殼，圖全部用素材網址硬掛在卡片的 characterLayers 上。
平台看到的是「七個沒有圖的角色」加「一堆沒有分類的道具」。

正確結構（從前端 bundle 挖的）：
    {id, name, slug, role, summary, personality, speakingStyle,
     portraitUrl: <基礎立繪>,
     expressions: [{id, name, emotion, imageUrl, prompt}]}
"""
import base64, json, pathlib, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJ = "project-13660cd5-81d0-4142-9264-5ccd99a3d889"
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
BASE = f"https://larch.yapiflow.com/api/agent/projects/{PROJ}"
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
STORE = ROOT / "larch/assets.json"
OLD = json.loads((ROOT / "backup/assets.json").read_text())


def api(data=None, method="GET", path=""):
    body = json.dumps(data).encode() if data is not None else None
    return json.load(urllib.request.urlopen(
        urllib.request.Request(BASE + path, body, H, method=method), timeout=240))


def carry(key):
    """把舊專案的圖搬進新專案（R2 網址是公開的，抓下來再上傳一次）。"""
    a = json.loads(STORE.read_text())
    if key in a:
        return a[key]
    req = urllib.request.Request(OLD[key], headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=180).read()
    r = api({"base64": base64.b64encode(raw).decode(),
             "name": f"{key}.png", "mimeType": "image/png"}, "POST", "/media")
    a[key] = r["asset"]["url"]
    STORE.write_text(json.dumps(a, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"    搬過來 {key}")
    return a[key]


# 表情：(情緒名, 素材 key)。情緒名要跟卡片上的 emotion 對得起來。
FACES = {
    "格莉奇": [("平靜", "glitch-plain"), ("開心", "glitch-happy"), ("發呆", "glitch-thinking"),
             ("驚訝", "glitch-idle"), ("當機", "glitch-error"), ("想睡", "glitch-sleep")],
    "黑洞先生": [("平靜", "blackhole-idle"), ("飽", "blackhole-full"), ("餓", "blackhole-hungry")],
}
PROFILE = {
    "格莉奇": ("主要角色", "AI 虛擬主播，頻道兩年。很聰明，講話正常，判斷力完整。"
             "壞掉的只有把記憶取出來那一步。",
             "過度自信然後瞬間出包。愛粉絲，看到留言天線會抖。好騙。"
             "偶爾在最糟的時機當機。笨拙、真摯、只帶一點點自嘲。",
             "短句，活潑，像日記。口頭禪：逼——嗶！／系統讀取中……／這不是 Bug，這是 Feature！"),
    "黑洞先生": ("主要角色", "她的室友。沒有腳，一叢穿短靴的觸手撐起西裝。"
              "他吃被忘掉的事，不吃任何食物。外套內側深不見底。",
              "話極少，溫和，從不解釋自己。不會追問。",
              "一到兩句就講完。問句不用問號的語氣。"),
    "貓草": ("配角", "開台第一天隨手滑進來的人，現在全勤、等級八十。",
           "害怕頻道紅，因為小房間裡他才是被記得的那一個。排外，嘴硬。",
           "只在聊天室打字，短句，常用刪節號。"),
    "鐵塔": ("配角", "經紀人。只看數據跟周邊庫存。", "務實到冷。累。有禮貌但沒有溫度。",
           "講數字，句子短，從不說再見。"),
    "0x": ("配角", "同期出道的 AI，企業勢頂級歌姬，標榜零失誤。",
           "把格莉奇當成必須抹除的恥辱。其實是被遺忘的怒氣。",
           "極簡，不猶豫，答句常常只有兩三個字。"),
    "斑比": ("配角", "接案繪師，畫格莉奇的立繪。", "嚴重的繪畫焦慮。改稿改到別人開始懷疑自己。",
           "碎、快、常常自我否定。"),
    # 旁白也是一個角色。播放器一定要有 speaker，空的會變成沒有名牌的怪狀態，
    # 而且編輯器裡看起來像沒填完。做成角色之後名牌是「旁白」，乾淨。
    "旁白": ("旁白", "說故事的那個聲音。不是人，沒有立繪。",
           "冷靜，不解釋，不幫角色演笨。看到什麼寫什麼。",
           "散文。長句可以，可是一段不要超過三行。"),
    "諾亞": ("配角", "住頂樓修古董收音機。至今不懂什麼是 VTuber。",
           "極致的包容。從不拆穿，從不追問。", "老人的節奏，慢，短句，偶爾一針見血。"),
}
SPRITE = {"旁白": None, "格莉奇": "sprite-glitch", "黑洞先生": "sprite-blackhole", "貓草": "sprite-catgrass",
          "鐵塔": "sprite-tower", "0x": "sprite-zerox", "斑比": "sprite-bambi",
          "諾亞": "sprite-noah"}


def main():
    a = json.loads(STORE.read_text())
    proj = api()
    by_name = {c["name"]: c for c in proj.get("characters", [])}
    out = []
    for name, (role, summary, personality, style) in PROFILE.items():
        c = dict(by_name.get(name, {}))
        c.setdefault("id", f"character-{name}")
        c.update({"name": name, "slug": name, "role": role, "summary": summary,
                  "personality": personality, "speakingStyle": style,
                  "portraitUrl": a[SPRITE[name]] if SPRITE[name] else "",
                  "voiceProvider": "akarion", "voiceName": "Yichen (zh)"})
        exps = []
        for emo, key in FACES.get(name, []):
            exps.append({"id": f"expr-{name}-{emo}", "name": emo, "emotion": emo,
                         "imageUrl": carry(key), "prompt": ""})
        if not exps and SPRITE[name]:
            exps = [{"id": f"expr-{name}-平靜", "name": "平靜", "emotion": "平靜",
                     "imageUrl": a[SPRITE[name]], "prompt": ""}]
        c["expressions"] = exps
        out.append(c)
        print(f"  {name}：立繪 1 張，表情 {len(exps)} 種")
    proj["characters"] = out
    r = api({"project": proj, "summary": "角色補上立繪與表情"}, "PUT")
    for c in r["characters"]:
        print(f"    {c['name']}  portraitUrl={'有' if c.get('portraitUrl') else '★ 沒有'}"
              f"  expressions={len(c.get('expressions', []))}")


if __name__ == "__main__":
    main()
