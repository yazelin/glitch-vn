"""42_mouth_A（生成的張嘴）往下移 14px 並把 alpha 裁到舊網格範圍（y>=598），以唇線為中心才落在 Cubism 舊網格內，不必重生網格。"""
from PIL import Image; import numpy as np
p='layers/42_mouth_A.png'; a=np.asarray(Image.open(p)).copy(); SH=14
b=np.zeros_like(a); b[SH:]=a[:-SH]; b[:598,:,3]=0
Image.fromarray(b,'RGBA').save(p)
al=b[...,3]>8; ys,xs=np.nonzero(al); print(f'42_mouth_A 移後 alpha y{ys.min()}-{ys.max()}')
