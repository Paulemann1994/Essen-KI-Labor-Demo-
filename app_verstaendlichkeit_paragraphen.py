# app_verstaendlichkeit.py – Essen-Branding + großes Sidebar-Logo + Wide-Layout
# + Beispiel-Lader mit exakter Ausrichtung + Textfeld darunter
# + Auto-Anonymisieren + Lesbarkeit + erweiterte Checkliste
# + PII-Guards mit Platzhalter-Ignore
# + Prompt-Patches (Abkürzungen, Zeitzone, Kanal) + Kompakt-Modus + Token-Warnung

import os, re
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from branding import brand_header

# -------------------- Setup --------------------
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

st.set_page_config(page_title="KI-Labor: Verwaltungstexte", layout="wide")
brand_header(
    title="Stadt Essen · KI-Labor",
    subtitle="Verwaltungstexte in 3 Verständlichkeitsstufen",
    logo_path="assets/essen_logo.png",
    color="#004f9f"
)
# --- Demo-Login (liest zuerst Streamlit-Secrets, sonst ENV) ---
def require_demo_login():
    demo_secrets = st.secrets.get("DEMO", {}) if hasattr(st, "secrets") else {}
    DEMO_USER = demo_secrets.get("USER") or os.getenv("DEMO_USER", "")
    DEMO_PASS = demo_secrets.get("PASS") or os.getenv("DEMO_PASS", "")
    if not DEMO_USER or not DEMO_PASS:
        return  # kein Login gefordert

    if not st.session_state.get("auth_ok"):
        with st.sidebar:
            st.markdown("### Demo-Login")
            u = st.text_input("Benutzer", key="demo_user")
            p = st.text_input("Passwort", type="password", key="demo_pass")
            if st.button("Anmelden"):
                if u == DEMO_USER and p == DEMO_PASS:
                    st.session_state["auth_ok"] = True
                else:
                    st.error("Falsche Zugangsdaten.")
        if not st.session_state.get("auth_ok"):
            st.stop()
require_demo_login()
# Großes Logo oben in der Sidebar (falls vorhanden)
with st.sidebar:
    if os.path.exists("assets/essen_logo.png"):
        st.image("assets/essen_logo.png", use_container_width=True)

# -------------------- Sensibilisierung --------------------
with st.expander("🔒 Nutzungs- & Datenschutz-Hinweis (bitte lesen)"):
    st.markdown("""
**Zweck:** Sprachliche **Umschreibhilfe** zur Verständlichkeit. **Keine** Rechtsberatung/-prüfung.

**Bitte NICHT eingeben:**
- Personenbezogene Daten (Name, Adresse, E-Mail, Telefon, Kennzeichen, Aktenzeichen u. Ä.)
- Besondere Kategorien (Gesundheit, Religion, Ethnie, politische Meinung, Gewerkschaft, Biometrie, Sexualleben)
- Straf-/Ordnungswidrigkeitendaten
- Verschlusssachen (z. B. VS-NfD, „Vertraulich“, „Geheim“), dienstliche Geheimnisse
- Geschäftsgeheimnisse Dritter, sicherheitsrelevante Informationen (Passwörter, Zugangsdaten)

**Stattdessen:** anonymisieren (z. B. _[Name]_, _[Az.]_, _[Adresse]_ ) oder generische Beispieltexte verwenden.
""")

# -------------------- Sidebar-Optionen --------------------
with st.sidebar:
    st.header("Einstellungen")
    # statt Multiselect: Checkboxen – ausgeschrieben
    chk_j = st.checkbox("Juristisch präzise", value=True)
    chk_p = st.checkbox("Praxisnah für Mitarbeitende", value=True)
    chk_b = st.checkbox("Bürgernah einfach", value=True)
    variants = [v for v, on in [
        ("Juristisch präzise", chk_j),
        ("Praxisnah für Mitarbeitende", chk_p),
        ("Bürgernah einfach", chk_b),
    ] if on]

    ansprache = st.selectbox("Ansprache", ["Sie-Form", "Du-Form"], index=0)
    creativity = st.slider("Kreativität (temperature)", 0.0, 1.0, 0.2, 0.05)
    max_out = st.slider("Max. Antwortlänge (Tokens)", 200, 1200, 800, 50)
    kompakt = st.checkbox("Kompakt-Modus (knappere Ausgabe)", value=False)
    disclaimer_on = st.checkbox("Hinweis am Ende einfügen", True)

