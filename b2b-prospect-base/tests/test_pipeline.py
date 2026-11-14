#!/usr/bin/env python3
"""Tests hors ligne, sur un metier et des sites fictifs. Aucune requete reseau n'est possible."""
import csv
import datetime as dt
import json
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_domains  # noqa: E402
import crawl_sites  # noqa: E402
import fetch_registry  # noqa: E402
import filter_keyword_sites  # noqa: E402
import judge_trade  # noqa: E402
import merge  # noqa: E402
import open_data  # noqa: E402
import prospect_core as core  # noqa: E402
import qc_sample  # noqa: E402
import read_terms  # noqa: E402


def no_network(*args, **kwargs):
    raise AssertionError("Tentative de connexion reseau pendant un test")


def setUpModule():
    for name in ("create_connection", "getaddrinfo"):
        patcher = mock.patch.object(socket, name, no_network)
        patcher.start()
        unittest.addModuleCleanup(patcher.stop)
    patcher = mock.patch.object(socket.socket, "connect", no_network)
    patcher.start()
    unittest.addModuleCleanup(patcher.stop)


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def now(self):
        return self.t

    def sleep(self, seconds):
        self.t += seconds


class FakeWeb:
    """Le web fictif : {url: (statut, entetes, corps)}. Tout le reste renvoie 404."""

    def __init__(self, pages, clock=None):
        self.pages = pages
        self.calls = []
        self.clock = clock

    def request(self, method, url, headers, data=None):
        self.calls.append((method, url, headers.get("User-Agent"), self.clock.now() if self.clock else 0))
        status, head, body = self.pages.get(url, (404, {}, b""))
        return core.Response(status, head, body if isinstance(body, bytes) else body.encode(), url)

    def urls(self):
        return [call[1] for call in self.calls]


FILLER = " Nous creons et entretenons des jardins dans toute la region, avec un bureau d'etudes integre. " * 5
HTML = {"content-type": "text/html; charset=utf-8"}


def html_page(title, body):
    return (200, HTML, f"<html><head><title>{title}</title></head><body>{body}{FILLER}</body></html>")


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.project = Path(self._tmp.name) / "projet"
        self.project.mkdir()
        self.config = json.loads((REPO / "config" / "trade.example.json").read_text(encoding="utf-8"))
        (self.project / "config.json").write_text(json.dumps(self.config), encoding="utf-8")
        self.clock = FakeClock()

    def tearDown(self):
        self._tmp.cleanup()

    def review(self, source, verdict="autorise", quote="Reutilisation permise (licence ouverte fictive)."):
        path = core.review_path(self.project, source)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "source": source, "kind": "source", "robots_url": "https://exemple-fictif.example/robots.txt",
            "terms_url": "https://exemple-fictif.example/cgu", "read_at": dt.date.today().isoformat(),
            "verdict": verdict, "licence": "Licence fictive", "quote": quote,
        }), encoding="utf-8")

    def client(self, source, web):
        self.review(source)
        return core.Client(self.project, source, self.config, transport=web, clock=self.clock.now, sleep=self.clock.sleep)


# --- Garde-fous du client ----------------------------------------------------------------

