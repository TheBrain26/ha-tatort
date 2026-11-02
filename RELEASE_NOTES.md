# Release Notes

## 1.0.0 – 02.11.2026

- Erste stabile Version der Tatort-Integration.
- Die Parser-Tests und Praxistests in Home Assistant sind abgeschlossen.
- Die bestehenden Entitäten, der ARD-Abruf und die Dashboard-Beispiele sind in der README dokumentiert.

Nach dem Update Home Assistant neu starten.

## 0.1.7 – 22.10.2026

- ARD-Seite und Vorschau-Metadaten werden bei Abruffehlern bis zu dreimal abgerufen, mit jeweils fünf Sekunden Pause und weiterhin 20 Sekunden Zeitlimit pro Versuch.
- Schlägt der Seitenabruf weiterhin fehl, bleiben die zuletzt erfolgreich geladenen Daten sichtbar.
- Scheitert nur der Metadatenabruf, bleiben Bild und Hinweis erhalten, sofern sie zur selben Folge gehören.
- Fehlermeldungen enthalten den Ausnahmetyp, damit beispielsweise Zeitüberschreitungen erkennbar sind.
- Das reguläre Aktualisierungsintervall bleibt bei sechs Stunden.

Die zwischengespeicherten Daten liegen nur im Arbeitsspeicher und können veraltet sein. Nach einem Neustart ist zunächst ein erfolgreicher Abruf erforderlich. Bei einer neu erkannten Folge wird kein Bild der vorherigen Folge übernommen.

Nach dem Update Home Assistant neu starten.
