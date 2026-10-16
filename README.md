# Tatort für Home Assistant

Eine kleine Custom Integration für HACS, die die bisherige Tatort-REST-Konfiguration als Integration in Home Assistant bereitstellt.

## Entitäten

- `sensor.tatort_aktuell` – `verfuegbar` oder `kein_tatort`
- `sensor.tatort_stadt`
- `sensor.tatort_titel`
- `sensor.tatort_ermittler`
- `sensor.tatort_folgen_id`
- `sensor.tatort_bild_api` – Bild-URL für die bestehende Lovelace-Karte

Die Integration ruft die Tatort-Seite und – sofern eine Folgen-ID gefunden wurde – die zugehörigen ARD-Mediathek-Metadaten alle 12 Stunden ab. Die ARD-Mediathek-API ist nicht als öffentliche, stabile API zugesichert. Änderungen an der ARD-Seite oder API können Anpassungen erforderlich machen.

## Installation zum Testen

1. Den Ordner `custom_components/tatort` nach `/config/custom_components/tatort` kopieren.
2. Home Assistant neu starten.
3. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach **Tatort** suchen.

Repository: [TheBrain26/ha-tatort](https://github.com/TheBrain26/ha-tatort).

In HACS unter **⋮ → Benutzerdefinierte Repositories** die Adresse `https://github.com/TheBrain26/ha-tatort` mit dem Typ **Integration** hinzufügen. Danach in HACS nach **Tatort** suchen und installieren. Das Repository muss öffentlich sein, damit HACS darauf zugreifen kann.

### Lovelace-Karte mit Bildvorschau

Unter [examples/tatort_dashboard.yaml](examples/tatort_dashboard.yaml) liegt eine einzelne Markdown-Karte mit dynamischer ARD-Bildvorschau, Titel, Stadt, Ermittler und Verfügbarkeitsstatus. Sie verwendet nur eingebaute Home-Assistant-Karten und benötigt keine Zusatz-Plugins.

Zum Einfügen ein Dashboard bearbeiten, **Karte hinzufügen → Manuell** auswählen und den Inhalt der YAML-Datei einfügen. Falls Home Assistant die Sensoren wegen bereits vorhandener YAML-Entitäten mit abweichenden Entity-IDs angelegt hat, die IDs in der Karte entsprechend anpassen.

## Migration der bestehenden YAML-Sensoren

Zuerst die Integration testweise hinzufügen und die erzeugten Entity-IDs prüfen. Danach die bisherigen Tatort-REST-Sensoren aus der YAML-Konfiguration entfernen, damit keine doppelten Entitäten entstehen. Die Sensor-Namen und eindeutigen Kennungen entsprechen der bisherigen Konfiguration; Home Assistant kann bei schon registrierten REST-Entitäten dennoch Entity-IDs anpassen. Falls nötig, die Entity-IDs in **Einstellungen → Geräte & Dienste → Entitäten** angleichen, damit vorhandene Lovelace-Karten unverändert weiterlaufen.

## Entwicklung

Die HTML- und JSON-Auswertung ist in `custom_components/tatort/parser.py` von Home Assistant entkoppelt und kann mit den Tests unter `tests/` geprüft werden.