# -------------------- Beispieltexte --------------------
SAMPLE_1 = """Amt für Stadtentwicklung und Bauen – Hinweis zur beabsichtigten Nutzungsänderung einer ehemaligen Lagerhalle in eine multifunktionale Versammlungsstätte.

1) Genehmigungserfordernis
Die Nutzungsänderung bedarf einer Baugenehmigung nach BauO NRW; eine vereinfachte Prüfung scheidet aus, sofern eine Höchstbesucherzahl von > 200 Personen vorgesehen ist (maßgeblich ist der höchste gleichzeitige Personenaufenthalt). Veranstaltungsflächen mit episodischer Nutzung (< 6 Nutzungstage je Kalendermonat) können auf Antrag einer Einzelfallprüfung unterzogen werden; die Entscheidung hierüber erfolgt unter pflichtgemäßem Ermessen.

2) Antragstellung und Form
Der förmliche Antrag ist **spätestens 8 Wochen vor dem beabsichtigten Betriebsbeginn** über das Serviceportal der Stadt einzureichen; die Authentifizierung erfolgt mittels eID. Eine papiergebundene Einreichung ersetzt die digitale Einreichung nicht. Upload je Datei max. 30 MB; Dateiformate: PDF (textbasiert, nicht gescannt), DWG/DXF für Pläne. **Unvollständige Anträge gelten als nicht gestellt.** Nachreichungen sind ausschließlich elektronisch über das Nutzerkonto vorzunehmen.

3) Mindestunterlagen
a) Brandschutzkonzept mit Räumungs- und Alarmierungsplan,
b) Nachweis Barrierefreiheit (u. a. stufenloser Zugang, Sanitär),
c) Schallschutz-/Immissionsprognose (Tag/Abend; Außenbereich berücksichtigen),
d) Stellplatznachweis gemäß örtlicher Satzung bzw. Ablöseerklärung,
e) Betriebskonzept (Hausrecht, Einlasskontrolle, Veranstaltungszeiten, An- und Abreise),
f) Konzept zur Lenkung von Menschenmengen (inkl. Ordnerzahl),
g) Anzeige nach Versammlungsstättenverordnung (sofern einschlägig).

4) Nebenbestimmungen / Koordination
Die Aufnahme des Probebetriebs darf erst **nach** Abnahme der sicherheitsrelevanten Einrichtungen erfolgen. Abweichungen von genehmigten Plänen bedürfen der vorherigen Zustimmung. Eine frühzeitige Beteiligung berührter Träger öffentlicher Belange (TÖB) wird empfohlen; die Federführung liegt beim Amt für Stadtentwicklung und Bauen.

5) Gebühren/Abgaben
Die Gebührenerhebung richtet sich nach dem jeweils gültigen Gebührentarif; die Zahlung erfolgt bargeldlos (z. B. SEPA-Lastschrift, gesonderte Erhebung der IBAN). Bei Rücknahme oder Ablehnung können Gebühren anteilig anfallen.

6) Rechtsbehelf
Gegen Nebenbestimmungen eines Bescheides kann **innerhalb eines Monats** nach Bekanntgabe Widerspruch eingelegt werden. Die Frist beginnt mit dem Tag der Zustellung.

Az. 2025/45-BAU"""

SAMPLE_2 = """Bewilligungsvorbehalt: Leistungen zur Unterkunft und Heizung werden vorläufig festgesetzt. Eine abschließende Entscheidung erfolgt nach Vorlage sämtlicher Nachweise zu Einkommen/Vermögen des Haushalts. **Mitwirkungspflichten** nach §§ 60 ff. SGB I: Fehlende Nachweise sind **innerhalb von 14 Tagen** ab Zugang dieses Schreibens elektronisch über das Postfach im Serviceportal einzureichen; andernfalls kann die Leistung versagt oder entzogen werden. Überzahlungen werden nach § 50 SGB X erstattet. **Änderungsmitteilungen** (Umzug, Haushaltsgröße, Einkommen) sind unverzüglich anzuzeigen. Rechtsbehelfsbelehrung: Gegen diese vorläufige Entscheidung kann **innerhalb eines Monats** Widerspruch erhoben werden.
Az. WOH-2025-00321"""

