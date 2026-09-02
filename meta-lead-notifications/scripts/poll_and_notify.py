#!/usr/bin/env python3
"""
Meta Lead → Slack notifier (polling).
Interroge l'API Meta Graph pour les leads d'un/des formulaire(s) Lead Ads et
poste chaque NOUVEAU lead dans un channel Slack via chat.postMessage.

Idempotent : garde un état des leadgen_id déjà notifiés (STATE_FILE).
Premier run (pas de state) : SEED silencieux = marque les leads existants comme
vus sans notifier (évite de spammer l'historique). Forcer la notif de l'existant
avec --notify-existing.

Config : variables d'env (cf. .env.example à la racine du skill), surchargées par le
fichier passé en --env. Aucune valeur secrète n'est imprimée.

Usage :
  poll_and_notify.py --env ~/.config/meta-lead-notifications/<client>.env
  poll_and_notify.py --env ... --test      # envoie 1 message de test puis sort
  poll_and_notify.py --env ... --seed       # marque l'existant comme vu, 0 notif
"""
import os, sys, json, time, argparse, urllib.request, urllib.parse, urllib.error

GV = os.environ.get("META_GRAPH_VERSION", "v21.0")
GBASE = f"https://graph.facebook.com/{GV}"
CLIENT_NAME = os.environ.get("CLIENT_NAME", "nouveau client")

# Libellés FR des clés de question connues (adapter aux clés de TON formulaire :
# full_name/email/phone_number/company_name sont natives Meta, le reste = questions custom)
LABELS = {
    "full_name": "Nom", "email": "Email", "phone_number": "Téléphone",
    "company_name": "Société", "profil": "Profil entreprise",
    "besoin": "Besoin principal", "volume": "Volume souhaité", "timing": "Timing",
}
ORDER = ["full_name", "company_name", "email", "phone_number",
         "profil", "besoin", "volume", "timing"]


def load_env(path):
    if path and os.path.exists(os.path.expanduser(path)):
        for line in open(os.path.expanduser(path)):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def http_json(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        return {"_http_error": e.read().decode()[:400], "_code": e.code}
    except Exception as e:
        return {"_error": str(e)}


def page_token(sys_token, page_id):
    d = http_json(f"{GBASE}/{page_id}?fields=access_token&access_token={sys_token}")
    return d.get("access_token")


def fetch_leads(form_id, token):
    """Tous les leads d'un form (paginé)."""
    out = []
    url = (f"{GBASE}/{form_id}/leads?fields=id,created_time,ad_id,form_id,"
           f"field_data&limit=100&access_token={token}")
    while url:
        d = http_json(url)
        if "data" not in d:
            print(f"  ⚠️ form {form_id}: {d.get('_http_error') or d.get('_error') or d}")
            break
        out += d["data"]
        url = d.get("paging", {}).get("next")
    return out


def fields_map(lead):
    m = {}
    for f in lead.get("field_data", []):
        vals = f.get("values", [])
        m[f.get("name")] = vals[0] if vals else ""
    return m


def format_message(lead, form_name=""):
    fm = fields_map(lead)
    when = lead.get("created_time", "")[:19].replace("T", " ")
    lines = [f":tada: *Nouveau lead — {CLIENT_NAME}*", ""]
    seen = set()
    for k in ORDER:
        if k in fm:
            seen.add(k)
            lines.append(f"*{LABELS.get(k, k)} :* {fm[k] or '—'}")
    for k, v in fm.items():           # toute clé non listée
        if k not in seen:
            lines.append(f"*{LABELS.get(k, k)} :* {v or '—'}")
    lines += ["", f"_Formulaire : {form_name or lead.get('form_id')} · reçu le {when}_"]
    return "\n".join(lines)


def slack_post(token, channel, text):
    body = json.dumps({"channel": channel, "text": text, "unfurl_links": False}).encode()
    d = http_json("https://slack.com/api/chat.postMessage", data=body,
                  headers={"Authorization": f"Bearer {token}",
                           "Content-Type": "application/json"})
    return d.get("ok"), d.get("error")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--notify-existing", action="store_true")
    args = ap.parse_args()
    load_env(args.env)
    global GV, GBASE, CLIENT_NAME
    GV = os.environ.get("META_GRAPH_VERSION", GV)
    GBASE = f"https://graph.facebook.com/{GV}"
    CLIENT_NAME = os.environ.get("CLIENT_NAME", CLIENT_NAME)

    missing = [k for k in ("META_ACCESS_TOKEN", "SLACK_TOKEN", "SLACK_CHANNEL",
                            "PAGE_ID", "FORM_IDS", "STATE_FILE") if not os.environ.get(k)]
    if missing:
        print(f"❌ variables manquantes : {', '.join(missing)} (voir .env.example)"); sys.exit(2)
    mtok = os.environ["META_ACCESS_TOKEN"]
    stok = os.environ["SLACK_TOKEN"]
    chan = os.environ["SLACK_CHANNEL"]
    page = os.environ["PAGE_ID"]
    forms = [f.strip() for f in os.environ["FORM_IDS"].split(",") if f.strip()]
    state_file = os.path.expanduser(os.environ["STATE_FILE"])

    if args.test:
        ok, err = slack_post(stok, chan,
            f":white_check_mark: *Notifications {CLIENT_NAME} activées* — vous recevrez ici "
            "chaque nouveau lead du formulaire Meta dès qu'il arrive. (message de test)")
        print("test slack:", "OK" if ok else f"ERR {err}")
        sys.exit(0 if ok else 1)

    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    seen = set()
    first_run = not os.path.exists(state_file)
    if not first_run:
        try:
            seen = set(json.load(open(state_file)).get("seen", []))
        except Exception:
            seen = set()

    pt = page_token(mtok, page)
    if not pt:
        print("❌ impossible d'obtenir le page token"); sys.exit(1)

    new_count = 0
    for form_id in forms:
        leads = fetch_leads(form_id, pt)
        for lead in leads:
            lid = lead["id"]
            if lid in seen:
                continue
            # premier run sans --notify-existing → seed silencieux
            if (first_run or args.seed) and not args.notify_existing:
                seen.add(lid); continue
            ok, err = slack_post(stok, chan, format_message(lead, form_id))
            if ok:
                seen.add(lid); new_count += 1
                print(f"  ✅ notifié {lid}")
            else:
                print(f"  ❌ slack {lid}: {err}")
    json.dump({"seen": sorted(seen), "updated": int(time.time())},
              open(state_file, "w"))
    mode = "SEED" if (first_run or args.seed) and not args.notify_existing else "RUN"
    print(f"[{mode}] forms={len(forms)} vus={len(seen)} nouveaux_notifiés={new_count}")


if __name__ == "__main__":
    main()
