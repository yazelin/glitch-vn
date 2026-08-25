"""talk() 逐行情緒的驗收。配負控制：沒有三元組的話那幾行就是空情緒。"""
import sys, pathlib
sys.path.insert(0, "/home/ct/glitch-vn/larch")
import novelkit as nk, voice as V

class Fake(nk.Chapter):
    def __init__(self): self.nodes=[]; self.cids={}; self.bid="t"; self.prev=None; self.pending=[]; self.cast=[]; self._bgm=None
    def _card(self, d, **kw): self.nodes.append({"data": d}); return d

c = Fake()
# 二元組：舊行為
a = c.talk(("諾亞","有啊。"), ("格莉奇","真的嗎。"), emotion="笑", who="諾亞")
# 三元組：逐行情緒
b = c.talk(("諾亞","有啊。","笑"), ("格莉奇","真的嗎。","驚訝"))
# 混用
m = c.talk(("諾亞","有啊。"), ("格莉奇","真的嗎。","驚訝"), emotion="笑", who="諾亞")

def emos(d): return [(l["speaker"], l["emotion"]) for l in d["dialogueLines"]]
print("二元組（舊行為）:", emos(a))
print("三元組（逐行）  :", emos(b))
print("混用            :", emos(m))

assert emos(a) == [("諾亞","笑"), ("格莉奇","")], emos(a)
assert emos(b) == [("諾亞","笑"), ("格莉奇","驚訝")], emos(b)
assert emos(m) == [("諾亞","笑"), ("格莉奇","驚訝")], emos(m)

# 鍵真的不同：同一句話有沒有情緒會算出不同代號
k_none = V.key("格莉奇","真的嗎。",None)
k_emo  = V.key("格莉奇","真的嗎。","驚訝")
print(f"\n無情緒的鍵 {k_none}")
print(f"有情緒的鍵 {k_emo}")
assert k_none != k_emo
# 負控制：如果 talk 忽略三元組，b 的第二行就會是空情緒，配音會去查 k_none
assert V.key(*emos(b)[1][:1], "真的嗎。", emos(b)[1][1]) == k_emo

print("\n全部通過")
