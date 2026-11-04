"""去背好的圖裁成跟現在正篇立繪同一個版型，存成 sprite/<代號>.webp（換進遊戲的就是這些）。

現在的 sprite-glitch 是貼齊人物裁的（頭頂到鞋底＝整張高），舞台上的大小照圖高算，所以新圖也要貼齊，不然人會變小、浮起來。
左右以腿的中心對稱，不用外框中心：直播面板、攪拌盆在身體一側，用外框中心人會偏離站位。
表情差分先用下半身對齊到同姿勢的原圖（臉和手勢會變，不拿來對），再用原圖那一框裁，換表情時身體不會跳。
用法：python3 crop.py [代號 ...]
"""
import pathlib, sys
import cv2, numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).parent
CUT, OUT = HERE / 'cut', HERE / 'sprite'


def box(a):
    m = a > 16; ys, xs = np.where(m); top, bot = int(ys.min()), int(ys.max())
    legs = np.where(m[bot - (bot - top) // 4: bot + 1])[1]   # 下四分之一＝腿和鞋
    cx = float(np.median(legs)); hw = max(cx - xs.min(), xs.max() - cx) + 4
    return int(round(cx - hw)), top, int(round(cx + hw)), bot + 1


def premul_warp(rgba, M, size):
    """預乘 alpha 再重採樣（直接內插會把透明處的黃幕混回邊緣），做完再除回來。"""
    a = rgba.astype(np.float32); al = a[..., 3:4] / 255
    pre = np.concatenate([a[..., :3] * al, a[..., 3:4]], -1)
    w = cv2.warpAffine(pre, M, size, flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    al2 = np.clip(w[..., 3:4] / 255, 1e-4, 1)
    return np.concatenate([np.clip(w[..., :3] / al2, 0, 255), np.clip(w[..., 3:4], 0, 255)], -1).round().astype(np.uint8)


def align(var, base):
    """回傳對齊後的 var 與相關係數。只拿腿那一段（人物高度 60% 以下）來對。"""
    gray = lambda x: cv2.cvtColor(np.asarray(Image.alpha_composite(Image.new('RGBA', (x.shape[1], x.shape[0]), (128, 128, 128, 255)), Image.fromarray(x)).convert('RGB')), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    m = base[..., 3] > 16; ys = np.where(m)[0]; top, bot = ys.min(), ys.max()
    mask = np.zeros(m.shape, np.uint8); mask[top + (bot - top) * 6 // 10: bot + 1] = 255
    warp = np.eye(2, 3, dtype=np.float32)
    cc, warp = cv2.findTransformECC(gray(base), gray(var), warp, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-7), mask, 5)
    return premul_warp(var, warp, (var.shape[1], var.shape[0])), cc, warp


def save(rgba, b, out):
    l, t, r, bt = b
    canvas = Image.new('RGBA', (r - l, bt - t), (0, 0, 0, 0)); canvas.paste(Image.fromarray(rgba), (-l, -t))
    canvas.save(out, 'WEBP', quality=86, method=6)   # 跟 larch/main_cdn.py 同一組參數
    return canvas.size


def main():
    OUT.mkdir(exist_ok=True)
    keys = [a for a in sys.argv[1:]] or sorted(p.stem for p in CUT.glob('glitch-*.png') if '-on-' not in p.stem)
    for k in keys:
        a = np.asarray(Image.open(CUT / f'{k}.png').convert('RGBA'))
        base_key = next((p for p in ('talk', 'stream', 'rulebook', 'hands', 'baking') if k.startswith(f'glitch-{p}-')), None)
        if base_key:
            base = np.asarray(Image.open(CUT / f'glitch-{base_key}.png').convert('RGBA'))
            a, cc, w = align(a, base)
            b = box(base[..., 3]); note = f'對齊 {base_key}（腿部相關 {cc:.3f}，位移 {w[0, 2]:+.1f},{w[1, 2]:+.1f}px，縮放 {w[0, 0]:.3f}/{w[1, 1]:.3f}）'
            # 手勢伸出原圖那一框（在算那張的手）：左右以同一個中心對稱放寬，高度不動（舞台照圖高縮放，人才不會變大小）
            xs = np.where(a[..., 3] > 16)[1]; cx = (b[0] + b[2]) / 2; hw = max(cx - xs.min(), xs.max() - cx, (b[2] - b[0]) / 2) + 4
            if hw > (b[2] - b[0]) / 2 + 4: b = (int(round(cx - hw)), b[1], int(round(cx + hw)), b[3]); note += f'，左右放寬到 {b[2] - b[0]}px'
            ys = np.where(a[..., 3] > 16)[0]
            if ys.min() < b[1] or ys.max() >= b[3]: note += f'，★ 上下超出框 {b[1] - ys.min()}/{ys.max() - b[3] + 1}px'
        else:
            b = box(a[..., 3]); note = ''
        print(k, save(a, b, OUT / f'{k}.webp'), note)


if __name__ == '__main__':
    main()
