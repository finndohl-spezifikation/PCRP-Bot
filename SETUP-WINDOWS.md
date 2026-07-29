# SETUP-WINDOWS.md — PCRP-Bot

> Komplettes Erst-Setup für PCRP-Bot-Entwicklung unter Windows.
> Getestete Reihenfolge, alle Befehle copy-paste-fähig.
> Geschrieben, weil das Setup am neuen PC / nach 6 Monaten ohne diese Notiz jedes Mal 2 Stunden kostet.

---

## Voraussetzungen

- Windows 10 oder 11
- PowerShell (in Windows schon dabei)
- Internet für Downloads (~200 MB insgesamt)
- Etwa **30 Minuten** Zeit für die Ersteinrichtung

---

## Schritt 1 — JDK 17 (Microsoft OpenJDK)

```powershell
winget install Microsoft.OpenJDK.17 --accept-package-agreements --accept-source-agreements
```

> PowerShell danach **komplett schließen und neu öffnen**. PATH-Änderungen werden nur beim Session-Start neu geladen — das gleiche gilt für jeden folgenden Install-Schritt.

Test:

```powershell
java -version
# Sollte zeigen: openjdk version "17.0.x" ...
```

---

## Schritt 2 — JAVA_HOME setzen

JAVA_HOME wird vom Maven-Build gebraucht. PowerShell erkennt Java zwar, aber Maven sucht explizit diese Variable.

```powershell
$j = Get-Command java -ErrorAction SilentlyContinue
$jh = Split-Path (Split-Path $j.Source -Parent) -Parent
[Environment]::SetEnvironmentVariable("JAVA_HOME", $jh, "User")
Write-Host "JAVA_HOME = $jh"
```

> PowerShell **wieder** schließen + neu öffnen. JAVA_HOME ist eine Environment-Variable und braucht einen Neustart der Shell.

Erwartete Ausgabe (bei dir kann die JDK-Versionsnummer leicht anders sein):

```
JAVA_HOME = C:\Program Files\Microsoft\jdk-17.0.xx-hotspot
```

> **Achtung:** der Pfad muss auf den JDK-**Root** zeigen (endet auf `-hotspot`), **NICHT** auf den `bin`-Unterordner.

---

## Schritt 3 — Maven 3.9+

**Browser-Download** ist am schnellsten:

