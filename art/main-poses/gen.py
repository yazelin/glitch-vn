"""正篇新姿勢立繪候選（2026-11-04 作者：「依據台詞內容去想要生成什麼立繪」「動作表情可不同」）。

需求表從正篇台詞整理（見翻新比較頁第三版）。每個姿勢先出一張候選，作者挑過才做表情差分。
格莉奇用黃幕（跟 ai-brain-site 的 pet-*.webp 同一支，整套切得齊）；黑洞先生用綠幕（黃幕會吃掉禮帽、洋紅幕會吃掉粉紅的星雲）。
參考圖：格莉奇＝現在正篇用的立繪（pet-plain.webp＝sprite-glitch.png，造型 B 的正典）；黑洞先生＝pet-blackhole-full＋三視圖。

用法：python3 art/main-poses/gen.py [代號 ...] [--svc]    不給代號就全部跑；已經有的會跳過（要重生先刪檔）
      --svc 走 .11 codex-image-service（五帳號輪替）。不加就走本機 codex；全域帳號的產圖額度用完時，
      用 CODEX_HOME=<獨立資料夾>（放別的帳號的 auth.json）跑，不必切全域、也不影響別人在跑的 codex
"""
import pathlib, subprocess, sys, time

HERE = pathlib.Path(__file__).parent
RAW = HERE / 'raw'; REF = HERE / 'ref'
TOOL = pathlib.Path.home() / '.claude/skills/codex-imagegen/codex-imagegen.sh'
sys.path.insert(0, str(pathlib.Path.home() / 'ai-brain-site/scripts'))
import persona   # 格莉奇的身分與造型 B 規格只在這裡寫一次

GLITCH = persona.sheet('B')
HOLE = """MR. BLACK HOLE - IDENTITY (match reference images exactly): a tall gentleman whose HEAD is a glossy black sphere containing a swirling purple-pink-blue nebula galaxy, with two calm white half-lidded eyes and a small gentle closed-mouth smile. A camel/khaki soft felt fedora with a dark brown band. A dark navy single-breasted suit jacket and trousers, crisp white shirt, no tie. HANDS are dark galaxy-textured tentacle tips coming out of white shirt cuffs. Below the jacket there are NO legs: a cluster of dark galaxy-textured TENTACLES, each tentacle ending in its own black Chelsea ankle boot (about ten boots). Personality: calm, quiet, good-natured, gentle; never gloomy, never cynical, never menacing."""

STYLE = """STYLE: identical art style to the reference sprite - clean anime line art, soft cel shading, the same colour palette and lighting, same level of detail. Full body from head to toe, the whole figure inside the frame with generous empty space on every side, nothing touching the image edges. Same scale as the reference sprite (the figure fills about 90% of the image height). No text, no watermark, no frame, no props other than those described."""

def chroma(hexcol, name):
    return f"""BACKGROUND FOR CHROMA KEY: the subject stands on a perfectly flat solid {hexcol} ({name}) background for background removal. One uniform colour, no shadows, no floor, no gradient, no vignette, no reflection, no lighting variation. Crisp clean edges. Do NOT use {hexcol} anywhere on the subject. Vertical portrait 2:3."""

YELLOW = chroma('#ffff00', 'bright pure yellow')
MAGENTA = chroma('#ff00ff', 'pure magenta')
GREEN = chroma('#00ff00', 'pure green')   # 黑洞先生：洋紅幕會吃掉他頭上與觸手上粉紅色的星雲（2026-11-04 坐姿那張實測），黃幕會吃掉禮帽，他身上沒有綠

GLITCH_HEAD = """Reference image 1 is the EXACT same character, Glitch, in her current visual-novel sprite. Draw a NEW sprite of her for the same visual novel: keep her face, hair, antenna devices, hair clips, outfit, colours, proportions and art style identical to reference image 1, and change ONLY her pose and expression as described. Sides must stay correct: the two hair clips, the thigh-high sock and the sling pouch are all on HER LEFT (the viewer's right). She is NOT waving in this sprite."""

