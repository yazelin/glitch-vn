"""sprite-glitch.png → Live2D 分層 PSD。
切法：由前往後，每層取「自己的多邊形 ∩ 還沒被前面的層拿走」。
補法：只補「被排在我上面的層拿走的像素」，加 12px 安全邊，並夾在角色輪廓內。
      這條規則是關鍵——用整個多邊形當補的範圍會蓋掉鄰居。"""
import os, glob, numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage

S, SRC = 2, '/home/ct/glitch-vn/art/sprite-glitch.png'
_im = Image.open(SRC).convert('RGBA')
_a = np.asarray(_im, np.float32); _al = _a[..., 3:4]/255.0
_pre = np.concatenate([_a[..., :3]*_al, _a[..., 3:4]], -1)
_r = np.asarray(Image.fromarray(_pre.round().astype(np.uint8), 'RGBA')
                .resize((_im.width*S, _im.height*S), Image.LANCZOS), np.float32)
_al2 = np.clip(_r[..., 3:4]/255.0, 1e-4, 1.0)
A_ = np.concatenate([np.clip(_r[..., :3]/_al2, 0, 255), _r[..., 3:4]], -1).round().astype(np.uint8)
H, W = A_.shape[:2]
R, G, B, AL = [A_[..., i].astype(np.int16) for i in range(4)]
solid = AL > 140
skin  = solid & (R-B > 12) & (R > 195)
dark  = solid & (R < 135) & (G < 135) & (B < 190)
hairish  = solid & ~skin & (B >= R-8)
hairband = solid & (B >= R-8) & (B > 150) & ~skin
SIL = ndimage.binary_dilation(solid, iterations=12)

def poly(pts):
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon([(x*S, y*S) for x, y in pts], fill=255)
    return np.asarray(m) > 0
def elli(cx, cy, rx, ry):
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).ellipse([(cx-rx)*S,(cy-ry)*S,(cx+rx)*S,(cy+ry)*S], fill=255)
    return np.asarray(m) > 0

FACE = poly([(196,232),(190,258),(196,290),(210,318),(232,338),(258,349),(288,347),(318,336),
             (340,318),(352,292),(356,258),(352,222),(338,198),(310,186),(270,182),(232,190),(208,208)])
EYE_R, EYE_L = elli(226,270,27,22), elli(323,239,28,24)
EYEZONE = (elli(226,270,30,26) | elli(323,239,31,28)
           | poly([(190,226),(256,222),(256,250),(190,252)]) | poly([(296,198),(358,196),(358,228),(296,230)]))

