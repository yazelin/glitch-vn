"""layers/*.png -> glitch.psd（Cubism Editor 能讀的 PSD）。

不用 pytoshop：它產的檔 ImageResources 長度是 0、也沒寫 Unicode 圖層名，
Cubism 解析到 Layer&Mask 段會丟 `error signature @ 0x00000026`。
這支照 Adobe 規格自己組，壓縮用 RLE(PackBits)——相容性最好，ZIP 有些讀取器不吃。
"""
import glob, os, struct, numpy as np
from PIL import Image

OUT = 'glitch.psd'

def packbits(row: bytes) -> bytes:
    """Adobe PackBits。連續重複 >=3 用重複碼，其餘走字面碼。"""
    out = bytearray(); i = 0; n = len(row)
    while i < n:
        j = i
        while j + 1 < n and row[j + 1] == row[j]:
            j += 1
        run = j - i + 1
        if run >= 3:
            while run >= 2:
                k = min(run, 128)
                out.append(257 - k); out.append(row[i]); run -= k
            if run == 1:                      # 257-1=256 會爆掉，剩一個就走字面碼
                out.append(0); out.append(row[i])
            i = j + 1
        else:
            j = i
            while j < n:
                if j + 2 < n and row[j] == row[j+1] == row[j+2]:
                    break
                j += 1
            lit = row[i:j]
            while lit:
                k = min(len(lit), 128)
                out.append(k - 1); out += lit[:k]; lit = lit[k:]
            i = j
    return bytes(out)

def rle_channel(plane: np.ndarray):
    """回傳 (每列長度表 bytes, 資料 bytes)。"""
    counts = bytearray(); data = bytearray()
    for r in plane:
        p = packbits(r.tobytes())
        counts += struct.pack('>H', len(p)); data += p
    return bytes(counts), bytes(data)

def pascal(s: bytes, pad=4) -> bytes:
    b = bytes([len(s)]) + s
    while len(b) % pad: b += b'\0'
    return b

def _unpackbits(b):
    o = bytearray(); i = 0
    while i < len(b):
        n = b[i]; i += 1
        if n < 128: o += b[i:i+n+1]; i += n+1
        elif n > 128: o += bytes([b[i]]) * (257-n); i += 1
    return bytes(o)

def demo():
    import random
    random.seed(0)
    for _ in range(200):
        raw = bytes(random.choice([random.randrange(256)]*random.choice([1,1,1,5,140]))
                    for _ in range(random.randrange(1, 400)))
        assert _unpackbits(packbits(raw)) == raw, raw[:40]
    for raw in (b'', b'\x01', b'\x01\x01', b'\xff'*129, b'\xab'*257, bytes(range(256))):
        assert _unpackbits(packbits(raw)) == raw
    print('packbits self-check OK')

if __name__ == '__main__' and os.environ.get('DEMO'):
    demo(); raise SystemExit

files = sorted(glob.glob('layers/*.png'))
W, H = Image.open(files[0]).size
layers = []
for f in files:
    a = np.asarray(Image.open(f).convert('RGBA'))
    ys, xs = np.nonzero(a[..., 3] > 0)
    if len(ys) == 0: continue
    t, b, l, r = int(ys.min()), int(ys.max())+1, int(xs.min()), int(xs.max())+1
    layers.append((os.path.basename(f)[:-4], t, l, b, r, a[t:b, l:r]))

# ---- Layer records ----
recs = bytearray(); chans = bytearray()
for name, t, l, b, r, crop in layers:
    recs += struct.pack('>iiii', t, l, b, r)
    recs += struct.pack('>H', 4)
    ch_blobs = []
    for cid, idx in ((-1, 3), (0, 0), (1, 1), (2, 2)):
        counts, data = rle_channel(np.ascontiguousarray(crop[..., idx]))
        blob = struct.pack('>H', 1) + counts + data     # 1 = RLE
        ch_blobs.append(blob)
        recs += struct.pack('>hI', cid, len(blob))
    recs += b'8BIM' + b'norm' + bytes([255]) + b'\0' + b'\0' + b'\0'   # opacity/clipping/flags/filler
    nb = name.encode('utf-8')
    luni = nb.decode('utf-8')
    uni = struct.pack('>I', len(luni)) + luni.encode('utf-16-be')
    if len(uni) % 4: uni += b'\0' * (4 - len(uni) % 4)
    extra = struct.pack('>I', 0) + struct.pack('>I', 0) + pascal(nb) \
            + b'8BIM' + b'luni' + struct.pack('>I', len(uni)) + uni
    recs += struct.pack('>I', len(extra)) + extra
    for blob in ch_blobs: chans += blob

layer_info = struct.pack('>h', len(layers)) + bytes(recs) + bytes(chans)
if len(layer_info) % 2: layer_info += b'\0'
lmi = struct.pack('>I', len(layer_info)) + layer_info + struct.pack('>I', 0)   # + global mask(0)

# ---- 合成影像（Cubism 不一定要，但規格要求這一段存在）----
comp = Image.new('RGBA', (W, H), (0, 0, 0, 0))
for f in files: comp.alpha_composite(Image.open(f))
flat = np.asarray(comp.convert('RGB'))
img_counts = bytearray(); img_data = bytearray()
for c in range(3):
    counts, data = rle_channel(np.ascontiguousarray(flat[..., c]))
    img_counts += counts; img_data += data
image_data = struct.pack('>H', 1) + bytes(img_counts) + bytes(img_data)

# ---- Image Resources：至少要有解析度區塊，pytoshop 漏掉的就是這個 ----
res = struct.pack('>IhhIhh', 72 << 16, 1, 1, 72 << 16, 1, 1)
ir = b'8BIM' + struct.pack('>H', 0x03ED) + b'\0\0' + struct.pack('>I', len(res)) + res

hdr = b'8BPS' + struct.pack('>H', 1) + b'\0'*6 + struct.pack('>HIIHH', 3, H, W, 8, 3)

with open(OUT, 'wb') as fh:
    fh.write(hdr)
    fh.write(struct.pack('>I', 0))                    # Color Mode Data
    fh.write(struct.pack('>I', len(ir))); fh.write(ir)
    fh.write(struct.pack('>I', len(lmi))); fh.write(lmi)
    fh.write(image_data)
print(f'{OUT}  {W}x{H}  {len(layers)} layers  {os.path.getsize(OUT)/1e6:.1f} MB')