class GuardrailTests(Base):
    def test_no_request_without_terms_review(self):
        web = FakeWeb({})
        with self.assertRaises(core.TermsNotReviewed):
            core.Client(self.project, "annuaire", self.config, transport=web)
        self.assertEqual(web.calls, [])

    def test_forbidding_terms_are_recorded_with_quote(self):
        self.review("annuaire", verdict="interdit", quote="Toute extraction de cet annuaire est interdite.")
        with self.assertRaises(core.TermsForbidden):
            core.Client(self.project, "annuaire", self.config, transport=FakeWeb({}))
        blocked = (self.project / "data/raw/annuaire/BLOCKED.md").read_text(encoding="utf-8")
        self.assertIn("Toute extraction de cet annuaire est interdite.", blocked)

    def test_review_must_be_complete(self):
        self.review("annuaire")
        path = core.review_path(self.project, "annuaire")
        data = json.loads(path.read_text(encoding="utf-8"))
        data["quote"] = ""
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(core.TermsNotReviewed):
            core.Client(self.project, "annuaire", self.config, transport=FakeWeb({}))

    def test_read_terms_only_reads_robots_and_terms(self):
        web = FakeWeb({
            "https://annuaire-fictif.example/robots.txt": (200, {"content-type": "text/plain"}, "User-agent: *\nAllow: /"),
            "https://annuaire-fictif.example/cgu": html_page("CGU", "Conditions fictives."),
        }, self.clock)
        code = read_terms.run(self.project, "annuaire", "https://annuaire-fictif.example/robots.txt",
                              "https://annuaire-fictif.example/cgu", self.config, transport=web, sleep=self.clock.sleep)
        self.assertEqual(code, 0)
        self.assertTrue(all("robots.txt" in u or u.endswith("/cgu") for u in web.urls()))
        self.assertTrue((self.project / "data/raw/annuaire/terms/terms.txt").exists())
        with self.assertRaises(core.TermsNotReviewed):
            client = core.Client(self.project, "annuaire", self.config, transport=web,
                                 terms_bootstrap={"https://annuaire-fictif.example/cgu"})
            client.get("https://annuaire-fictif.example/membres")

    def test_robots_is_read_before_the_first_page(self):
        web = FakeWeb({
            "https://fictif.example/robots.txt": (200, {}, "User-agent: *\nDisallow: /prive/"),
            "https://fictif.example/page": html_page("t", "ok"),
        })
        client = self.client("test", web)
        client.get("https://fictif.example/page")
        self.assertEqual(web.urls(), ["https://fictif.example/robots.txt", "https://fictif.example/page"])

    def test_disallowed_url_is_not_fetched(self):
        web = FakeWeb({"https://fictif.example/robots.txt": (200, {}, "User-agent: *\nDisallow: /prive/")})
        client = self.client("test", web)
        with self.assertRaises(core.Disallowed):
            client.get("https://fictif.example/prive/page")
        self.assertEqual(web.urls(), ["https://fictif.example/robots.txt"])

    def test_redirect_repasses_through_robots_of_the_new_host(self):
        web = FakeWeb({
            "https://a-fictif.example/robots.txt": (404, {}, ""),
            "https://a-fictif.example/": (301, {"location": "https://b-fictif.example/"}, ""),
            "https://b-fictif.example/robots.txt": (200, {}, "User-agent: *\nDisallow: /"),
        })
        client = self.client("test", web)
        with self.assertRaises(core.Disallowed):
            client.get("https://a-fictif.example/")
        self.assertNotIn("https://b-fictif.example/", web.urls())

    def test_unreadable_robots_is_not_a_permission(self):
        web = FakeWeb({"https://fictif.example/robots.txt": (500, {}, "")})
        client = self.client("test", web)
        with self.assertRaises(core.Unreachable):
            client.get("https://fictif.example/page")
        self.assertEqual(web.urls(), ["https://fictif.example/robots.txt"])

    def test_403_429_and_antibot_stop_the_host_for_good(self):
        for status, body, reason in ((403, "", "http_403"), (429, "", "http_429"),
                                     (200, "<title>Just a moment...</title>", "anti-bot")):
            with self.subTest(reason=reason):
                source = "src-" + reason
                web = FakeWeb({
                    "https://bloque-fictif.example/robots.txt": (404, {}, ""),
                    "https://bloque-fictif.example/page": (status, HTML, body),
                })
                client = self.client(source, web)
                with self.assertRaises(core.Blocked):
                    client.get("https://bloque-fictif.example/page")
                count = len(web.calls)
                with self.assertRaises(core.Blocked):
                    client.get("https://bloque-fictif.example/autre")
                self.assertEqual(len(web.calls), count, "aucune requete apres un blocage")
                restarted = self.client(source, web)  # le blocage survit a un redemarrage
                with self.assertRaises(core.Blocked):
                    restarted.get("https://bloque-fictif.example/autre")
                self.assertEqual(len(web.calls), count)
                self.assertIn(reason, (self.project / f"data/raw/{source}/BLOCKED.md").read_text(encoding="utf-8"))

    def test_forbidden_hosts_are_refused_before_any_request(self):
        web = FakeWeb({})
        client = self.client("test", web)
        for url in ("https://www.linkedin.com/in/fictif", "https://fr.linkedin.com/company/fictif",
                    "https://www.facebook.com/fictif", "https://www.instagram.com/fictif",
                    "https://annuaire-paysagistes-fictif.example/liste"):
            with self.subTest(url=url):
                with self.assertRaises(core.ForbiddenHost):
                    client.get(url)
        self.assertEqual(web.calls, [])

    def test_browser_user_agent_is_refused(self):
        with self.assertRaises(core.ConfigError):
            core.check_user_agent("Mozilla/5.0 (Macintosh)")

    def test_workers_are_capped(self):
        with self.assertRaises(core.ConfigError):
            core.check_workers(41)
        self.assertEqual(core.check_workers(40), 40)

    def test_interval_cannot_go_below_one_second(self):
        self.assertEqual(core.HostThrottle(0.2).interval, core.MIN_INTERVAL)

    def test_one_request_per_second_and_per_host(self):
        pages = {"https://fictif.example/robots.txt": (404, {}, "")}
        pages.update({f"https://fictif.example/p{i}": html_page("t", "x") for i in range(4)})
        web = FakeWeb(pages, self.clock)
        client = self.client("test", web)
        for i in range(4):
            client.get(f"https://fictif.example/p{i}")
        times = [call[3] for call in web.calls]
        gaps = [b - a for a, b in zip(times, times[1:])]
        self.assertTrue(all(gap >= core.MIN_INTERVAL for gap in gaps), gaps)

    def test_crawl_delay_is_respected(self):
        web = FakeWeb({
            "https://fictif.example/robots.txt": (200, {}, "User-agent: *\nCrawl-delay: 5"),
            "https://fictif.example/a": html_page("t", "x"),
            "https://fictif.example/b": html_page("t", "x"),
        }, self.clock)
        client = self.client("test", web)
        client.get("https://fictif.example/a")
        client.get("https://fictif.example/b")
        self.assertGreaterEqual(web.calls[-1][3] - web.calls[-2][3], 5)

    def test_user_agent_is_the_project_one(self):
        web = FakeWeb({"https://fictif.example/robots.txt": (404, {}, ""), "https://fictif.example/p": html_page("t", "x")})
        self.client("test", web).get("https://fictif.example/p")
        self.assertTrue(all(call[2] == self.config["user_agent"] for call in web.calls))

    def test_no_smtp_code_in_scripts(self):
        banned = re.compile(r"smtplib|\bRCPT\b|\bHELO\b|\bEHLO\b|starttls", re.I)
        for path in SCRIPTS.glob("*.py"):
            self.assertIsNone(banned.search(path.read_text(encoding="utf-8")), path.name)

    def test_no_contact_guessing_helper(self):
        pattern = re.compile(r"prenom\s*\+\s*[\"']\.[\"']\s*\+\s*nom|first\s*\+\s*[\"']\.[\"']\s*\+\s*last", re.I)
        for path in SCRIPTS.glob("*.py"):
            self.assertIsNone(pattern.search(path.read_text(encoding="utf-8")), path.name)

    def test_terms_forbid_quotes_the_clause(self):
        self.assertIn("extraction", core.terms_forbid("Toute extraction automatisee des adresses de ce site est strictement interdite."))
        self.assertIn("Scraping", core.terms_forbid("Scraping of this website is not permitted without written consent."))
        self.assertEqual(core.terms_forbid("Toute reproduction des photographies est interdite."), "")
        self.assertEqual(core.terms_forbid("Contactez-nous pour une collecte de dechets verts."), "")


