"""只改素材包的說明文字：純文字排版，不用 Markdown。素材原封不動送回去。"""
import json, os, time, urllib.request

K = open(os.path.expanduser("~/.config/larch/key")).read().strip()
URL = "https://larch.ink/api/agent/asset-packs/pack-5bb678c9-a6bc-4d19-8680-219d9bf842ed"

DESC = """格莉奇在寫偵探小說，而且寫不完。

她講話用偵探的腔調，推的卻是自己的稿子。每一句聽起來像在審問嫌犯的台詞，其實都是對著自己寫壞的章節講的：「兇手居然是我」是寫到一半發現伏筆是自己埋壞的，「時間線對不上！」是自己的章節時序兜不攏，「動機是什麼？」問的是她筆下那個角色為什麼要做那件事，而她自己也答不出來。

這是偵探小說家的日常，不是偵探的日常。她沒有案子可破，只有一份交不出去的稿。

前 18 張是偵探腔：放大鏡、格紋偵探帽、記事本、打字機、身後一整面紅線板。可以當純推理梗的貼圖用，跟創作完全無關的場合也接得上。

後 9 張回到創作現場：筆電、繪圖板、耳機、瀏覽器分頁，句子也換成創作者的話，「這趴我要修十遍」「分歧選項怎麼選」「卡稿中求救靈感」。

所以同一包能走兩種用法，推理梗，或者創作者之間互相取暖。在 Larch 社群裡討論劇本、分歧、卡稿的時候，後半段那九張是主力。"""

def call(method, body=None):
    r = urllib.request.Request(URL, method=method,
        data=json.dumps(body, ensure_ascii=False).encode() if body else None,
        headers={"Authorization": "Bearer " + K, "Content-Type": "application/json"})
    for i in range(4):
        try:
            with urllib.request.urlopen(r, timeout=300) as f:
                return json.load(f)
        except Exception as e:
            print(" ", method, "第", i+1, "次失敗", repr(e)[:120], flush=True)
            time.sleep(20)
    raise SystemExit(method + " 四次都失敗")

b = call("GET"); b = b.get("pack", b)
assert len(b["assets"]) == 28, len(b["assets"])
call("PUT", {"name": b["name"], "description": DESC, "cover": b["cover"],
             "creator": b["creator"], "category": b["category"],
             "categories": b["categories"], "assets": b["assets"],
             "assetOrder": b["assetOrder"], "summary": "說明改成純文字排版，不用 Markdown"})
a = call("GET"); a = a.get("pack", a)
print("素材仍是", len(a["assets"]), "筆 | emoji",
      sum(1 for x in a["assets"] if x["category"] == "emoji"),
      "| cover 未動", a["cover"] == b["cover"])
print("換行有保住:", "\n" in a["description"], "| 段落數", len([x for x in a["description"].split("\n") if x.strip()]))
print("殘留 Markdown 記號:", [m for m in ("##", "**", "- ", "* ") if m in a["description"]] or "無")
print("---- 線上實際內容 ----")
print(a["description"])
