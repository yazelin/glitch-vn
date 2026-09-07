"""把舉手那隻袖子（71_arm_L）疊在軀幹上的部分搬到帽T（62_hoodie）。
原本袖子有 49% 疊在帽T 上（原畫的肩膀 + build.py 為了肩縫不露而往軀幹脹的 24px），
Cubism 的 D_ArmWave 一轉，那整塊直線切口就掃過胸口。搬完袖子只剩手臂本體。

規則：肩縫左側留在袖子，右側逐像素以「直通 alpha 的 over 合成」寫進帽T（帽T 自己也可能半透明，
底下有 58_hood，所以不能直接覆蓋）。休息姿態的合成結果必須完全不變，這支會驗。
用法：在 ../ 目錄跑 python3 refine/split_sleeve.py（layers/ 先是 build.py 的乾淨輸出）"""
from PIL import Image; import numpy as np, glob, os, sys
L='layers'
SEAM=[(340,760),(340,780),(300,820),(262,880),(235,960),(222,1060),(215,1150),(215,1260)]   # 2x 座標，右側＝軀幹
def comp():
    c=Image.new('RGBA',(1196,3072),(0,0,0,0))
    for f in sorted(glob.glob(f'{L}/*.png')):
        if os.path.basename(f)[:-4] in ('43_mouth_I','44_mouth_U','45_mouth_E','46_mouth_O','22_lid_R','23_lid_L','42_mouth_A'): continue
        c.alpha_composite(Image.open(f))
    return np.asarray(c).astype(int)
before=comp()
arm=np.asarray(Image.open(f'{L}/71_arm_L.png')).astype(np.float32); hood=np.asarray(Image.open(f'{L}/62_hoodie.png')).astype(np.float32)
H,W=arm.shape[:2]; yy,xx=np.mgrid[0:H,0:W]; sx=np.interp(yy[:,0],[p[1] for p in SEAM],[p[0] for p in SEAM])
move=(xx>=sx[:,None])&(yy>=760)&(yy<=1260)&(arm[...,3]>0)
a=(arm[...,3]/255.0)[...,None]; ha=(hood[...,3]/255.0)[...,None]; oa=a+ha*(1-a)
orgb=np.where(oa>0,(arm[...,:3]*a+hood[...,:3]*ha*(1-a))/np.maximum(oa,1e-6),hood[...,:3])
hood2=np.where(move[...,None],np.dstack([orgb,oa*255]),hood).round().clip(0,255).astype(np.uint8)
arm2=arm.copy(); arm2[move]=0; arm2=arm2.round().astype(np.uint8)
Image.fromarray(arm2,'RGBA').save(f'{L}/71_arm_L.png'); Image.fromarray(hood2,'RGBA').save(f'{L}/62_hoodie.png')
after=comp(); m=before[...,3]>0; dd=np.abs(after[...,:3]-before[...,:3]).sum(2)
print(f'搬走 {int(move.sum())} px；合成差異最大 {dd[m].max()}，>30 的像素 {((dd>30)&m).sum()}')
assert ((dd>30)&m).sum()==0, '休息姿態變了'