# 由後往前（＝疊放順序）。切的時候反過來跑。
LAYERS = [
 ('05_hair_back',  hairband & poly([(60,0),(486,0),(486,404),(60,404)]) & ~FACE),
 ('10_face_base',  FACE),
 ('20_eye_R',      EYE_R, 1), ('21_eye_L', EYE_L, 1),
 ('30_brow_R',     poly([(196,236),(232,228),(252,238),(250,246),(228,238),(198,246)]), 1),
 ('31_brow_L',     poly([(300,214),(330,203),(356,212),(354,222),(328,213),(300,224)]), 1),
 ('40_mouth',      poly([(272,308),(302,310),(303,322),(272,320)])),
 ('50_hair_front', hairish & FACE & ~ndimage.binary_dilation(EYE_R|EYE_L, iterations=4)),
 ('55_clip',       poly([(300,140),(368,120),(374,150),(306,172)]) | poly([(296,168),(360,150),(364,176),(300,196)])
                   | poly([(96,78),(150,96),(140,130),(88,112)]) | poly([(300,10),(342,22),(336,58),(296,46)])
                   | poly([(196,0),(240,0),(236,60),(198,60)])),
 ('56_leg_L',      poly([(103,752),(234,752),(230,900),(214,1012),(202,1122),(200,1170),(110,1170),(106,1042),(98,900)])),
 ('57_leg_R',      poly([(263,752),(397,752),(407,960),(424,1090),(430,1174),(320,1174),(308,1020),(283,900)])),
 ('58_hood',       poly([(146,350),(258,344),(342,344),(380,352),(382,438),(300,392),(252,390),(150,436)])),
 ('59_skirt',      poly([(62,790),(80,710),(200,696),(332,698),(414,728),(410,822),(300,830),(160,832),(66,826)])),
 ('60_neck',       poly([(228,330),(340,330),(342,400),(302,420),(266,417),(238,396)]) & skin & ~FACE),
 ('61_choker',     poly([(243,328),(338,328),(338,362),(243,362)]) & dark),
 ('62_hoodie',     poly([(140,352),(440,352),(470,560),(496,706),(92,706),(112,540)])),
 ('70_hand_L',     poly([(10,296),(58,286),(106,318),(110,392),(70,418),(22,402)])),
 ('71_arm_L',      poly([(26,412),(98,374),(168,398),(218,468),(202,562),(150,610),(66,604),(20,516)])),
 ('73_hand_R',     poly([(502,786),(560,782),(597,812),(592,858),(540,868),(505,842)])),
 ('74_arm_R',      poly([(398,388),(470,404),(510,500),(545,600),(572,700),(566,790),(486,796),(428,720),(396,602),(386,466)])),
 ('80_bag',        poly([(388,698),(420,658),(502,662),(508,792),(470,818),(386,814)])),
 ('86_strap_hang', poly([(56,806),(94,806),(97,892),(56,892)])),
 ('95_warmer_L',   poly([(118,1146),(220,1146),(217,1252),(212,1342),(202,1376),(86,1376),(74,1290),(83,1198)])),
 ('96_warmer_R',   poly([(336,1144),(432,1144),(452,1240),(466,1330),(456,1380),(316,1380),(306,1270),(318,1192)])),
 ('98_shoe_L',     poly([(98,1350),(237,1350),(242,1452),(240,1536),(88,1536),(80,1440)])),
 ('99_shoe_R',     poly([(323,1350),(457,1350),(460,1462),(454,1536),(316,1536),(310,1440)])),
]

# ---- 切：由前往後搶像素，owner 記下每個像素屬於第幾層 ----
LAYERS = [(t[0], t[1], (len(t) > 2 and t[2])) for t in LAYERS]   # (名稱, 多邊形, 獨立層)
owner = np.full((H, W), -1, np.int16)
masks = {}
for z in range(len(LAYERS)-1, -1, -1):
    name, p, alone = LAYERS[z]
    m = p & solid if alone else p & solid & (owner < 0)    # 獨立層不搶：眼眉本來就被瀏海蓋著
    if not alone: owner[m] = z
    masks[name] = m
rest = solid & (owner < 0)                       # glitch 粒子等漏網
lab, n = ndimage.label(rest)
print(f'切完：{len(LAYERS)} 層，漏網 {int(rest.sum())} px（→ 01_particles）')

os.makedirs('layers', exist_ok=True)
for f in glob.glob('layers/*.png'): os.remove(f)

def write(name, mask, rgb=None, feather=0.9):
    out = A_.copy()
    if rgb is not None: out[..., :3] = rgb
    al = cv2.GaussianBlur((mask.astype(np.uint8)*255), (0, 0), feather)
    out[..., 3] = (out[..., 3].astype(np.float32)*(al/255.0)).round().astype(np.uint8) if rgb is None else al
    Image.fromarray(out, 'RGBA').save(f'layers/{name}.png')