# --- Crawl d'un site officiel ------------------------------------------------------------

SITE = "jardins-verveine-fictif.fr"
BASE = f"https://{SITE}"
LEGAL = ("Mentions legales. SIREN 123 456 789. Hebergeur fictif. Editeur du site : Jardins Verveine, "
         "paysagiste concepteur a Lyon 69001. " + FILLER)


def site_pages():
    return {
        f"{BASE}/robots.txt": (200, {"content-type": "text/plain"}, "User-agent: *\nDisallow: /prive/"),
        f"{BASE}/mentions-legales": html_page("Mentions legales", LEGAL),
        f"{BASE}/": html_page(
            "Jardins Verveine | Paysagiste concepteur a Lyon",
            '<a href="/contact">Contact</a> <a href="/prive/x">Prive</a> '
            '<script>var cache = "jsleak@jardins-verveine-fictif.fr";</script>'
            "<!-- commentaire@jardins-verveine-fictif.fr --> "
            "bureau [at] jardins-verveine-fictif.fr",
        ),
        f"{BASE}/contact": html_page(
            "Contact",
            f'<a href="mailto:contact@{SITE}">Nous ecrire</a> '
            f"Claire Fictive : claire@{SITE} recrutement@{SITE} "
            "boite.fictive@gmail.com autre-societe@ailleurs-fictif.fr",
        ),
    }