SAMPLE_3 = """Öffentliche Ausschreibung nach UVgO – Lieferleistung. Angebotsabgabe ausschließlich elektronisch über die eVergabeplattform der Stadt, **Frist: 12:00 Uhr am 24.10.2025**. Bieterfragen bis spätestens 10 Kalendertage vor Ablauf der Frist; Antworten erfolgen ausschließlich über die Plattform. Eignungsnachweis mittels EEE; Eignungsleihe zulässig. **Nebenangebote sind unzulässig.** Zuschlagskriterien: Preis 60 %, Qualität 40 % (Unterkriterien siehe Vergabeunterlagen). Erforderlich: Formblatt 124, Eigenerklärung Tariftreue, Referenzliste. Signaturformat XAdES; Containerformat .zip, max. 80 MB. Angebote per E-Mail oder Papier sind ausgeschlossen.
Az. V-2025-117"""

def _load_sample(choice: str):
    mapping = {
        "Test 1: Nutzungsänderung/Versammlungsstätte": SAMPLE_1,
        "Test 2: Unterkunft & Heizung (SGB)": SAMPLE_2,
        "Test 3: eVergabe/UVgO": SAMPLE_3,
    }
    st.session_state["eingabe"] = mapping.get(choice, "")

# -------------------- Eingabe-Block (Ausrichtung + Textfeld darunter) --------------------
st.subheader("Eingabe")

# Gemeinsame Label-Zeile für perfekte Ausrichtung
lab1, lab2 = st.columns([3, 1])
with lab1:
    st.markdown("**Beispiel auswählen (optional)**")
with lab2:
    st.markdown("&nbsp;")  # optischer Spacer

# Auswahl links, Button rechts – exakt gleiche Linie
col1, col2 = st.columns([3, 1])
with col1:
    sample_choice = st.selectbox(
        "",
        ["— bitte wählen —",
         "Test 1: Nutzungsänderung/Versammlungsstätte",
         "Test 2: Unterkunft & Heizung (SGB)",
         "Test 3: eVergabe/UVgO"],
        label_visibility="collapsed"
    )
with col2:
    st.button("Beispiel laden", on_click=_load_sample, args=(sample_choice,), use_container_width=True)

# Textfeld direkt darunter (außerhalb der Spalten!)
DEFAULT_TEXT = ("Der Antrag ist schriftlich bis spätestens sechs Wochen vor Fristende einzureichen. "
                "Unvollständige Anträge können nicht berücksichtigt werden.")
if "eingabe" not in st.session_state or st.session_state["eingabe"] is None:
    st.session_state["eingabe"] = DEFAULT_TEXT

eingabe = st.text_area(
    "Verwaltungstext eingeben (bitte anonymisieren):",
    key="eingabe",
    height=180,
    placeholder="Text hier einfügen oder über „Beispiel laden“ einsetzen …",
)

# -------------------- Helfer: Anonymisieren / Lesbarkeit / Checkliste --------------------
REPLACEMENTS = {
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}": "[E-Mail]",
    r"\b(?:\+49[\s\-]?)?(?:0\d{2,5}[\s\-]?)\d{3,}\s?\d{2,}\b": "[Telefon]",
    r"\bDE\d{20}\b": "[IBAN]",
    r"\b(0[1-9]|[1-9]\d)\d{3}\b": "[PLZ]",
    r"\b[A-ZÄÖÜ]{1,3}-[A-Z]{1,2}\s?\d{1,4}\b": "[Kfz]",
    r"\bAz\.\s*[A-Za-z0-9\/\-\._]+\b": "[Az.]",
    r"\b(?:Herr|Frau)\s+[A-ZÄÖÜ][a-zäöüß\-]+": "[Name]",
}
def anonymize_text(t: str) -> str:
    out = t
    for pat, token in REPLACEMENTS.items():
        out = re.sub(pat, token, out, flags=re.IGNORECASE)
    return out

def readability_de(t: str):
    sentences = [s for s in re.split(r"[.!?]+", t) if s.strip()]
    words = re.findall(r"\w+", t, re.UNICODE)
    def syl_de(w):
        groups = re.findall(r"[aeiouyäöü]+", w.lower())
        return max(1, len(groups))
    syll = sum(syl_de(w) for w in words) or 1
    asl = len(words) / max(1, len(sentences))
    asw = syll / max(1, len(words))
    fre = 180 - asl - 58.5 * asw
    level = "leicht" if fre >= 90 else "mittel" if fre >= 60 else "anspruchsvoll"
    return round(fre,1), level, len(sentences), len(words)

