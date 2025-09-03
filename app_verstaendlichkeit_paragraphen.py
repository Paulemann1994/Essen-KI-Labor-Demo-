# app_verstaendlichkeit_paragraphen.py
# Stadt Essen · KI-Labor – Verwaltungstexte in 3 Verständlichkeitsstufen
# Sidebar-Hilfe & Impressum · Wort/Zeichen-Zähler · Verlauf · Diff · optionaler PDF-Export
# NEU: Demo-/Prototyp-Hinweis als blauer Banner direkt unter dem Header

import os, re, difflib, io
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from branding import brand_header

# Optional: PDF-Export (falls lib vorhanden)
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

# -------------------- Setup & API-Key --------------------
st.set_page_config(page_title="KI-Labor: Verwaltungstexte", layout="wide")
load_dotenv()

def get_api_key():
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    try:
        key = (st.secrets.get("general", {}) or {}).get("OPENAI_API_KEY")
        if key:
            return key
        key = st.secrets.get("OPENAI_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return None

api_key = get_api_key()
if not api_key:
    st.error(
        "OPENAI_API_KEY nicht gefunden. Bitte in **Settings → Secrets** setzen.\n\n"
        "Beispiel (TOML):\n\n"
        "[general]\nOPENAI_API_KEY = \"sk-…\"\n\n[DEMO]\nUSER = \"essen-demo\"\nPASS = \"gutertext2025\"\n\nDEMO_MODE = \"1\""
    )
    st.stop()

client = OpenAI(api_key=api_key)

# -------------------- Branding-Header --------------------
PRIMARY = "#004f9f"
brand_header(
    title="Stadt Essen · KI-Labor",
    subtitle="Verwaltungstexte in 3 Verständlichkeitsstufen",
    logo_path="assets/essen_logo.png",
    color=PRIMARY,
)

# NEU: Blauer Hinweisbanner direkt unter dem Header
st.markdown(
    f"""
    <div style="
      background:{PRIMARY};
      color:#fff;
      padding:8px 14px;
      border-radius:10px;
      margin-top:-8px;
      margin-bottom:14px;
      font-size:0.95rem;
      line-height:1.35;
      display:flex;
      gap:10px;
      flex-wrap:wrap;">
      <span style="font-weight:700;">Demo · intern · Stadt Essen – KI-Labor</span>
      <span>Diese Anwendung ist ein Prototyp und ersetzt keine Rechts- oder Fachprüfung.</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Demo-Login (optional über Secrets aktivierbar)
def require_demo_login():
    demo_secrets = st.secrets.get("DEMO", {}) if hasattr(st, "secrets") else {}
    DEMO_USER = demo_secrets.get("USER") or os.getenv("DEMO_USER", "")
    DEMO_PASS = demo_secrets.get("PASS") or os.getenv("DEMO_PASS", "")
    if not DEMO_USER or not DEMO_PASS:
        return
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

# -------------------- Hilfe & Impressum (Sidebar) --------------------
with st.sidebar:
    st.markdown("### Hilfe & Impressum")

    with st.expander("❓ Hilfe – Kurzüberblick", expanded=False):
        st.markdown("""
**Was macht dieses Tool?**  
Es formuliert amtliche Texte sprachlich um – **ohne** Inhalte/Fristen zu verändern – und erzeugt drei Varianten:
- *Juristisch präzise*
- *Praxisnah für Mitarbeitende*
- *Bürgernah einfach*

**So geht’s**
1. Optional ein **Beispiel** wählen → **Beispiel laden**.  
2. **🧼 Automatisch anonymisieren** (keine realen PII verwenden).  
3. Checkbox bestätigen → **Text umwandeln**.

**Nicht eingeben:** PII, besondere Kategorien, Verschlusssachen, Geheimnisse Dritter (siehe Hinweisbox).
""")

    with st.expander("ℹ️ Impressum (Demo/PoC)", expanded=False):
        st.markdown("""
**Stadt Essen – [Fachbereich / OE]**  
[Straße Nr.], [PLZ Ort]  
E-Mail: [kontakt@example.de] · Tel.: [0201 / …]

**Verantwortlich für den Inhalt:** [Name, Funktion]  
**Datenschutz:** Keine produktiven personenbezogenen Daten eingeben.  
**Hinweis:** Demoversion ausschließlich für interne Tests.
""")

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
... (gekürzt; gleicher Inhalt wie zuvor) ...
Az. 2025/45-BAU"""
SAMPLE_2 = """Bewilligungsvorbehalt: Leistungen zur Unterkunft und Heizung werden vorläufig festgesetzt. ...
Az. WOH-2025-00321"""
SAMPLE_3 = """Öffentliche Ausschreibung nach UVgO – Lieferleistung. ...
Az. V-2025-117"""

def _load_sample(choice: str):
    mapping = {
        "Test 1: Nutzungsänderung/Versammlungsstätte": SAMPLE_1,
        "Test 2: Unterkunft & Heizung (SGB)": SAMPLE_2,
        "Test 3: eVergabe/UVgO": SAMPLE_3,
    }
    st.session_state["eingabe"] = mapping.get(choice, "")

# -------------------- Eingabe-Block --------------------
st.subheader("Eingabe")

lab1, lab2 = st.columns([3, 1])
with lab1:
    st.markdown("**Beispiel auswählen (optional)**")
with lab2:
    st.markdown("&nbsp;")

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

# Live-Zähler
def _count_words_chars(text: str):
    words = re.findall(r"\w+", text, re.UNICODE)
    return len(words), len(text)
wcount, ccount = _count_words_chars(st.session_state.get("eingabe", ""))
st.caption(f"Wörter: {wcount} · Zeichen: {ccount}")

# -------------------- Helfer-Tools --------------------
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

def _anonymize_state():
    st.session_state["eingabe"] = anonymize_text(st.session_state.get("eingabe", ""))

# Drei Helfer-Buttons in einer Zeile
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
\"\"\"{text}\"\"\"\n
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

# -------------------- PDF-Export (optional) --------------------
def build_pdf_bytes(title: str, original: str, output_md: str, logo_path: str = "assets/essen_logo.png") -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 2*cm
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, x=2*cm, y=y-1.6*cm, width=2.2*cm, height=1.6*cm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    c.setFont("Helvetica-Bold", 14); c.drawString(4.6*cm, y, title)
    c.setFont("Helvetica", 9); c.drawRightString(width-2*cm, y, datetime.now().strftime("%d.%m.%Y %H:%M"))
    y -= 1.2*cm
    c.setFont("Helvetica-Bold", 11); c.drawString(2*cm, y, "Original"); y -= 0.5*cm
    c.setFont("Helvetica", 10)
    for para in (original or "").split("\n"):
        y = _pdf_wrapped_line(c, para, y, width)
    y -= 0.6*cm
    c.setFont("Helvetica-Bold", 11); c.drawString(2*cm, y, "Umschreibung"); y -= 0.5*cm
    c.setFont("Helvetica", 10)
    for para in (output_md or "").split("\n"):
        y = _pdf_wrapped_line(c, para, y, width)
    c.showPage(); c.save(); buf.seek(0)
    return buf.read()

def _pdf_wrapped_line(c, text, y, page_w):
    from reportlab.lib.pagesizes import A4
    left, right = 2*cm, page_w - 2*cm
    max_w = right - left
    if y < 3*cm:
        c.showPage(); y = A4[1] - 2*cm; c.setFont("Helvetica", 10)
    words, line = text.split(" "), ""
    for w in words:
        probe = (line + " " + w).strip()
        if c.stringWidth(probe, "Helvetica", 10) <= max_w:
            line = probe
        else:
            c.drawString(left, y, line); y -= 0.42*cm; line = w
            if y < 3*cm:
                c.showPage(); y = A4[1]-2*cm; c.setFont("Helvetica", 10)
    if line:
        c.drawString(left, y, line); y -= 0.42*cm
    return y

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
            st.markdown(out)

            with st.expander("Vorher/Nachher – Diff (Text)"):
                diff = difflib.unified_diff(
                    text_current.splitlines(),
                    out.splitlines(),
                    fromfile="Original",
                    tofile="Umschreibung",
                    lineterm=""
                )
                st.code("\n".join(diff), language="diff")

            with st.expander("Rohtext anzeigen (kopierbar)"):
                st.text_area("Rohtext", out, height=260)

            md = f"# Verwaltungstext – Verständlichkeitsstufen\n\n**Original**\n\n{text_current}\n\n---\n\n{out}\n"
            st.download_button("Ergebnis als Markdown herunterladen", data=md,
                               file_name="verstaendlichkeit.md", mime="text/markdown")

            if REPORTLAB_OK:
                pdf_bytes = build_pdf_bytes(
                    title="Stadt Essen · KI-Labor – Verwaltungstexte",
                    original=text_current,
                    output_md=out,
                    logo_path="assets/essen_logo.png"
                )
                st.download_button("Ergebnis als PDF herunterladen", data=pdf_bytes,
                                   file_name="verstaendlichkeit.pdf", mime="application/pdf")
            else:
                st.button("Ergebnis als PDF herunterladen (ReportLab fehlt)", disabled=True,
                          help="Füge 'reportlab' in requirements.txt hinzu, um PDF zu aktivieren.")

            if est_cost is not None:
                st.caption(f"Token: in {in_toks}, out {out_toks} · ~Kosten: ${est_cost:.4f}")
                if out_toks == max_out:
                    st.warning("Antwort hat die Token-Obergrenze erreicht – Text könnte abgeschnitten sein. "
                               "Erhöhe 'Max. Antwortlänge' oder aktiviere den Kompakt-Modus.")

            hist = st.session_state.get("history", [])
            hist.insert(0, {
                "ts": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "original": text_current,
                "output": out,
                "settings": {
                    "variants": variants, "ansprache": ansprache,
                    "temp": creativity, "max_out": max_out, "kompakt": kompakt
                }
            })
            st.session_state["history"] = hist[:3]
        except Exception as e:
            st.error(f"Fehler bei der Anfrage: {e}")

# -------------------- Verlauf (Sidebar) --------------------
with st.sidebar:
    st.markdown("---")
    st.markdown("### Verlauf (Session)")
    hist = st.session_state.get("history", [])
    if not hist:
        st.caption("Noch keine Ergebnisse in dieser Sitzung.")
    else:
        labels = [f"{i+1}. {item['ts']} – {', '.join(item['settings']['variants'] or ['Bürgernah'])}" for i, item in enumerate(hist)]
        pick = st.selectbox("Ergebnis auswählen", options=list(range(len(hist))), format_func=lambda i: labels[i])
        if st.button("Ausgewähltes Ergebnis anzeigen"):
            st.session_state["preview"] = hist[pick]

if st.session_state.get("preview"):
    st.markdown("### Vorschau aus Verlauf")
    st.markdown(st.session_state["preview"]["output"])

# -------------------- Footer --------------------
st.markdown("---")
st.caption("Demo · intern · Stadt Essen – KI-Labor · Diese Anwendung ist ein Prototyp und ersetzt keine Rechts- oder Fachprüfung.")