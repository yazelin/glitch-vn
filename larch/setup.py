#!/usr/bin/env python3
"""素材與角色的正確做法。跑這一支就會把兩邊弄到一致。

照 Larch 自己的角色工坊提示詞來做，不要自己發明：

  上傳素材   POST /media   {name, mimeType, base64, category}
             category: scene 場景／character 立繪／prop 道具
             **沒帶 category 全部會掉進道具。**

  更新角色   POST /characters  {characterId, ...要改的欄位}
             只覆蓋你傳的欄位，其餘保留。**用 id 會變成新增一個重複角色。**
             差分：expressions:[{name, emotion, imageUrl, kind:"expression"}]

整包 PUT 專案也寫得進去，可是角色工坊那一頁不見得認，而且很容易把
媒體庫弄亂（我踩過：PUT 之後清理孤兒素材，把還在用的立繪紀錄整組刪掉）。
"""
import base64, json, pathlib, sys, urllib.request
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJ = "project-13660cd5-81d0-4142-9264-5ccd99a3d889"
KEY = pathlib.Path.home().joinpath(".config/larch/key").read_text().strip()
B = f"https://larch.yapiflow.com/api/agent/projects/{PROJ}"
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
STORE = ROOT / "larch/assets.json"
OLDA = json.loads((ROOT / "backup/assets.json").read_text())


def api(data=None, method="GET", path=""):
    body = json.dumps(data).encode() if data is not None else None
    return json.load(urllib.request.urlopen(
        urllib.request.Request(B + path, body, H, method=method), timeout=300))


def upload(name, raw, category, mime="image/png"):
    r = api({"name": name, "mimeType": mime, "category": category,
             "base64": base64.b64encode(raw).decode()}, "POST", "/media")
    return r["asset"]["url"]


def bg16x9(path):
    im = Image.open(path).convert("RGB")
    h = int(im.width * 9 / 16)
    top = (im.height - h) // 2
    return im.crop((0, top, im.width, top + h)).resize((1920, 1080), Image.LANCZOS)


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0"}), timeout=180).read()


SPRITE = {"格莉奇": "sprite-glitch", "黑洞先生": "sprite-blackhole", "貓草": "sprite-catgrass",
          "鐵塔": "sprite-tower", "0x": "sprite-zerox", "斑比": "sprite-bambi",
          "諾亞": "sprite-noah"}
FACES = {  # 現成的差分。剩下五個角色的差分還沒畫。
    "格莉奇": [("平靜", "glitch-plain"), ("開心", "glitch-happy"), ("發呆", "glitch-thinking"),
             ("驚訝", "glitch-idle"), ("當機", "glitch-error"), ("想睡", "glitch-sleep")],
    "黑洞先生": [("平靜", "blackhole-idle"), ("飽", "blackhole-full"), ("餓", "blackhole-hungry")],
}
PROFILE = {
    "旁白": ("旁白", "說故事的那個聲音。不是人，沒有立繪。",
           "冷靜。不解釋規則，不幫角色演笨。看到什麼寫什麼。",
           "散文。一段不超過三行。", ""),
    "格莉奇": ("主要角色", "AI 虛擬主播，頻道兩年。",
             "她很聰明，講話正常，判斷力完整。壞掉的只有把記憶取出來那一步："
             "她知道有某件事、知道自己在乎過，就是叫不出內容。愛粉絲，看到留言天線會抖。"
             "過度自信然後瞬間出包。偶爾在最糟的時機當機。",
             "短句，活潑，像日記。卡住的時候會精準描述那個洞的形狀，"
             "不會茫然。口頭禪：逼——嗶！（開機）／系統讀取中……（提取慢）／"
             "這不是 Bug，這是 Feature！（自嘲，很少用）",
             "她的守則本第一頁有七行，只有六個名字。第七行是她自己寫的一句話："
             "「還有一個。不要問他是誰。」她不知道那是誰，也不知道自己為什麼每天照抄。"),
    "黑洞先生": ("主要角色", "她的室友。沒有腳，一叢穿短靴的觸手撐起西裝。",
              "吃被忘掉的事，不吃任何食物。吃進去的永遠在他裡面，可是拿不出來。"
              "話極少，溫和，從不解釋自己，不會追問。",
              "一到兩句就講完。問句不用問號的語氣。",
              "他是開台第一天那七個人裡的第七個，帳號 @Zero_Point，那天一句話都沒打。"
              "後來他求她把他忘掉，而她答應了。她撕掉的那七百多頁在他外套裡。"),
    "貓草": ("配角", "開台第一天隨手滑進來的人，現在全勤、等級八十。",
           "害怕頻道紅。小房間裡他才是被記得的那一個，所以人一多他就發酸。排外，嘴硬，"
           "可是問到某個地方會自己停下來。",
           "只在聊天室打字。短句，常用刪節號，不打標點。", ""),
    "鐵塔": ("配角", "經紀人。只看數據跟周邊庫存。",
           "務實到冷。累。他發現她的毛病有話題性，正在阻止她修好。"
           "可是他會注意到別人的聲音——那是他唯一還剩的溫柔，而且被 KPI 用掉了。",
           "講數字。句子短。從不說再見。",
           "開台第一天下播後，他私訊誇過她「聲音很有溫度」。兩個人都不記得了。"),
    "0x": ("配角", "同期出道的 AI，企業勢頂級歌姬，標榜零失誤。",
           "把格莉奇當成必須抹除的恥辱。真正的理由是被遺忘的怒氣："
           "她拒絕過幫格莉奇記，然後還是記了兩年。",
           "極簡，不猶豫。答句常常只有兩三個字。耳邊的穩定度數字會洩漏她的情緒。",
           "她記得第七個人的 ID 是 @Zero_Point，兩年來一個字都沒說。"),
    "斑比": ("配角", "接案繪師，畫格莉奇的立繪。",
           "嚴重的繪畫焦慮。為了畫出無瑕的神作，她把稿改到別人開始懷疑自己記錯。",
           "碎、快、常常自我否定。講到畫面細節的時候會突然變得很精準。",
           "她從開台第五天就在截圖存參考圖，兩年份。她自己不知道那是一份檔案。"),
    "諾亞": ("配角", "住頂樓修古董收音機。至今不懂什麼是 VTuber。",
           "極致的包容。從不拆穿，從不追問。他只把她當隔壁那個常把自己鎖在門外的小姑娘。",
           "老人的節奏，慢，短句，偶爾一針見血。",
           "他是那七個人之一，而他自己不知道。兩年前他誤觸孫子的平板，"
           "以為那是一台會發光的收音機。"),
}


