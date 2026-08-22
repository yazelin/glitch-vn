#!/usr/bin/env python3
"""把「使用者聽過、指名要用」的錄音記下來，寫成 art/voice/picked.json。

為什麼要這個：檔名是從畫面上的文字算雜湊的，所以任何重生都會就地覆蓋。
挑過的錄音沒有任何標記的話，一次整批重生就把幾十次試聽的結果洗掉。
實際發生過一次（「第三則是斑比自己轉的」被蓋成唸錯的版本），也差一點
發生第二次（92 句整批重生，停在轉 mp3 之前）。

來源是這台機器上的 session 逐字稿：使用者訊息裡帶 .wav 路徑、而且語氣是
肯定的那些。比對方式是把那支錄音轉出來，跟七章的台詞做模糊比對。

    python3 tools/collect_picks.py <逐字稿.jsonl>
"""
import difflib, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "larch"))
OUT = ROOT / "art/voice/picked.json"
# 肯定：指名要用。否定：當場否決或還在試，那些不算數。
# 肯定放寬到「這個」「可以」「OK」這類；否定只留明確的退回。
YES = re.compile(r"這[個支]|可以|OK|正確|好了|定案|就用|用它")
NO = re.compile(r"不要|不行|不對|不像|會唱|再生|聽看看|試試|可能要改|還是|太過|過於")
CN = re.compile(r"[^一-鿿]")


def messages(jsonl):
    for line in pathlib.Path(jsonl).open(encoding="utf-8"):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("type") != "user":
            continue
        c = d.get("message", {}).get("content")
        if isinstance(c, list):
            c = "".join(x.get("text", "") for x in c if isinstance(x, dict))
        if isinstance(c, str) and len(c) <= 700 and "task-notification" not in c:
            yield d.get("timestamp", ""), c.strip()


def main():
    import voice as V
    sys.path.insert(0, str(ROOT / "tools"))
    from gen_voice import utterances
    import whisper

    picks = {}
    for ts, c in messages(sys.argv[1]):
        if not YES.search(c) or NO.search(c):
            continue
        for f in re.findall(r"'(/[^']+\.wav)'", c):
            if pathlib.Path(f).exists():
                picks[f] = (ts, c.replace("\n", " ")[:120])
    print(f"逐字稿裡肯定語氣的挑選：{len(picks)} 支")

    lines = {k: (w, V.to_speech(t), t) for w, t, e, k in utterances()}
    m = whisper.load_model("large-v3-turbo", device="cuda")
    got = json.loads(OUT.read_text()) if OUT.exists() else {}
    for f, (ts, said) in sorted(picks.items()):
        heard = CN.sub("", m.transcribe(
            f, language="zh", initial_prompt="以下是正體中文的台灣用語對白。")["text"])
        if len(heard) < 3:
            continue
        best, score = None, 0.0
        for k, (w, st, _) in lines.items():
            r = difflib.SequenceMatcher(None, heard, CN.sub("", st)).ratio()
            if r > score:
                best, score = k, r
        if score < 0.6:
            print(f"  對不到台詞（{score:.2f}）：{pathlib.Path(f).name}")
            continue
        w, _, t = lines[best]
        got[best] = {"speaker": w, "text": t, "source": f,
                     "said": said, "when": ts, "match": round(score, 2)}
        print(f"  {best} {w}　{pathlib.Path(f).name}　比對 {score:.2f}")
    OUT.write_text(json.dumps(got, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n寫好 {len(got)} 筆 → {OUT}")


if __name__ == "__main__":
    main()
