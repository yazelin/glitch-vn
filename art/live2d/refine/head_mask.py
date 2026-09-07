"""頭部層（05_hair_back / 10_face_base / 50_hair_front / 55_clip）只能有頭。
用顏色分不開同色系的髮與帽T，所以改用幾何：HEAD_BOTTOM 是沿髮絲與衣服交界手描的折線（2x 座標），
折線以下的像素一律不是頭。搬出去的規則：上方有不透明層蓋住的直接刪（休息時本來就看不見，頭轉才會露出）；
露在外面的用 over 合成寫進正上方最近的衣服層（有帽子 alpha 進 58_hood，否則進 62_hoodie），休息姿態不變。"""
from PIL import Image, ImageDraw; import numpy as np, glob, os
L='layers'
HEAD_BOTTOM=[(0,560),(200,575),(225,640),(265,700),(310,728),(340,716),(420,696),(450,690),(520,700),(600,702),(650,690),
             (700,652),(760,705),(805,692),(845,650),(900,600),(960,560),(1196,560)]
HEAD=['05_hair_back','10_face_base','50_hair_front','55_clip']
ABOVE_HEAD=['56_leg_L','57_leg_R','58_hood','59_skirt','60_neck','61_choker','62_hoodie','70_hand_L','71_arm_L','73_hand_R','74_arm_R','80_bag']
def comp():
    c=Image.new('RGBA',(1196,3072),(0,0,0,0))
    for f in sorted(glob.glob(f'{L}/*.png')):
        if os.path.basename(f)[:-4] in ('43_mouth_I','44_mouth_U','45_mouth_E','46_mouth_O','22_lid_R','23_lid_L','42_mouth_A'): continue
        c.alpha_composite(Image.open(f))
    return np.asarray(c).astype(int)
ld=lambda n: np.asarray(Image.open(f'{L}/{n}.png')).copy()
sv=lambda n,a: Image.fromarray(a,'RGBA').save(f'{L}/{n}.png')
before=comp()
H,W=3072,1196
m=Image.new('L',(W,H),0); ImageDraw.Draw(m).polygon(HEAD_BOTTOM+[(1196,0),(0,0)],fill=255); head_ok=np.asarray(m)>0
opaque_above=np.zeros((H,W),bool)
for n in ABOVE_HEAD: opaque_above|=ld(n)[...,3]==255
hood=ld('58_hood'); hoodie=ld('62_hoodie'); hood_a=hood[...,3]>0
def over(dst,src,sel):
    t=dst.astype(np.float32); s=src.astype(np.float32); ta=t[...,3:4]/255; sa=s[...,3:4]/255; oa=ta+sa*(1-ta)
    rgb=np.where(oa>0,(t[...,:3]*ta+s[...,:3]*sa*(1-ta))/np.maximum(oa,1e-6),t[...,:3])
    return np.where(sel[...,None],np.dstack([rgb,oa*255]),t).round().clip(0,255).astype(np.uint8)
total=0
for n in HEAD:
    a=ld(n); out=(a[...,3]>0)&~head_ok
    if not out.any(): continue
    drop=out&opaque_above; vis=out&~opaque_above
    hood=over(hood,a,vis&hood_a); hoodie=over(hoodie,a,vis&~hood_a)
    a[out]=0; sv(n,a); total+=int(out.sum())
    print(f'  {n}: 線下 {int(out.sum())} px（刪 {int(drop.sum())}、進帽子 {int((vis&hood_a).sum())}、進帽T {int((vis&~hood_a).sum())}）')
sv('58_hood',hood); sv('62_hoodie',hoodie)
after=comp(); mm=before[...,3]>0; dd=np.abs(after[...,:3]-before[...,:3]).sum(2)
print(f'頭部層搬出 {total} px；休息姿態合成差異最大 {dd[mm].max()}，>30 的像素 {((dd>30)&mm).sum()}')
assert ((dd>30)&mm).sum()<=40, '休息姿態變了'