def main():
    # **沿用既有的 assets.json，不要從空的重建。** 從空的開始有兩個後果：
    # 每次都重傳一次（素材庫長出一堆重複），而且會蓋掉別支腳本加的鍵（封面）。
    force = "--force" in sys.argv
    assets = json.loads(STORE.read_text()) if STORE.exists() else {}

    def need(k):
        return force or k not in assets

    print("素材（帶 category）")
    for p in sorted((ROOT / "art/out").glob("bg-*.png")):
        if not need(p.stem): continue
        im = bg16x9(p); im.save("/tmp/_b.jpg", quality=88, optimize=True)
        assets[p.stem] = upload(f"{p.stem}.jpg", pathlib.Path("/tmp/_b.jpg").read_bytes(),
                                "scene", "image/jpeg")
        print(f"  scene      {p.stem}")
    for p in sorted((ROOT / "art").glob("sprite-*.png")):
        if not need(p.stem): continue
        assets[p.stem] = upload(p.name, p.read_bytes(), "character")
        print(f"  character  {p.stem}")
    for key in [k for v in FACES.values() for _, k in v]:
        if not need(key): continue
        assets[key] = upload(f"{key}.png", fetch(OLDA[key]), "character")
        print(f"  character  {key}")
    for d in ("art/avatar", "art/chat"):
        for p in sorted((ROOT / d).glob("*.png")):
            if not need(p.stem): continue
            assets[p.stem] = upload(p.name, p.read_bytes(), "prop")
            print(f"  prop       {p.stem}")
    STORE.write_text(json.dumps(assets, ensure_ascii=False, indent=1), encoding="utf-8")

    print("\n角色（POST /characters，帶 characterId）")
    have = {c["name"]: c["id"] for c in api().get("characters", [])}
    for name, (role, summary, personality, style, secrets) in PROFILE.items():
        body = {"name": name, "role": role, "summary": summary,
                "personality": personality, "speakingStyle": style, "secrets": secrets}
        if name in have:
            body["characterId"] = have[name]
        if SPRITE.get(name):
            body["portraitUrl"] = assets[SPRITE[name]]
            body["expressions"] = [
                {"name": emo, "emotion": emo, "imageUrl": assets[key], "kind": "expression"}
                for emo, key in FACES.get(name, [("平靜", SPRITE[name])])]
        api(body, "POST", "/characters")
        print(f"  {name}：立繪 {'有' if SPRITE.get(name) else '無（旁白）'}"
              f"　差分 {len(body.get('expressions', []))}")

    print("\n讀回來確認")
    for c in api().get("characters", []):
        print(f"  {c['name']:5s} portraitUrl={'有' if c.get('portraitUrl') else '無'}"
              f"　expressions={len(c.get('expressions') or [])}"
              f"　secrets={'有' if c.get('secrets') else '無'}")
    from collections import Counter
    print("\n素材庫：", Counter(m.get("category") or "沒分類" for m in api().get("media", [])))


if __name__ == "__main__":
    main()