1. Browser → <https://maven.apache.org/download.cgi>
2. In der Tabelle **"Binary zip archive"** klicken (z. B. `apache-maven-3.9.16-bin.zip`)
3. Speichern in den Standard-Downloads-Ordner (`C:\Users\finnd\Downloads\`)

PowerShell:

```powershell
Expand-Archive "$HOME\Downloads\apache-maven-3.9.xx-bin.zip" -DestinationPath "$HOME\Downloads"
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$HOME\Downloads\apache-maven-3.9.xx\bin", "User")
```

> PowerShell schließen + neu öffnen.

Test:

```powershell
mvn --version
# Sollte zeigen:
#   Apache Maven 3.9.xx (...)
#   Java version: 17.0.x, vendor: Microsoft, runtime: ...
```

✅ Wenn diese zwei Zeilen passen, ist die Toolchain startklar.

---

## Schritt 4 — Git für Windows

```powershell
winget install Git.Git --accept-package-agreements --accept-source-agreements
```

> Während der Installation fragt Git nach **"Adjusting your PATH environment"** — die **Default-Option belassen** ("Git from the command line and also from 3rd-party software").

PowerShell schließen + neu öffnen.

Test:

```powershell
git --version
# Sollte zeigen: git version 2.55.0.windows.x
```

---

## Schritt 5 — Git-Identity setzen

Ersetze die Platzhalter mit deinen echten Werten:

```powershell
git config --global user.name "Dein Name"
git config --global user.email "deine@email.de"
```

> Ohne diese Werte schlägt jeder `git commit` mit "Author identity unknown" fehl.

---

## Schritt 6 — Git Credential Manager (kein wiederholtes Token-Tippen)

```powershell
git config --global credential.helper manager
```

> Damit speichert Git deinen GitHub-Token sicher im Windows-Credential-Manager. Beim **nächsten** `git push` wirst du **einmal** nach Username + Token gefragt, danach nie wieder.

Optional für noch schnelleres Arbeiten — GitHub CLI:

```powershell
winget install GitHub.cli
gh auth login
```

Damit geht auch `git push` automatisch authentifiziert.

---

## Schritt 7 — Repo klonen

```powershell
cd "C:\Users\finnd\Projects"
git clone https://github.com/finndohl-spezifikation/PCRP-Bot.git
cd PCRP-Bot
```

> Bei der Clone-Frage nach Credentials: GitHub-Username + Personal Access Token (wie in Schritt 6 vorbereitet).

---

## Schritt 8 — Erster Build

```powershell
cd pcrp-bot
mvn package -DskipTests -q
```

> Erster Build dauert **2–3 Minuten** (Maven lädt JDA, Jetty, Gson, … erstmalig aus dem Internet).

Erwartet am Ende:

```
[INFO] BUILD SUCCESS
```

Oder stille Ausgabe, weil `-q` (quiet) den Output unterdrückt. In dem Fall liegt die JAR in `target\pcrp-bot.jar`.

---

## Schritt 9 — Änderungen deployen (Standard-Workflow)

```powershell
# 1. Bauen
cd pcrp-bot
mvn package -DskipTests -q
cd ..

# 2. Git: was hat sich geändert?
git status

# 3. Stage (Beispiel, an deine Files anpassen!)
git add pcrp-bot\src\main\java\de\pcrp\bot\common\LoggingConfig.java `
            pcrp-bot\src\main\java\de\pcrp\bot\common\InventoryManager.java `
            pcrp-bot\src\main\java\de\pcrp\bot\Main.java

# 4. Commit
git commit -m "Beschreibung der Änderung"

# 5. Push
git push -u origin main
```

> Railway baut **automatisch** in 1–3 Minuten. Discord-Bot ist live.

---

## Häufige PowerShell-Stolperfallen

| Was du tippst (cmd.exe-Style) | Was passiert | PowerShell-Equivalent |
|---|---|---|
| `copy a b /Y` | **Fehler**: "/Y" wird nicht akzeptiert | `Copy-Item a b -Force` oder `cp a b` |
| `git log \| head -10` | **Fehler**: "head" nicht gefunden | `git log \| Select-Object -First 10` |
| `git log \| grep foo` | **Fehler**: "grep" nicht gefunden | `git log \| Select-String foo` |
| `cp -r src dst` | **Fehler**: "-r" nicht akzeptiert | `Copy-Item src dst -Recurse` |
| `rm -rf foo` | **Fehler**: keine "-rf"-Option | `Remove-Item foo -Recurse -Force` |
| `mkdir foo` | funktioniert | `mkdir foo` oder `New-Item -ItemType Directory -Name foo` |

> **Faustregel:** PowerShell bevorzugt **verb-noun** statt nur **verb** (`Copy-Item`, `Remove-Item`, `Get-ChildItem`, `Set-Location`), und Flags sind typischerweise `-Force`, `-Recurse` statt `/Y`, `/S`, `/Q`.

---

## Typische Anfänger-Probleme und Fixes

### PowerShell reagiert nicht auf neue PATH-Variable

→ PowerShell **komplett schließen + neu öffnen**. PATH wird nur beim Session-Start geladen.

### `mvn` findet Java nicht: "JAVA_HOME environment variable is not defined correctly"

→ JAVA_HOME zeigt auf den falschen Pfad (z. B. `bin`-Unterordner statt JDK-Root). Fix:

```powershell
[Environment]::SetEnvironmentVariable("JAVA_HOME", "C:\Program Files\Microsoft\jdk-17.0.xx-hotspot", "User")
```

### `git push` fragt nach Username/Password

→ Bei GitHub wird **nicht** dein Account-Passwort akzeptiert, sondern ein **Personal Access Token**.

Schnell-Flow auf github.com:
1. <https://github.com/settings/personal-access-tokens/new>
2. Token-Name: z. B. `PCRP-Bot Push`
3. Resource owner: dein Account
4. Repository: **Only select** → `PCRP-Bot`
5. Permissions → **Contents: Read and write**
6. Generate → Token kopieren → im PowerShell als Passwort einfügen

### Großer Copy-Paste aus dem Chat hat Zeilen verklebt

→ Im PowerShell siehst du `>>` als Continuation-Prompt oder einen verstümmelten Befehl. **Ctrl+C** drücken, dann den Block **eine Zeile nach der anderen** pasten.

### `git pull --rebase` blockiert wegen untracked Files

→ Dein lokaler Working Tree hat Dateien, die das Remote auch enthält (z. B. Config-Files). Lösung:

```powershell
# NUR die modifizierten Java-Files lokal sichern
# (vorher in einen Backup-Ordner kopieren)
md C:\PCRP-Backup
copy pcrp-bot\src\main\java\de\pcrp\bot\*.java C:\PCRP-Backup\
copy pcrp-bot\src\main\java\de\pcrp\bot\common\*.java C:\PCRP-Backup\
copy pcrp-bot\src\main\java\de\pcrp\bot\listeners\*.java C:\PCRP-Backup\

# Remote komplett reinholen, eigene Änderungen darüber legen
git fetch origin main
git reset --hard origin/main
Copy-Item C:\PCRP-Backup\*.java pcrp-bot\src\main\java\de\pcrp\bot\ -Recurse -Force
# ... + an gleicher Pfad-Struktur wieder einsortieren

git add <deine files>
git commit -m "..."
git push -u origin main
```

Oder eleganter: **frisches Clone** statt `git pull`:

```powershell
cd ..
rmdir /s /q PCRP-Bot   # oder: Remove-Item -Recurse -Force
git clone https://github.com/finndohl-spezifikation/PCRP-Bot.git
# Modifizierte Files aus dem Backup zurückkopieren
```

---

## Hilfe

Wenn etwas schiefgeht: **ganze Fehlermeldung** kopieren (inkl. der letzten 10 Zeilen, falls Stack-Trace), und idealerweise mit Schritt-Nummer wo es passiert ist. Lieber eine Frage zu viel als eine Stunde Debug.

Discord-Probleme direkt im **`#support`**-Kanal des Servers besprechen. Railway-Build-Failures im Reiter **Deployments → Logs** des jeweiligen Builds prüfen.
