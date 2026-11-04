"""把候選立繪放進它要用的那一幕背景，旁邊並排現在用的揮手立繪（給作者在比較頁上看進遊戲的樣子）。
站位與大小照 Larch 舞台：立繪高度約畫面 92%，腳貼底。
用法：python3 compose.py <代號> <背景檔名片段> [out]"""
import sys, pathlib
import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).parent
WEBP = HERE.parent / 'main-webp'
NOW = {'glitch': WEBP / '1787364930429_sprite-glitch.webp', 'hole': WEBP / '1787364905531_sprite-blackhole.webp'}


def place(bg, sprite, cx, h_ratio=0.92, bottom=1.0):
    W, H = bg.size
    h = int(H * h_ratio); w = round(sprite.width * h / sprite.height)
    # premultiplied 縮放（cutout skill：直接縮會把幕色混回邊緣）
    a = np.asarray(sprite.convert('RGBA'), np.float32); al = a[..., 3:4] / 255.0
    pre = Image.fromarray(np.concatenate([a[..., :3] * al, a[..., 3:4]], -1).round().astype(np.uint8), 'RGBA').resize((w, h), Image.LANCZOS)
    r = np.asarray(pre, np.float32); al2 = np.clip(r[..., 3:4] / 255.0, 1e-4, 1)
    sp = Image.fromarray(np.concatenate([np.clip(r[..., :3] / al2, 0, 255), r[..., 3:4]], -1).astype(np.uint8), 'RGBA')
    bg.alpha_composite(sp, (int(cx * W - w / 2), int(H * bottom) - h))


def main():
    key, bgpart = sys.argv[1], sys.argv[2]
    out = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else HERE / f'preview/{key}.webp'
    out.parent.mkdir(exist_ok=True)
    bgf = next(WEBP.glob(f'*{bgpart}*.webp'))
    who = 'hole' if key.startswith('hole') else 'glitch'
    panels = []
    # 坐姿：縮小、往上提，坐上背景裡的沙發（Larch 立繪可以設 scale 與 offsetY，遊戲裡照這組數字）
    seat = {'hole-sitting': (0.70, 0.985)}
    for i, sprite in enumerate([Image.open(NOW[who]), Image.open(HERE / f'cut/{key}.png')]):
        bg = Image.open(bgf).convert('RGBA').resize((1280, 720), Image.LANCZOS)
        if i == 1 and key in seat: place(bg, sprite, 0.5, *seat[key])
        else: place(bg, sprite, 0.5)
        panels.append(bg)
    S = Image.new('RGB', (1280 * 2 + 12, 720), (20, 18, 30))
    for i, p in enumerate(panels): S.paste(p.convert('RGB'), (i * (1280 + 12), 0))
    S.save(out, 'WEBP', quality=82)
    print(out)


if __name__ == '__main__':
    main()
