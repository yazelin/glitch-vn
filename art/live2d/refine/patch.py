"""把生成的閉眼／張嘴臉對齊回原圖，摳出眼睛與嘴，寫進 Live2D 圖層。
用法：python3 patch.py closed out_closed.png   → 更新 22_lid_R / 23_lid_L
      python3 patch.py mouth  out_mouth.png    → 更新 42_mouth_A
輸出到 ./layers_out/，不動原始 layers/。"""
import sys, os, numpy as np, cv2
from PIL import Image, ImageDraw

LAYERS = '/home/ct/glitch-vn/art/live2d/layers'
OUT = 'layers_out'; os.makedirs(OUT, exist_ok=True)
S = 2                                          # 圖層畫布是原圖的 2x
BOX = tuple(map(int, open('in_geo.box').read().split()))   # 1x 座標的臉部裁框
GEO_SCALE = 840 / (BOX[2]-BOX[0])              # in_geo 是裁框放大到 840
W, H = 1196, 3072

def load_rgb(p, size=None):
    im = Image.open(p).convert('RGB')
    if size and im.size != size: im = im.resize(size, Image.LANCZOS)
    return np.asarray(im)

def align(gen, ref):
    """把 gen 仿射對齊到 ref。回 (對齊後影像, ECC 分數)。"""
    g = cv2.cvtColor(gen, cv2.COLOR_RGB2GRAY).astype(np.float32)/255
    r = cv2.cvtColor(ref, cv2.COLOR_RGB2GRAY).astype(np.float32)/255
    warp = np.eye(2, 3, dtype=np.float32)
    crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6)
    try:
        cc, warp = cv2.findTransformECC(r, g, warp, cv2.MOTION_AFFINE, crit, None, 5)
    except cv2.error as e:
        return None, 0.0
    out = cv2.warpAffine(gen, warp, (ref.shape[1], ref.shape[0]),
                         flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
    return out, float(cc)

def to_canvas(face840):
    """840x840 的臉 → 貼回 2x 圖層畫布上的正確位置（其餘透明）。"""
    w1 = BOX[2]-BOX[0]; h1 = BOX[3]-BOX[1]
    face2x = cv2.resize(face840, (w1*S, h1*S), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((H, W, 3), np.uint8)
    canvas[BOX[1]*S:BOX[3]*S, BOX[0]*S:BOX[2]*S] = face2x
    return canvas

def ellipse_mask(cx, cy, rx, ry):
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).ellipse([(cx-rx)*S, (cy-ry)*S, (cx+rx)*S, (cy+ry)*S], fill=255)
    return np.asarray(m) > 0

def write_layer(name, rgb_canvas, alpha_mask, feather=1.0):
    al = cv2.GaussianBlur((alpha_mask.astype(np.uint8)*255), (0, 0), feather)
    out = np.dstack([rgb_canvas, al])
    Image.fromarray(out, 'RGBA').save(f'{OUT}/{name}.png')
    print(f'  寫入 {OUT}/{name}.png  不透明 {int((al>128).sum())} px')

mode, gen_path = sys.argv[1], sys.argv[2]
ref = load_rgb('in_geo.webp'); gen = load_rgb(gen_path, (840, 840))
aligned, cc = align(gen, ref)
print(f'ECC = {cc:.4f}  ({"通過" if cc >= 0.98 else "未達 0.98，對不準，先別用"})')
if mode != 'closed' and (aligned is None or cc < 0.98): sys.exit(2)
if aligned is not None: Image.fromarray(aligned).save(f'aligned_{mode}.png')
canvas = to_canvas(aligned if aligned is not None else gen)

if mode == 'closed':
    # 眼皮：ECC 對不了「睜 vs 閉」。改抓生成圖裡的兩道深色眼皮線（眼睛附近唯一的深色長條），
    # 量其中心與寬度，用相似變換對到已知的眼睛中心／寬度，貼進眼睛橢圓。
    from scipy import ndimage
    g = gen.astype(int); dark = (g.sum(2) < 330)
    band = np.zeros(dark.shape, bool); band[int(840*.25):int(840*.62), :] = True       # 眼睛所在的水平帶
    lab, n = ndimage.label(dark & band)
    blobs = []
    for k in range(1, n+1):
        ys, xs = np.nonzero(lab == k)
        if len(xs) < 150: continue
        w = xs.max()-xs.min()+1; h = ys.max()-ys.min()+1
        if w < 60 or w/h < 1.6: continue                                         # 眼皮線：寬、扁
        blobs.append((xs.mean(), ys.mean(), w, h, len(xs)))
    blobs.sort(key=lambda b: b[0])
    print('  深色扁長 blob:', [(int(b[0]), int(b[1]), int(b[2]), int(b[3])) for b in blobs])
    assert len(blobs) >= 2, '找不到兩道眼皮線'
    # 左右各取離眼睛目標最近的一個
    targets = [('22_lid_R', (226, 270, 33, 29)), ('23_lid_L', (323, 239, 34, 31))]
    for name, (cx, cy, rx, ry) in targets:
        tx = (cx - BOX[0]) * GEO_SCALE; ty = (cy - BOX[1]) * GEO_SCALE
        b = min(blobs, key=lambda b: (b[0]-tx)**2 + (b[1]-ty)**2)
        bx, by, bw = b[0], b[1], b[2]
        sc = (2*rx*GEO_SCALE*0.92) / bw                                          # 閉眼線約佔眼寬 92%
        # 相似變換：以 blob 中心為錨，縮放 sc，平移到眼睛中心（眼皮線在眼睛中心略上方 → 往上 12%）
        M = np.array([[sc, 0, tx - sc*bx], [0, sc, (ty - ry*GEO_SCALE*0.12) - sc*by]], np.float32)
        warped = cv2.warpAffine(gen, M, (840, 840), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        # 只取「線條」：深色程度當遮罩，限制在眼皮 blob 外擴一圈內（避免把髮絲輪廓也當線）
        lum = warped.astype(np.float32).sum(2) / 3
        stroke = np.clip((205 - lum) / 110, 0, 1)
        bb = np.zeros((840, 840), bool)
        bw_s, bh_s = b[2]*sc, b[3]*sc
        bb[int(ty - ry*GEO_SCALE*0.12 - bh_s*0.9):int(ty - ry*GEO_SCALE*0.12 + bh_s*0.9), int(tx - bw_s*0.62):int(tx + bw_s*0.62)] = True
        stroke *= bb
        # 底：既有臉底層的膚色（沒有眼睛），疊上線條
        fb = np.asarray(Image.open(f'{LAYERS}/10_face_base.png').convert('RGB'))
        fb840 = cv2.resize(fb[BOX[1]*S:BOX[3]*S, BOX[0]*S:BOX[2]*S], (840, 840), interpolation=cv2.INTER_LINEAR)
        a3 = stroke[..., None]
        full = (fb840 * (1 - a3) + warped * a3).round().astype(np.uint8)
        print(f'  {name}: blob 中心 ({bx:.0f},{by:.0f}) 寬 {bw} → 縮放 {sc:.2f}，線條像素 {int((stroke>0.5).sum())}')
        write_layer(name, to_canvas(full), ellipse_mask(cx, cy, rx, ry), feather=3.0)
elif mode == 'mouth':
    # 開口層：範圍取「跟原圖差異明顯」的區域 ∩ 嘴附近，讓 alpha 貼著新嘴的實際大小
    orig = to_canvas(ref)
    diff = np.abs(canvas.astype(int) - orig.astype(int)).sum(2) > 60
    near = ellipse_mask(287, 316, 40, 26)                # 嘴附近的搜尋範圍（1x）
    m = diff & near
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)) > 0
    m = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    ys, xs = np.nonzero(m); print(f'  新嘴範圍@2x x{xs.min()}-{xs.max()} y{ys.min()}-{ys.max()}')
    write_layer('42_mouth_A', canvas, m)
