"""把舉手那隻袖子（71_arm_L）疊在軀幹上的部分搬到帽T（62_hoodie）。
原本袖子有 49% 疊在帽T 上，Cubism 的 D_ArmWave 一轉整塊直線切口就掃過胸口。

縫線不是手畫的折線，是每一列量出來的：在袖子內側輪廓附近找最右邊的深色像素，縫線放在它右邊 4px，
整條輪廓線保證留在袖子上，切口落在平色布料裡。（第一版用折線＋常數偏移，輪廓線被切成兩半，
袖子一轉帽T 上留一條複製的線，看起來像手臂裂開。）
搬過去用直通 alpha 的 over 合成；休息姿態合成必須嚴格不變。
用法：在 ../ 跑 python3 refine/split_sleeve.py（layers/ 先是 build.py 的乾淨輸出）"""
from PIL import Image; import numpy as np, glob, os
from scipy.ndimage import median_filter
L='layers'
GUIDE=[(340,760),(340,780),(300,820),(262,880),(235,960),(222,1060),(215,1150),(215,1260)]  # 大概位置，只用來限定搜尋範圍
def comp():
    c=Image.new('RGBA',(1196,3072),(0,0,0,0))
    for f in sorted(glob.glob(f'{L}/*.png')):
        if os.path.basename(f)[:-4] in ('43_mouth_I','44_mouth_U','45_mouth_E','46_mouth_O','22_lid_R','23_lid_L','42_mouth_A'): continue
        c.alpha_composite(Image.open(f))
    return np.asarray(c).astype(int)
before=comp()
arm=np.asarray(Image.open(f'{L}/71_arm_L.png')).astype(np.float32); hood=np.asarray(Image.open(f'{L}/62_hoodie.png')).astype(np.float32)
H,W=arm.shape[:2]; yy,xx=np.mgrid[0:H,0:W]
gx=np.interp(np.arange(H),[p[1] for p in GUIDE],[p[0] for p in GUIDE])
lum=arm[...,:3].sum(2); dark=(lum<400)&(arm[...,3]>100)
seam=gx.copy()
for y in range(760,1261):
    lo,hi=int(gx[y]-14),int(gx[y]+26)
    xs=np.nonzero(dark[y,lo:hi])[0]
    seam[y]=(lo+xs.max()+4) if len(xs) else gx[y]+8
seam[760:1261]=median_filter(seam[760:1261],size=9)          # 去掉單列跳動
move=(xx>=seam[:,None])&(yy>=760)&(yy<=1260)&(arm[...,3]>0)
a=(arm[...,3]/255.0)[...,None]; ha=(hood[...,3]/255.0)[...,None]; oa=a+ha*(1-a)
orgb=np.where(oa>0,(arm[...,:3]*a+hood[...,:3]*ha*(1-a))/np.maximum(oa,1e-6),hood[...,:3])
hood2=np.where(move[...,None],np.dstack([orgb,oa*255]),hood).round().clip(0,255).astype(np.uint8)
arm2=arm.copy(); arm2[move]=0; arm2=arm2.round().astype(np.uint8)
Image.fromarray(arm2,'RGBA').save(f'{L}/71_arm_L.png'); Image.fromarray(hood2,'RGBA').save(f'{L}/62_hoodie.png')
after=comp(); m=before[...,3]>0; dd=np.abs(after[...,:3]-before[...,:3]).sum(2)
print(f'搬走 {int(move.sum())} px；縫線 x 範圍 {int(seam[760:1261].min())}-{int(seam[760:1261].max())}；合成差異最大 {dd[m].max()}，>30 的像素 {((dd>30)&m).sum()}')
assert ((dd>30)&m).sum()==0, '休息姿態變了'
np.save('refine/seam.npy', seam)
