"""去背後補一刀：離背景超過 N 像素的主體內部一律不透明（黃幕會把偏黃的膚色算成 85～95% 不透明）。
邊緣 N 像素以內照 cutout.py 解出來的覆蓋率，髮絲與輪廓的柔邊不動。
用法：python3 solid.py cut/x.png [N=4]（就地改寫）"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
p = sys.argv[1]; n = float(sys.argv[2]) if len(sys.argv) > 2 else 4
a = np.array(Image.open(p).convert('RGBA'))
bg = a[..., 3] == 0
dist = ndimage.distance_transform_edt(~bg)
before = int(((a[..., 3] > 0) & (a[..., 3] < 255)).sum())
a[..., 3] = np.where(dist > n, 255, a[..., 3])
after = int(((a[..., 3] > 0) & (a[..., 3] < 255)).sum())
Image.fromarray(a).save(p)
print(p, '半透明', before, '→', after)
