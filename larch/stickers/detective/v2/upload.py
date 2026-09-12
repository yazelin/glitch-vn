"""序列上傳 27 張新貼圖（並行會撞 revision，實測 502/409），存下網址供 PUT 用。"""
import base64, json, os, time, urllib.request, urllib.error, glob

K = open(os.path.expanduser("~/.config/larch/key")).read().strip()
PROJ = "project-bec1644c-0dfe-4447-86c0-0c592e2f939f"
URL = f"https://larch.ink/api/agent/projects/{PROJ}/media"
D = "/home/ct/glitch-vn/larch/stickers/detective/"
OUT = D + "v2/uploaded-v2.json"

SHORT = {"01":"fishy","02":"motive","03":"nocoincidence","04":"blocked","05":"itsme",
 "06":"cantwrite","07":"illogical","08":"deadtalk","09":"onetruth","10":"onetruthyell",
 "11":"unusual","12":"amongus","13":"boldguess","14":"dyingmessage","15":"timeline",
 "16":"nohiding","17":"tipoficeberg","18":"casesolved","19":"tenrevisions","20":"ideastruck",
 "21":"greatart","22":"giveup","23":"whichbranch","24":"finishtonight","25":"perfectbgm",
 "26":"wheresbug","27":"needidea"}

files = sorted(f for f in glob.glob(D + "*.webp") if not f.endswith("cover.webp"))
assert len(files) == 27, len(files)
done = json.load(open(OUT)) if os.path.exists(OUT) else {}

for path in files:
    base = os.path.basename(path)
    num, label = base[:2], base[3:-5]
    if num in done:
        continue
    b64 = base64.b64encode(open(path, "rb").read()).decode()
    body = json.dumps({"name": f"glitch-detective-v2-{num}.webp", "mimeType": "image/webp",
                       "base64": b64, "category": "prop"}).encode()
    for attempt in range(5):
        req = urllib.request.Request(URL, data=body, headers={
            "Authorization": "Bearer " + K, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as f:
                a = json.load(f)["asset"]
            done[num] = {"num": num, "label": label, "short": SHORT[num],
                         "id": a["id"], "url": a["url"]}
            json.dump(done, open(OUT, "w"), ensure_ascii=False, indent=1)
            print(num, label, "ok")
            break
        except Exception as e:
            print(num, "第", attempt + 1, "次失敗", repr(e)[:110], flush=True)
            time.sleep(20)
    else:
        print(num, "五次都失敗，先跳過")
    time.sleep(2)

print("完成", len(done), "/ 27")