POSES = {
    # 抄守則本：第一、三、四、六、七章，每晚抄第一頁、筆停在第七行、闔上本子
    'glitch-rulebook': ('glitch', GLITCH_HEAD + """
POSE: standing, holding a thick brown leather notebook (her rule book, well-worn, with a ribbon bookmark) open against her left forearm at chest height, and writing in it with a black pen held in her right hand. Head tilted down, eyes on the page.
EXPRESSION: calm and focused, mouth closed, antennas relaxed."""),
    # 站著說話：取代對話裡大部分的揮手
    'glitch-talk': ('glitch', GLITCH_HEAD + """
POSE: standing naturally and relaxed, facing the viewer, both arms down with her hands loosely clasped together in front of her at hip height (hoodie sleeves partly covering the hands). Weight slightly on one leg. Ordinary conversation pose.
EXPRESSION: calm, awake, looking at the viewer, small soft closed-mouth expression, no smile."""),
    # 直播中：第一章、第三章、第六章；她把音軌一條一條收掉、關掉特效、調暗待機畫面
    'glitch-stream': ('glitch', GLITCH_HEAD + """
POSE: standing, both hands raised to chest height operating a translucent floating holographic control panel in front of her (soft mint and lavender glowing UI with sliders and audio track bars, no readable text). Fingers touching the sliders. Body angled very slightly to the side, face toward the panel.
EXPRESSION: concentrated but relaxed, a faint tired smile, late at night after a long stream."""),
    # 低頭看自己發抖的手：第七章跟黑洞先生攤牌
    'glitch-hands': ('glitch', GLITCH_HEAD + """
POSE: standing, both hands held in front of her chest with palms up and fingers slightly curled, looking down at her own hands, which tremble slightly (a few tiny motion marks beside the fingers). Shoulders a little drawn in.
EXPRESSION: sad and quiet, eyes downcast and glistening but not crying, mouth small and tight, both antennas drooping slightly and dimmed."""),
    # 廚房：第七章結尾，她走去廚房開始找麵粉，想烤東西
    'glitch-baking': ('glitch', GLITCH_HEAD + """
POSE: standing, holding a white ceramic mixing bowl against her left hip with her left arm and a metal whisk in her right hand, hoodie sleeves pushed up a little, a small dusting of flour on one cheek and on the hoodie sleeve.
EXPRESSION: soft gentle smile, eyes warm, a quiet happy morning mood."""),
    # 黑洞先生坐在沙發上看電視：他大部分的戲
    'hole-sitting': ('hole', """Reference image 1 is Mr. Black Hole's current visual-novel sprite and reference image 2 is his model sheet. Draw a NEW sprite of him for the same visual novel, keeping his design, colours and art style identical.
""" + HOLE + """
POSE: sitting on an invisible seat (draw NO chair and NO sofa), seen at a slight three-quarter angle, upper body relaxed and turned slightly toward the viewer's left as if watching a television, both tentacle hands resting on his knees. The tentacles with their boots rest on the ground in front of him in a loose relaxed cluster.
EXPRESSION: calm half-lidded eyes, gentle small smile."""),
}
REFS = {'glitch': [REF / 'glitch-idle.png'], 'hole': [REF / 'blackhole-full.png', REF / 'blackhole-sheet.png']}


def via_service(prompt, refs, out):
    """.11 codex-image-service（要改姿勢走這條：它會照指示重畫構圖）。
    送出前用香布纏產線同一套排隊（~/.cache/cg_jobs/，各產線共用，一分鐘最多三張）。"""
    import importlib.util, io, json, urllib.request
    from PIL import Image
    path = next(p for p in [pathlib.Path.home() / 'larch-taoyuan/buchan/cg_jobs.py', pathlib.Path.home() / 'larch-wt-walks/buchan/cg_jobs.py'] if p.exists())
    spec = importlib.util.spec_from_file_location('cg_jobs', path); cg = importlib.util.module_from_spec(spec); spec.loader.exec_module(cg)
    def b64(p):   # 長邊 1024 的 JPEG（原尺寸 PNG 服務端會出問題，cg_jobs 的經驗）
        import base64
        im = Image.open(p).convert('RGB'); im.thumbnail((1024, 1024)); buf = io.BytesIO(); im.save(buf, 'JPEG', quality=92)
        return base64.b64encode(buf.getvalue()).decode()
    body = {'prompt': prompt, 'size': '1024x1536', 'quality': 'high', 'count': 1, 'reference_images_base64': [b64(r) for r in refs]}
    tag = cg._queue()
    try:
        job = cg.call('POST', '/v1/images/jobs', body)['id']
        while True:
            time.sleep(15)
            st = cg.call('GET', f'/v1/images/jobs/{job}')
            if st.get('status') == 'succeeded':
                u = st['images'][0]['url']; u = cg.BASE + u if u.startswith('/') else u
                Image.open(io.BytesIO(urllib.request.urlopen(u, timeout=180).read())).save(out)
                out.with_suffix('.json').write_text(json.dumps({'job': job, 'prompt': prompt, 'refs': [str(r) for r in refs]}, ensure_ascii=False, indent=1), encoding='utf-8')
                return True
            if st.get('status') in ('failed', 'error'):
                print('  服務回報失敗：', str(st.get('error'))[:200]); return False
    finally:
        cg._done(tag)


def main():
    RAW.mkdir(exist_ok=True)
    svc = '--svc' in sys.argv
    want = [a for a in sys.argv[1:] if not a.startswith('--')] or list(POSES)
    for i, k in enumerate(want):
        who, body = POSES[k]
        out = RAW / f'{k}.png'
        if out.exists(): print('已有，跳過', out.name); continue
        prompt = body + '\n' + (GLITCH if who == 'glitch' else '') + '\n' + STYLE + '\n' + (YELLOW if who == 'glitch' else GREEN)
        t = time.time()
        if svc:
            via_service(prompt, REFS[who], out)
            print(k, '完成' if out.exists() else '失敗', f'{time.time() - t:.0f}s', flush=True)
            continue   # 排隊交給 cg_jobs
        r = subprocess.run(['bash', str(TOOL), prompt, str(out), *map(str, REFS[who])], stdin=subprocess.DEVNULL, capture_output=True, text=True)
        print(k, '完成' if out.exists() else '失敗', f'{time.time() - t:.0f}s', (r.stdout or r.stderr).strip()[-200:])
        if i < len(want) - 1: time.sleep(30)   # 產圖排隊：一分鐘最多兩張


if __name__ == '__main__':
    main()
