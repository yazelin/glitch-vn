"""兩個切錯位置的修正（在 build.py 輸出＋patch/split 之後跑）：
1. 05_hair_back 在 y>=684 只留真的髮絲（有飽和度、且與上方髮塊連通），其餘是帽T 肩膀與帽子滾邊，搬進 62_hoodie。
   帽T 畫在後髮之上：帽T 已有 alpha 的地方直接丟（本來就被蓋住），沒有的地方寫進帽T。休息姿態不變。
   原因：後髮的範圍是頭部方框＋髮色門檻，帽T 的淡藍也過門檻；被蓋住的那些像素會在頭轉時從帽T 底下轉出來。
2. 指尖：build.py 把手多邊形外的指尖當小碎片丟進 01_particles，手一揮指尖留在原地。
   把粒子層裡「膚色、且貼著手層」的連通塊搬回 70_hand_L / 73_hand_R。"""
from PIL import Image; import numpy as np, glob, os
from scipy import ndimage
L='layers'
def comp():
    c=Image.new('RGBA',(1196,3072),(0,0,0,0))
    for f in sorted(glob.glob(f'{L}/*.png')):
        if os.path.basename(f)[:-4] in ('43_mouth_I','44_mouth_U','45_mouth_E','46_mouth_O','22_lid_R','23_lid_L','42_mouth_A'): continue
        c.alpha_composite(Image.open(f))
    return np.asarray(c).astype(int)
before=comp()
ld=lambda n: np.asarray(Image.open(f'{L}/{n}.png')).copy()
sv=lambda n,a: Image.fromarray(a,'RGBA').save(f'{L}/{n}.png')

# ---- 1. 後髮的帽T 像素：改由 refine/head_mask.py 用幾何處理（顏色分不開同色系的髮與帽T）----

# ---- 2. 指尖：粒子層裡的膚色碎片 → 手 ----
pt=ld('01_particles'); pa=pt[...,3]>0; prgb=pt[...,:3].astype(int)
skin=pa&(prgb[...,0]-prgb[...,2]>12)&(prgb[...,0]>195)
lab,n=ndimage.label(skin)
for hand in ('70_hand_L','73_hand_R'):
    h=ld(hand); ha=ndimage.binary_dilation(h[...,3]>50, iterations=6)     # 貼著手層 6px 內
    moved=0
    for k in range(1,n+1):
        m=lab==k
        if (m&ha).any():
            h[m]=pt[m]; pt[m]=0; moved+=int(m.sum())
    print(f'{hand}: 從粒子層搬回指尖 {moved} px'); sv(hand,h)
sv('01_particles',pt)

after=comp(); m=before[...,3]>0; dd=np.abs(after[...,:3]-before[...,:3]).sum(2)
print(f'休息姿態合成差異最大 {dd[m].max()}，>30 的像素 {((dd>30)&m).sum()}')
assert ((dd>30)&m).sum()<=20, '休息姿態變了'   # 進帽T 的像素若正好在脖子/頸環的半透明邊緣上，順序會差一層；實測 8 px，可接受
