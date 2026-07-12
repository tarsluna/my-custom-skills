#!/usr/bin/env python3
"""Pool batch respectant concurrent_jobs_limit.
Usage: python3 gen_pool.py <plan.json>
plan.json = { "model":"nano_banana_2", "max_concurrent":6, "items":[ {"id","aspect","prompt","outdir"}, ... ] }
Crée jusqu'à max_concurrent jobs en vol, télécharge dès completion, relance.
"""
import json, sys, subprocess, time, re, os, urllib.request

plan = json.load(open(sys.argv[1]))
MODEL = plan.get("model", "nano_banana_2")
MAXC = plan.get("max_concurrent", 6)
RES = plan.get("resolution", "2k")
items = plan["items"]

LOG = plan.get("log", "/tmp/gen_pool.log")
def log(m):
    line = f"{time.strftime('%H:%M:%S')} {m}"
    print(line, flush=True)
    open(LOG, "a").write(line + "\n")

def run(args, t=120):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=t)
    except Exception as e:
        class R: stdout=""; stderr=str(e)
        return R()

log(f"=== POOL model={MODEL} items={len(items)} maxc={MAXC} ===")

# filtrer ce qui existe déjà
todo = []
for it in items:
    out = os.path.join(it["outdir"], f"{it['id']}.png")
    if os.path.exists(out) and os.path.getsize(out) > 50000:
        log(f"{it['id']} déjà présent, skip")
    else:
        os.makedirs(it["outdir"], exist_ok=True)
        todo.append(it)

def create_job(it):
    args = ["higgsfield", "generate", "create", MODEL,
            "--prompt", " ".join(it["prompt"].split()),
            "--aspect_ratio", it.get("aspect", "4:5"), "--resolution", RES, "--json"]
    if MODEL in ("gpt_image_2", "imagegen_2_0"):
        args += ["--quality", "high"]
    r = run(args, 90)
    txt = (r.stdout or "") + (r.stderr or "")
    if "concurrent_jobs_limit" in txt:
        return None, "limit"
    # 2 formats possibles : {"id":"uuid"} (gpt) OU ["uuid"] (nano). On prend le 1er UUID.
    m = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', txt)
    return (m.group(1) if m else None), (txt[:80] if not m else "")

def job_state(jid):
    r = run(["higgsfield", "generate", "get", jid, "--json"], 60)
    txt = r.stdout or ""
    st = re.search(r'"status"\s*:\s*"(\w+)"', txt)
    url = re.findall(r'https://\S+?\.png', txt)
    return (st.group(1) if st else "?"), (url[-1] if url else "")

def download(it, url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=60).read()
    open(os.path.join(it["outdir"], f"{it['id']}.png"), "wb").write(data)
    return len(data)

inflight = {}   # jid -> item
queue = list(todo)
ok = 0
deadline = time.time() + 2400
while (queue or inflight) and time.time() < deadline:
    # remplir le pool
    while queue and len(inflight) < MAXC:
        it = queue[0]
        jid, err = create_job(it)
        if jid:
            inflight[jid] = it
            queue.pop(0)
            log(f"{it['id']} → job {jid[:8]} ({len(inflight)} en vol)")
        elif err == "limit":
            log(f"limite atteinte, on attend (en vol={len(inflight)})")
            break
        else:
            log(f"{it['id']} création échouée: {err}")
            queue.pop(0)
        time.sleep(1)
    # vérifier les jobs en vol
    time.sleep(12)
    for jid, it in list(inflight.items()):
        st, url = job_state(jid)
        if st == "completed" and url:
            try:
                sz = download(it, url)
                log(f"{it['id']} OK ({sz} o)")
                ok += 1
            except Exception as e:
                log(f"{it['id']} dl FAIL {e}")
            inflight.pop(jid)
        elif st in ("failed", "error", "canceled"):
            log(f"{it['id']} job {st}")
            inflight.pop(jid)

if queue or inflight:
    rem = [i["id"] for i in queue] + [it["id"] for it in inflight.values()]
    log(f"⚠ non terminés: {rem}")
log(f"=== POOL END ok={ok}/{len(todo)} ===")
