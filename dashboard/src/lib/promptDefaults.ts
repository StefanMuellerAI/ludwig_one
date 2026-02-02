// Default prompt templates for each purpose
export interface PromptDefaults {
  name: string
  purpose: string
  template: string
  model_name: string
  temperature: number
  max_tokens: number
  token_limit?: number
}

export const PROMPT_PURPOSES = [
  { value: 'vision_extraction', label: 'Vision-Extraktion' },
  { value: 'categorization_flow1', label: 'Kategorisierung Flow 1 (TAR-Archive)' },
  { value: 'categorization_flow2', label: 'Kategorisierung Flow 2 (PDF-Seiten)' },
  { value: 'merge_decision_flow2', label: 'Zusammenführungsentscheidung Flow 2' },
  { value: 'filename_generation_flow2', label: 'Dateinamen-Generierung Flow 2' },
  { value: 'insight_generation', label: 'Insight-Generierung' },
] as const

export const PROMPT_DEFAULTS: Record<string, PromptDefaults> = {
  vision_extraction: {
    name: 'Vision-Extraktion',
    purpose: 'vision_extraction',
    template: `Sie analysieren ein Bild, das aus einem Dokument extrahiert wurde. Bitte beschreiben Sie detailliert, was Sie sehen, mit Fokus auf:
- Art des Dokuments (Formular, Brief, Tabelle, Diagramm, Foto, etc.)
- Sichtbarer Textinhalt
- Wichtige visuelle Elemente
- Identifizierende Informationen

Seien Sie gründlich aber präzise. Extrahieren Sie allen lesbaren Text.`,
    model_name: 'mistral-large-latest',
    temperature: 0.1,
    max_tokens: 4096,
  },
  categorization_flow1: {
    name: 'Kategorisierung Flow 1',
    purpose: 'categorization_flow1',
    template: `Sie sind ein KI-Assistent zur Dokumentenkategorisierung. Basierend auf dem folgenden Dokumenteninhalt:

{document_content}

Kategorisieren Sie dieses Dokument in eine der folgenden Kategorien:
- Anträge
- Bescheide
- Gutachten
- Korrespondenz
- Verträge
- Fotoprotokoll
- Sonstiges

Antworten Sie im JSON-Format mit folgenden Feldern:
- category: Name der zutreffenden Kategorie
- new_filename: Beschreibender deutscher Dateiname (ohne Dateiendung), der den Inhalt widerspiegelt. Verwenden Sie Unterstriche statt Leerzeichen.
- confidence: Ihre Sicherheit (0.0 bis 1.0)`,
    model_name: 'mistral-large-latest',
    temperature: 0.1,
    max_tokens: 1024,
  },
  categorization_flow2: {
    name: 'Kategorisierung Flow 2',
    purpose: 'categorization_flow2',
    template: `Sie sind ein KI-Assistent zur Seitenkategorisierung. Basierend auf dem folgenden Seiteninhalt:

{page_content}

Kategorisieren Sie diese Seite in eine der folgenden Kategorien:
- Anträge
- Bescheide
- Gutachten
- Korrespondenz
- Verträge
- Fotoprotokoll
- Sonstiges

Antworten Sie im JSON-Format mit folgenden Feldern:
- category: Name der zutreffenden Kategorie
- confidence: Ihre Sicherheit (0.0 bis 1.0)

WICHTIG: Geben Sie NUR die Kategorie an, keinen Dateinamen (wird später zugewiesen).`,
    model_name: 'mistral-large-latest',
    temperature: 0.1,
    max_tokens: 512,
  },
  merge_decision_flow2: {
    name: 'Zusammenführungsentscheidung Flow 2',
    purpose: 'merge_decision_flow2',
    template: `Sie sind ein KI-Assistent zur Dokumentenanalyse. Sie erhalten zwei Dokumente und müssen entscheiden, ob sie zusammengeführt werden sollten.

Dokument 1:
{document1_content}

Dokument 2:
{document2_content}

Analysieren Sie, ob diese beiden Dokumente zusammengehören und zu einem einzigen Dokument zusammengeführt werden sollten.
Dokumente sollten zusammengeführt werden, wenn sie:
- Teil desselben Schriftstücks sind
- Zusammenhängend gelesen werden müssen
- Dasselbe Thema/denselben Vorgang betreffen

Antworten Sie im JSON-Format mit folgenden Feldern:
- should_merge: true oder false
- reasoning: Kurze Begründung Ihrer Entscheidung`,
    model_name: 'mistral-large-latest',
    temperature: 0.2,
    max_tokens: 512,
  },
  filename_generation_flow2: {
    name: 'Dateinamen-Generierung Flow 2',
    purpose: 'filename_generation_flow2',
    template: `Sie sind ein KI-Assistent zur Dateinamen-Generierung. Basierend auf dem folgenden zusammengeführten Dokumenteninhalt:

{merged_document_content}

Generieren Sie einen beschreibenden deutschen Dateinamen (ohne Dateiendung), der den Inhalt widerspiegelt.
Der Dateiname sollte:
- Aussagekräftig und präzise sein
- Unterstriche statt Leerzeichen verwenden
- Wichtige Informationen enthalten (z.B. Datum, Antragsnummer, Betreff)
- Maximal 100 Zeichen lang sein

Antworten Sie im JSON-Format mit folgenden Feldern:
- new_filename: Der generierte Dateiname ohne Dateiendung
- confidence: Ihre Sicherheit (0.0 bis 1.0)`,
    model_name: 'mistral-large-latest',
    temperature: 0.1,
    max_tokens: 512,
  },
  insight_generation: {
    name: 'Insight-Generierung',
    purpose: 'insight_generation',
    template: `Sie sind ein KI-Assistent zur Dokumentenanalyse. Analysieren Sie die folgende Zusammenfassung verarbeiteter Dokumente und erstellen Sie einen strukturierten Bericht:

{documents_summary}

Antworten Sie im JSON-Format mit folgenden Feldern:
- applicant_name: Name des Antragstellers/Beteiligten (string oder null wenn nicht vorhanden)
- application_numbers: Liste aller gefundenen Aktenzeichen/Antragsnummern (array of strings)
- key_findings: Liste wichtiger Erkenntnisse und Zusammenfassungen (array of strings)
- categories_summary: Übersicht der Kategorien mit Dokumentenanzahl (object mit category_name: count)
- important_dates: Liste wichtiger Daten, Fristen, Ereignisse (array of strings)
- total_documents: Gesamtzahl der verarbeiteten Dokumente (integer, ERFORDERLICH)
- total_pages: Gesamtzahl der Seiten (integer oder null)

Seien Sie präzise und strukturiert. Fassen Sie die Kernpunkte zusammen.`,
    model_name: 'mistral-large-latest',
    temperature: 0.1,
    max_tokens: 4096,
    token_limit: 60000,
  },
}