CHECKS = {
    "Frist erkennbar": r"(bis\s+zum|spätestens|frist|innerhalb\s+von\s+\d+)",
    "Zuständigkeit benannt": r"(zuständig|Ansprechpartner|Kontakt|Amt\s+für)",
    "Aktion klar": r"(beantragen|einreichen|vorlegen|ausfüllen|melden)",
    "Unterlagen erwähnt": r"(Unterlagen|Nachweis|Formular|Beleg|Dokumente)",
}
CHECKS.update({
    "Einreichung über eVergabeplattform": r"(eVergabe|Vergabeplattform)",
    "Andere Wege ausgeschlossen": r"(E-?Mail|Papier).*(ausgeschlossen|nicht.*zulässig|nicht.*erlaubt)",
    "Deadline mit Datum+Uhrzeit": r"\b\d{1,2}\.\d{1,2}\.\d{4}\b.*\b\d{1,2}:\d{2}\b",
    "Bieterfragen-Frist vorhanden": r"Bieterfragen.*\b\d+\s*(Kalendertage|Tage)",
    "Nebenangebote unzulässig": r"Nebenangebote.*(unzulässig|nicht.*erlaubt|nicht.*zulässig)",
    "Zuschlagskriterien Prozent": r"(Preis)\s*\d+\s*%.*(Qualität)\s*\d+\s*%",
    "Dokumentenliste vorhanden": r"(Formblatt\s*124|Tariftreue|Referenzliste)",
    "Signatur/Container/Größe": r"(XAdES|Signatur).*(\.zip|80\s*MB)",
})
def quality_flags(t: str):
    return {label: bool(re.search(pat, t, flags=re.IGNORECASE)) for label, pat in CHECKS.items()}

# PII-Prüfung: echte Muster; Platzhalter vorher entfernen
PII_REGEX = {
    "E-Mail": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "Telefon": r"\b(?:\+49[\s\-]?)?(?:0\d{2,5}[\s\-]?)\d{3,}\s?\d{2,}\b",
    "IBAN (DE)": r"\bDE\d{20}\b",
    "PLZ": r"\b(0[1-9]|[1-9]\d)\d{3}\b",
    "Kfz-Kennzeichen": r"\b[A-ZÄÖÜ]{1,3}-[A-Z]{1,2}\s?\d{1,4}\b",
    "Aktenzeichen (Az.)": r"\bAz\.\s*[A-Za-z0-9\/\-\._]+\b",
}
PLACEHOLDER_TAGS = r"\[(?:E-Mail|Telefon|IBAN|PLZ|Kfz|Az\.)\]"

def find_pii(text: str) -> dict:
    clean = re.sub(PLACEHOLDER_TAGS, "", text, flags=re.IGNORECASE)
    hits = {}
    for label, pat in PII_REGEX.items():
        m = re.findall(pat, clean, flags=re.IGNORECASE)
        if m: hits[label] = len(m)
    return hits

# Session-State safe callbacks
def _anonymize_state():
    st.session_state["eingabe"] = anonymize_text(st.session_state.get("eingabe", ""))

# Drei Helfer-Buttons in einer Zeile (mittlere Spalte etwas breiter)
bcols = st.columns([1, 1.5, 1])
if bcols[0].button("🔍 Lesbarkeit prüfen"):
    fre, level, s, w = readability_de(st.session_state.get("eingabe", ""))
    st.info(f"Lesbarkeit (FRE-DE): **{fre}** · Einstufung: **{level}** · Sätze: {s} · Wörter: {w}")

if bcols[1].button("✅ Qualitäts-Checkliste"):
    flags = quality_flags(st.session_state.get("eingabe", ""))
    st.markdown("**Check:**\n\n" + "\n".join([f"- {'✅' if v else '⚠️'} {k}" for k, v in flags.items()]))

bcols[2].button("🧼 Automatisch anonymisieren", on_click=_anonymize_state)

confirm = st.checkbox("Ich bestätige, dass ich **keine** personenbezogenen Daten, Verschlusssachen oder Geheimnisse eingegeben habe.")

