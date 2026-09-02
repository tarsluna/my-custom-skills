#!/usr/bin/env python3
"""
Surveille un channel Slack et détecte l'envoi d'une clé API GoHighLevel (GHL).
Lit les messages depuis le dernier ts vu (état), scanne les patterns de clé GHL,
et écrit un fichier flag + dump de la clé quand détectée.

Sortie (stdout) :
  - "NO_KEY · <n> nouveaux messages"          → rien trouvé
  - "KEY_FOUND · <key> · by <user> · <ts>"     → clé détectée (+ flag écrit)

Patterns GHL :
  - JWT (clé API agency/location v1) : eyJ....eyJ....sig
  - Private Integration Token v2     : pit-xxxxxxxx
  - Token alphanum long précédé de "api"/"clé"/"key"/"ghl"/"highlevel"
Usage : slack_watch_ghl_key.py --env <secrets.env>
Env attendus : SLACK_TOKEN, SLACK_WATCH_CHANNEL, GHL_WATCH_STATE, GHL_KEY_OUT
"""
import os, sys, re, json, argparse, urllib.request, urllib.parse

def load_env(path):
    if path and os.path.exists(os.path.expanduser(path)):
        for line in open(os.path.expanduser(path)):
            line=line.strip()
            if line and not line.startswith("#") and "=" in line:
                k,v=line.split("=",1); os.environ.setdefault(k.strip(), v.strip())

def slack(method, params, token):
    url=f"https://slack.com/api/{method}?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url, headers={"Authorization":f"Bearer {token}"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

# Formats réels d'une clé API GHL : JWT v1 (eyJ.eyJ.sig) ou Private Integration Token v2 (pit-...).
# On ne matche QUE ça → zéro faux positif sur les liens de booking leadconnectorhq.
JWT  = re.compile(r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{8,}')
PIT  = re.compile(r'pit-[A-Za-z0-9-]{12,}')

def find_key(text):
    if not text: return None
    t=re.sub(r'[<>]', ' ', text)  # Slack entoure les liens de < >
    m=JWT.search(t) or PIT.search(t)
    return m.group(0) if m else None

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--env"); a=ap.parse_args()
    load_env(a.env)
    for k in ("SLACK_TOKEN","SLACK_WATCH_CHANNEL"):
        if not os.environ.get(k): print(f"❌ variable manquante : {k} (voir .env.example)"); sys.exit(2)
    token=os.environ["SLACK_TOKEN"]; chan=os.environ["SLACK_WATCH_CHANNEL"]
    state_f=os.path.expanduser(os.environ.get("GHL_WATCH_STATE",os.path.expanduser("~/.local/state/meta-lead-notifications/ghl-watch.json")))
    out_f=os.path.expanduser(os.environ.get("GHL_KEY_OUT",os.path.expanduser("~/.local/state/meta-lead-notifications/ghl-key.json")))
    last_ts="0"
    if os.path.exists(state_f):
        try: last_ts=json.load(open(state_f)).get("last_ts","0")
        except: pass
    params={"channel":chan,"limit":"50"}
    if last_ts!="0": params["oldest"]=last_ts
    r=slack("conversations.history", params, token)
    if not r.get("ok"):
        print("SLACK_ERR",r.get("error")); sys.exit(2)
    msgs=[m for m in r.get("messages",[]) if m.get("ts")!=last_ts]
    newest=last_ts
    found=None
    for m in msgs:
        if m.get("ts","0")>newest: newest=m["ts"]
        k=find_key(m.get("text",""))
        if k and not found:
            found=(k, m.get("user") or m.get("username") or "?", m.get("ts"), m.get("text","")[:200])
    # MAJ état
    os.makedirs(os.path.dirname(state_f) or ".", exist_ok=True)
    json.dump({"last_ts":newest}, open(state_f,"w"))
    if found:
        os.makedirs(os.path.dirname(out_f) or ".", exist_ok=True)
        json.dump({"key":found[0],"user":found[1],"ts":found[2],"text":found[3]}, open(out_f,"w"))
        print(f"KEY_FOUND · {found[0]} · by {found[1]} · {found[2]}")
    else:
        print(f"NO_KEY · {len(msgs)} nouveaux messages (last_ts={newest})")

if __name__=="__main__":
    main()