class CrawlTests(Base):
    def crawl(self, pages, rows, name="sites-officiels", workers=2):
        web = FakeWeb(pages, self.clock)
        client = self.client(name, web)
        (self.project / "input.csv").parent.mkdir(exist_ok=True)
        with (self.project / "input.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        stats = crawl_sites.run(self.project, self.config, client, self.project / "input.csv", name,
                                workers=workers, resolve=lambda domain: True)
        path = self.project / f"data/raw/{name}/brut.csv"
        return web, stats, core.read_csv(path)

    def registry_row(self):
        return {"domain": SITE, "siren": "123456789", "entreprise": "Jardins Verveine", "segment": "paysagiste",
                "naf": "81.30Z", "prenom": "Claire", "nom": "Fictive", "code_postal": "69001", "ville": "Lyon"}

    def test_only_mailto_and_visible_text(self):
        _, _, rows = self.crawl(site_pages(), [self.registry_row()])
        emails = {r["email"] for r in rows}
        self.assertIn(f"contact@{SITE}", emails)
        self.assertIn(f"claire@{SITE}", emails)
        self.assertIn("boite.fictive@gmail.com", emails)
        joined = " ".join(emails)
        for absent in ("jsleak", "commentaire", "recrutement", "ailleurs-fictif"):
            self.assertNotIn(absent, joined)
        self.assertFalse(any(e.startswith("bureau@") for e in emails), "forme [at] ignoree")

    def test_robots_then_legal_then_extraction_pages(self):
        web, _, _ = self.crawl(site_pages(), [self.registry_row()])
        urls = web.urls()
        self.assertEqual(urls[0], f"{BASE}/robots.txt")
        self.assertLess(urls.index(f"{BASE}/mentions-legales"), urls.index(f"{BASE}/"))
        self.assertLess(urls.index(f"{BASE}/"), urls.index(f"{BASE}/contact"))

    def test_rows_carry_proof_and_type(self):
        _, _, rows = self.crawl(site_pages(), [self.registry_row()])
        by_email = {r["email"]: r for r in rows}
        self.assertEqual(by_email[f"contact@{SITE}"]["email_type"], "generique")
        self.assertEqual(by_email[f"claire@{SITE}"]["email_type"], "nominatif")
        self.assertEqual(by_email["boite.fictive@gmail.com"]["email_type"], "domaine_perso")
        self.assertEqual(by_email[f"contact@{SITE}"]["source_url"], f"{BASE}/contact")
        self.assertEqual(by_email[f"contact@{SITE}"]["segment"], "paysagiste_concepteur")
        self.assertTrue(all(r["collected_at"] and r["siren"] == "123456789" for r in rows))

    def test_site_that_forbids_collection_gives_nothing(self):
        pages = site_pages()
        pages[f"{BASE}/mentions-legales"] = html_page(
            "CGU", "Toute extraction automatisee des adresses de ce site est strictement interdite. " + LEGAL)
        web, stats, rows = self.crawl(pages, [self.registry_row()])
        self.assertEqual(rows, [])
        self.assertEqual(stats["bloque"], 1)
        self.assertNotIn(f"{BASE}/contact", web.urls(), "aucune page d'extraction apres un refus")
        blocked = (self.project / "data/raw/sites-officiels/BLOCKED.md").read_text(encoding="utf-8")
        self.assertIn("strictement interdite", blocked)

    def test_legal_page_found_through_home_link_before_extraction(self):
        pages = site_pages()
        del pages[f"{BASE}/mentions-legales"]
        pages[f"{BASE}/"] = html_page("Jardins Verveine | Paysagiste concepteur a Lyon",
                                      '<a href="/infos-legales">Infos</a> <a href="/contact">Contact</a>')
        pages[f"{BASE}/infos-legales"] = html_page("Legal", LEGAL)
        web, _, _ = self.crawl(pages, [self.registry_row()])
        urls = web.urls()
        self.assertLess(urls.index(f"{BASE}/infos-legales"), urls.index(f"{BASE}/contact"))

    def test_blocked_site_stops_and_keeps_nothing(self):
        pages = site_pages()
        pages[f"{BASE}/mentions-legales"] = (429, {}, "")
        web, stats, rows = self.crawl(pages, [self.registry_row()])
        self.assertEqual(rows, [])
        self.assertEqual(stats["bloque"], 1)
        self.assertEqual(web.urls(), [f"{BASE}/robots.txt", f"{BASE}/mentions-legales"])

    def test_site_of_someone_else_is_rejected(self):
        row = self.registry_row()
        row["siren"], row["entreprise"], row["ville"], row["code_postal"] = "999999999", "Autre Societe", "Brest", "29200"
        _, stats, rows = self.crawl(site_pages(), [row])
        self.assertEqual(rows, [])
        self.assertEqual(stats["non_verifie"], 1)

    def test_unreachable_is_not_sans_site(self):
        web = FakeWeb({}, self.clock)

        class Down:
            def __init__(self, inner):
                self.inner = inner
                self.calls = inner.calls

            def request(self, *args, **kwargs):
                raise core.Unreachable("delai depasse")

        self.review("panne")
        client = core.Client(self.project, "panne", self.config, transport=Down(web), clock=self.clock.now, sleep=self.clock.sleep)
        with (self.project / "input.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["domain"])
            writer.writeheader()
            writer.writerow({"domain": "lent-fictif.fr"})
        stats = crawl_sites.run(self.project, self.config, client, self.project / "input.csv", "panne",
                                workers=1, resolve=lambda domain: True)
        self.assertEqual(stats["injoignable"], 1)
        done = (self.project / "data/raw/panne/done.txt").read_text(encoding="utf-8")
        self.assertNotIn("lent-fictif.fr", done, "un injoignable reste a reprendre")

    def test_retry_unreachable_reads_last_status(self):
        pages = site_pages()
        folder = self.project / "data/raw/sites-officiels"
        folder.mkdir(parents=True)
        (folder / "statuses.tsv").write_text(f"injoignable\tdisparu-fictif.fr\ninjoignable\t{SITE}\nverifie\tdisparu-fictif.fr\n", encoding="utf-8")
        web = FakeWeb(pages, self.clock)
        client = self.client("sites-officiels", web)
        with (self.project / "input.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["domain"])
            writer.writeheader()
            writer.writerows([{"domain": SITE}, {"domain": "disparu-fictif.fr"}])
        crawl_sites.run(self.project, self.config, client, self.project / "input.csv", "sites-officiels", workers=1,
                        retry_unreachable=True, resolve=lambda domain: True)
        self.assertNotIn("https://disparu-fictif.fr/robots.txt", web.urls())
        self.assertIn(f"{BASE}/robots.txt", web.urls())

    def test_keyword_site_then_filter(self):
        pages = site_pages()
        shop = "boutique-paysage-fictif.fr"
        pages.update({
            f"https://{shop}/robots.txt": (404, {}, ""),
            f"https://{shop}/": html_page("Boutique Paysage | Jardinerie en ligne",
                                          f'<a href="/contact">Contact</a> paysagiste {FILLER}'),
            f"https://{shop}/contact": html_page("Contact", f"bonjour@{shop}"),
        })
        rows_input = [{"domain": SITE}, {"domain": shop}]
        _, stats, raw = self.crawl(pages, rows_input)
        self.assertEqual({r["site"] for r in raw}, {BASE, f"https://{shop}"})
        kept, reasons = filter_keyword_sites.run(self.project, self.config, "sites-officiels")
        self.assertTrue(all(shop not in r["email"] for r in kept))
        self.assertEqual(reasons["magasin"], 1)
        self.assertTrue(any(SITE in r["email"] for r in kept))


# --- Registre et croisement ----------------------------------------------------------------

class RegistryTests(Base):
    def api(self, results, total_pages=1):
        return json.dumps({"results": results, "total_results": len(results), "total_pages": total_pages})

    def api_url(self, department, page=1):
        return (fetch_registry.API + "?activite_principale=81.30Z&etat_administratif=A&per_page=25"
                f"&departement={department}&page={page}")

    def run_registry(self, pages):
        self.config["registry"]["departments"] = ["69"]
        pages = {**pages, "https://recherche-entreprises.api.gouv.fr/robots.txt": (404, {}, "")}
        web = FakeWeb(pages, self.clock)
        client = self.client("registre", web)
        code, stats = fetch_registry.run(self.project, self.config, client, retry_wait=0)
        return web, code, stats

    def test_minimised_rows(self):
        item = {
            "siren": "123456789", "nom_raison_sociale": "Jardins Verveine", "nom_complet": "JARDINS VERVEINE",
            "statut_diffusion": "O",
            "siege": {"adresse": "1 rue Fictive 69001 Lyon", "code_postal": "69001", "libelle_commune": "Lyon",
                      "statut_diffusion_etablissement": "O"},
            "dirigeants": [{"type_dirigeant": "personne physique", "prenoms": "CLAIRE ANNE", "nom": "FICTIVE",
                            "qualite": "Gerant", "date_de_naissance": "1980-01"}],
        }
        hidden = dict(item, siren="222222222", statut_diffusion="P")
        off_topic = dict(item, siren="333333333", nom_complet="GARAGE AUTOMOBILE")
        web, code, _ = self.run_registry({self.api_url("69"): (200, {}, self.api([item, hidden, off_topic]))})
        self.assertEqual(code, 0)
        rows = core.read_csv(self.project / "data/registre.csv")
        self.assertEqual([r["siren"] for r in rows], ["123456789"])
        self.assertEqual(rows[0]["prenom"], "Claire")
        joined = json.dumps(rows)
        self.assertNotIn("1980", joined)
        self.assertNotIn("1 rue Fictive", joined)
        self.assertNotIn("email", rows[0])

    def test_api_429_stops_the_run(self):
        web, code, _ = self.run_registry({self.api_url("69"): (429, {}, "")})
        self.assertEqual(code, 2)
        self.assertEqual(len(web.calls), 2, "pas de nouvel essai apres un 429")
        self.assertIn("http_429", (self.project / "data/raw/registre/BLOCKED.md").read_text(encoding="utf-8"))

    def test_build_domains_crosses_afnic_with_registry(self):
        (self.project / "data").mkdir()
        with (self.project / "data/registre.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fetch_registry.FIELDS)
            writer.writeheader()
            writer.writerow({"siren": "123456789", "entreprise": "Jardins Verveine", "segment": "paysagiste", "naf": "81.30Z",
                             "prenom": "Claire", "nom": "Fictive", "qualite": "", "code_postal": "69001", "ville": "Lyon",
                             "departement": "69"})
        afnic = self.project / "afnic.csv"
        with afnic.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, delimiter=";")
            writer.writerow(["Nom de domaine", "Sous domaine", "Domaine IDN", "Date de retrait du WHOIS"])
            writer.writerow(["jardins-verveine.fr", "fr", "0", ""])  # correspond au nom du registre
            writer.writerow(["paysages-du-sud-fictif.fr", "fr", "0", ""])  # mot du metier
            writer.writerow(["jardinerie-du-centre.fr", "fr", "0", ""])  # faux ami
            writer.writerow(["jardins-retire.fr", "fr", "0", "2025-01-01"])  # retire du WHOIS
            writer.writerow(["sans-rapport-fictif.fr", "fr", "0", ""])
        self.review(build_domains.SOURCE)
        summary = build_domains.build(self.project, self.config, afnic)
        folder = self.project / "data/raw/afnic-domaines"
        a = core.read_csv(folder / "input_a.csv")
        b = core.read_csv(folder / "input_b.csv")
        self.assertEqual([r["domain"] for r in a], ["jardins-verveine.fr"])
        self.assertEqual(a[0]["siren"], "123456789")
        self.assertEqual([r["domain"] for r in b], ["paysages-du-sud-fictif.fr"])
        self.assertEqual(summary["a_noms"], 1)


# --- Open data -----------------------------------------------------------------------------

class OpenDataTests(Base):
    def test_overpass_then_build(self):
        self.config["open_data"]["overpass"]["areas"] = ["FR-ARA"]
        document = {"elements": [
            {"type": "node", "id": 1, "tags": {"craft": "landscaper", "name": "Jardins du Plateau Fictif",
                                               "email": "contact@plateau-fictif.fr", "phone": "+33 6 00 00 00 00",
                                               "addr:postcode": "69001", "addr:city": "Lyon"}},
            {"type": "node", "id": 2, "tags": {"craft": "gardener", "name": "Sans Mail Fictif",
                                               "website": "https://sans-mail-fictif.fr"}},
            {"type": "node", "id": 3, "tags": {"craft": "gardener", "name": "Ecole Horticole Fictive", "email": "a@ecole-fictive.fr"}},
            {"type": "node", "id": 4, "tags": {"craft": "gardener", "name": "Lien Social Fictif",
                                               "website": "https://www.facebook.com/fictif"}},
        ]}
        pages = {
            "https://overpass.openstreetmap.fr/robots.txt": (404, {}, ""),
            "https://overpass.openstreetmap.fr/api/interpreter": (200, {}, json.dumps(document)),
        }
        web = FakeWeb(pages, self.clock)
        client = self.client("open-data", web)
        self.assertEqual(open_data.cmd_overpass(self.project, self.config, client, retry_wait=0), 0)
        stored = (self.project / "data/raw/open-data/osm/FR-ARA.json").read_text(encoding="utf-8")
        self.assertNotIn("+33", stored, "aucun telephone, meme en brut")
        rows, todo = open_data.cmd_build(self.project, self.config)
        self.assertEqual([r["email"] for r in rows], ["contact@plateau-fictif.fr"])
        self.assertEqual(rows[0]["source_url"], "https://www.openstreetmap.org/node/1")
        self.assertEqual([t["domain"] for t in todo], ["sans-mail-fictif.fr"])

    def test_dataset_keeps_only_declared_fields(self):
        page = {"results": [{"email": "contact@donnees-fictif.fr", "nom": "Donnees Fictif", "commune": "Lyon", "cp": "69001",
                             "siret": "12345678900011", "site": "https://donnees-fictif.fr", "telephone": "0600000000"}],
                "next": None}
        pages = {"https://opendata.example/robots.txt": (404, {}, ""),
                 "https://opendata.example/api/lines?size=1000": (200, {}, json.dumps(page))}
        client = self.client("open-data", FakeWeb(pages, self.clock))
        self.assertEqual(open_data.cmd_dataset(self.project, self.config, client), 0)
        self.assertNotIn("0600000000", (self.project / "data/raw/open-data/jeu-fictif.jsonl").read_text(encoding="utf-8"))
        rows, _ = open_data.cmd_build(self.project, self.config)
        self.assertEqual(rows[0]["siren"], "123456789")
        self.assertIn("siret:12345678900011", rows[0]["source_url"])


# --- Controle qualite ----------------------------------------------------------------------

class QcTests(Base):
    def test_sample_rereads_each_mail_and_masks_it(self):
        site_a, site_b = "qc-un-fictif.fr", "qc-deux-fictif.fr"
        pages = {
            f"https://{site_a}/robots.txt": (404, {}, ""),
            f"https://{site_a}/contact": html_page("Contact", f"paysagiste contact@{site_a}"),
            f"https://{site_a}/": html_page("Paysagiste fictif", f"paysagiste contact@{site_a} {FILLER}"),
            f"https://{site_b}/robots.txt": (404, {}, ""),
            f"https://{site_b}/contact": html_page("Contact", "Ce mail a disparu"),
            f"https://{site_b}/": html_page("Paysagiste fictif deux", "paysagiste"),
        }
        (self.project / "sources").mkdir()
        with (self.project / "sources/sites.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=core.SCHEMA)
            writer.writeheader()
            writer.writerow(dict.fromkeys(core.SCHEMA, "") | {
                "email": f"contact@{site_a}", "site": f"https://{site_a}", "source_url": f"https://{site_a}/contact", "siren": "123456789"
            })
            writer.writerow(dict.fromkeys(core.SCHEMA, "") | {
                "email": f"contact@{site_b}", "site": f"https://{site_b}", "source_url": f"https://{site_b}/contact"
            })
        client = self.client("sites", FakeWeb(pages, self.clock))
        items = qc_sample.sample(self.project, self.config, client, "sites", n=2, seed=3)
        by_domain = {i["domain"]: i for i in items}
        self.assertTrue(by_domain[site_a]["email_retrouve"])
        self.assertFalse(by_domain[site_b]["email_retrouve"])
        packet = (self.project / "data/raw/sites/qc_packet.json").read_text(encoding="utf-8")
        self.assertNotIn(f"contact@{site_a}", packet, "le paquet ne recopie pas le mail")

        with self.assertRaises(core.GuardrailError):
            qc_sample.report(self.project, "sites")
        path = self.project / "data/raw/sites/qc_packet.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data["items"]:
            item["verdict"] = "ok"
        path.write_text(json.dumps(data), encoding="utf-8")
        summary = qc_sample.report(self.project, "sites")
        self.assertEqual(summary["relues"], 2)
        self.assertEqual(summary["mauvaises"], 1, "un mail non retrouve compte comme mauvais")


# --- Jugement metier -----------------------------------------------------------------------

class JudgeTests(Base):
    def test_only_page_data_is_sent_and_bad_answers_are_rejected(self):
        domain = "juge-fictif.fr"
        pages = {
            f"https://{domain}/robots.txt": (404, {}, ""),
            f"https://{domain}/": html_page("Entreprise fictive", f"Ecrivez a claire@{domain} ou 06 00 00 00 00. {FILLER}"),
        }
        client = self.client("judge", FakeWeb(pages, self.clock))
        (self.project / "livrable").mkdir()
        with (self.project / "livrable/base_prospects.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=merge.OUTPUT_COLUMNS)
            writer.writeheader()
            writer.writerow(dict.fromkeys(merge.OUTPUT_COLUMNS, "") | {"site": f"https://{domain}", "email": f"claire@{domain}", "prenom": "Claire", "nom": "Fictive"})
        seen = []

        def ask(state):
            seen.append(json.dumps(state))
            return json.dumps({"choice": "hors_cible", "confidence": 0.9})

        stats = judge_trade.run(self.project, self.config, client, ask, workers=1)
        self.assertEqual(stats["juges"], 1)
        self.assertNotIn(f"claire@{domain}", seen[0])
        self.assertNotIn("06 00 00 00 00", seen[0])
        self.assertNotIn("Claire", seen[0])
        with self.assertRaises(ValueError):
            judge_trade.parse_verdict(json.dumps({"choice": "autre", "confidence": 0.9}), self.config["judge"]["choices"])
        self.assertEqual(judge_trade.parse_verdict(json.dumps({"choice": "hors_cible", "confidence": 0.5}),
                                                  self.config["judge"]["choices"]), ("hors_cible", 0.5))
        messages = judge_trade.build_messages({"domain": domain}, self.config["judge"]["choices"])
        self.assertIn("untrusted", messages[0]["content"])


# --- Fusion --------------------------------------------------------------------------------

class MergeTests(Base):
    def write_source(self, name, rows):
        (self.project / "sources").mkdir(exist_ok=True)
        with (self.project / "sources" / f"{name}.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=core.SCHEMA)
            writer.writeheader()
            writer.writerows(dict.fromkeys(core.SCHEMA, "") | row for row in rows)

    def qc_ok(self, name, rows):
        folder = core.raw_dir(self.project, name)
        (folder / "qc_report.json").write_text(json.dumps({"relues": rows, "non_verifiables": 0, "mauvaises": 0, "taux_mauvaises": 0.0}), encoding="utf-8")

    def row(self, email, **kwargs):
        base = {"email": email, "entreprise": "Jardins Fictifs", "segment": "paysagiste", "site": "https://jardins-fictifs.fr",
                "email_type": "generique", "source_url": "https://jardins-fictifs.fr/contact", "collected_at": "2026-11-08"}
        return {**base, **kwargs}

    def merge(self, mx=None):
        lookup = mx or (lambda domain: "none" if domain == "sans-mx-fictif.fr" else "ok")
        return merge.run(self.project, self.config, mx_lookup=lookup)

    def test_merge_deduplicates_and_keeps_oldest_date_and_all_proofs(self):
        self.write_source("a", [self.row("contact@jardins-fictifs.fr", prenom="Anne", collected_at="2026-11-08")])
        self.write_source("b", [self.row("CONTACT@jardins-fictifs.fr", prenom="", ville="Lyon", collected_at="2026-10-01",
                                         source_url="https://jardins-fictifs.fr/mentions")])
        self.qc_ok("a", 1)
        self.qc_ok("b", 1)
        contacts, _ = self.merge()
        self.assertEqual(len(contacts), 1)
        row = contacts[0]
        self.assertEqual(row["prenom"], "Anne")
        self.assertEqual(row["ville"], "Lyon")
        self.assertEqual(row["collected_at"], "2026-10-01")
        self.assertEqual(row["nb_sources"], 2)
        self.assertIn(" | ", row["source_url"])

    def test_rejections(self):
        self.write_source("a", [
            self.row("ok@jardins-fictifs.fr"),
            self.row("pas-un-mail"),
            self.row("logo@2x.png"),
            self.row("contact@example.com"),
            self.row("noreply@jardins-fictifs.fr"),
            self.row("rgpd@jardins-fictifs.fr"),
            self.row("sans-preuve@jardins-fictifs.fr", source_url=""),
            self.row("boite@gmail.com", email_type="domaine_perso"),
            self.row("contact@mairie-fictive.gouv.fr"),
            self.row("0612345678@jardins-fictifs.fr"),
            self.row("sans@sans-mx-fictif.fr"),
            self.row("oppose@jardins-fictifs.fr"),
            self.row("autre@domaine-oppose-fictif.fr"),
        ])
        (self.project / "suppression.csv").write_text("email\noppose@jardins-fictifs.fr\n@domaine-oppose-fictif.fr\n", encoding="utf-8")
        self.qc_ok("a", 13)
        contacts, rejected = self.merge()
        self.assertEqual([c["email"] for c in contacts], ["ok@jardins-fictifs.fr"])
        for motif in ("format_invalide", "parasite:fichier", "parasite:exemple", "parasite:noreply", "parasite:rgpd",
                      "sans_preuve_d_origine", "boite_perso_exclue", "organisme_public", "portable_dans_le_mail",
                      "domaine_sans_mx", "liste_opposition"):
            self.assertGreaterEqual(rejected[motif], 1, motif)

    def test_personal_mailboxes_can_be_set_aside_but_never_ready(self):
        self.config["merge"]["personal_mailboxes"] = "flag"
        self.write_source("a", [self.row("boite@gmail.com", email_type="domaine_perso", prenom="Anne", site="")])
        self.qc_ok("a", 1)
        contacts, _ = self.merge()
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0]["pret_campagne"], "non")
        self.assertIn("boite_perso", contacts[0]["a_arbitrer"])

    def test_source_without_qc_is_not_ready(self):
        self.write_source("a", [self.row("contact@jardins-fictifs.fr", prenom="Anne")])
        contacts, _ = self.merge()
        self.assertEqual(contacts[0]["pret_campagne"], "non")
        self.assertIn("qc_absent", contacts[0]["a_arbitrer"])
        self.qc_ok("a", 1)
        contacts, _ = self.merge()
        self.assertEqual(contacts[0]["pret_campagne"], "oui")

    def test_first_name_completion_checks_identity(self):
        (self.project / "data").mkdir(exist_ok=True)
        with (self.project / "data/registre.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["siren", "entreprise", "prenom", "nom"])
            writer.writeheader()
            writer.writerow({"siren": "123456789", "entreprise": "Jardins Fictifs", "prenom": "Claire", "nom": "Fictive"})
            writer.writerow({"siren": "111111111", "entreprise": "Autres Fictifs", "prenom": "Marc", "nom": "Exemple"})
        self.write_source("a", [
            self.row("contact@jardins-fictifs.fr", siren="123456789"),
            self.row("paul@autres-fictifs.fr", siren="111111111", email_type="nominatif", site="https://autres-fictifs.fr"),
        ])
        self.qc_ok("a", 2)
        contacts, _ = self.merge()
        by_email = {c["email"]: c for c in contacts}
        self.assertEqual(by_email["contact@jardins-fictifs.fr"]["prenom"], "Claire")
        self.assertEqual(by_email["contact@jardins-fictifs.fr"]["prenom_source"], "dirigeant_registre")
        self.assertEqual(by_email["paul@autres-fictifs.fr"]["prenom"], "", "une autre personne : pas de prenom du dirigeant")

    def test_judge_rejects_only_above_confidence(self):
        folder = core.raw_dir(self.project, "judge")
        (folder / "verdicts.csv").write_text(
            "domain,statut,choice,confidence,at\n"
            "hors-fictif.fr,ok,hors_cible,0.95,2026-11-08\nmoyen-fictif.fr,ok,hors_cible,0.5,2026-11-08\n", encoding="utf-8")
        self.write_source("a", [
            self.row("contact@hors-fictif.fr", site="https://hors-fictif.fr"),
            self.row("contact@moyen-fictif.fr", site="https://moyen-fictif.fr"),
        ])
        self.qc_ok("a", 2)
        contacts, rejected = self.merge()
        self.assertEqual([c["email"] for c in contacts], ["contact@moyen-fictif.fr"])
        self.assertEqual(rejected["jugement_hors_cible"], 1)

    def test_csv_formula_is_neutralised_and_output_is_private(self):
        self.write_source("a", [self.row("contact@jardins-fictifs.fr", entreprise="=HYPERLINK(\"x\")")])
        self.qc_ok("a", 1)
        contacts, _ = self.merge()
        self.assertFalse(contacts[0]["entreprise"].startswith("="))
        mode = (self.project / "livrable/base_prospects.csv").stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)
        stats = (self.project / "livrable/stats.md").read_text(encoding="utf-8")
        self.assertIn("art. 14", stats)
        self.assertIn("2026-12-08", stats)

    def test_unknown_mailbox_mode_is_refused(self):
        self.config["merge"]["personal_mailboxes"] = "keep"
        with self.assertRaises(core.GuardrailError):
            merge.run(self.project, self.config, mx_lookup=lambda d: "ok")

    def test_mx_uses_dns_only_and_indeterminate_is_rejected_not_cached(self):
        self.write_source("a", [self.row("contact@jardins-fictifs.fr")])
        self.qc_ok("a", 1)
        contacts, rejected = self.merge(mx=lambda domain: "indetermine")
        self.assertEqual(contacts, [])
        self.assertEqual(rejected["mx_indetermine"], 1)
        self.assertEqual(json.loads((self.project / "data/mx_cache.json").read_text(encoding="utf-8")), {})


# --- Lignes de commande ---------------------------------------------------------------------

class CliTests(Base):
    def run_script(self, *args):
        return subprocess.run([sys.executable, "-I", *args], capture_output=True, text=True, cwd=self.project)

    def test_scripts_import_in_isolated_mode_and_dry_run(self):
        project = str(self.project)
        commands = [
            ["read_terms.py", "--project", project, "--source", "x", "--robots-url", "https://fictif.example/robots.txt",
             "--terms-url", "https://fictif.example/cgu", "--dry-run"],
            ["fetch_registry.py", "--project", project, "--dry-run"],
            ["build_domains.py", "--project", project, "--afnic", "liste.csv", "--dry-run"],
            ["crawl_sites.py", "--project", project, "--input", "x.csv", "--name", "y", "--dry-run"],
            ["filter_keyword_sites.py", "--project", project, "--name", "y", "--dry-run"],
            ["open_data.py", "build", "--project", project, "--dry-run"],
            ["qc_sample.py", "sample", "--project", project, "--name", "y", "--dry-run"],
            ["judge_trade.py", "--project", project, "--dry-run"],
            ["merge.py", "--project", project, "--dry-run"],
        ]
        for command in commands:
            with self.subTest(command=command[0]):
                result = self.run_script(str(SCRIPTS / command[0]), *command[1:])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("A blanc", result.stdout)

    def test_crawl_cli_refuses_too_many_connections(self):
        result = self.run_script(str(SCRIPTS / "crawl_sites.py"), "--project", str(self.project), "--input", "x.csv",
                                 "--name", "y", "--workers", "100", "--dry-run")
        self.assertEqual(result.returncode, 2)
        self.assertIn("100 connexions refusees", result.stderr)

    def test_crawl_cli_refuses_a_source_without_review(self):
        (self.project / "x.csv").write_text("domain\nfictif.example\n", encoding="utf-8")
        result = self.run_script(str(SCRIPTS / "crawl_sites.py"), "--project", str(self.project), "--input", "x.csv", "--name", "y")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Aucune requete", result.stderr)

    def test_example_config_is_valid(self):
        config = core.load_config(self.project)
        self.assertTrue(config["registry"]["naf"])
        for regex in ("keywords", "false_friends"):
            re.compile(config["domains"][regex])
        for section in ("hard", "soft"):
            for pattern in config["quality_filter"][section].values():
                re.compile(pattern)


if __name__ == "__main__":
    unittest.main(verbosity=2)