# -------------------- Prompt & LLM --------------------
def build_prompt(text: str) -> str:
    want = "\n".join(f"- {v}" for v in (variants or ["Bürgernah einfach"]))
    hinweis = ("\nHinweis: Dies ist eine sprachliche Umschreibung zur Verständlichkeit und ersetzt keine rechtliche Prüfung."
               if disclaimer_on else "")
    len_rule = "Begrenze jede Variante auf ca. 120–180 Wörter." if kompakt else "Keine harte Längenbegrenzung."
    return f"""
Du bist Sprach- und Verwaltungsexperte. Formuliere den folgenden Verwaltungstext neu.
Gib NUR **Markdown** zurück. Gliedere die Ausgabe mit den Überschriften:

{want}

Vorgaben:
- Behalte ALLE inhaltlichen Angaben unverändert bei (keine neuen Pflichten, nichts weglassen).
- Fristen immer vollständig: **Dauer + Datum + Uhrzeit + Zeitzone (MEZ/MESZ)**.
- Einreichungskanal explizit nennen, falls im Text: **ausschließlich** über die eVergabeplattform (E-Mail/Papier ausgeschlossen).
- Abkürzungen beim ersten Auftreten ausschreiben, z. B.: **UVgO (Unterschwellenvergabeordnung)**, **EEE (Einheitliche Europäische Eigenerklärung)**, **XAdES (XML Advanced Electronic Signatures)**, **TÖB (Träger öffentlicher Belange)**.
- Prozentwerte/Kriterien aus dem Original unverändert übernehmen.
- Verwende die {ansprache}. Kurze Sätze, klare Struktur; in „Praxisnah“ gerne als Checkliste.
- {len_rule}
- Kein Modell-Disclaimer in der Ausgabe; nur, falls unten gefordert.

Text:
\"\"\"{text}\"\"\"

{hinweis}
""".strip()

@st.cache_data(ttl=600, show_spinner=False)
def call_llm(prompt: str, temperature: float, max_tokens: int):
    rsp = client.responses.create(
        model="gpt-4o-mini",
        input=prompt,
        temperature=temperature,
        max_output_tokens=max_tokens,
    )
    out = rsp.output_text
    usage = getattr(rsp, "usage", None)
    in_toks = usage.input_tokens if usage else None
    out_toks = usage.output_tokens if usage else None
    est_cost = (in_toks/1_000_000)*0.60 + (out_toks/1_000_000)*2.40 if (in_toks is not None and out_toks is not None) else None
    return out, in_toks, out_toks, est_cost

# -------------------- Aktion --------------------
if st.button("Text umwandeln", disabled=not confirm):
    text_current = st.session_state.get("eingabe", "").strip()
    if not text_current:
        st.warning("Bitte zuerst einen Text eingeben.")
        st.stop()

    hits = find_pii(text_current)
    if hits:
        st.error("⚠️ Der Text enthält potentiell **personenbezogene** oder vertrauliche Inhalte:")
        st.write(hits)
        st.info("Bitte anonymisieren (z. B. _[Name]_, _[Az.]_, _[Adresse]_ ) und erneut versuchen – oder den Anonymisieren-Button nutzen.")
        st.stop()

    prompt = build_prompt(text_current)
    with st.spinner("Erzeuge Varianten …"):
        try:
            out, in_toks, out_toks, est_cost = call_llm(prompt, creativity, max_out)

            st.markdown("### Ergebnis")
            # Markdown-Rendering -> Umbruch ohne horizontales Scrollen
            st.markdown(out)

            # Kopierfreundliche Rohansicht
            with st.expander("Rohtext anzeigen (kopierbar)"):
                st.text_area("Rohtext", out, height=260)

            # Download
            md = f"# Verwaltungstext – Verständlichkeitsstufen\n\n**Original**\n\n{text_current}\n\n---\n\n{out}\n"
            st.download_button("Ergebnis als Markdown herunterladen", data=md,
                               file_name="verstaendlichkeit.md", mime="text/markdown")

            # Kosten & Token-Hinweis
            if est_cost is not None:
                st.caption(f"Token: in {in_toks}, out {out_toks} · ~Kosten: ${est_cost:.4f}")
                if out_toks == max_out:
                    st.warning("Antwort hat die Token-Obergrenze erreicht – Text könnte abgeschnitten sein. "
                               "Erhöhe 'Max. Antwortlänge' oder aktiviere den Kompakt-Modus.")
        except Exception as e:
            st.error(f"Fehler bei der Anfrage: {e}")