# ---- 補：只補被上層拿走的像素 ----
print('補洞（只補被上層拿走的）：')
for z, (name, p, alone) in enumerate(LAYERS):
    have = masks[name]
    if name == '10_face_base': continue
    if alone: write(name, have); print(f'  {name:16s} 獨立層'); continue                      # 臉另外合成
    need = SIL & (owner > z) & (p | ndimage.binary_dilation(have, iterations=12))
    full = have | need
    if not need.any(): write(name, have); print(f'  {name:16s} 無洞'); continue
    med = np.median(A_[..., :3][have], 0) if have.sum() else np.array([200,200,210.])
    dist, idx = ndimage.distance_transform_edt(~have, return_distances=True, return_indices=True)
    near = A_[..., :3].astype(np.float32)[idx[0], idx[1]]
    w = np.clip(dist/26.0, 0, 1)[..., None]                  # 洞太大就漸變到自己的中位色
    rgb = np.where(have[..., None], A_[..., :3].astype(np.float32),
                   cv2.GaussianBlur(near*(1-w) + med.astype(np.float32)*w, (0, 0), 5))
    write(name, full, rgb.round().clip(0,255).astype(np.uint8))
    print(f'  {name:16s} 補 {int(need.sum()):7d} px')

# ---- 臉底：只用乾淨頰色，遠處漸變到中位膚色 ----
clean = FACE & solid & (R-B > 12) & (R > 205) & (G > 195)
med = np.median(A_[..., :3][clean], 0)
dist, idx = ndimage.distance_transform_edt(~clean, return_distances=True, return_indices=True)
near = A_[..., :3].astype(np.float32)[idx[0], idx[1]]
w = np.clip(dist/34.0, 0, 1)[..., None]
fb = np.where(clean[..., None], A_[..., :3].astype(np.float32),
              cv2.GaussianBlur(near*(1-w) + med.astype(np.float32)*w, (0, 0), 8))
fb = cv2.GaussianBlur(fb, (0, 0), 1.5)
write('10_face_base', FACE, fb.round().clip(0,255).astype(np.uint8))
print(f'  10_face_base     合成，中位膚色 {med.astype(int)}')

write('01_particles', rest, feather=0.6)

# ---- 眼皮 ----
LASH = (38, 24, 62)
for tag, (cx,cy,rx,ry) in [('22_lid_R',(226,270,33,29)), ('23_lid_L',(323,239,34,31))]:
    el = elli(cx,cy,rx,ry)
    out = np.zeros((H,W,4), np.uint8)
    out[...,:3] = fb.round().clip(0,255).astype(np.uint8)
    out[...,3] = cv2.GaussianBlur(np.where(el,255,0).astype(np.uint8), (0,0), 0.9)
    lid = Image.fromarray(out, 'RGBA'); d = ImageDraw.Draw(lid)
    bx = [(cx-rx)*S, (cy-ry*0.15)*S, (cx+rx)*S, (cy+ry*1.25)*S]   # 閉眼的睫毛是一道 ⌒
    d.arc(bx, 180, 360, fill=LASH+(255,), width=7)
    lid.save(f'layers/{tag}.png')

# ---- 嘴形 A/I/U/E/O（50x12 撐不起五形，直接畫）----
LINE, INNER, TONGUE = (142,104,112), (194,126,138), (224,156,166)
MX, MY = 287*S, 316*S
for tag,(w_,h_,tg) in {'42_mouth_A':(46,30,1),'43_mouth_I':(56,12,0),'44_mouth_U':(24,24,1),
                       '45_mouth_E':(50,20,1),'46_mouth_O':(28,32,1)}.items():
    img = Image.new('RGBA',(W,H),(0,0,0,0)); d = ImageDraw.Draw(img)
    bx = [MX-w_//2, MY-h_//2, MX+w_//2, MY+h_//2]
    d.ellipse(bx, fill=INNER+(255,), outline=LINE+(255,), width=5)
    if tg: d.ellipse([bx[0]+w_//4, bx[1]+h_*3//5, bx[2]-w_//4, bx[3]-3], fill=TONGUE+(255,))
    img.save(f'layers/{tag}.png')
print(f'完成：{len(glob.glob("layers/*.png"))} 層')
