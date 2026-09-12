"""3x3 貼圖表：一次九格，走 .11 codex-image-service。"""
import base64, json, os, sys, time, urllib.request

BASE = "https://ching-tech.ddns.net/codex-image"
KEY = os.environ["CODEX_IMAGE_KEY"]
D = "/home/ct/glitch-vn/larch/stickers/detective/"
OUT = D + "v2/"
REFS = ["01-這案子怪怪的.webp", "18-案件解決！.webp", "21-立繪這張神好看.webp"]

SPECS = [
 ("01", "pushing her glasses up with one hand, holding a round brass magnifying glass up in the other, eyes narrowed with suspicion"),
 ("02", "one hand cupping her chin, brows slightly furrowed, thinking hard"),
 ("03", "arms folded across her chest, face turned away, refusing to believe it"),
 ("04", "slumped face-down onto an antique black typewriter, eyes shut, completely out of energy"),
 ("05", "pointing at her own face with one finger, mouth open in shock"),
 ("06", "gripping a sheet of manuscript paper in both hands, head thrown back, mouth wide open screaming"),
 ("07", "one palm pressed to her forehead, a small notebook in the other hand, falling apart"),
 ("08", "index finger touching her lips, head tilted, puzzled"),
 ("09", "index finger raised and pointing upward, calm and declarative, faint confident smile"),
 ("10", "same raised index finger but yelling at the top of her lungs, sharp eyes, dramatic shadow across the upper face"),
 ("11", "chin resting on the hand that holds the magnifying glass, eyes closed, deep in thought"),
 ("12", "index finger pointing straight forward at the viewer, stern and serious"),
 ("13", "pushing her glasses up with a sly grin, the other index finger pointing at her own cheek"),
 ("14", "holding a pen, pointing it off to one side, body turned slightly away"),
 ("15", "both palms slammed flat on an open notebook, eyes wide, alarmed"),
 ("16", "arms folded, heavy shadow across her eyes, cold sharp stare"),
 ("17", "holding up a small glowing evidence bag between two fingers, certain of herself"),
 ("18", "wearing a dark plaid detective cap, eyes closed in a warm smile, hugging a brown leather notebook"),
 ("19", "both hands clutching her own head, collapsed forward onto a wooden desk, wailing"),
 ("20", "typing fast on a laptop, sweat drops flying around her, excited and grinning"),
 ("21", "holding a drawing tablet and stylus, sparkling star-struck eyes, yellow sparkles around her"),
 ("22", "slumped sideways in a chair, a puff of white sigh-steam leaving her mouth, given up"),
 ("23", "pointing at a floating translucent browser window with option boxes, confused"),
 ("24", "hoodie hood pulled up over her head, gripping a pen, determined glare"),
 ("25", "wearing large headphones, eyes shut, happy tears streaming down both cheeks"),
 ("26", "holding the magnifying glass right against a laptop screen, squinting, annoyed"),
 ("27", "kneeling with both palms pressed together in prayer, eyes brimming with tears, begging"),
]

HEAD = """CANVAS RULES — READ FIRST AND OBEY EXACTLY:
Produce ONE image that is a 3 x 3 grid of nine separate character stickers, three across and three down.
Every cell contains exactly one drawing of the same character, and nothing else.
The background of the WHOLE image, inside every cell and between cells, is flat pure green RGB(0,255,0) — chroma-key green. Nothing in the drawings may be green. No gradient, no texture, no shadow, no drop shadow, no vignette, no frame, no grid lines, no borders, no dividing lines, no text, no numbers, no captions, no watermark anywhere.

MOST IMPORTANT RULE: nothing a character wears, holds, leans on or sits at may touch or cross the edge of its cell. Every drawing — the character AND every prop, desk, typewriter, laptop or chair in the cell — must sit fully inside its cell with a clear band of empty green background on ALL FOUR sides: above, below, left and right. Props must be drawn whole, not running off the side. Above the head the gap must be the most generous of the four. The two crystal antenna clips standing up on her head must be drawn WHOLE, with their pointed tips complete and a visible gap of green background above them. The reference images you were given are all cropped at the top with the antenna tips sliced off, and their props run off the sides — that crop is the mistake you are fixing. Never repeat it.

CHARACTER — copy her design exactly from the reference images:
A cute anime girl, chest-up bust shot. Short mint-to-lavender gradient bob with one stray ahoge strand. Two pale-blue glowing crystal antenna clips standing up from her head, one on each side, each a small rounded triangular crystal on a short dark stalk. A silver double hair clip on her left bangs. Large blue-green eyes. Black choker. Oversized off-white hoodie with a dark navy inner collar, lavender-and-navy striped cuffs, a dark strap crossing her chest, and a small dark red ERROR badge on the chest. A chunky cyan-lit wristband on one wrist.

ART STYLE — match the references: soft pastel anime, clean crisp thin linework, cel shading with gentle gradients, mint / lavender / pale blue palette, rounded cute face, sticker art.

THE NINE CELLS, in reading order (left to right, top row first):
"""

TAIL = """
Keep all nine drawings at the same scale and the same eye level so they read as one set. Same character, same outfit, same colours in every cell. Vary only the pose, the expression and the prop as listed."""

def sheet(n):
    part = SPECS[n * 9:(n + 1) * 9]
    lines = "\n".join(f"{i+1}. {d}" for i, (_, d) in enumerate(part))
    prompt = HEAD + lines + TAIL
    refs = [base64.b64encode(open(D + r, "rb").read()).decode() for r in REFS]
    body = json.dumps({"prompt": prompt, "reference_images_base64": refs,
                       "size": "1536x1024", "n": 1}).encode()
    req = urllib.request.Request(BASE + "/v1/images/generate", data=body,
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=1200) as r:
        d = json.load(r)
    u = d["images"][0]["url"]
    dst = f"{OUT}sheet{n+1}.png"
    urllib.request.urlretrieve(u, dst)
    print("sheet%d  %.0fs  %s" % (n + 1, time.time() - t, dst))

for n in [int(x) - 1 for x in sys.argv[1:]]:
    sheet(n)
