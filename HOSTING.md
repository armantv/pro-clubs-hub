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

## Einmalige Einrichtung (ca. 10 Minuten)

### 1. Git installieren (falls noch nicht da)
<https://git-scm.com/download/win> — einfach durchklicken, Standardeinstellungen passen.

### 2. GitHub-Konto + Repository
1. Auf <https://github.com> anmelden (kostenlos).
2. Oben rechts **+** → **New repository** → Name z. B. `pro-clubs-hub` → **Public** → **Create repository**.

### 3. Diesen Ordner hochladen
In diesem Ordner PowerShell öffnen (Shift+Rechtsklick → „PowerShell-Fenster hier öffnen") und
— mit deinem GitHub-Nutzernamen statt `DEINNAME` — eingeben:

```powershell
git remote add origin https://github.com/DEINNAME/pro-clubs-hub.git
git push -u origin main
```

Beim ersten Push öffnet sich ein Anmeldefenster von GitHub — einmal einloggen, fertig.
(Das lokale Git-Repository mit allen Dateien ist hier schon vorbereitet.)

### 4. GitHub Pages einschalten
Im Repository: **Settings → Pages → Branch: `main` / Ordner: `/ (root)` → Save**.
Nach 1–2 Minuten ist die Seite erreichbar unter:

```
https://DEINNAME.github.io/pro-clubs-hub/
```

### 5. Auto-Update aktivieren
Doppelklick auf **`Auto-Update-einrichten.bat`**. Ab jetzt gilt:

- alle 10 Minuten (und kurz nach jeder PC-Anmeldung) holt dein PC unsichtbar frische EA-Daten,
- neue Daten werden automatisch committet und zu GitHub gepusht,
- die gehostete Seite lädt `data.js` ohnehin jede Minute neu — **niemand muss je wieder etwas von Hand machen**.

Kontrolle: `update.log` in diesem Ordner. Abschalten: `Auto-Update-entfernen.bat`.

## Bonus: Cloud-Update ohne PC (optional)

Mit dem Repo wird auch `.github/workflows/update-data.yml` hochgeladen: GitHub selbst
prüft dann alle 10 Minuten **ourproclub.app** auf neue Spiele — das funktioniert auch,
wenn dein PC aus ist. EA direkt kann die Cloud nicht abfragen (geblockt), der volle
EA-Abruf (inkl. Karrierewerte) kommt also weiterhin von deinem PC.
Falls unerwünscht: die Datei einfach löschen.

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
