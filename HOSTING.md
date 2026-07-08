# Pro Clubs Hub hosten — Schritt für Schritt

Die Seite ist eine reine statische Webseite (`index.html` + `data.js` + die drei Wappen).
Sie kann kostenlos gehostet werden. **Empfohlen: GitHub Pages**, weil sich die Daten
dann vollautomatisch aktualisieren.

## So greift alles ineinander

```
Dein PC (alle 10 Min, unsichtbar)         GitHub                    Besucher
┌───────────────────────────┐       ┌──────────────────┐      ┌──────────────────┐
│ Aufgabenplanung startet   │       │                  │      │ Webseite lädt    │
│ update.py --auto          │ push  │  GitHub Pages    │      │ data.js alle 60s │
│  → EA-Daten holen         │──────▶│  liefert Seite   │─────▶│ neu → Statistiken│
│  → data.js schreiben      │       │  + data.js aus   │      │ springen von     │
│  → git commit + push      │       │                  │      │ selbst um        │
└───────────────────────────┘       └──────────────────┘      └──────────────────┘
```

EA blockt Server-Abrufe (Akamai-Schutz) — darum holt **dein PC** die Daten
und schiebt sie hoch. Die Seite selbst braucht keinen Server.

## Status: eingerichtet ✅ (08.07.2026)

Alles Folgende ist bereits erledigt:

- **Repository:** <https://github.com/armantv/pro-clubs-hub> (öffentlich)
- **Webseite live:** <https://armantv.github.io/pro-clubs-hub/>
- **Cloud-Update aktiv:** GitHub prüft alle 10 Minuten ourproclub.app auf neue
  Spiele und pusht sie — **auch wenn dein PC aus ist**. Committet wird nur bei
  echten neuen Spielen (plus ein „Heartbeat" alle ~12 h, damit die Frische-Anzeige
  auf der Seite ehrlich bleibt).

**Der einzige offene Handgriff** (einmalig, für die vollen EA-Daten inkl.
Karrierewerte, die die Cloud nicht abrufen kann):

### Auto-Update auf dem PC aktivieren
Doppelklick auf **`Auto-Update-einrichten.bat`**. Ab jetzt gilt:

- alle 10 Minuten (und kurz nach jeder PC-Anmeldung) holt dein PC unsichtbar frische EA-Daten,
- neue Daten werden automatisch committet und zu GitHub gepusht,
- die gehostete Seite lädt `data.js` ohnehin jede Minute neu — **niemand muss je wieder etwas von Hand machen**.

Kontrolle: `update.log` in diesem Ordner. Abschalten: `Auto-Update-entfernen.bat`.

## Cloud-Update ohne PC (läuft bereits)

`.github/workflows/update-data.yml` ist aktiv: GitHub prüft alle 10 Minuten
**ourproclub.app** auf neue Spiele — das funktioniert auch, wenn dein PC aus ist.
EA direkt kann die Cloud nicht abfragen (Akamai blockt Server-IPs), der volle
EA-Abruf (inkl. Karrierewerte und Freundschaftsspiele) kommt von deinem PC,
sobald er läuft. Kontrolle: Repo → **Actions** → „Daten-Update (Cloud)".
Falls unerwünscht: die Datei einfach löschen.

**Hinweis:** GitHub schaltet zeitgesteuerte Workflows nach 60 Tagen ohne
Repo-Aktivität schlafend — die automatischen Daten-Commits zählen als Aktivität,
solange gespielt wird. Nach langer Pause einmal unter Actions auf
„Enable workflow" klicken.

## Alternativen ohne GitHub

- **Netlify Drop** (<https://app.netlify.com/drop>): Ordner per Drag & Drop hochziehen — fertig.
  Nachteil: Daten aktualisieren sich nur, wenn du den Ordner neu hochziehst.
- Jeder beliebige Webspace: `index.html`, `data.js`, `logo_katalin.png`, `logo_cedric.png`,
  `logo_kepler.png` hochladen. Gleicher Nachteil.

## Häufige Fragen

**Muss der PC dafür laufen?** Nur für frische EA-Daten. Die Seite selbst ist immer online.
Ist der PC aus, zeigt sie einfach den letzten Stand (und der Cloud-Updater füllt
ourproclub-Spiele nach).

**Was wird gepusht?** Nur `data.js` und `matches_store.json` — automatische Commits
mit Zeitstempel („Daten-Update 08.07.2026 14:00").

**Push schlägt fehl?** Einmal `git push` von Hand in PowerShell ausführen und die
GitHub-Anmeldung durchklicken — danach läuft es automatisch.
