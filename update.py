# -*- coding: utf-8 -*-
"""
Pro Clubs Hub - Daten-Updater (3 Vereine)
======================================================================
Holt alle Spiele DIREKT von EA fuer alle drei Vereine, baut die volle
Historie lokal zusammen und schreibt sie nach `data.js`. Die Webseite
(index.html) liest diese Datei beim Laden.

Vereine:
  * Katalin FC        (7537035)
  * Cedric sigmas     (1395195)
  * Kepler AllStars   (8343567)

So funktioniert es:
  * EA (Akamai) blockt normale HTTP-Abrufe mit 403. Nur ein echter
    Browser von DEINEM Rechner kommt zuverlaessig durch - darum oeffnet
    sich kurz ein Chromium-Fenster (off-screen positioniert, springt
    nicht ins Bild). Einfach laufen lassen.
  * Zusaetzlich wird ourproclub.app abgefragt - als Bonus, um auch
    aeltere Spiele zu behalten, die aus EAs kurzem Verlaufsfenster
    schon rausgefallen sind. Faellt der Dienst aus, macht das nichts.
  * Neben den Spielen werden EA-Karrierewerte gezogen: Vereinsbilanz
    (overallStats), Spielerwerte (members) und Saison-Historie
    (seasonalStats) - als Snapshot in data.js eingebettet.
  * Alles landet in `matches_store.json` (waechst mit jedem Lauf,
    verliert nie ein Spiel) und wird als `data.js` ausgegeben.
  * Liegt der Ordner in einem Git-Repo mit Remote (z. B. GitHub Pages),
    werden neue Daten automatisch committet und gepusht - die gehostete
    Webseite aktualisiert sich dann von selbst.

Benutzung:
  Doppelklick auf "Daten-aktualisieren.bat"      (manuell, mit Ausgabe)
  python update.py --auto                        (fuer die Aufgabenplanung:
                                                  wartet auf Internet,
                                                  probiert mehrfach, pusht)
  python update.py --cloud                       (nur ourproclub, ohne
                                                  Browser - fuer Server/CI)
  python update.py --no-push                     (nie zu Git pushen)
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

CLUBS = {
    "7537035": "Katalin FC",
    "1395195": "Cedric sigmas",
    "8343567": "Kepler AllStars",
}
PLATFORM = "common-gen5"
HERE = Path(__file__).resolve().parent
STORE_PATH = HERE / "matches_store.json"
DATA_JS_PATH = HERE / "data.js"
LOG_PATH = HERE / "update.log"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# EA legt diese drei Werte nicht als eigenes Feld ab, sondern kodiert sie in
# match_event_aggregate_* (Format "eventId:anzahl,..."). Die IDs wurden ueber
# 36 Spieler-Spiele gegen die dekodierten ourproclub-Werte eindeutig bestaetigt.
EV_DRIBBLES = 174
EV_INTERCEPTIONS = 6
EV_SECOND_ASSISTS = 115

EA_BASE = "https://proclubs.ea.com/api/fc"

# Endpunkte, an denen sich schnell prueft, ob ueberhaupt Internet da ist.
NET_PROBES = (
    "https://www.gstatic.com/generate_204",
    "https://www.msftconnecttest.com/connecttest.txt",
)


def log(line):
    stamped = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {line}"
    try:
        if LOG_PATH.exists() and LOG_PATH.stat().st_size > 400_000:
            tail = LOG_PATH.read_text(encoding="utf-8").splitlines()[-200:]
            LOG_PATH.write_text("\n".join(tail) + "\n", encoding="utf-8")
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(stamped + "\n")
    except Exception:
        pass


def say(line):
    print(line)
    sys.stdout.flush()


# ---------------------------------------------------------------- Netz

def internet_ok(timeout=6):
    for url in NET_PROBES:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            urllib.request.urlopen(req, timeout=timeout)
            return True
        except Exception:
            continue
    return False


def wait_for_internet(max_wait_s):
    """Wartet (poll alle 15 s), bis Internet da ist. True = da."""
    t0 = time.monotonic()
    while True:
        if internet_ok():
            return True
        waited = time.monotonic() - t0
        if waited >= max_wait_s:
            return False
        say(f"  Kein Internet - warte ... ({int(waited)}s/{max_wait_s}s)")
        time.sleep(15)


def http_json(url, timeout=25, retries=2, backoff=4):
    """GET -> JSON mit Wiederholungen. Wirft beim letzten Fehlschlag."""
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Origin": "null"})
            return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8"))
        except Exception as e:
            last = e
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
    raise last


# ---------------------------------------------------------------- Parsing

def parse_agg(p):
    """match_event_aggregate_0..3 -> {eventId(int): summe(int)}"""
    out = {}
    for i in range(4):
        s = p.get(f"match_event_aggregate_{i}", "") or ""
        for tok in s.split(","):
            if ":" in tok:
                k, _, v = tok.partition(":")
                try:
                    out[int(k)] = out.get(int(k), 0) + int(v)
                except ValueError:
                    pass
    return out


def convert_ea_match(m, match_type, club_id, club_name):
    """EA-Match-Objekt -> dasselbe Format, das index.html schon liest
    (player_data je Spielername, match_data.clubs je clubId)."""
    ts = int(m["timestamp"])
    clubs = {}
    for cid, c in m.get("clubs", {}).items():
        clubs[cid] = {
            "goals": str(c.get("goals", "0")),
            "clubName": (c.get("details") or {}).get("name", "Unbekannt"),
            "winnerByDnf": str(c.get("winnerByDnf", "0")),
        }
    player_data = {}
    for _pid, p in m.get("players", {}).get(club_id, {}).items():
        name = p.get("playername", "")
        if not name:
            continue
        agg = parse_agg(p)
        player_data[name] = {
            "mom": str(p.get("mom", "0")),
            "pos": p.get("pos", ""),
            "goals": str(p.get("goals", "0")),
            "saves": str(p.get("saves", "0")),
            "shots": str(p.get("shots", "0")),
            "rating": str(p.get("rating", "0")),
            "assists": str(p.get("assists", "0")),
            "dribbles": agg.get(EV_DRIBBLES, 0),
            "redcards": str(p.get("redcards", "0")),
            "passesmade": str(p.get("passesmade", "0")),
            "archetypeid": str(p.get("archetypeid", "0")),
            "tacklesmade": str(p.get("tacklesmade", "0")),
            "passattempts": str(p.get("passattempts", "0")),
            "cleansheetsgk": str(p.get("cleansheetsgk", "0")),
            "interceptions": agg.get(EV_INTERCEPTIONS, 0),
            "secondAssists": agg.get(EV_SECOND_ASSISTS, 0),
            "secondsPlayed": str(p.get("secondsPlayed", "0")),
            "cleansheetsdef": str(p.get("cleansheetsdef", "0")),
            "tackleattempts": str(p.get("tackleattempts", "0")),
        }
    return {
        "id": ts,
        "club_id": club_id,
        "club_name": club_name,
        "match_type": match_type,
        "match_date": ts,
        "match_data": {"clubs": clubs},
        "player_data": player_data,
    }


# ---------------------------------------------------------------- Quellen

def fetch_ourproclub(club_id):
    """Bonus-Quelle (aeltere Historie). Best effort - Fehler werden geschluckt."""
    url = f"https://api.ourproclub.app/api/match/history?clubId={club_id}&limit=500"
    try:
        data = http_json(url, timeout=25, retries=1)
        if isinstance(data, list):
            return data
    except Exception as e:
        say(f"  (ourproclub nicht erreichbar - egal, EA ist die Hauptquelle: {str(e)[:80]})")
    return []


def fetch_ea_all():
    """Liga-/Playoff-Spiele + Karriere-Snapshots fuer ALLE Vereine.
    Ein Browserfenster, alle Abrufe nacheinander, jeder Abruf mit
    eigenen Wiederholungen."""
    from playwright.sync_api import sync_playwright

    matches = []
    ea_meta = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, args=[
            "--window-position=-2400,-2400", "--window-size=900,700"])
        ctx = browser.new_context(user_agent=UA, locale="en-US")
        page = ctx.new_page()

        def get_json(url, what, tries=3):
            last = None
            for attempt in range(tries):
                try:
                    resp = page.goto(url, wait_until="domcontentloaded", timeout=40000)
                    body = page.evaluate("() => document.body ? document.body.innerText : ''")
                    body = body.strip()
                    if not (body.startswith("[") or body.startswith("{")):
                        raise RuntimeError(
                            f"EA lieferte '{what}' nicht als JSON (HTTP "
                            f"{resp.status if resp else '?'}) - vermutlich vom Schutz geblockt.")
                    return json.loads(body)
                except Exception as e:
                    last = e
                    if attempt < tries - 1:
                        time.sleep(3 * (attempt + 1))
            raise last

        try:
            for cid, cname in CLUBS.items():
                say(f"  {cname} ...")
                for mt in ("leagueMatch", "playoffMatch"):
                    url = (f"{EA_BASE}/clubs/matches?platform={PLATFORM}"
                           f"&clubIds={cid}&matchType={mt}&maxResultCount=50")
                    try:
                        got = get_json(url, f"{cname}/{mt}")
                    except Exception:
                        # Fallback: das alte, garantiert akzeptierte Limit.
                        url20 = url.replace("maxResultCount=50", "maxResultCount=20")
                        got = get_json(url20, f"{cname}/{mt} (Limit 20)")
                    for m in got:
                        matches.append(convert_ea_match(m, mt, cid, cname))
                meta = {"fetchedAt": int(datetime.now().timestamp())}
                # Karriere-Snapshots: best effort, ein Fehler kippt nicht den Lauf
                try:
                    ov = get_json(f"{EA_BASE}/clubs/overallStats?platform={PLATFORM}&clubIds={cid}",
                                  f"{cname}/overallStats")
                    meta["overall"] = ov[0] if isinstance(ov, list) and ov else ov
                except Exception as e:
                    say(f"    (overallStats fehlgeschlagen: {str(e)[:60]})")
                try:
                    mc = get_json(f"{EA_BASE}/members/career/stats?platform={PLATFORM}&clubId={cid}",
                                  f"{cname}/membersCareer")
                    meta["membersCareer"] = mc.get("members", []) if isinstance(mc, dict) else mc
                except Exception as e:
                    say(f"    (membersCareer fehlgeschlagen: {str(e)[:60]})")
                try:
                    ms = get_json(f"{EA_BASE}/members/stats?platform={PLATFORM}&clubId={cid}",
                                  f"{cname}/membersStats")
                    meta["membersStats"] = ms.get("members", []) if isinstance(ms, dict) else ms
                except Exception as e:
                    say(f"    (membersStats fehlgeschlagen: {str(e)[:60]})")
                try:
                    se = get_json(f"{EA_BASE}/clubs/seasonalStats?platform={PLATFORM}&clubIds={cid}",
                                  f"{cname}/seasonalStats")
                    meta["seasonal"] = se[0] if isinstance(se, list) and se else se
                except Exception as e:
                    say(f"    (seasonalStats fehlgeschlagen: {str(e)[:60]})")
                ea_meta[cid] = meta
        finally:
            browser.close()
    return matches, ea_meta


# ---------------------------------------------------------------- Store / Ausgabe

def load_store():
    """Store-Format: {"matches": [...], "ea": {clubId: {...}}}.
    Alte Version war eine flache Liste (nur Katalin) - wird migriert."""
    matches, ea = {}, {}
    if STORE_PATH.exists():
        try:
            raw = json.loads(STORE_PATH.read_text(encoding="utf-8"))
            arr = raw if isinstance(raw, list) else raw.get("matches", [])
            ea = {} if isinstance(raw, list) else raw.get("ea", {})
            for m in arr:
                if "match_date" not in m:
                    continue
                cid = str(m.get("club_id") or "7537035")
                matches[(cid, int(m["match_date"]))] = m
        except Exception:
            pass
    return matches, ea


def write_outputs(store, ea_meta):
    matches = sorted(store.values(), key=lambda m: int(m["match_date"]), reverse=True)
    STORE_PATH.write_text(
        json.dumps({"matches": matches, "ea": ea_meta}, ensure_ascii=False),
        encoding="utf-8")
    now = int(datetime.now().timestamp())
    clubs_out = {}
    for cid, cname in CLUBS.items():
        clubs_out[cid] = {
            "name": cname,
            "matches": [m for m in matches if str(m.get("club_id")) == cid],
            "ea": ea_meta.get(cid, {}),
        }
    payload = json.dumps({"updated": now, "clubs": clubs_out}, ensure_ascii=False)
    js = (f"window.CLUB_DATA = {payload};\n"
          # Rueckwaerts-Kompatibilitaet fuer aeltere Seitenversionen:
          f"window.KATALIN_MATCHES = window.CLUB_DATA.clubs['7537035'].matches;\n"
          f"window.KATALIN_DATA_TS = {now};\n")
    DATA_JS_PATH.write_text(js, encoding="utf-8")


# ---------------------------------------------------------------- Git-Push

def run_git(*args, timeout=90):
    return subprocess.run(
        ["git", *args], cwd=str(HERE), capture_output=True, text=True, timeout=timeout)


def git_autopush():
    """Committet & pusht neue Daten, wenn der Ordner ein Git-Repo mit
    Remote ist. Scheitert leise - der Datenlauf ist dann trotzdem ok.
    Rueckgabe: kurzer Status-Text fuers Log."""
    if not (HERE / ".git").exists():
        return "kein Git-Repo (Push uebersprungen)"
    try:
        remotes = run_git("remote").stdout.split()
        if not remotes:
            return "Git-Repo ohne Remote (Push uebersprungen)"
        run_git("add", "--", "data.js", "matches_store.json")
        if run_git("diff", "--cached", "--quiet").returncode == 0:
            return "keine Datenaenderung (kein Push noetig)"
        msg = f"Daten-Update {datetime.now():%d.%m.%Y %H:%M}"
        c = run_git("commit", "-m", msg)
        if c.returncode != 0:
            return f"Commit fehlgeschlagen: {c.stderr.strip()[:120]}"
        p = run_git("push", timeout=180)
        if p.returncode != 0:
            return f"Push fehlgeschlagen: {p.stderr.strip()[:120]}"
        return "gepusht - gehostete Seite aktualisiert sich"
    except FileNotFoundError:
        return "git nicht installiert (Push uebersprungen)"
    except Exception as e:
        return f"Git-Fehler: {str(e)[:120]}"


# ---------------------------------------------------------------- Ablauf

def collect(auto=False, cloud=False):
    """Ein kompletter Datenlauf. Gibt (store, ea_meta, ea_count) zurueck.
    ea_count = None, wenn EA nicht abrufbar war."""
    store, ea_meta = load_store()
    before = len(store)
    say(f"Gespeicherte Spiele bisher: {before}")

    say("Hole aeltere Historie von ourproclub.app (Bonus) ...")
    for cid, cname in CLUBS.items():
        for m in fetch_ourproclub(cid):
            try:
                mcid = str(m.get("club_id") or cid)
                store[(mcid, int(m["match_date"]))] = m
            except Exception:
                pass
    say(f"  -> {len(store)} Spiele nach ourproclub")

    ea_count = None
    if not cloud:
        say("Hole aktuelle Spiele + Karrierewerte DIREKT von EA")
        say("  (ein Browserfenster oeffnet sich kurz off-screen - einfach warten) ...")
        rounds = 3 if auto else 2
        for attempt in range(rounds):
            try:
                ea_matches, ea_new = fetch_ea_all()
                for m in ea_matches:
                    store[(str(m["club_id"]), int(m["match_date"]))] = m
                ea_meta.update(ea_new)
                ea_count = len(ea_matches)
                break
            except Exception as e:
                say(f"  EA-Abruf fehlgeschlagen (Versuch {attempt + 1}/{rounds}): {str(e)[:120]}")
                log(f"EA-Abruf Versuch {attempt + 1}/{rounds} fehlgeschlagen: {str(e)[:160]}")
                if attempt < rounds - 1:
                    wait_for_internet(120 if auto else 20)
                    time.sleep(5)
    return store, ea_meta, before, ea_count


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="Pro Clubs Hub - Daten-Updater")
    ap.add_argument("--auto", action="store_true",
                    help="Unbeaufsichtigter Lauf (Aufgabenplanung): wartet auf Internet, probiert haerter, pusht.")
    ap.add_argument("--cloud", action="store_true",
                    help="Nur ourproclub.app abfragen, kein Browser/EA (fuer Server/CI).")
    ap.add_argument("--no-push", action="store_true",
                    help="Neue Daten nicht zu Git pushen.")
    args = ap.parse_args()

    say("Pro Clubs Hub - Daten aktualisieren (3 Vereine)")
    say("===============================================")

    if not internet_ok():
        say("Kein Internet - warte auf Verbindung ...")
        if not wait_for_internet(600 if args.auto else 60):
            say("FEHLER: Immer noch kein Internet. Abbruch.")
            log("FEHLER: kein Internet, Lauf abgebrochen")
            return 1

    store, ea_meta, before, ea_count = collect(auto=args.auto, cloud=args.cloud)

    if not store:
        say("FEHLER: Keine einzige Datenquelle erreichbar und kein lokaler Bestand.")
        log("FEHLER: keine Daten (alle Quellen down, Store leer)")
        return 1

    write_outputs(store, ea_meta)
    after = len(store)
    added = after - before
    newest = max((k[1] for k in store), default=0)
    newest_str = datetime.fromtimestamp(newest).strftime("%d.%m.%Y %H:%M") if newest else "-"

    say("\nOK - data.js geschrieben.")
    for cid, cname in CLUBS.items():
        n = sum(1 for k in store if k[0] == cid)
        say(f"  {cname}: {n} Spiele")
    say(f"  Spiele gesamt: {after}  (neu dazu: {added})")
    say(f"  Neuestes Spiel: {newest_str}")

    push_note = ""
    if args.no_push:
        push_note = "Push per --no-push deaktiviert"
    else:
        push_note = git_autopush()
    say(f"  Git: {push_note}")

    ea_note = f"EA lieferte {ea_count}" if ea_count is not None else ("EA uebersprungen (--cloud)" if args.cloud else "EA NICHT erreichbar")
    log(f"OK {after} Spiele (+{added}), neuestes {newest_str}, {ea_note}, Git: {push_note}")
    say("\nFertig." + ("" if args.auto or args.cloud else " Webseite mit Strg+F5 neu laden."))

    # Fuer die Aufgabenplanung zaehlt ein Lauf ohne EA als Fehlschlag,
    # damit man es im Task-Verlauf sieht - Daten wurden trotzdem geschrieben.
    if ea_count is None and not args.cloud:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
