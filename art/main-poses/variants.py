"""新姿勢的表情差分（2026-11-04 作者：五個姿勢都用）。只做 table.py 算出來真的有句子要用的組合。

參考圖一＝那個姿勢的原圖（黃幕，raw/<姿勢>.png），參考圖二＝現有那張表情（貼黃底）。
臉照圖二，其他全部照圖一：姿勢、手、道具、衣服、大小與在畫面裡的位置都不動，切換表情時身體才不會跳。
用法：python3 art/main-poses/variants.py [代號 ...]    走 .11 服務（gen.via_service 排隊）；已經有的會跳過
"""
import pathlib, sys, time
from PIL import Image
import gen

HERE = gen.HERE; RAW = gen.RAW; REF = gen.REF
FACES = gen.HERE.parent / 'main-webp'
POSE = {'talk': 'standing relaxed and facing the viewer, both hands loosely clasped together in front of her at hip height',
        'stream': 'standing with both hands raised to chest height, operating a translucent floating holographic audio control panel (soft mint and lavender glow, sliders and track bars, no readable text)',
        'rulebook': 'standing and holding her thick brown leather rule book open against her left forearm at chest height, a black pen in her right hand'}
# 代號：(姿勢, 現有表情檔, 表情說明)。說明寫台詞要的那個樣子
VARIANTS = {
    'glitch-stream-happy': ('stream', 'glitch-happy', 'a bright playful teasing smile: eyes closed in happy upward arcs, mouth open in a cheerful grin, antennas perked up'),   # 一・虧貓草老花
    'glitch-stream-laugh': ('stream', 'face-glitch-laugh', 'a small genuine laugh she rarely shows on stream: eyes gently closed, cheeks lifted, mouth corners up, mouth slightly open'),   # 一・「她笑了」
    'glitch-stream-error': ('stream', 'glitch-error', 'a frozen crashed look, the same as reference image 2: the same eye colour and glitch marks around the antennas, stunned face, mouth slightly open'),   # 三・當機
    'glitch-talk-sad': ('talk', 'face-glitch-sad', 'quietly sad and deflated: eyebrows raised in the middle, eyes lowered and slightly glossy, small closed mouth, antennas drooping a little'),   # 七・「……喔。」「那你講給我聽」
    'glitch-talk-surprised': ('talk', 'glitch-idle', 'surprised: eyes wide open, eyebrows raised, small open mouth'),   # 四・「妳怎麼知道。」
    'glitch-talk-count': ('talk', 'face-glitch-count', 'quick clever calculating look, eyes glancing up to one side, small confident mouth. Gesture: her right hand (on the viewer\'s left) is raised to shoulder height with the index finger pointing up, the other hand rests relaxed at her side'),   # 一・一邊講話一邊算營運成本
    'glitch-rulebook-thinking': ('rulebook', 'glitch-thinking', 'a blank absent-minded stare at the open page: eyes half open and unfocused, mouth slightly open, antennas still'),   # 二・「……七。」
}


def face_ref(stem):
    """現有表情貼黃底（透明 PNG 直接送會被當成黑底）。"""
    out = REF / f'{stem}-yellow.png'
    if not out.exists():
        im = Image.open(next(FACES.glob(f'*_{stem}.webp'))).convert('RGBA')
        bg = Image.new('RGBA', im.size, (255, 255, 0, 255)); bg.alpha_composite(im); bg.convert('RGB').save(out)
    return out


def prompt(pose, expr):
    return f"""Reference image 1 is the EXACT sprite to edit: Glitch, {POSE[pose]}, on a flat yellow background. Reference image 2 is the same character showing the facial expression to use.
Redraw reference image 1 keeping the same pose, hands, props, outfit, colours, proportions, framing, figure size and position in the frame, and the same art style. Change ONLY her face to this expression, matching the face in reference image 2: {expr}.
Sides must stay correct: the two hair clips, the thigh-high sock and the sling pouch are all on HER LEFT (the viewer's right).
{gen.GLITCH}
{gen.STYLE}
{gen.YELLOW}"""


def main():
    want = [a for a in sys.argv[1:] if not a.startswith('--')] or list(VARIANTS)
    for k in want:
        pose, stem, expr = VARIANTS[k]
        out = RAW / f'{k}.png'
        if out.exists(): print('已有，跳過', out.name); continue
        t = time.time()
        gen.via_service(prompt(pose, expr), [RAW / f'glitch-{pose}.png', face_ref(stem)], out)
        print(k, '完成' if out.exists() else '失敗', f'{time.time() - t:.0f}s', flush=True)


if __name__ == '__main__':
    main()
