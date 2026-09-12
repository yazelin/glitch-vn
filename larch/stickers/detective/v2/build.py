"""3x3 表 → 九張 370x320 透明貼圖。切格 → 綠幕去背 → 等比縮進畫布 → 再 despill。"""
import json, subprocess, sys, os
import numpy as np
from PIL import Image

V2 = "/home/ct/glitch-vn/larch/stickers/detective/v2/"
CUT = "/home/ct/.claude/skills/cutout/cutout.py"
W, H = 370, 320
MARGIN_TOP, MARGIN_SIDE, MARGIN_BOTTOM = 16, 12, 8   # 頂端留最多，這次的重點
TMP = V2 + "tmp/"

CAPTIONS = [
 "這案子怪怪的","動機是什麼？","我不相信巧合","靈感又斷線","兇手居然是我","寫不出來啦！",
 "這不合邏輯啊","死者說話了嗎","真相只有一個","真相只有一個！","這很不尋常⋯","兇手就在我們之中",
 "我有個大膽的推測","死者留下的訊息是？","時間線對不上！","別想隱瞞真相","這只是冰山一角","案件解決！",
 "這趴我要修十遍","靈感來了快記下來","立繪這張神好看","劇本卡住算了吧","分歧選項怎麼選","今晚一定要完稿",
 "背景音樂太到位","這個Bug到底在哪","卡稿中求救靈感",
]

def premul_resize(im, size):
    """縮放一定要在 premultiplied alpha 下做，否則透明像素的幕色會混回邊緣。"""
    a = np.asarray(im, np.float32)
    al = a[..., 3:4] / 255.0
    pre = np.concatenate([a[..., :3] * al, a[..., 3:4]], -1)
    r = np.asarray(Image.fromarray(pre.round().astype(np.uint8), "RGBA")
                   .resize(size, Image.LANCZOS), np.float32)
    al2 = np.clip(r[..., 3:4] / 255.0, 1e-4, 1.0)
    rgb = np.clip(r[..., :3] / al2, 0, 255)
    return Image.fromarray(np.concatenate([rgb, r[..., 3:4]], -1)
                           .round().astype(np.uint8), "RGBA")

def run(*args):
    p = subprocess.run([sys.executable, CUT, *args], capture_output=True, text=True)
    if p.returncode:
        raise SystemExit(f"cutout 失敗: {' '.join(args)}\n{p.stdout}\n{p.stderr}")
    return p.stdout.strip()

def build(sheet_no):
    os.makedirs(TMP, exist_ok=True)
    sheet = Image.open(f"{V2}sheet{sheet_no}.png").convert("RGB")
    sw, sh = sheet.size
    cw, ch = sw // 3, sh // 3
    report = []
    for i in range(9):
        n = (sheet_no - 1) * 9 + i
        num = f"{n+1:02d}"
        cx, cy = i % 3, i // 3
        raw = f"{TMP}{num}-raw.png"
        cutp = f"{TMP}{num}-cut.png"
        sheet.crop((cx*cw, cy*ch, (cx+1)*cw, (cy+1)*ch)).save(raw)
        run("key", raw, "-o", cutp)                       # auto 會判到綠幕

        im = Image.open(cutp).convert("RGBA")
        al = np.asarray(im)[..., 3]
        ys, xs = np.nonzero(al > 8)
        im = im.crop((xs.min(), ys.min(), xs.max()+1, ys.max()+1))

        box = (W - 2*MARGIN_SIDE, H - MARGIN_TOP - MARGIN_BOTTOM)
        s = min(box[0]/im.width, box[1]/im.height)
        new = premul_resize(im, (max(1,round(im.width*s)), max(1,round(im.height*s))))
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.paste(new, ((W - new.width)//2, H - MARGIN_BOTTOM - new.height), new)
        out = f"{TMP}{num}-fit.png"
        canvas.save(out)
        run("despill", out, "--key", "green")             # 重採樣後綠會長回來
        report.append((num, CAPTIONS[n], out))
    return report

if __name__ == "__main__":
    for s in [int(x) for x in sys.argv[1:]]:
        for num, cap, out in build(s):
            txt = run("check", out, "--key", "green")
            r = dict(l.split(": ", 1) for l in txt.splitlines() if ": " in l)
            print(f"{num} {cap:<13} 不透明 {r['不透明 px']:>6}  半透明 {r['半透明 px']:>5}  "
                  f"殘留色邊 {r['殘留色邊 px']:>4}  四角全透明 {r['四角全透明']:>5}  "
                  f"背景沒去乾淨 {r['背景沒去乾淨']}")
